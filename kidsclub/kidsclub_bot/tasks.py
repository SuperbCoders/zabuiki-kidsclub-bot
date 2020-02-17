import logging
from datetime import date, timedelta

import telegram
from celery.utils.log import get_task_logger
from django.db import transaction
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from kidsclub.celery import app
from kidsclub_bot.bot import bot
from kidsclub_bot.bot_handlers import want_to_party_keyboard, get_user_feedback_keyboard
from kidsclub_bot.models import Person, InviteIntent, BotMessage, PersonMeeting

logger = get_task_logger(__name__)
db_logger = logging.getLogger('db_log')


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


@app.task(name='create_invite_intent', autoretry_for=(Exception,), max_retries=2)
def create_invite_intent():
    today = date.today()

    # if not today.weekday() >= 5:
    #     logger.info('Must run on weekend')
    #     return

    intent_day = next_weekday(today, 0)  # zero for monday

    # disable previous intents
    prev_intent_day = intent_day - timedelta(days=7)
    (
        InviteIntent.objects.filter(
            date__lte=prev_intent_day,
            is_deleted=False,
        ).update(is_deleted=True)
    )

    persons = Person.objects.raw(f"""
        SELECT a.*
        FROM kidsclub_bot_person AS a
        LEFT JOIN (
            SELECT *
            FROM kidsclub_bot_inviteintent
            WHERE date = '{intent_day}'
        ) AS b ON a.tg_id = b.person_id
        WHERE b.person_id IS NULL
            AND a.tg_id IS NOT NULL
            AND a.location_id IS NOT NULL
            AND a.is_blocked = false
    """)

    if persons:
        with transaction.atomic():
            InviteIntent.objects.bulk_create([
                InviteIntent(person=person, date=intent_day)
                for person in persons
            ])
        logger.info(f'Created {len(persons)} intents')
        db_logger.info(f'[{intent_day}] Создано {len(persons)} запросов на встречу')
    else:
        logger.info(f'Intents already created')


@app.task(name='send_invite', autoretry_for=(Exception,), max_retries=1)
def send_invite():
    invite_text = BotMessage.objects.get(type=BotMessage.MessageTypes.INVITE)
    n = 10
    send_cnt = 0

    while True:
        intents = (
            InviteIntent.objects
                .filter(is_message_send=False, is_deleted=False)
                .order_by('person_id')
            [:n]
        )
        if not intents.exists():
            break

        for intent in intents.all():
            bot.send_message(
                intent.person_id,
                invite_text.text,
                reply_markup=want_to_party_keyboard
            )
            intent.is_message_send = True
            intent.save()

            send_cnt += 1

        logger.info(f'Send {send_cnt} invite messages')

    db_logger.info(f'Разослано {send_cnt} сообщений')


@app.task(name='find_pair', autoretry_for=(Exception,), max_retries=1)
def find_pair():
    today = date.today()

    # if not today.weekday() <= 1:
    #     logger.info('Must run on week start')
    #     return

    invite_intents = InviteIntent.objects.filter(
        is_deleted=False,
        is_user_agreed=True,
        person_meeting__isnull=True,
    )

    cnt = 0
    for invite_intent in invite_intents.all():

        invite_intent.refresh_from_db()
        if invite_intent.person_meeting:
            continue

        already_seen_person_ids = invite_intent.person.person_meeting.values_list('tg_id', flat=True)
        available_persons = invite_intents.exclude(person=invite_intent.person).values_list('person_id', flat=True)

        persons_with_same_kid_ids = [p.id for p in Person.objects.raw(f"""
            SELECT *
            FROM kidsclub_bot_person
            WHERE id in (
                SELECT B.person_id
                FROM (
                    SELECT age, sex
                    FROM kidsclub_bot_personkid
                    WHERE person_id = {invite_intent.person.id}
                ) AS A INNER JOIN (
                    SELECT person_id, age, sex
                    FROM kidsclub_bot_personkid
                    WHERE person_id != {invite_intent.person.id}
                ) AS B ON (
                    A.age = B.age AND A.sex = B.sex
                )
            ) AND is_blocked = false
        """)]

        candidates = Person.objects.filter(
            id__in=persons_with_same_kid_ids,
            location=invite_intent.person.location,
            tg_id__in=available_persons,
        ).exclude(
            tg_id__in=already_seen_person_ids
        )

        if not candidates.exists():
            candidates = Person.objects.filter(
                id__in=persons_with_same_kid_ids,
                tg_id__in=available_persons,
                is_blocked=False,
            ).exclude(
                tg_id__in=already_seen_person_ids
            )

            if not candidates.exists():
                db_logger.info(f'Сочетания пар закончились для {invite_intent.person}, звать в друзья некого')
                continue

        candidate = candidates.first()

        pm = PersonMeeting.objects.create(
            from_person=invite_intent.person,
            to_person=candidate,
        )
        invite_intent.person_meeting = pm
        invite_intent.save()

        reverse_pm = PersonMeeting.objects.create(
            from_person=candidate,
            to_person=invite_intent.person,
        )
        candidate_intent = invite_intents.filter(person=candidate).get()
        candidate_intent.person_meeting = reverse_pm
        candidate_intent.save()

        cnt += 1

    db_logger.info(f'Составлено {cnt} пар')


@app.task(name='send_pair_info', autoretry_for=(Exception,), max_retries=1)
def send_pair_info():
    msg_template = BotMessage.objects.get(type=BotMessage.MessageTypes.SEND_PAIR_INFO).text

    n = 10
    send_cnt = 0

    while True:
        pm_q = PersonMeeting.objects.filter(
            is_message_send=False
        )[:n]

        if not pm_q.exists():
            break

        for pm in pm_q.all():
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton('Написать', url=f"https://t.me/{pm.to_person.tg_username}")]
            ])

            bot.send_message(
                pm.from_person_id,
                msg_template.format(
                    username=pm.to_person.username,
                    social_networks=pm.to_person.social_networks,
                ),
                reply_markup=keyboard
            )
            pm.is_message_send = True
            pm.save()

            send_cnt += 1

            logger.info(f'Send {send_cnt} invite messages')

    db_logger.info(f'Разослано {send_cnt} уведомлений о паре')


@app.task(name='send_feedback_collect', autoretry_for=(Exception,), max_retries=1)
def send_feedback_collect():
    msg_text = BotMessage.objects.get(type=BotMessage.MessageTypes.FEEDBACK_REQUEST).text
    today = date.today()

    # if not today.weekday() <= 5:
    #     logger.info('Must run on week end')
    #     return

    n = 10
    send_cnt = 0

    while True:
        pm_q = PersonMeeting.objects.filter(
            is_feedback_message_send=False
        )[:n]

        if not pm_q.exists():
            break

        for pm in pm_q.all():

            bot.send_message(
                pm.from_person_id,
                msg_text,
                reply_markup=get_user_feedback_keyboard(pm.to_person_id)
            )
            pm.is_feedback_message_send = True
            pm.save()

            send_cnt += 1

            logger.info(f'Send {send_cnt} feedback request messages')

    db_logger.info(f'Разослано {send_cnt} запросов о фидбеке')
