# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 15:35:20 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter)
from command_helpers import support_handlers, help_function
from telegram import ReplyKeyboardMarkup
import datetime, time
from db_connection import moderators, admins, event_posts, users
import pytz
tz_msk = pytz.timezone('Europe/Moscow')


#processing conversation
def check(bot, update):
    """
    """
    if (admins.find_one({'chat_id' : update.message.chat_id}) != None) or (moderators.find_one({'chat_id' : update.message.chat_id}) != None):
        text = "можем начинать обработку запросов на публикацию?"
        keyboard = [["Yes", "No"]]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id=update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
        return "processing"
    else:
        text = "Такой команды нет. Выбери команду из списка:)"
        bot.send_message(chat_id=update.message.chat_id,
                 text = text)
        help_function(bot, update)

def processing(bot, update):
    """
    """
    if (update.message.text == 'Yes') or (update.message.text == 'Next'):
        bot.send_message(chat_id = update.message.chat_id,
                         text = "Processing - one at a time. Чтобы закончить, жми 'Finish'")
        cursor = event_posts.find_one({'processed?' : False, 'processing?' : False})
        if cursor != None:
            event_posts.update_one({'chat_id' : cursor['chat_id'],
                                             'link' : cursor['link'],
                                             'processing?' : False},
                                            {'$set' : {'processing?' : True, 'moderator' : update.message.chat_id}})
            try:
                event_name = cursor['event_name']
            except KeyError:
                event_name = 'NA'
            text = 'Тематика: ' + cursor['event_theme'] + '\n\n'
            if event_name != 'NA':
                text += event_name + '\n'
            text += 'Локация: ' + cursor['location'] + '.\n'
            text += ('Дата и время: ' + (cursor['date_time_msk']).strftime('%d.%m.%Y %H:%M') + '. ' + cursor['organization'] +'\n' + cursor["link"])
            keyboard = [["Approve", "Reject"],["Finish"]]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            bot.send_message(chat_id=update.message.chat_id, text = text, reply_markup = reply_markup)
            return "decision"
        else:
            bot.send_message(chat_id=update.message.chat_id,
                     text = "Новых запросов нет. Завершаем процесс.",
                     reply_markup = None)
            return -1
    elif update.message.text == 'No':
        bot.send_message(chat_id=update.message.chat_id,
                         text = "Adiós")
        return -1

def decision(bot, update): #добавить персонализацию в рассылке по организациям
    """
    """
    cursor = event_posts.find_one({'processing?' : True, 'moderator' : update.message.chat_id})
    location = cursor['location']
    if update.message.text == "Approve":
        event_posts.update_one({'_id' : cursor['_id'], 'chat_id' : cursor['chat_id'], 'processing?' : True, 'moderator' : update.message.chat_id},
                                        {'$set' : {'processed?' : True,
                                                   'decision' : 'approved',
                                                   'decision-maker' : update.message.chat_id,
                                                   'decision_time' : datetime.datetime.now(tz=tz_msk),
                                                   'processing?' : 'finished'}})
        theme_filter = 'event_theme.' + cursor['event_theme'] + '.status'
        organization_filter = 'organization.' + cursor['organization'] + '.status'
        users_sent = []

        try:
            event_name = cursor['event_name']
        except KeyError:
            event_name = 'NA'
        text = '#' + cursor['event_theme'].replace(" ", "_") + '\n\n'
        if event_name != 'NA':
            text += event_name + '\n'
        text += ('Дата и время: ' + (cursor['date_time_msk']).strftime('%d.%m.%Y %H:%M') + '. ' + cursor['organization'] +'\n' + cursor["link"])

        cursor_users = users.find({theme_filter : True,
                                   organization_filter : True,
                                   'location' : location,
                                   'subscriber' : True,
                                   'preferences_logic' : 'ТОЛЬКО'})
        if cursor_users != None:
            for user in cursor_users:
                if user['chat_id'] not in users_sent:
                    users_sent.append(user['chat_id'])
                    bot.send_message(chat_id = user['chat_id'], text = text)
                    time.sleep(1)

        cursor_users = users.find({theme_filter : True,
                                   'location' : location,
                                   'subscriber' : True,
                                   'preferences_logic' : 'ИЛИ'})
        if cursor_users != None:
            for user in cursor_users:
                if user['chat_id'] not in users_sent:
                    users_sent.append(user['chat_id'])
                    bot.send_message(chat_id = user['chat_id'], text = text)
                    time.sleep(1)

        cursor_users = users.find({organization_filter : True,
                                   'location' : location,
                                   'subscriber' : True,
                                   'preferences_logic' : 'ИЛИ'})
        if cursor_users != None:
            for user in cursor_users:
                if user['chat_id'] not in users_sent:
                    users_sent.append(user['chat_id'])
                    bot.send_message(chat_id = user['chat_id'], text = text)
                    time.sleep(1)

        reply_markup = ReplyKeyboardMarkup(keyboard = [["Next"], ["Finish"]],
                           one_time_keyboard = True,
                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = "The job is done!",
                         reply_markup = reply_markup)
    elif update.message.text == "Reject":
        event_posts.update_one({'chat_id' : cursor['chat_id'], 'processing?' : True, 'moderator' : update.message.chat_id},
                                        {'$set' : {'processed?' : True,
                                                   'decision' : 'rejected',
                                                   'decision-maker' : update.message.chat_id,
                                                   'decision_time' : datetime.datetime.now(tz=tz_msk),
                                                   'processing?' : 'finished'}})

        reply_markup = ReplyKeyboardMarkup(keyboard = [["Next"],["Finish"]],
                           one_time_keyboard = True,
                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = "The application declined",
                         reply_markup = reply_markup)
    elif update.message.text == "Finish":
        event_posts.update_one({'chat_id' : cursor['chat_id'], 'processing?' : True},
                                        {'$set' : {'processing?' : False}})
        bot.send_message(chat_id=update.message.chat_id,
                         text = "Adiós")
        return -1
    return "processing"

class check_filter(BaseFilter):
    def filter(self, message):
        return '/check' in message.text
filter_check = check_filter()


check_handler = CommandHandler('check', check)
check_handler_2 = MessageHandler(filter_check, check)
processing_handler = MessageHandler(Filters.text, processing)
decision_handler = MessageHandler(Filters.text, decision)
processingConversation_states = {"processing":[processing_handler],
                                 "decision":[decision_handler]}
processingConversation_handler = ConversationHandler([check_handler, check_handler_2],
                                                     processingConversation_states,
                                                     fallbacks=support_handlers,
                                                     allow_reentry = True)