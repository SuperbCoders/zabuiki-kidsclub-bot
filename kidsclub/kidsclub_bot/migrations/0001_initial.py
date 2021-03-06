# Generated by Django 3.0.2 on 2020-01-10 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BotMessage',
            fields=[
                ('type', models.IntegerField(choices=[(0, 'Приветствие нового пользователя'), (1, 'Обновить данные пользователя'), (2, 'Профиль сохранен'), (3, 'Не заполнены необходимые поля')], primary_key=True, serialize=False, unique=True)),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tg_id', models.IntegerField(unique=True)),
                ('username', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('about', models.TextField()),
                ('social_networks', models.TextField()),
            ],
        ),
    ]
