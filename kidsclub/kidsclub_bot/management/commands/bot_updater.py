from django.core.management.base import BaseCommand
from telegram import ext

from kidsclub_bot import bot_handlers
from kidsclub_bot.bot import bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        updater = ext.Updater(bot=bot, use_context=True)

        dp = updater.dispatcher

        dp.add_handler(bot_handlers.start_handler)
        dp.add_handler(bot_handlers.help_handler)

        dp.add_handler(bot_handlers.reg_conv_handler)

        dp.add_handler(bot_handlers.invite_intent_handler)
        dp.add_handler(bot_handlers.collect_feedback_conv_handler)

        updater.start_polling()
        print('Started')
        updater.idle()
