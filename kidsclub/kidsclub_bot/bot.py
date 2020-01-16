import telegram
from telegram.utils import request

from kidsclub import settings

bot = telegram.Bot(settings.BOT_TOKEN, request=request.Request(con_pool_size=8))
