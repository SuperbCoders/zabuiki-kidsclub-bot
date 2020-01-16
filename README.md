# Бот для организации встреч

## Структура

* kidsclub.bot_handlers - обработчики диалогов для бота. здесь заданы константы и все используемые клавиатуры
* kidsclub.tasks - переодические задачи
    * create_intive_intent - создаем модель обозначающее намерение пользователя встречаться на этой неделе. дата привязывается к понедельнику
    * send_invite - спрашивает пользователя о намерении встречаться
    * find_pair - среди согласившихся собираются пары, для каждой встречи создается пара моделей, обозначающая от кого к кому и в ней же храним рейтинг и отзыв
    * send_pair_info - отправляем инфу о паре
    * send_feedback_collect - спрашиваем в субботу о том как прошла встреча
    
* kidsclub_bot.management.commands.bot_updater - запускает демона бота, реагирующего на действия пользователя

## Деплой

Деплой ansible'ом (deploy-playbook.yml), с использованием ansible-vault (secrets). На целевой машине нужен postgres и redis.
Разворачиваются демоны для celery, вебсервер и демон бота.
