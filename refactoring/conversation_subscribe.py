# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 15:15:41 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter)
from command_helpers import support_handlers, help_function
from telegram import ReplyKeyboardMarkup
import datetime
import pytz
tz_msk = pytz.timezone('Europe/Moscow')
from db_connection import users, event_themes, analytics, locations, event_themes_dict_reverse, organizations

def subscribe(bot, update):
    """
    """
    cursor = users.find_one({'chat_id' : update.message.chat_id,
                             'subscriber' : True})
    if cursor == None:
        users.update_one({'chat_id' : update.message.chat_id},
                         {"$set": {"start_subscription" : datetime.datetime.now(tz=tz_msk),
                                   'subscriber' : True}})
        for theme in event_themes:
            add = 'event_theme.' + theme
            users.update_one({'chat_id' : update.message.chat_id},
                             {'$set' : {add : {'status' : True, 'RU': event_themes_dict_reverse[theme]},
                                        'last_modified' : datetime.datetime.now(tz=tz_msk)}})
        analytics.update_one({"segment" : "users"},
                             {'$inc' : {'data.user_base' : 1}})
        text = 'В какой локации хочешь получать анонсы?'
        keyboard = [locations]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text, reply_markup = reply_markup)
        return 'set location'
    else:
        text = "Ты уже подписан:)"
        bot.send_message(chat_id = update.message.chat_id,
                         text = text)
        help_function(bot, update)

def set_location(bot, update):
    '''
    '''
    if (update.message.text == 'Москва' or update.message.text == 'Санкт-Петербург'):
        users.update_one({'chat_id' : update.message.chat_id},
                         {'$set' : {'location' : update.message.text}})
        cursor_organizations = organizations.find({'location' : update.message.text})
        organizations_list = []
        for unit in cursor_organizations:
            organizations_list.append(unit['name'])
            add = 'organization.' + unit['name']
            users.update_one({'chat_id' : update.message.chat_id},
                             {'$set' : {add : {'status' : False,
                                               'name' : unit['name']}}})
        organizations_list.append('Закончить')
        keyboard = [organizations_list]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'На какие организации ты хочешь подписаться? Выбирай по-очереди!',
                         reply_markup = reply_markup)
        return 'set organizations recurrent'
    else:
        keyboard = [locations]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Для выбора, нажми на соответствующую кнопку:)',
                         reply_markup = reply_markup)
        return 'set location'

def set_organizations_recurrent(bot, update):
    '''
    '''
    non_subscribed_organizations_list = []
    subscribed_organizations_list = []
    cursor_user = users.find_one({'chat_id' : update.message.chat_id})
    for unit in organizations.find({'location' : cursor_user['location']}):
        if cursor_user['organization'][unit['name']]['status'] == False:
            non_subscribed_organizations_list.append(unit['name'])
        else:
            subscribed_organizations_list.append(unit['name'])

    if update.message.text in non_subscribed_organizations_list:
        users.update_one({'chat_id' : update.message.chat_id},
                         {'$set' : {('organization.' + update.message.text) : {'status' : True, 'name' : update.message.text}}})
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Добавлено!')
        non_subscribed_organizations_list.remove(update.message.text)
        subscribed_organizations_list.append(update.message.text)


        cursor_organizations = organizations.find({})
        if len(non_subscribed_organizations_list) == 0:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Ты уже подписался на все доступные организации)')
            return set_preferences_logic(bot, update)
        elif len(subscribed_organizations_list) == 0:
            non_subscribed_organizations_list.append('Закончить')
            keyboard = [non_subscribed_organizations_list]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'На какие организации ты хочешь подписаться?',
                             reply_markup = reply_markup)
            return 'set organizations recurrent'
        else:
            non_subscribed_organizations_list.append('Закончить')
            keyboard = [non_subscribed_organizations_list]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'На какие ещё организации ты хочешь подписаться?',
                             reply_markup = reply_markup)
            return 'set organizations recurrent'
    elif update.message.text == 'Закончить':
        if len(subscribed_organizations_list) > 0:
            keyboard = ['ИЛИ', 'ТОЛЬКО']
            reply_markup = ReplyKeyboardMarkup([keyboard],
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            text = 'Выбери "ИЛИ", если хочешь получать анонсы событий выбранных категорий не только в организации, на которую ты подписался, но и в остальных в твоём городе.\n'
            text += 'Выбери "ТОЛЬКО", если хочешь получать анонсы только по выбранным категориям и только в организациях, на которые ты подписался)'
            bot.send_message(chat_id = update.message.chat_id,
                             text = text,
                             reply_markup = reply_markup)
            return 'set preferences logic'
        else:
            text = """
        А теперь получай анонсы событий в одном месте:). По мере появления, я буду отправлять их тебе.\n
По умолчанию, тебе будут приходить все анонсы. Для большей персонализации, жми /settings :)
        """
            bot.send_message(chat_id = update.message.chat_id, text = text)
            help_function(bot, update)
            return -1
    else:
        cursor_organizations = organizations.find({})
        organizations_list = []
        for unit in cursor_organizations:
            organizations_list.append(unit['name'])
        organizations_list.append('Закончить')
        keyboard = [organizations_list]
        reply_markup = ReplyKeyboardMarkup([keyboard],
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Для выбора нажми на соответствующую кнопку. На какие организации ты хочешь подписаться? Выбирай по-очереди!',
                         reply_markup = reply_markup)
        return 'set organizations recurrent'

def set_preferences_logic(bot, update):
    '''
    '''
    if update.message.text in ['ИЛИ', 'ТОЛЬКО']:
        users.update_one({'chat_id' : update.message.chat_id},
                         {'$set' : {'preferences_logic' : update.message.text}})
        text = """
        А теперь получай анонсы событий в одном месте:). По мере появления, я буду отправлять их тебе.\n
По умолчанию, тебе будут приходить все анонсы. Для большей персонализации, жми /settings :)
        """
        bot.send_message(chat_id = update.message.chat_id, text = text)
        help_function(bot, update)
        return -1
    else:
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Для выбора, нажми на соответствующую кнопку:)')
        keyboard = ['ИЛИ', 'ТОЛЬКО']
        reply_markup = ReplyKeyboardMarkup([keyboard],
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        text = 'Выбери "ИЛИ", если хочешь получать анонсы, как по категориям, так и по организациямю\n'
        bot.send_message(chat_id = update.message.chat_id,
                         text = text + 'Выбери "ТОЛЬКО", если хочешь получать анонсы только от выбранных организаций по заданным тематикам)',
                         reply_markup = reply_markup)
        return 'set preferences logic'

class SubscribeFilter(BaseFilter):
    def filter(self, message):
        return 'Подписаться' in message.text
filter_subscribe = SubscribeFilter()


subscribe_handler = CommandHandler('subscribe', subscribe)
subscribe_handler2 = MessageHandler(filter_subscribe, subscribe)
subscribe_set_location_handler = MessageHandler(Filters.text, set_location)
subscribe_set_organizations_recurrent_handler = MessageHandler(Filters.text, set_organizations_recurrent)
subscribe_set_preferences_logic = MessageHandler(Filters.text, set_preferences_logic)
subscribeConversation_states = {'set location' : [subscribe_set_location_handler],
                                'set organizations recurrent' : [subscribe_set_organizations_recurrent_handler],
                                'set preferences logic' : [subscribe_set_preferences_logic]}
subscribeConversation_handler = ConversationHandler([subscribe_handler, subscribe_handler2],
                                                    subscribeConversation_states,
                                                    fallbacks = support_handlers,
                                                    allow_reentry = True)