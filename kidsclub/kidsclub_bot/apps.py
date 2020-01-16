from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class BookclubEntitiesConfig(AppConfig):
    name = 'kidsclub_bot'


class BookclubAdminConfig(AdminConfig):
    default_site = 'kidsclub_bot.admin.BookclubAdminSite'
