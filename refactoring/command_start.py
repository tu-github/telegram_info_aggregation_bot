# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:34:59 2019

@author: HP
"""

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler
import datetime
from db_connection import users
import pytz
tz_msk = pytz.timezone('Europe/Moscow')
from command_helpers import help_function

salutation_text = """
                Привет! Подписывайся и получай анонсы событий в МГИМО и ВШЭ:)

Если хочешь поделиться анонсом, жми /post
                """
current_subscriber_text = "Ты уже подписан:)"


def start(bot, update, salutation_text, current_subscriber_text):
    cursor = users.find_one({'chat_id' : update.message.chat_id,
                             'subscriber' : True})
    if cursor == None:
        if users.find_one({'chat_id' : update.message.chat_id}) == None:
            users.insert_one({'chat_id' : update.message.chat_id,
                              'first_interaction' : datetime.datetime.now(tz=tz_msk),
                              'subscriber' : False})
        else:
            users.update_one({'chat_id' : update.message.chat_id},
                             {'$set' : {'latest_start_interaction' : datetime.datetime.now(tz=tz_msk)}})
        keyboard = [["Подписаться", "Помощь"]]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id=update.message.chat_id,
                         text = salutation_text,
                         reply_markup = reply_markup)
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text = current_subscriber_text)
        help_function(bot, update)

start_handler = CommandHandler('start', start)