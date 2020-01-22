import telegram
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from kidsclub_bot.models import BotMessage, Person, InviteIntent, Location, PersonMeeting, PersonKid

#
# Common date for callbacks
#

KID_MALE = 'kid_male'
KID_FEMALE = 'kid_female'

kid_sex_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Мальчик', callback_data=KID_MALE),
        InlineKeyboardButton('Девочка', callback_data=KID_FEMALE),
    ]
])

START_REGISTER = '0'
AGREE_TO_PARTY = 'lets_party'
DECLINE_TO_PARTY = 'decline_party'

want_to_party_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Участвую', callback_data=AGREE_TO_PARTY),
        InlineKeyboardButton('Не участвую', callback_data=DECLINE_TO_PARTY),
    ]
])

FEEDBACK_GOOD = 'meet_good'
FEEDBACK_BAD = 'meet_bad'
FEEDBACK_NOT_MET = 'meet_not_met'


def get_user_feedback_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Хорошо', callback_data=f'{FEEDBACK_GOOD}|{user_id}'),
            InlineKeyboardButton('Плохо', callback_data=f'{FEEDBACK_BAD}|{user_id}'),
        ],
        [InlineKeyboardButton('Не встретились', callback_data=f'{FEEDBACK_NOT_MET}|{user_id}')]
    ])


#
# Start handler
#

AVAILABLE_LOCATIONS = list(Location.objects.values_list('name', flat=True))


def send_greeting_text(update, context):
    update.message.reply_text(
        BotMessage.objects.get(type=BotMessage.MessageTypes.USER_WELCOME).text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Регистрация', callback_data=START_REGISTER)]
        ])
    )


start_handler = CommandHandler('start', send_greeting_text)
help_handler = CommandHandler('help', send_greeting_text)

WAIT_FOR_NAME, WAIT_FOR_KID_AMOUNT, WAIT_FOR_KID_AGE, WAIT_FOR_KID_SEX, WAIT_FOR_SOCIAL, WAIT_FOR_CITY = range(6)


def register_button_and_name_handler(update, context):
    """
    Ask for name
    """
    user, created = Person.objects.get_or_create(
        tg_id=update.effective_user.id,
        tg_username=update.effective_user.username,
    )

    ask_for_name = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_NAME)

    user.username = update.effective_user.first_name
    user.save()

    PersonKid.objects.filter(person=user).delete()

    update.effective_message.reply_text(ask_for_name.text)

    return WAIT_FOR_NAME


def record_name_ask_kid_amount(update, context):
    text = update.message.text

    user = Person.objects.get(tg_id=update.effective_user.id)
    user.username = text
    user.save()

    ask_for_about = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_KID_AMOUNT)

    update.message.reply_text(ask_for_about.text)

    return WAIT_FOR_KID_AMOUNT


def record_kid_amount_start_kid_loop(update, context):
    try:
        kid_amount = int(update.message.text)
    except ValueError:
        type_number_error = BotMessage.objects.get(type=BotMessage.MessageTypes.NUMBER_INPUT_ERROR)
        update.message.reply_text(type_number_error.text)
        return WAIT_FOR_KID_AMOUNT

    user = Person.objects.get(tg_id=update.effective_user.id)
    user.kid_amount = kid_amount
    user.save()

    return ask_kid_age(update, context)


KID_AMOUNT_VERBOSE = {
    1: '',
    2: ['младшему', 'старшему'],
    3: ['младшему', 'среднему', 'старшему'],
    4: ['младшему', 'среднему', 'старшему', 'самому старшему'],
    5: ['самому младшему', 'младшему', 'среднему', 'старшему', 'самому старшему'],
}


def ask_kid_age(update, context):
    user = Person.objects.get(tg_id=update.effective_user.id)
    max_kid = PersonKid.objects.filter(person=user).order_by('-kid_seg_number').first()

    if max_kid is None:
        max_kid = PersonKid.objects.create(person=user, kid_seg_number=0)
    elif max_kid.kid_seg_number + 1 >= user.kid_amount:
        return ask_person_location(update, context)
    else:
        max_kid = PersonKid.objects.create(person=user, kid_seg_number=max_kid.kid_seg_number + 1)

    try:
        verbose_age = KID_AMOUNT_VERBOSE[user.kid_amount][max_kid.kid_seg_number]
    except Exception:
        verbose_age = ''

    kid_age_text = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_KID_AGE)
    update.effective_message.reply_text(kid_age_text.text.format(verbose_age))

    return WAIT_FOR_KID_AGE


def record_age_ask_sex(update, context):
    try:
        kig_age = int(update.message.text)
    except ValueError:
        type_number_error = BotMessage.objects.get(type=BotMessage.MessageTypes.NUMBER_INPUT_ERROR)
        update.message.reply_text(type_number_error.text)
        return WAIT_FOR_KID_AGE

    user = Person.objects.get(tg_id=update.effective_user.id)
    max_kid = PersonKid.objects.filter(person=user).order_by('-kid_seg_number').first()
    max_kid.age = kig_age
    max_kid.save()

    kig_sex_text = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_KID_SEX)
    update.message.reply_text(kig_sex_text.text, reply_markup=kid_sex_keyboard)
    return WAIT_FOR_KID_SEX


def record_sex_ask_age(update, context):
    sex_data = update.callback_query.data
    user = Person.objects.get(tg_id=update.effective_user.id)

    max_kid = PersonKid.objects.filter(person=user).order_by('-kid_seg_number').first()
    max_kid.sex = PersonKid.Sex.MALE if sex_data == KID_MALE else PersonKid.Sex.FEMALE
    max_kid.save()

    return ask_kid_age(update, context)


def ask_person_location(update, context):
    ask_for_city = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_CITY)
    n = 3
    packed_locations = [AVAILABLE_LOCATIONS[i:i + n] for i in range(0, len(AVAILABLE_LOCATIONS), n)]
    markup = ReplyKeyboardMarkup(packed_locations, resize_keyboard=True, one_time_keyboard=True)

    update.effective_message.reply_text(ask_for_city.text, reply_markup=markup)
    return WAIT_FOR_CITY


def record_location_ask_social(update, context):
    text = update.message.text
    location = Location.objects.filter(name=text).get()

    user = Person.objects.get(tg_id=update.effective_user.id)
    user.location = location
    user.save()

    text_obj = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_SOCIAL)
    update.message.reply_text(text_obj.text)
    return WAIT_FOR_SOCIAL


def record_social_register_end(update, context):
    user = Person.objects.get(tg_id=update.effective_user.id)
    user.social_networks = update.message.text
    user.save()

    text_obj = BotMessage.objects.get(type=BotMessage.MessageTypes.PROFILE_SAVED)
    update.message.reply_text(text_obj.text)

    if not update.effective_user.username:
        username_not_set_text = BotMessage.objects.get(type=BotMessage.MessageTypes.USERNAME_NOT_SET)
        update.effective_message.reply_text(
            username_not_set_text.text, parse_mode=telegram.ParseMode.MARKDOWN
        )

    return ConversationHandler.END


def try_again(update, context):
    update.message.reply_text("Что-то пошло не так, нажмите на кнопку Регистрация снова")


reg_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(register_button_and_name_handler, pattern=f'^{START_REGISTER}$')
    ],
    states={
        WAIT_FOR_NAME: [MessageHandler(Filters.text, record_name_ask_kid_amount)],
        WAIT_FOR_KID_AMOUNT: [MessageHandler(Filters.text, record_kid_amount_start_kid_loop)],

        WAIT_FOR_KID_AGE: [MessageHandler(Filters.text, record_age_ask_sex)],
        WAIT_FOR_KID_SEX: [CallbackQueryHandler(record_sex_ask_age, pattern=f'^({KID_MALE}|{KID_FEMALE})$')],

        WAIT_FOR_CITY: [
            MessageHandler(Filters.regex(f"^({'|'.join(AVAILABLE_LOCATIONS)})$"), record_location_ask_social)
        ],
        WAIT_FOR_SOCIAL: [MessageHandler(Filters.text, record_social_register_end)],
    },
    fallbacks=[MessageHandler(Filters.text, try_again)],
)


#
# Invite intent handling
#


def set_invite_intent(update, context):
    person = Person.objects.filter(tg_id=update.effective_user.id).get()
    if not update.effective_user.username:
        username_not_set_text = BotMessage.objects.get(type=BotMessage.MessageTypes.USERNAME_NOT_SET)
        update.effective_message.reply_text(
            username_not_set_text.text, parse_mode=telegram.ParseMode.MARKDOWN
        )
        return
    else:
        person.tg_username = update.effective_user.username
        person.save()

    q = InviteIntent.objects.filter(
        person_id=update.effective_user.id,
        is_deleted=False,
    )

    if update.callback_query.data == AGREE_TO_PARTY:
        q.update(is_user_agreed=True)
        reply_text = BotMessage.objects.get(type=BotMessage.MessageTypes.INVITE_CONFIRMED).text
    else:
        q.update(is_user_agreed=False)
        reply_text = BotMessage.objects.get(type=BotMessage.MessageTypes.INVITE_DECLINED).text

    update.effective_message.reply_text(reply_text)


invite_intent_handler = CallbackQueryHandler(set_invite_intent, pattern=f'^({AGREE_TO_PARTY}|{DECLINE_TO_PARTY})$')

#
# Collect feedback
#

WAIT_FOR_REASON = range(1)


def collect_feedback_handler(update, context):
    data, to_person_id = update.callback_query.data.split('|')
    pm = PersonMeeting.objects.filter(
        from_person_id=update.effective_user.id,
        to_person_id=int(to_person_id),
    ).get()

    context.user_data['to_person_id'] = to_person_id

    if data == FEEDBACK_GOOD:
        pm.rate = PersonMeeting.MeetingRate.GOOD
        pm.save()

        reply_text = BotMessage.objects.get(type=BotMessage.MessageTypes.FEEDBACK_GOOD).text
        update.effective_message.reply_text(reply_text)
        return ConversationHandler.END

    elif data == FEEDBACK_BAD:
        pm.rate = PersonMeeting.MeetingRate.BAD
        reply_text = BotMessage.objects.get(type=BotMessage.MessageTypes.FEEDBACK_BAD).text
    else:
        pm.rate = PersonMeeting.MeetingRate.NOT_MET
        reply_text = BotMessage.objects.get(type=BotMessage.MessageTypes.FEEDBACK_NOT_MET).text

    pm.save()
    update.effective_message.reply_text(reply_text)
    return WAIT_FOR_REASON


def record_feedback_reason(update, context):
    to_person_id = context.user_data['to_person_id']
    pm = PersonMeeting.objects.filter(
        from_person_id=update.effective_user.id,
        to_person_id=int(to_person_id),
    ).get()
    pm.review = update.effective_message.text
    pm.save()

    reply_text = BotMessage.objects.get(type=BotMessage.MessageTypes.FEEDBACK_REASON_COLLECTED).text
    update.effective_message.reply_text(reply_text)

    return ConversationHandler.END


collect_feedback_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(collect_feedback_handler, pattern=f'^({FEEDBACK_GOOD}|{FEEDBACK_BAD}|{FEEDBACK_NOT_MET})')
    ],
    states={
        WAIT_FOR_REASON: [MessageHandler(Filters.text, record_feedback_reason)],
    },
    fallbacks=[MessageHandler(Filters.text, try_again)],
)
