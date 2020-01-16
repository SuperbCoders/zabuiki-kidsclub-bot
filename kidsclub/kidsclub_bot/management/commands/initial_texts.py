from django.core.management.base import BaseCommand

from kidsclub_bot.models import BotMessage, Location


class Command(BaseCommand):

    DEFAULT_TEXTS = {
        BotMessage.MessageTypes.USER_WELCOME: 'Привет! Я бот для встреч клуба, зарегестрируйся с помощью команды',

        BotMessage.MessageTypes.ASK_FOR_NAME: 'Как тебя зовут?',
        BotMessage.MessageTypes.ASK_FOR_ABOUT: 'Расскажи о себе',
        BotMessage.MessageTypes.ASK_FOR_SOCIAL: 'Супер! И дай ссылку на свой профиль в Инстагрме или Фейсбуке',
        BotMessage.MessageTypes.ASK_FOR_CITY: 'Отлично! Из какого ты округа?',

        BotMessage.MessageTypes.PROFILE_SAVED: 'Ваш профиль сохранен. Ждите приглашения на встречу!',

        BotMessage.MessageTypes.INVITE: 'Участвуете во встрече на следующей неделе?',
        BotMessage.MessageTypes.INVITE_CONFIRMED: 'Вы участвуете в составлении пар на следующую неделю',
        BotMessage.MessageTypes.INVITE_DECLINED: 'Вы отказались от встречи на следующую неделю',

        BotMessage.MessageTypes.SEND_PAIR_INFO: (
            'Вот твоя пара на этой неделе: {username} \n'
            'О себе: {about} \n'
            'Ссылка: {social_networks}'
        ),

        BotMessage.MessageTypes.USERNAME_NOT_SET: (
            'У вас не установлен username, вот '
            '[инструкция](https://nashkomp.ru/user-name-telegram-vse-o-nastroyke-i-smene-imeni).'
            'Без него никто не сможет вам написать'
        ),

        BotMessage.MessageTypes.FEEDBACK_REQUEST: 'Как прошла ваша встреча?',

        BotMessage.MessageTypes.FEEDBACK_GOOD: 'Здорово! Ждем вас на следующей неделе',
        BotMessage.MessageTypes.FEEDBACK_BAD: 'Ого! А что случилось?',
        BotMessage.MessageTypes.FEEDBACK_NOT_MET: 'Ого! А что случилось?',

        BotMessage.MessageTypes.FEEDBACK_REASON_COLLECTED: (
            'Спасибо за ваш отзыв! '
            'Ждем вас на следующей неделе, надеемся будет лучше'
        ),
    }

    LOCATIONS = [
        'Центральны',
        'Северный',
        'Северо-Восточный',
        'Восточный',
        'Юго-Восточный',
        'Южный',
        'Юго-Западный',
        'Западный',
        'Северо-Западный',
    ]

    def handle(self, *args, **options):
        for msg_type, msg_text in self.DEFAULT_TEXTS.items():
            if not BotMessage.objects.filter(type=msg_type).exists():
                BotMessage.objects.create(
                    type=msg_type,
                    text=msg_text
                )

        print('Text saved')

        for loc in self.LOCATIONS:
            if not Location.objects.filter(name=loc).exists():
                Location.objects.create(
                    name=loc,
                )

        print('Loc saved')