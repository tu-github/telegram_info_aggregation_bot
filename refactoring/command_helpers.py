# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:57:20 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, Filters)
import time
from db_connection import admins

def unknown(bot, update):
    """
    """
    text = "Такой команды нет. Выбери команду из списка:)"
    bot.send_message(chat_id=update.message.chat_id,
                     text = text)
    help_function(bot, update)
    
def help_function(bot, update):
    """
    """
    if admins.find_one({'chat_id' : update.message.chat_id}) != None:
        text = """
            Вот список команд, который поможет тебе пользоваться ботом:

        /analytics - Получить аналитику
        /check - Проверить заявки на публикацию
        /notify - Написать сообщение юзерам
        /today - Анонсы на сегодня
        /tomorrow - Анонсы на завтра
        /week - Анонсы на неделю
        /settings - Настройки
        /feedback - Обратная связь
        /post - Опубликовать пост о событии
            """
    elif moderators.find_one({'chat_id' : update.message.chat_id}) != None:
        text = """
            Вот список команд, который поможет тебе пользоваться ботом:

        /start - Начать
        /subscribe - Подписаться
        /today - Анонсы на сегодня
        /tomorrow - Анонсы на завтра
        /week - Анонсы на неделю
        /check - Проверить заявки на публикацию
        /settings - Настройки
        /feedback - Обратная связь
        /post - Опубликовать пост о событии
            """
    else:
        text = """
            Вот список команд, который поможет тебе пользоваться ботом:

        /start - Начать
        /subscribe - Подписаться
        /today - Анонсы на сегодня
        /tomorrow - Анонсы на завтра
        /week - Анонсы на неделю
        /settings - Настройки
        /feedback - Обратная связь
        /post - Опубликовать пост о событии
            """
    bot.send_message(chat_id=update.message.chat_id, text = text)

def other(bot, update):
    text = "Чем я могу помочь?"
    bot.send_message(chat_id=update.message.chat_id, text = text)
    time.sleep(1)
    help_function(bot, update)

error_logs = []
def error(bot, update, TelegramError):
    """
    """
    bot.send_message(chat_id=40287333, text = TelegramError)
    print(TelegramError)
    error_logs.append(TelegramError)

help_function_handler = CommandHandler('help', help_function)
unknown_handler = MessageHandler(Filters.command, unknown)
other_handler = MessageHandler(Filters.all, other)
error_handler = MessageHandler(Filters.all, error)
support_handlers=[help_function_handler, unknown_handler, other_handler, error_handler]