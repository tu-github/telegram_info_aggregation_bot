# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 15:22:33 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter)
from command_helpers import support_handlers
from telegram import ReplyKeyboardMarkup
import datetime, time
import pytz
tz_msk = pytz.timezone('Europe/Moscow')
from db_connection import event_posts, event_themes_russian, event_themes_dict, locations, organizations


def post(bot, update):
    text = '''Студенческие организации могут свободно присылать мероприятия через бот. Юридические лица могут опубликовать мероприятия в частном порядке, для этого нужно написать сообщение @artemkalyuta.
Мероприятия будут опубликованы в следующем формате:

    *Лекция CEO компании X*
    23.02.2019. ВШЭ
    /ссылка на пост или регистрацию/
'''
    bot.send_message(chat_id = update.message.chat_id, text = text)
    text = 'Начинаем создавать пост. Как называется событие?'
    keyboard = [['Отмена']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id, text = text, reply_markup = reply_markup)
    return 'theme'

def post_theme(bot, update):
    '''
    '''
    if update.message.text == 'Отмена':
        bot.send_message(chat_id = update.message.chat_id, text = 'See you!')
        return -1
    else:
        event_posts.insert_one({'chat_id' : update.message.chat_id,
                                "application_completed?" : False,
                                'event_name' : update.message.text,
                                'application_started' : datetime.datetime.now(tz=tz_msk)})
        text = 'К какой тематике (выбери наиболее близкую) относится событие?'
        keyboard = [event_themes_russian[0:3],
                    event_themes_russian[3:6],
                    event_themes_russian[6:]]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
        return 'date'

def post_date(bot, update):
    '''
    '''
    try:
        event_theme = event_themes_dict[update.message.text]
    except KeyError:
        bot.send_message(chat_id = update.message.chat_id, text = 'Выбери один из вариантов:)')
        text = 'К какой тематике (выбери наиболее близкую) относится событие?'
        keyboard = [event_themes_russian[0:3],
                    event_themes_russian[3:6],
                    event_themes_russian[6:]]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
        return 'date'
    event_posts.update_one({'chat_id' : update.message.chat_id, "application_completed?" : False}, {'$set' : {'event_theme' : event_theme}})
    text = '''Когда состоится мероприятие? Пришли пожалуйста, в дату и время в этом формате - dd.mm.yyyy hh:mm
Если точное время ещё не известно, используй формат - dd.mm.yy
        '''
    bot.send_message(chat_id = update.message.chat_id, text = text)
    return 'location'

def post_location(bot, update):
    '''
    '''
    if len(update.message.text.split(' ')) == 2:
        try:
            date_time_msk = datetime.datetime.strptime(update.message.text, '%d.%m.%Y %H:%M')
        except ValueError:
            try:
                date_time_msk = datetime.datetime.strptime(update.message.text, '%d.%m.%Y %H.%M')
            except ValueError:
                try:
                    date_time_msk = datetime.datetime.strptime(update.message.text, '%d/%m/%Y %H:%M')
                except ValueError:
                    date_time_msk = datetime.datetime.strptime(update.message.text, '%d/%m/%Y %H.%M')
    elif len(update.message.text.split(' ')) == 1:
        try:
            date_time_msk = datetime.datetime.strptime(update.message.text, '%d/%m/%Y')
        except ValueError:
            date_time_msk = datetime.datetime.strptime(update.message.text, '%d.%m.%Y')
    try:
        event_posts.update_one({'chat_id' : update.message.chat_id,
                            'application_completed?' : False},
                           {'$set' : {'date_time_msk': date_time_msk,
                                      'year' : date_time_msk.year,
                                      'month' : date_time_msk.month,
                                      'day' : date_time_msk.day,
                                      'hour' : date_time_msk.hour,
                                      'minute' : date_time_msk.minute}})
    except ValueError:
        text = '''Когда состоится мероприятие? Пришли пожалуйста, в дату и время в этом формате - dd.mm.yy hh:mm
Если точное время ещё не известно, используй формат - dd.mm.yy
        '''
        bot.send_message(chat_id = update.message.chat_id, text = text)
        return 'location'
    text = 'В каком городе пройдет событие?'
    keyboard = [locations]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id, text = text,
                     reply_markup = reply_markup)
    return 'vuz'

def post_vuz(bot, update):
    '''
    '''
    event_posts.update_one({'chat_id' : update.message.chat_id,
                            "application_completed?" : False},
                            {'$set' : {"location" : update.message.text}})
    text = 'В каком ВУЗе будет проходить мероприятие?'
    cursor_organizations = organizations.find({'location' : update.message.text})
    org_list = []
    for unit in cursor_organizations:
        org_list.append(unit['name'])
    keyboard = [org_list]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id, text = text,
                     reply_markup = reply_markup)
    return 'description'

def post_description(bot, update):
    """
    """
    event_posts.update_one({'chat_id' : update.message.chat_id,
                            "application_completed?" : False},
                            {'$set' : {"organization" : update.message.text}})
    text = 'Пришлите ссылку на пост или регистрацию. Далее запрос будет рассмотрен модератором.'
    bot.send_message(chat_id=update.message.chat_id, text = text)
    return "link"

def get_post(bot, update):
    """
    """
    cursor = event_posts.find_one({'chat_id' : update.message.chat_id, 'application_completed?' : False})
    id = cursor['_id']
    event_posts.update_one({'chat_id' : update.message.chat_id, 'application_completed?' : False},
                           {'$set' : {"link":update.message.text,
                                      'application_completed?' : True,
                                      'processing?' : False,
                                      "processed?" : False,
                                      'application_ended' : datetime.datetime.now(tz=tz_msk),
                                      'last_modified' : datetime.datetime.now(tz=tz_msk)}})
    bot.send_message(chat_id = update.message.chat_id, text = "Спасибо! Твой пост будет выглядеть так:")

    cursor = event_posts.find_one({'_id' : id})
    try:
        event_name = cursor['event_name']
    except KeyError:
        event_name = 'NA'
    text = '#' + cursor['event_theme'].replace(" ", "_") + '\n\n'
    if event_name != 'NA':
        text += event_name + '\n'
    text += ('Дата и время: ' + (cursor['date_time_msk']).strftime('%d.%m.%Y %H:%M') + '. ' + cursor['organization'] +'\n' + cursor["link"])
    bot.send_message(chat_id = update.message.chat_id, text = text)
    time.sleep(1)
    bot.send_message(chat_id = update.message.chat_id,
                     text = 'Ты можешь добавить ещё анонсы нажав /post :)')
    return -1

class post_filter(BaseFilter):
    def filter(self, message):
        return '/post' in message.text
filter_post = post_filter()

post_handler = CommandHandler('post', post)
post_handler_2 = MessageHandler(filter_post, post)
theme_handler = MessageHandler(Filters.text, post_theme)
date_handler = MessageHandler(Filters.text, post_date)
location_handler = MessageHandler(Filters.text, post_location)
vuz_handler = MessageHandler(Filters.text, post_vuz)
description_handler = MessageHandler(Filters.text, post_description)
post_link_handler = MessageHandler(Filters.text, get_post)
postConversation_states = {'theme' : [theme_handler], "date":[date_handler],
                           "location" : [location_handler],
                           'vuz' : [vuz_handler],
                           "description":[description_handler],
                           "link":[post_link_handler]}
postConversation_handler = ConversationHandler([post_handler, post_handler_2],
                                               postConversation_states,
                                               fallbacks=support_handlers,
                                               allow_reentry = True)