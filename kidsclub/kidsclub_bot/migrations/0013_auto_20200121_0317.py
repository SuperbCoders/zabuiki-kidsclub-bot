# Generated by Django 3.0.2 on 2020-01-21 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kidsclub_bot', '0012_auto_20200121_0107'),
    ]

    operations = [
        migrations.AddField(
            model_name='personkid',
            name='kid_seg_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='botmessage',
            name='type',
            field=models.IntegerField(choices=[(0, 'Приветсвие пользователя'), (1, 'Спрашиваем имя'), (2, 'Спрашиваем о количестве детей'), (3, 'Спрашиваем возраст ребенка'), (4, 'Спрашиваем пол ребенка'), (17, 'Спрашиваем город'), (5, 'Профиль сохранен'), (6, 'Участвуем в следующей рассылке'), (7, 'Человек подтвердил участие в рассылке'), (8, 'Человек отказался от участия в рассылке'), (9, 'Информация о встрече'), (10, 'Юзернейм не установлен'), (11, 'Фидбек, встреча прошла хорошо'), (12, 'Фидбек, встреча прошла плохо'), (13, 'Фидбек, не встретились'), (14, 'Фидбек, отзыв собран'), (15, 'Фидбек, как прошло'), (16, 'Введено некорректное число')], primary_key=True, serialize=False, unique=True),
        ),
    ]
