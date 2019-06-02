# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 15:38:47 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter)
from command_helpers import support_handlers, help_function
from telegram import ReplyKeyboardMarkup
import datetime, time
from db_connection import users, admins, notifications
import pytz
tz_msk = pytz.timezone('Europe/Moscow')


def notify_users(bot, update):
    '''
    '''
    if admins.find_one({'chat_id' : update.message.chat_id}) != None:
        reply_markup = ReplyKeyboardMarkup(keyboard = [["Cancel"]],
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         reply_markup = reply_markup,
                         text = 'О чем оповестим юзеров? Напиши мне текст, я отправлю юзерам)')
        return 'submit notification'
    else:
        text = "Такой команды нет. Выбери команду из списка:)"
        bot.send_message(chat_id=update.message.chat_id,
                 text = text)
        help_function(bot, update)

def submit_notification(bot, update):
    '''
    '''
    if update.message.text == 'Cancel':
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Adios!')
        return -1
    else:
        notifications.insert_one({'chat_id' : update.message.chat_id,
                                  'notification message' : update.message.text,
                                  'date_time' : datetime.datetime.now(tz=tz_msk),
                                  'status' : 'in progress'})
        reply_markup = ReplyKeyboardMarkup(keyboard = [["Yes"],["No"]],
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Are you sure? You are going to send this message:',
                         reply_markup = reply_markup)
        bot.send_message(chat_id = update.message.chat_id,
                         text = update.message.text)
        return 'confirm notification'

def confirm_notification(bot, update):
    '''
    '''
    cursor_notification = notifications.find_one({'chat_id' : update.message.chat_id,
                                                 'status' : 'in progress'})
    if update.message.text == 'Yes':
        notifications.update_one({'chat_id' : cursor_notification['chat_id'], 'status' : 'in progress'},
                                 {'$set' : {'status' : 'sent',
                                            'date_time_sent' : datetime.datetime.now(tz=tz_msk)}})
        cursor = users.find({})
        for user in cursor:
            bot.send_message(chat_id = user['chat_id'],
                             text = cursor_notification['notification message'])
            time.sleep(1)
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Job is done! The following notification was sent to users:\n\n' + cursor_notification['notification message'])
        return -1
    elif update.message.text == 'No':
        notifications.update_one({'chat_id' : cursor_notification['chat_id'], 'status' : 'in progress'},
                                 {'$set' : {'status' : 'declined'}})
        return notify_users(bot, update)
    else:
        notifications.update_one({'chat_id' : cursor_notification['chat_id'], 'status' : 'in progress'},
                                 {'$set' : {'status' : 'forgot'}})
        return -1
   
class notify_filter(BaseFilter):
    def filter(self, message):
        return '/notify' in message.text
filter_notify = notify_filter()

notification_handler = CommandHandler('notify', notify_users)
notification_handler_2 = MessageHandler(filter_notify, notify_users)
submit_notification_handler = MessageHandler(Filters.text,submit_notification)
confirm_notification_handler = MessageHandler(Filters.text, confirm_notification)
notificationConversation_states = {'submit notification' : [submit_notification_handler],
                                   'confirm notification' : [confirm_notification_handler]}
notificationConversation_handler = ConversationHandler([notification_handler, notification_handler_2],
                                                       notificationConversation_states,
                                                       fallbacks=support_handlers,
                                                       allow_reentry = True)