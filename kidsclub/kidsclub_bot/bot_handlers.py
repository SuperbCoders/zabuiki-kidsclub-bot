import telegram
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from kidsclub_bot.models import BotMessage, Person, InviteIntent, Location, PersonMeeting

#
# Common date for callbacks
#

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

WAIT_FOR_NAME, WAIT_FOR_ABOUT, WAIT_FOR_SOCIAL, WAIT_FOR_CITY = range(4)


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

    update.effective_message.reply_text(ask_for_name.text)

    return WAIT_FOR_NAME


def record_name_ask_about(update, context):
    text = update.message.text

    user = Person.objects.get(tg_id=update.effective_user.id)
    user.username = text
    user.save()

    ask_for_about = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_ABOUT)

    update.message.reply_text(ask_for_about.text)

    return WAIT_FOR_ABOUT


def record_about_ask_social(update, context):
    text = update.message.text

    user = Person.objects.get(tg_id=update.effective_user.id)
    user.about = text
    user.save()

    ask_for_social = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_SOCIAL)

    update.message.reply_text(ask_for_social.text)

    return WAIT_FOR_SOCIAL


def record_social_ask_city(update, context):
    text = update.message.text

    user = Person.objects.get(tg_id=update.effective_user.id)
    user.social_networks = text
    user.save()

    ask_for_city = BotMessage.objects.get(type=BotMessage.MessageTypes.ASK_FOR_CITY)
    n = 3
    packed_locations = [AVAILABLE_LOCATIONS[i:i + n] for i in range(0, len(AVAILABLE_LOCATIONS), n)]
    markup = ReplyKeyboardMarkup(packed_locations, resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text(ask_for_city.text, reply_markup=markup)
    return WAIT_FOR_CITY


def record_city_register_end(update, context):
    text = update.message.text
    location = Location.objects.filter(name=text).get()

    user = Person.objects.get(tg_id=update.effective_user.id)
    user.location = location
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
        WAIT_FOR_NAME: [MessageHandler(Filters.text, record_name_ask_about)],
        WAIT_FOR_ABOUT: [MessageHandler(Filters.text, record_about_ask_social)],
        WAIT_FOR_SOCIAL: [MessageHandler(Filters.text, record_social_ask_city)],
        WAIT_FOR_CITY: [
            MessageHandler(
                Filters.regex(f"^({'|'.join(AVAILABLE_LOCATIONS)})$"),
                record_city_register_end
            )
        ],
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