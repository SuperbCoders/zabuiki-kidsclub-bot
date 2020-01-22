from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'

    def __str__(self):
        return self.name


class Person(models.Model):
    tg_id = models.IntegerField(null=False, unique=True)
    tg_username = models.CharField(max_length=255, null=True, blank=True)

    username = models.CharField(max_length=255)
    kid_amount = models.IntegerField(default=0)
    location = models.ForeignKey(Location, null=True, on_delete=models.CASCADE)
    social_networks = models.TextField(blank=True)

    is_blocked = models.BooleanField(default=False)

    meetings = models.ManyToManyField('self', through='PersonMeeting',
                                           symmetrical=False,
                                           related_name='person_meeting')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.tg_id} - {self.username} - {self.location}"


class PersonKid(models.Model):
    class Sex(models.IntegerChoices):
        MALE = 0, 'Мальчик'
        FEMALE = 1, 'Девочка'

    kid_seg_number = models.IntegerField(default=0)
    age = models.IntegerField(default=0, blank=True)
    sex = models.IntegerField(choices=Sex.choices, default=Sex.MALE, blank=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.person.username} - {self.age} - {self.get_sex_display()}"


class BotMessage(models.Model):
    class MessageTypes(models.IntegerChoices):
        USER_WELCOME = 0, 'Приветсвие пользователя'

        ASK_FOR_NAME = 1, 'Спрашиваем имя'
        ASK_FOR_KID_AMOUNT = 2, 'Спрашиваем о количестве детей'
        ASK_FOR_KID_AGE = 3, 'Спрашиваем возраст ребенка'
        ASK_FOR_KID_SEX = 4, 'Спрашиваем пол ребенка'
        ASK_FOR_CITY = 17, 'Спрашиваем округ'
        ASK_FOR_SOCIAL = 18, 'Спрашиваем соцсети'

        PROFILE_SAVED = 5, 'Профиль сохранен'

        INVITE = 6, 'Участвуем в следующей рассылке'
        INVITE_CONFIRMED = 7, 'Человек подтвердил участие в рассылке'
        INVITE_DECLINED = 8, 'Человек отказался от участия в рассылке'

        SEND_PAIR_INFO = 9, 'Информация о встрече'

        USERNAME_NOT_SET = 10, 'Юзернейм не установлен'

        FEEDBACK_GOOD = 11, 'Фидбек, встреча прошла хорошо'
        FEEDBACK_BAD = 12, 'Фидбек, встреча прошла плохо'
        FEEDBACK_NOT_MET = 13, 'Фидбек, не встретились'
        FEEDBACK_REASON_COLLECTED = 14, 'Фидбек, отзыв собран'

        FEEDBACK_REQUEST = 15, 'Фидбек, как прошло'

        NUMBER_INPUT_ERROR = 16, 'Введено некорректное число'

    type = models.IntegerField(choices=MessageTypes.choices, unique=True, primary_key=True)
    text = models.TextField()

    class Meta:
        verbose_name = 'Шаблон сообщения'
        verbose_name_plural = 'Шаблоны сообщений'

    def __str__(self):
        return self.MessageTypes.choices[self.type][1]


class InviteIntent(models.Model):
    date = models.DateField()
    person = models.ForeignKey(Person, to_field='tg_id', on_delete=models.CASCADE)

    is_message_send = models.BooleanField(default=False)
    is_user_agreed = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    person_meeting = models.ForeignKey('PersonMeeting', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ['date', 'person']

    def __str__(self):
        return f"{self.date} - {self.person_id}"


class PersonMeeting(models.Model):
    class MeetingRate(models.IntegerChoices):
        GOOD = 0, 'Хорошо'
        BAD = 1, 'Плохо'
        NOT_MET = 2, 'Не встретились'

    from_person = models.ForeignKey(Person, to_field='tg_id', related_name='+', on_delete=models.CASCADE)
    to_person = models.ForeignKey(Person, to_field='tg_id', related_name='+', on_delete=models.CASCADE)

    is_message_send = models.BooleanField(default=False)
    is_feedback_message_send = models.BooleanField(default=False)

    rate = models.IntegerField(choices=MeetingRate.choices, null=True, blank=True)
    review = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Встреча пользователя'
        verbose_name_plural = 'Встречи пользователей'

    def __str__(self):
        return f"{self.from_person} - {self.to_person}"
