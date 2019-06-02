"""
# -*- coding: utf-8 -*-
Created on Thu Dec 13 21:49:29 2018
@author: HP
"""
import datetime
import time
import pytz
import telegram
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter)
tz_msk = pytz.timezone('Europe/Moscow')

#collect logs for further development
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

#CONNECTING TO MONGO DB
from pymongo import MongoClient
client = MongoClient("mongodb+srv://Admin:RUJl1ZRJDnSykPvu@gettingstarted-ry5t1.mongodb.net/test?retryWrites=true")
db_test = client.test
db = client.university_events
users = db.users
event_posts = db.event_posts
organizations = db.organizations
admins = db.admins
notifications = db.notifications
moderators = db.moderators
feedback_data = db.feedback_data
analytics = db.analytics
event_themes = ['Career', 'Business & start-ups', 'Science', 'Culture', 'Self-development', 'Sport', 'Entertainment & networking', 'Other']
event_themes_dict = {'Карьера':'Career', 'Бизнес и предпринимательство': 'Business & start-ups', 'Наука' : 'Science', 'Культура' : 'Culture',
                     'Саморазвитие' : 'Self-development', 'Спорт' : 'Sport', 'Развлечения и нетворкинг' : 'Entertainment & networking', 'Иное' : 'Other'}
event_themes_dict_reverse = {'Career':'Карьера', 'Business & start-ups': 'Бизнес и предпринимательство', 'Science' : 'Наука',
                             'Culture' : 'Культура', 'Self-development' : 'Саморазвитие', 'Sport':'Спорт', 'Entertainment & networking' : 'Развлечения и нетворкинг', 'Other' : 'Иное'}
locations = ['Москва', 'Санкт-Петербург']
first_users = [153738613, 222287997, 159721328]
event_themes_russian = list(event_themes_dict_reverse.values())

#INTERFACE
def start(bot, update):
    """
    """
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
        text = """
                Привет! Подписывайся и получай анонсы событий в МГИМО и ВШЭ:)

Если хочешь поделиться анонсом, жми /post
                """
        keyboard = [["Подписаться", "Помощь"]]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id=update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
    else:
        text = "Ты уже подписан:)"
        bot.send_message(chat_id=update.message.chat_id,
                         text = text)
        help_function(bot, update)

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

# settings conversation
def settings(bot, update):
    """
    """
    cursor = users.find_one({'chat_id' : update.message.chat_id,
                             'subscriber' : True})
    if cursor == None:
        text = "Начни с подписки - /subscribe:)"
        bot.send_message(chat_id = update.message.chat_id,
                         text = text)
    else:
        cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                          'subscriber' : True})
        subscriptions_themes = ''
        subscriptions_organization = ''
        count_themes_non_subscribed = 0
        count_themes_subscribed = 0
        count_organizations_non_subscribed = 0
        count_organizations_subscribed = 0

        # getting event themes followed
        count = 0
        for theme in cursor_settings['event_theme']:
            if cursor_settings['event_theme'][theme]['status'] == True:
                count_themes_subscribed += 1
                if count == 0:
                    subscriptions_themes += cursor_settings['event_theme'][theme]['RU'].lower()
                    count += 1
                else:
                    subscriptions_themes += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
            else:
                count_themes_non_subscribed += 1
        #getting organizations followed
        count = 0
        for organization in cursor_settings['organization']:
            if cursor_settings['organization'][organization]['status'] == True:
                count_organizations_subscribed += 1
                if count == 0:
                    subscriptions_organization += cursor_settings['organization'][organization]['name']
                    count += 1
                else:
                    subscriptions_organization += (', ' + cursor_settings['organization'][organization]['name'])
            else:
                count_organizations_non_subscribed += 1
        # getting location name
        if cursor_settings['location'] == 'Москва':
            location = 'Москве'
        elif cursor_settings['location'] == 'Санкт-Петербург':
            location = 'Питере'
        # figuring out the text to send
        if count_themes_non_subscribed != 0:
            text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions_themes + '.\n'
        elif count_themes_subscribed == 0:
            text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n"
        else:
            text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions_themes + '.\n'
        if count_organizations_non_subscribed == 0:
            text += 'Также ты подписан на все организации в ' + location + ': ' + subscriptions_organization +'.\n'
        elif count_organizations_subscribed == 0:
            text += 'Также ты не подписан ни на одну из организаций в ' + location + '.\n'
        else:
            text += 'Также ты подписан на эти организации в ' + location + ': ' + subscriptions_organization + '.\n'
        text += 'Что сделать?:)'
        keyboard = [['Изменить тематики'], ['Изменить организации'], ['Изменить регион'], ['Изменить тип персонализации'], ['Всё ок!']]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
    return 'change settings'

def change_settings(bot, update):
    """
    """
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    if update.message.text == 'Изменить регион':
        text = 'В какой локации хочешь получать анонсы?'
        keyboard = [locations]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text, reply_markup = reply_markup)
        return 'change settings location'
    elif update.message.text == 'Изменить тематики':
        subscriptions_themes = ''
        count_themes_non_subscribed = 0
        count_themes_subscribed = 0
        count = 0
        for theme in cursor_settings['event_theme']:
            if cursor_settings['event_theme'][theme]['status'] == True:
                count_themes_subscribed += 1
                if count == 0:
                    subscriptions_themes += cursor_settings['event_theme'][theme]['RU'].lower()
                    count += 1
                else:
                    subscriptions_themes += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
            else:
                count_themes_non_subscribed += 1
        if cursor_settings['location'] == 'Москва':
            location = 'Москве'
        elif cursor_settings['location'] == 'Санкт-Петербург':
            location = 'Питере'
        if count_themes_non_subscribed != 0:
            text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions_themes + '.\n'
            keyboard = [['Добавить'], ['Удалить'], ['Всё ок!']]
        elif count_themes_subscribed == 0:
            text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n"
            keyboard = [['Добавить'], ['Всё ок!']]
        else:
            text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions_themes + '.\n'
            keyboard = [['Всё ок!'], ['Удалить']]
        text += 'Что сделать?:)'
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
        return 'change settings event themes'
    elif update.message.text == 'Изменить организации':
        subscriptions_organization = ''
        count_organizations_non_subscribed = 0
        count_organizations_subscribed = 0
        count = 0
        for organization in cursor_settings['organization']:
            if cursor_settings['organization'][organization]['status'] == True:
                count_organizations_subscribed += 1
                if count == 0:
                    subscriptions_organization += cursor_settings['organization'][organization]['name']
                    count += 1
                else:
                    subscriptions_organization += (', ' + cursor_settings['organization'][organization]['name'])
            else:
                count_organizations_non_subscribed += 1
        if cursor_settings['location'] == 'Москва':
            location = 'Москве'
        elif cursor_settings['location'] == 'Санкт-Петербург':
            location = 'Питере'
        if count_organizations_non_subscribed == 0:
            text = 'Ты подписан на все организации в ' + location + ': ' + subscriptions_organization +'.\n'
            keyboard = [['Всё ок!'], ['Удалить']]
        elif count_organizations_subscribed == 0:
            text = 'Ты не подписан ни на одну из организаций в ' + location + '.\n'
            keyboard = [['Добавить'], ['Всё ок!']]
        else:
            text = 'Ты подписан на эти организации в ' + location + ': ' + subscriptions_organization + '.\n'
            keyboard = [['Добавить'], ['Удалить'], ['Всё ок!']]
        text += 'Что сделать?:)'
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
        return 'change settings organizations'
    elif update.message.text == 'Всё ок!':
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Adiós!)')
        return -1
    elif update.message.text == 'Изменить тип персонализации':
            keyboard = ['ИЛИ', 'ТОЛЬКО']
            reply_markup = ReplyKeyboardMarkup([keyboard],
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            text = 'Выбери "ИЛИ", если хочешь получать анонсы событий выбранных категорий не только в организации, на которую ты подписался, но и в остальных в твоём городе.\n'
            bot.send_message(chat_id = update.message.chat_id,
                             text = text + 'Выбери "ТОЛЬКО", если хочешь получать анонсы только по выбранным категориям и только в организациях, на которые ты подписался)',
                             reply_markup = reply_markup)
            return 'change settings logic'

def change_settings_event_themes(bot, update):
    '''
    '''
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    if update.message.text == 'Добавить':
        non_subscriptions = []
        for theme in cursor_settings['event_theme']:
            if cursor_settings['event_theme'][theme]['status'] != True:
                non_subscriptions.append(cursor_settings['event_theme'][theme]['RU'])
        if len(non_subscriptions) > 0:
            text = 'Ты можешь подписаться на эти категории)'
            keyboard = [non_subscriptions]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            bot.send_message(chat_id = update.message.chat_id,
                             text = text,
                             reply_markup = reply_markup)
            return 'change settings event themes add'
        else:
            text = 'Ты уже подписан на все категории)'
            bot.send_message(chat_id = update.message.chat_id,
                             text = text)
            return -1
    elif update.message.text == 'Удалить':
        subscriptions = []
        for theme in cursor_settings['event_theme']:
            if cursor_settings['event_theme'][theme]['status'] == True:
                subscriptions.append(cursor_settings['event_theme'][theme]['RU'])
        if len(subscriptions) > 0:
            text = 'Что удалить из текущих подписок?'
            keyboard = [subscriptions]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
            return 'change settings event themes delete'
        else:
            text = "Хей, ты больше ни на что не подписан. Может стоит на что-то подписаться?"
            keyboard = [["Добавить", 'Всё ок!']]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
            bot.send_message(chat_id=update.message.chat_id,
                             text = text,
                             reply_markup = reply_markup)
            return 'change settings event themes'
    elif update.message.text == 'Всё ок!':
        subscriptions_themes = ''
        subscriptions_organization = ''
        count_themes_non_subscribed = 0
        count_themes_subscribed = 0
        count_organizations_non_subscribed = 0
        count_organizations_subscribed = 0

        # getting event themes followed
        count = 0
        for theme in cursor_settings['event_theme']:
            if cursor_settings['event_theme'][theme]['status'] == True:
                count_themes_subscribed += 1
                if count == 0:
                    subscriptions_themes += cursor_settings['event_theme'][theme]['RU'].lower()
                    count += 1
                else:
                    subscriptions_themes += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
            else:
                count_themes_non_subscribed += 1
        #getting organizations followed
        count = 0
        for organization in cursor_settings['organization']:
            if cursor_settings['organization'][organization]['status'] == True:
                count_organizations_subscribed += 1
                if count == 0:
                    subscriptions_organization += cursor_settings['organization'][organization]['name']
                    count += 1
                else:
                    subscriptions_organization += (', ' + cursor_settings['organization'][organization]['name'])
            else:
                count_organizations_non_subscribed += 1
        # getting location name
        if cursor_settings['location'] == 'Москва':
            location = 'Москве'
        elif cursor_settings['location'] == 'Санкт-Петербург':
            location = 'Питере'
        # figuring out the text to send
        if count_themes_non_subscribed != 0:
            text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions_themes + '.\n'
        elif count_themes_subscribed == 0:
            text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n"
        else:
            text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions_themes + '.\n'
        if count_organizations_non_subscribed == 0:
            text += 'Также ты подписан на все организации в ' + location + ': ' + subscriptions_organization +'.\n'
        elif count_organizations_subscribed == 0:
            text += 'Также ты не подписан ни на одну из организаций в ' + location + '.\n'
        else:
            text += 'Также ты подписан на эти организации в ' + location + ': ' + subscriptions_organization + '.\n'
        text += 'Что сделать?:)'
        keyboard = [['Изменить тематики'], ['Изменить организации'], ['Изменить регион'], ['Изменить тип персонализации'], ['Всё ок!']]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
        return 'change settings'

def change_settings_event_themes_add(bot, update):
    '''
    '''
    users.update_one({'chat_id' : update.message.chat_id, 'subscriber' : True},
                     {'$set' : {('event_theme.'+event_themes_dict[update.message.text]+'.status'):True}})
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    subscriptions = ''
    count_unsubscribed = 0
    count_subscribed = 0
    count = 0
    for theme in cursor_settings['event_theme']:
        if cursor_settings['event_theme'][theme]['status'] == True:
            count_subscribed += 1
            if count == 0:
                subscriptions += cursor_settings['event_theme'][theme]['RU'].lower()
                count += 1
            else:
                subscriptions += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
        else:
            count_unsubscribed += 1
    if cursor_settings['location'] == 'Москва':
        location = 'Москве'
    elif cursor_settings['location'] == 'Санкт-Петербург':
        location = 'Питере'

    if count_unsubscribed != 0:
        text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь подписаться / отписаться от каких-то категорий или оставить как есть. Что сделать?)'
        keyboard = [['Добавить', 'Удалить'], ['Всё ок!']]
    elif count_subscribed == 0:
        text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n\n" + 'Ты можешь добавить подписку или оставить как есть. Что сделать?)'
        keyboard = [['Добавить'], ['Всё ок!']]
    else:
        text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь оставить подписки как есть или отписаться от чего-то. Что сделать?)'
        keyboard = [['Всё ок!'], ['Удалить']]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id,
                     text = text,
                     reply_markup = reply_markup)
    return 'change settings event themes'

def change_settings_event_themes_delete(bot, update):
    '''
    '''
    users.update_one({'chat_id' : update.message.chat_id},
                     {'$set' : {('event_theme.'+event_themes_dict[update.message.text]+'.status'):False}})
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    subscriptions = ''
    count_unsubscribed = 0
    count_subscribed = 0
    count = 0
    for theme in cursor_settings['event_theme']:
        if cursor_settings['event_theme'][theme]['status'] == True:
            count_subscribed += 1
            if count == 0:
                subscriptions += cursor_settings['event_theme'][theme]['RU'].lower()
                count += 1
            else:
                subscriptions += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
        else:
            count_unsubscribed += 1
    if cursor_settings['location'] == 'Москва':
        location = 'Москве'
    elif cursor_settings['location'] == 'Санкт-Петербург':
        location = 'Питере'

    if count_unsubscribed != 0:
        text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь подписаться / отписаться от каких-то категорий или оставить как есть. Что сделать?)'
        keyboard = [['Добавить', 'Удалить'], ['Всё ок!']]
    elif count_subscribed == 0:
        text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n\n" + 'Ты можешь добавить подписку или оставить как есть. Что сделать?)'
        keyboard = [['Добавить'], ['Всё ок!']]
    else:
        text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь оставить подписки как есть или отписаться от чего-то. Что сделать?)'
        keyboard = [['Всё ок!'], ['Удалить']]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id,
                     text = text,
                     reply_markup = reply_markup)
    return 'change settings event themes'

def change_settings_organizations(bot, update):
    '''
    '''
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    if update.message.text == 'Добавить':
        non_subscriptions = []
        for unit in organizations.find({'location' : cursor_settings['location']}):
            if cursor_settings['organization'][unit['name']]['status'] != True:
                non_subscriptions.append(cursor_settings['organization'][unit['name']]['name'])
        if len(non_subscriptions) > 0:
            text = 'Ты можешь подписаться на эти организации)'
            keyboard = [non_subscriptions]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            bot.send_message(chat_id = update.message.chat_id,
                             text = text,
                             reply_markup = reply_markup)
            return 'change settings organizations add'
        else:
            text = 'Ты уже подписан на все категории)'
            bot.send_message(chat_id = update.message.chat_id,
                             text = text)
            return -1
    elif update.message.text == 'Удалить':
        subscriptions = []
        for unit in organizations.find({'location' : cursor_settings['location']}):
            if cursor_settings['organization'][unit['name']]['status'] != False:
                subscriptions.append(cursor_settings['organization'][unit['name']]['name'])
        if len(subscriptions) > 0:
            text = 'Что удалить из текущих подписок?'
            keyboard = [subscriptions]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard = True,
                                               resize_keyboard = True)
            bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
            return 'change settings organizations delete'
        else:
            text = "Хей, ты больше ни на что не подписан. Может стоит на что-то подписаться?"
            keyboard = [["Добавить", 'Всё ок!']]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
            bot.send_message(chat_id=update.message.chat_id,
                             text = text,
                             reply_markup = reply_markup)
            return 'change settings'
    elif update.message.text == 'Всё ок!':
        subscriptions_themes = ''
        subscriptions_organization = ''
        count_themes_non_subscribed = 0
        count_themes_subscribed = 0
        count_organizations_non_subscribed = 0
        count_organizations_subscribed = 0

        # getting event themes followed
        count = 0
        for theme in cursor_settings['event_theme']:
            if cursor_settings['event_theme'][theme]['status'] == True:
                count_themes_subscribed += 1
                if count == 0:
                    subscriptions_themes += cursor_settings['event_theme'][theme]['RU'].lower()
                    count += 1
                else:
                    subscriptions_themes += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
            else:
                count_themes_non_subscribed += 1
        #getting organizations followed
        count = 0
        for organization in cursor_settings['organization']:
            if cursor_settings['organization'][organization]['status'] == True:
                count_organizations_subscribed += 1
                if count == 0:
                    subscriptions_organization += cursor_settings['organization'][organization]['name']
                    count += 1
                else:
                    subscriptions_organization += cursor_settings['organization'][organization]['name']
            else:
                count_organizations_non_subscribed += 1
        # getting location name
        if cursor_settings['location'] == 'Москва':
            location = 'Москве'
        elif cursor_settings['location'] == 'Санкт-Петербург':
            location = 'Питере'
        # figuring out the text to send
        if count_themes_non_subscribed != 0:
            text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions_themes + '.\n'
        elif count_themes_subscribed == 0:
            text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n"
        else:
            text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions_themes + '.\n'
        if count_organizations_non_subscribed == 0:
            text += 'Также ты подписан на все организации в ' + location + ': ' + subscriptions_organization +'.\n'
        elif count_organizations_subscribed == 0:
            text += 'Также ты не подписан ни на одну из организаций в ' + location + '.\n'
        else:
            text += 'Также ты подписан на эти организации в ' + location + ': ' + subscriptions_organization + '.\n'
        text += 'Что сделать?:)'
        keyboard = [['Изменить тематики'], ['Изменить организации'], ['Изменить регион'], ['Изменить тип персонализации'], ['Всё ок!']]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard = True,
                                           resize_keyboard = True)
        bot.send_message(chat_id = update.message.chat_id,
                         text = text,
                         reply_markup = reply_markup)
        return 'change settings'

def change_settings_organizations_add(bot, update):
    '''
    '''
    users.update_one({'chat_id' : update.message.chat_id},
                     {'$set' : {('organization.'+update.message.text+'.status') : True}})
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    subscriptions = ''
    count_unsubscribed = 0
    count_subscribed = 0
    count = 0
    for unit in cursor_settings['organization']:
        if cursor_settings['organization'][unit]['status'] == True:
            count_subscribed += 1
            if count == 0:
                subscriptions += cursor_settings['organization'][unit]['name']
                count += 1
            else:
                subscriptions += (', ' + cursor_settings['organization'][unit]['name'])
        else:
            count_unsubscribed += 1
    if cursor_settings['location'] == 'Москва':
        location = 'Москве'
    elif cursor_settings['location'] == 'Санкт-Петербург':
        location = 'Питере'

    if count_unsubscribed != 0:
        text = "Сейчас ты подписан на эти организации в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь подписаться / отписаться на организации или оставить как есть. Что сделать?)'
        keyboard = [['Добавить', 'Удалить'], ['Всё ок!']]
    elif count_subscribed == 0:
        text = "Сейчас ты не подписан ни на одну организацию в " + location + ".\n\n" + 'Ты можешь добавить подписку или оставить как есть. Что сделать?)'
        keyboard = [['Добавить'], ['Всё ок!']]
    else:
        text = "Сейчас ты подписан на все организации в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь оставить подписки как есть или отписаться от чего-то. Что сделать?)'
        keyboard = [['Всё ок!'], ['Удалить']]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id,
                     text = text,
                     reply_markup = reply_markup)
    return 'change settings organizations'

def change_settings_organizations_delete(bot, update):
    '''
    '''
    users.update_one({'chat_id' : update.message.chat_id},
                     {'$set' : {('organization.'+update.message.text+'.status') : False}})
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    subscriptions = ''
    count_unsubscribed = 0
    count_subscribed = 0
    count = 0
    for unit in cursor_settings['organization']:
        if cursor_settings['organization'][unit]['status'] == True:
            count_subscribed += 1
            if count == 0:
                subscriptions += cursor_settings['organization'][unit]['name']
                count += 1
            else:
                subscriptions += (', ' + cursor_settings['organization'][unit]['name'])
        else:
            count_unsubscribed += 1
    if cursor_settings['location'] == 'Москва':
        location = 'Москве'
    elif cursor_settings['location'] == 'Санкт-Петербург':
        location = 'Питере'

    if count_unsubscribed == 0:
        text = "Сейчас ты подписан на эти организации в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь подписаться / отписаться на организации или оставить как есть. Что сделать?)'
        keyboard = [['Добавить', 'Удалить'], ['Всё ок!']]
    elif count_unsubscribed != 0:
        text = "Сейчас ты не подписан ни на одну из оргазинацию в " + location + ".\n\n" + 'Ты можешь добавить подписку или оставить как есть. Что сделать?)'
        keyboard = [['Добавить'], ['Всё ок!']]
    else:
        text = "Сейчас ты подписан на все организации в " + location + ": " + subscriptions + '.' + '\n\n' + 'Ты можешь оставить подписки как есть или отписаться от чего-то. Что сделать?)'
        keyboard = [['Всё ок!'], ['Удалить']]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id,
                     text = text,
                     reply_markup = reply_markup)
    return 'change settings organizations'

def change_settings_logic(bot, update):
    '''
    '''
    users.update_one({'chat_id' : update.message.chat_id, 'subscriber' : True},
                     {'$set' : {'preferences_logic' : update.message.text}})
    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    subscriptions_themes = ''
    subscriptions_organization = ''
    count_themes_non_subscribed = 0
    count_themes_subscribed = 0
    count_organizations_non_subscribed = 0
    count_organizations_subscribed = 0

    # getting event themes followed
    count = 0
    for theme in cursor_settings['event_theme']:
        if cursor_settings['event_theme'][theme]['status'] == True:
            count_themes_subscribed += 1
            if count == 0:
                subscriptions_themes += cursor_settings['event_theme'][theme]['RU'].lower()
                count += 1
            else:
                subscriptions_themes += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
        else:
            count_themes_non_subscribed += 1
    #getting organizations followed
    count = 0
    for organization in cursor_settings['organization']:
        if cursor_settings['organization'][organization]['status'] == True:
            count_organizations_subscribed += 1
            if count == 0:
                subscriptions_organization += cursor_settings['organization'][organization]['name']
                count += 1
            else:
                subscriptions_organization += (', ' + cursor_settings['organization'][organization]['name'])
        else:
            count_organizations_non_subscribed += 1
    # getting location name
    if cursor_settings['location'] == 'Москва':
        location = 'Москве'
    elif cursor_settings['location'] == 'Санкт-Петербург':
        location = 'Питере'
    # figuring out the text to send
    if count_themes_non_subscribed != 0:
        text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions_themes + '.\n'
    elif count_themes_subscribed == 0:
        text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n"
    else:
        text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions_themes + '.\n'
    if count_organizations_non_subscribed == 0:
        text += 'Также ты подписан на все организации в ' + location + ': ' + subscriptions_organization +'.\n'
    elif count_organizations_subscribed == 0:
        text += 'Также ты не подписан ни на одну из организаций в ' + location + '.\n'
    else:
        text += 'Также ты подписан на эти организации в ' + location + ': ' + subscriptions_organization + '.\n'
    text += 'Что сделать?:)'
    keyboard = [['Изменить тематики'], ['Изменить организации'], ['Изменить регион'], ['Изменить тип персонализации'], ['Всё ок!']]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id,
                     text = text,
                     reply_markup = reply_markup)
    return 'change settings'

def change_settings_location(bot, update):
    '''
    '''
    users.update_one({'chat_id' : update.message.chat_id, 'subscriber' : True},
                     {'$set' : {'location' : update.message.text}})

    cursor_settings = users.find_one({'chat_id' : update.message.chat_id,
                                      'subscriber' : True})
    cursor_organizations = organizations.find({})
    for unit in cursor_organizations:
        add = 'organization.' + unit['name']
        users.update_one({'chat_id' : update.message.chat_id},
                         {'$set' : {add : {'status' : False,
                                           'name' : unit['name']}}})
    subscriptions_themes = ''
    subscriptions_organization = ''
    count_themes_non_subscribed = 0
    count_themes_subscribed = 0
    count_organizations_non_subscribed = 0
    count_organizations_subscribed = 0

    # getting event themes followed
    count = 0
    for theme in cursor_settings['event_theme']:
        if cursor_settings['event_theme'][theme]['status'] == True:
            count_themes_subscribed += 1
            if count == 0:
                subscriptions_themes += cursor_settings['event_theme'][theme]['RU'].lower()
                count += 1
            else:
                subscriptions_themes += (', ' + cursor_settings['event_theme'][theme]['RU'].lower())
        else:
            count_themes_non_subscribed += 1
    #getting organizations followed
    count = 0
    for organization in cursor_settings['organization']:
        if cursor_settings['organization'][organization]['status'] == True:
            count_organizations_subscribed += 1
            if count == 0:
                subscriptions_organization += cursor_settings['organization'][organization]['name']
                count += 1
            else:
                subscriptions_organization += (', ' + cursor_settings['organization'][organization]['name'])
        else:
            count_organizations_non_subscribed += 1
    # getting location name
    if cursor_settings['location'] == 'Москва':
        location = 'Москве'
    elif cursor_settings['location'] == 'Санкт-Петербург':
        location = 'Питере'
    # костыльно меняем текст))))
    count_organizations_subscribed = 0
    if count_themes_non_subscribed != 0:
        text = "Сейчас ты подписан на эти категории событий в " + location + ": " + subscriptions_themes + '.\n'
    elif count_themes_subscribed == 0:
        text = "Сейчас ты не подписан ни на одну из категорий событий  в " + location + ".\n"
    else:
        text = "Сейчас ты подписан на все категории событий в " + location + ": " + subscriptions_themes + '.\n'
    if count_organizations_non_subscribed == 0:
        text += 'Также ты подписан на все организации в ' + location + ': ' + subscriptions_organization +'.\n'
    elif count_organizations_subscribed == 0:
        text += 'Также ты не подписан ни на одну из организаций в ' + location + '.\n'
    else:
        text += 'Также ты подписан на эти организации в ' + location + ': ' + subscriptions_organization + '.\n'
    text += 'Что сделать?:)'
    keyboard = [['Изменить тематики'], ['Изменить организации'], ['Изменить регион'], ['Изменить тип персонализации'], ['Всё ок!']]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard = True,
                                       resize_keyboard = True)
    bot.send_message(chat_id = update.message.chat_id,
                     text = text,
                     reply_markup = reply_markup)
    return 'change settings'

#get updates on demand
def send_today(bot, update):
    '''
    ??? for now - just all the events
    #event after that time on that particular day
    '''
    cursor = users.find_one({'chat_id' : update.message.chat_id, 'subscriber' : True})


    if cursor != None:
        location = cursor['location']
        # iterate through subscriptions
        sent_objectID = []
        today = datetime.date.today()
        cursor_events = event_posts.find({'decision':'approved', 'location' : location,
                                          'year' : today.year,
                                          'month' : today.month,
                                          'day' : today.day})
        if cursor_events != None:
            if cursor['preferences_logic'] == 'ИЛИ':
                # iterating through categories
                for theme in cursor['event_theme']:
                    if cursor['event_theme'][theme]['status'] == True:
                        cursor_events = event_posts.find({'event_theme' : theme, 'location' : location,
                                                          'decision':'approved',
                                                          'year' : today.year,
                                                          'month' : today.month,
                                                          'day' : today.day})
                        if cursor_events != None:
                            for event in cursor_events:
                                if event['_id'] not in sent_objectID:
                                    sent_objectID.append(event['_id'])
                                    time = str(event['date_time_msk'].time())[:-3]
                                    if str(time) == '00:00':
                                        time = 'NA'
                                    try:
                                        event_name = event['event_name']
                                    except KeyError:
                                        event_name = 'NA'
                                    text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                    if event_name != 'NA':
                                        text += event_name + '\n'
                                    text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                                    bot.send_message(chat_id = update.message.chat_id,
                                                     text = text)
                                    time.sleep(1)
                # iterating through organizers
                for unit in cursor['organization']:
                    if cursor['organization'][unit]['status'] == True:
                        cursor_events = event_posts.find({'organization' : unit, 'location' : location,
                                                          'decision':'approved',
                                                          'year' : today.year,
                                                          'month' : today.month,
                                                          'day' : today.day})
                        if cursor_events != None:
                            for event in cursor_events:
                                if event['_id'] not in sent_objectID:
                                    sent_objectID.append(event['_id'])
                                    time = str(event['date_time_msk'].time())[:-3]
                                    if str(time) == '00:00':
                                        time = 'NA'
                                    try:
                                        event_name = event['event_name']
                                    except KeyError:
                                        event_name = 'NA'
                                    text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                    if event_name != 'NA':
                                        text += event_name + '\n'
                                    text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                                    bot.send_message(chat_id = update.message.chat_id,
                                                     text = text)
                                    time.sleep(1)
            elif cursor['preferences_logic'] == 'ТОЛЬКО':
                # iterating through categories
                for theme in cursor['event_theme']:
                    if cursor['event_theme'][theme]['status'] == True:
                        for unit in cursor['organization']:
                            if cursor['organization'][unit]['status'] == True:
                                cursor_events = event_posts.find({'event_theme' : theme, 'location' : location,
                                                                  'organization' : unit,
                                                                  'decision':'approved',
                                                                  'year' : today.year,
                                                                  'month' : today.month,
                                                                  'day' : today.day})
                                if cursor_events != None:
                                    for event in cursor_events:
                                        if event['_id'] not in sent_objectID:
                                            sent_objectID.append(event['_id'])
                                            time = str(event['date_time_msk'].time())[:-3]
                                            if str(time) == '00:00':
                                                time = 'NA'
                                            try:
                                                event_name = event['event_name']
                                            except KeyError:
                                                event_name = 'NA'
                                            text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                            if event_name != 'NA':
                                                text += event_name + '\n'
                                            text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                                            bot.send_message(chat_id = update.message.chat_id,
                                                             text = text)
                                            time.sleep(1)
        else:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Событий на сегодня нет')
        if len(sent_objectID) == 0:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Событий на сегодня нет')
    else:
        users.update_one({'chat_id' : update.message.chat_id, 'subscriber' : False},
                         {'$set' : {'latest_send_today_interaction' : str(datetime.date.today())}})
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Ты не подписан, поэтому отправлю тебе все события на сегодня без персонализации. Чтобы подписаться, жми /subscribe')
        sent_objectID = []
        today = datetime.date.today()
        cursor_events = event_posts.find({'decision' : 'approved',
                                          'year' : today.year,
                                          'month' : today.month,
                                          'day' : today.day})
        if cursor_events != None:
            for event in cursor_events:
                if event['_id'] not in sent_objectID:
                    sent_objectID.append(event['_id'])
                    time = str(event['date_time_msk'].time())[:-3]
                    if str(time) == '00:00':
                        time = 'NA'
                    try:
                        event_name = event['event_name']
                    except KeyError:
                        event_name = 'NA'
                    text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                    if event_name != 'NA':
                        text += event_name + '\n'
                    text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                    bot.send_message(chat_id = update.message.chat_id,
                                     text = text)
                    time.sleep(1)
        else:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Событий на сегодня нет')

def send_tomorrow(bot, update):
    '''
    '''
    cursor = users.find_one({'chat_id' : update.message.chat_id, 'subscriber' : True})

    if cursor != None:
        location = cursor['location']
        # iterate through subscriptions
        sent_objectID = []
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        cursor_events = event_posts.find({'decision':'approved', 'location' : location,
                                          'year' : tomorrow.year,
                                          'month' : tomorrow.month,
                                          'day' : tomorrow.day})
        if cursor_events != None:
            if cursor['preferences_logic'] == 'ИЛИ':
                # iterating through categories
                for theme in cursor['event_theme']:
                    if cursor['event_theme'][theme]['status'] == True:
                        cursor_events = event_posts.find({'event_theme' : theme, 'location' : location,
                                                          'decision':'approved',
                                                          'year' : tomorrow.year,
                                                          'month' : tomorrow.month,
                                                          'day' : tomorrow.day})
                        if cursor_events != None:
                            for event in cursor_events:
                                if event['_id'] not in sent_objectID:
                                    sent_objectID.append(event['_id'])
                                    time = str(event['date_time_msk'].time())[:-3]
                                    if str(time) == '00:00':
                                        time = 'NA'
                                    try:
                                        event_name = event['event_name']
                                    except KeyError:
                                        event_name = 'NA'
                                    text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                    if event_name != 'NA':
                                        text += event_name + '\n'
                                    text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                                    bot.send_message(chat_id = update.message.chat_id,
                                                     text = text)
                                    time.sleep(1)
                # iterating through organizers
                for unit in cursor['organization']:
                    if cursor['organization'][unit]['status'] == True:
                        cursor_events = event_posts.find({'organization' : unit, 'location' : location,
                                                          'decision':'approved',
                                                          'year' : tomorrow.year,
                                                          'month' : tomorrow.month,
                                                          'day' : tomorrow.day})
                        if cursor_events != None:
                            for event in cursor_events:
                                if event['_id'] not in sent_objectID:
                                    sent_objectID.append(event['_id'])
                                    time = str(event['date_time_msk'].time())[:-3]
                                    if str(time) == '00:00':
                                        time = 'NA'
                                    try:
                                        event_name = event['event_name']
                                    except KeyError:
                                        event_name = 'NA'
                                    text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                    if event_name != 'NA':
                                        text += event_name + '\n'
                                    text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                                    bot.send_message(chat_id = update.message.chat_id,
                                                     text = text)
                                    time.sleep(1)
            elif cursor['preferences_logic'] == 'ТОЛЬКО':
                # iterating through categories
                for theme in cursor['event_theme']:
                    if cursor['event_theme'][theme]['status'] == True:
                        for unit in cursor['organization']:
                            if cursor['organization'][unit]['status'] == True:
                                cursor_events = event_posts.find({'event_theme' : theme, 'location' : location,
                                                                  'organization' : unit,
                                                                  'decision':'approved',
                                                                  'year' : tomorrow.year,
                                                                  'month' : tomorrow.month,
                                                                  'day' : tomorrow.day})
                                if cursor_events != None:
                                    for event in cursor_events:
                                        if event['_id'] not in sent_objectID:
                                            sent_objectID.append(event['_id'])
                                            time = str(event['date_time_msk'].time())[:-3]
                                            if str(time) == '00:00':
                                                time = 'NA'
                                            try:
                                                event_name = event['event_name']
                                            except KeyError:
                                                event_name = 'NA'
                                            text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                            if event_name != 'NA':
                                                text += event_name + '\n'
                                            text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                                            bot.send_message(chat_id = update.message.chat_id,
                                                             text = text)
                                            time.sleep(1)
        else:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Событий на завтра нет')
        if len(sent_objectID) == 0:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Событий на завтра нет')
    else:
        users.update_one({'chat_id' : update.message.chat_id, 'subscriber' : False},
                         {'$set' : {'latest_send_tomorrow_interaction' : str(datetime.date.today())}})
        bot.send_message(chat_id = update.message.chat_id,
                         text = 'Ты не подписан, поэтому отправлю тебе все события на завтра без персонализации. Чтобы подписаться, жми /subscribe')
        sent_objectID = []
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        cursor_events = event_posts.find({'decision' : 'approved',
                                          'year' : tomorrow.year,
                                          'month' : tomorrow.month,
                                          'day' : tomorrow.day})
        if cursor_events != None:
            for event in cursor_events:
                if event['_id'] not in sent_objectID:
                    sent_objectID.append(event['_id'])
                    time = str(event['date_time_msk'].time())[:-3]
                    if str(time) == '00:00':
                        time = 'NA'
                    try:
                        event_name = event['event_name']
                    except KeyError:
                        event_name = 'NA'
                    text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                    if event_name != 'NA':
                        text += event_name + '\n'
                    text += ('Время: ' + time + '. ' + event['organization'] +'\n' + event["link"])
                    bot.send_message(chat_id = update.message.chat_id,
                                     text = text)
                    time.sleep(1)
        else:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Событий на завтра нет')

def send_week(bot, update, num_days = 7):
    '''
    '''
    cursor = users.find_one({'chat_id' : update.message.chat_id,'subscriber' : True})
    if cursor != None: # iterate through subscriptions
        location = cursor['location']
        sent_objectID = []
        days = []
        today = datetime.date.today()
        iterate = 0
        for i in range(num_days + 1):
            days.append(today + datetime.timedelta(days=iterate))
            iterate += 1
        days_no_events = 0
        days_processed = 0

        if cursor['preferences_logic'] == 'ИЛИ':
            for day in days:
                    for theme in cursor['event_theme']:
                        if cursor['event_theme'][theme]['status'] == True:

                                cursor_events = event_posts.find({'event_theme' : theme, 'location' : location,
                                                                  'decision':'approved',
                                                                  'year' : day.year,
                                                                  'month' : day.month,
                                                                  'day' : day.day})
                                if cursor_events != None:
                                    for event in cursor_events:
                                        if event['_id'] not in sent_objectID:
                                            date_time = event['date_time_msk'].strftime('%d.%m.%Y %H:%M')
                                            if date_time[-5:] == '00:00':
                                                date_time = date_time[:-5] + 'NA'
                                            try:
                                                event_name = event['event_name']
                                            except KeyError:
                                                event_name = 'NA'
                                            text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                            if event_name != 'NA':
                                                text += event_name + '\n'
                                            sent_objectID.append(event['_id'])
                                            text += ('Дата и время: ' + date_time + '. ' + event['organization'] +'\n' + event["link"])
                                            bot.send_message(chat_id = update.message.chat_id,
                                                             text = text)
                                            time.sleep(1)
                    for unit in cursor['organization']:
                        if cursor['organization'][unit]['status'] == True:
                            cursor_events = event_posts.find({'organization' : unit, 'location' : location,
                                                              'decision':'approved',
                                                              'year' : day.year,
                                                              'month' : day.month,
                                                              'day' : day.day})
                            if cursor_events != None:
                                for event in cursor_events:
                                    if event['_id'] not in sent_objectID:
                                        date_time = event['date_time_msk'].strftime('%d.%m.%Y %H:%M')
                                        if date_time[-5:] == '00:00':
                                            date_time = date_time[:-5] + 'NA'
                                        sent_objectID.append(event['_id'])
                                        try:
                                            event_name = event['event_name']
                                        except KeyError:
                                            event_name = 'NA'
                                        text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                        if event_name != 'NA':
                                            text += event_name + '\n'
                                        text += ('Дата и время: ' + date_time + '. ' + event['organization'] +'\n' + event["link"])
                                        bot.send_message(chat_id = update.message.chat_id,
                                                         text = text)
                                        time.sleep(1)
        elif cursor['preferences_logic'] == 'ТОЛЬКО':
            for day in days:
                for theme in cursor['event_theme']:
                    if cursor['event_theme'][theme]['status'] == True:
                        for unit in cursor['organization']:
                            if cursor['organization'][unit]['status'] == True:
                                cursor_events = event_posts.find({'event_theme' : theme, 'location' : location,
                                                                  'organization' : unit,
                                                                  'decision':'approved',
                                                                  'year' : day.year,
                                                                  'month' : day.month,
                                                                  'day' : day.day})
                                if cursor_events != None:
                                    for event in cursor_events:
                                        if event['_id'] not in sent_objectID:
                                            date_time = event['date_time_msk'].strftime('%d.%m.%Y %H:%M')
                                            if date_time[-5:] == '00:00':
                                                date_time = date_time[:-5] + 'NA'
                                            sent_objectID.append(event['_id'])
                                            try:
                                                event_name = event['event_name']
                                            except KeyError:
                                                event_name = 'NA'
                                            text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                                            if event_name != 'NA':
                                                text += event_name + '\n'
                                            text += ('Дата и время: ' + date_time + '. ' + event['organization'] +'\n' + event["link"])
                                            bot.send_message(chat_id = update.message.chat_id,
                                                             text = text)
                                            time.sleep(1)
        if len(sent_objectID) == 0:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'Событий на неделю нет')
    else:
        users.update_one({'chat_id' : update.message.chat_id, 'subscriber' : False},
                         {'$set' : {'latest_send_week_interaction' : str(datetime.date.today())}})
        bot.send_message(chat_id = update.message.chat_id,
                 text = 'Ты не подписан, поэтому отправлю тебе все события на неделю без персонализации. Чтобы подписаться, жми /subscribe')
        sent_objectID = []
        days = []
        today = datetime.date.today()
        iterate = 0
        for i in range(num_days + 1):
            days.append(today + datetime.timedelta(days=iterate))
            iterate += 1
        days_no_events = 0
        days_processed = 0
        for day in days:
            days_processed += 1
            cursor_events = event_posts.find({'decision':'approved',
                                              'year' : day.year,
                                              'month' : day.month,
                                              'day' : day.day})
            if cursor_events != None:
                for event in cursor_events:
                    if event['_id'] not in sent_objectID:
                        date_time = event['date_time_msk'].strftime('%d.%m.%Y %H:%M')
                        if date_time[-5:] == '00:00':
                            date_time = date_time[:-5] + 'NA'
                        sent_objectID.append(event['_id'])
                        try:
                            event_name = event['event_name']
                        except KeyError:
                            event_name = 'NA'
                        text = '#' + event['event_theme'].replace(" ", "_") + '\n\n'
                        if event_name != 'NA':
                            text += event_name + '\n'
                        text += ('Дата и время: ' + date_time + '. ' + event['organization'] +'\n' + event["link"])
                        bot.send_message(chat_id = update.message.chat_id,
                                         text = text)
                        time.sleep(1)
            else:
                days_no_events += 1
        if days_processed == days_no_events:
            bot.send_message(chat_id = update.message.chat_id,
                             dtext = 'Событий на неделю нет')

#feedback conversation
def feedback(bot, update):
    """
    """
    text = "Спасибо, что помогаешь мне становиться лучше;) Каждую неделю мы обрабатываем отзывы:)\nЧего не хватает? Отправляй, пожалуйста, одним сообщением."
    bot.send_message(chat_id=update.message.chat_id, text = text)
    return "feedback better"

def feedback_better(bot, update):
    """
    """
    if feedback_data.find_one({'chat_id' : update.message.chat_id}) == None:
        feedback_data.insert_one({'chat_id' : update.message.chat_id, "what doest it lack?":update.message.text})
    else:
        feedback_data.update_one({'chat_id' : update.message.chat_id}, {"$set":{"what does it lack?":update.message.text}})
    text = "Что мне стоит улучшить?"
    bot.send_message(chat_id=update.message.chat_id, text = text)
    return "feedback else"

def feedback_else(bot, update):
    """
    """
    feedback_data.update_one({'chat_id' : update.message.chat_id}, {"$set":{"how to do better?":update.message.text}})
    text = "Что-нибудь ещё?"
    bot.send_message(chat_id=update.message.chat_id, text = text)
    return "thank you"

def feedback_thank_you(bot, update):
    """
    """
    feedback_data.update_one({'chat_id' : update.message.chat_id}, {"$set":{"Anything else?":update.message.text}, "$currentDate":{"lastModified":True}})
    text = "Спасибо!"
    bot.send_message(chat_id=update.message.chat_id, text = text)
    help_function(bot, update)
    return -1

#post conversation
def post(bot, update):
    """
    """
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

### communication with users

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

## search
#def find_events(bot, update):
#    '''
#    '''
#    keyboard = [['Сегодня', 'Завтра'], ['Эта неделя', 'Следующая неделя'], ['Иная дата']]
#    reply_markup = ReplyKeyboardMarkup(keyboard,
#                                       one_time_keyboard = True,
#                                       resize_keyboard = True)
#    bot.send_messsage(chat_id = update.message.chat_id, reply_markup = reply_markup, text = 'Когда ищешь события?')
#    return 'date'
#
#def find_events_date(bot, update):
#    '''
#    '''
#    date = []
#    if update.message.text == 'Сегодня':
#        date.append(datetime.date.today())
#    elif update.message.text == 'Завтра':
#        date.append(datetime.date.today() + datetime.timedelta(days=1))
#    elif update.message.text == 'Эта неделя':
#        today = datetime.date.today()
#        date.append(today)
#        for i in range(7):
#            days.append(today + datetime.timedelta(days = i))
#    elif update.message.text == 'Следующая неделя':
#        aaaaaaaa
#    elif update.message.text == 'Иная дата':
#        bot.send_message(chat_id = update.message.chat_id, text = '')
#        return 'find_events_date_specific'
#    cursor = users.find_one({'chat_id' : update.message.chat_id})
#    try:
#        if cursor['search']['id_counter'] != None:
#            new_search_id = cursor['search']['id_counter'] + 1
#    except KeyError:
#        new_search_id = 1
#    users.update_one({'chat_id' : update.message.chat_id}, {'$set' : {'search.collection' : {'id' : new_search_id, 'current' : True, 'date' : update.message.text}}}})
#    return ''
#
#def find_events_date_specific(bot, update):
#    '''
#    '''


# HELP // FALLBACK FUNCTIONS

def unknown(bot, update):
    """
    """
    text = "Такой команды нет. Выбери команду из списка:)"
    bot.send_message(chat_id=update.message.chat_id,
                     text = text)
    time.sleep(1)
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


"""
CUSTOM FILTERS
"""

class SubscribeFilter(BaseFilter):
    def filter(self, message):
        return 'Подписаться' in message.text
filter_subscribe = SubscribeFilter()

class notify_filter(BaseFilter):
    def filter(self, message):
        return '/notify' in message.text
filter_notify = notify_filter()

class post_filter(BaseFilter):
    def filter(self, message):
        return '/post' in message.text
filter_post = post_filter()

class check_filter(BaseFilter):
    def filter(self, message):
        return '/check' in message.text
filter_check = check_filter()

class feedback_filter(BaseFilter):
    def filter(self, message):
        return '/feedback' in message.text
filter_feedback = feedback_filter()

class send_today_filter(BaseFilter):
    def filter(self, message):
        return '/today' in message.text
filter_send_today = send_today_filter()

class send_tomorrow_filter(BaseFilter):
    def filter(self, message):
        return '/tomorrow' in message.text
filter_send_tomorrow = send_tomorrow_filter()

class send_week_filter(BaseFilter):
    def filter(self, message):
        return '/week' in message.text
filter_send_week = send_week_filter()

"""
adding commands to handlers and dispatchers
"""
start_handler = CommandHandler('start', start)
send_today_handler = CommandHandler('today', send_today)
send_today_handler_2 = MessageHandler(filter_send_today, send_today)
send_tomorrow_handler = CommandHandler('tomorrow', send_tomorrow)
send_tomorrow_handler_2 = MessageHandler(filter_send_tomorrow, send_tomorrow)
send_week_handler = CommandHandler('week', send_week)
send_week_handler_2 = MessageHandler(filter_send_week, send_week)
help_function_handler = CommandHandler('help', help_function)
unknown_handler = MessageHandler(Filters.command, unknown)
other_handler = MessageHandler(Filters.all, other)
error_handler = MessageHandler(Filters.all, error)
support_handlers=[help_function_handler, unknown_handler, other_handler, error_handler]

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

settings_handler = CommandHandler('settings', settings)
change_settings_handler = MessageHandler(Filters.text, change_settings)
change_settings_organizations_handler = MessageHandler(Filters.text,change_settings_organizations)
change_settings_event_themes_handler = MessageHandler(Filters.text, change_settings_event_themes)
change_settings_logic_handler = MessageHandler(Filters.text, change_settings_logic)
change_settings_event_themes_add_handler = MessageHandler(Filters.text, change_settings_event_themes_add)
change_settings_event_themes_delete_handler = MessageHandler(Filters.text, change_settings_event_themes_delete)
change_settings_organizations_add_handler = MessageHandler(Filters.text, change_settings_organizations_add)
change_settings_organizations_delete_handler = MessageHandler(Filters.text, change_settings_organizations_delete)
change_settings_location_handler = MessageHandler(Filters.text, change_settings_location)
settingsConversation_states = {'change settings' : [change_settings_handler],
                               'change settings event themes' : [change_settings_event_themes_handler],
                               'change settings organizations' : [change_settings_organizations_handler],
                               'change settings logic' : [change_settings_logic_handler],
                               'change settings event themes add' : [change_settings_event_themes_add_handler],
                               'change settings event themes delete' : [change_settings_event_themes_delete_handler],
                               'change settings organizations add' : [change_settings_organizations_add_handler],
                               'change settings organizations delete' : [change_settings_organizations_delete_handler],
                               'change settings location' : [change_settings_location_handler]}
settingsConversation_handler = ConversationHandler([settings_handler],
                                                   settingsConversation_states,
                                                   fallbacks = support_handlers,
                                                   allow_reentry = True)

feedback_handler = CommandHandler('feedback', feedback)
feedback_handler_2 = MessageHandler(filter_feedback, feedback)
feedback_message = MessageHandler(Filters.text, feedback_better)
feedback_message2 = MessageHandler(Filters.text, feedback_else)
feedback_thankyou_handler = MessageHandler(Filters.text, feedback_thank_you)
feedbackConversation_states = {"feedback better":[feedback_message],
                               "feedback else": [feedback_message2],
                               "thank you": [feedback_thankyou_handler]}
feedbackConversation_handler = ConversationHandler([feedback_handler, feedback_handler_2],
                                                   feedbackConversation_states,
                                                   fallbacks = support_handlers,
                                                   allow_reentry = True)

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

'''
setting up MessageQueue to avoid flood limits
'''
from telegram.ext import messagequeue as mq
from telegram.utils.request import Request

class MQBot(telegram.bot.Bot):
    '''A subclass of Bot which delegates send method handling to MQ'''
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(MQBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).send_message(*args, **kwargs)

"""
START THE BOT
"""
if __name__ == '__main__':
    # token real bot - '758302240:AAE4I8YXlhy5UKRMOTcYcxR2WDJOkRsiB3k'
    # token test bot - '722203998:AAEbkJlsVsL6GEtoaM1P5uOwEO1cp59Jii0'
    token = '722203998:AAEbkJlsVsL6GEtoaM1P5uOwEO1cp59Jii0' #test
    #token = '669950033:AAFIslzL5nfxPms-aV6ivQmZdMEWPr1z6vw' # my another account
    #bot = telegram.Bot(token)
    queue = mq.MessageQueue(all_burst_limit = 29, all_time_limit_ms = 1017)
    request = Request(con_pool_size = 8)
    MQBot_test = MQBot(token, request = request, mqueue = queue)
    updater = Updater(bot = MQBot_test)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(subscribeConversation_handler)
    dispatcher.add_handler(postConversation_handler) # not working
    dispatcher.add_handler(processingConversation_handler) # not working
    dispatcher.add_handler(send_today_handler)
    dispatcher.add_handler(send_tomorrow_handler)
    dispatcher.add_handler(send_week_handler)
    dispatcher.add_handler(send_today_handler_2)
    dispatcher.add_handler(send_tomorrow_handler_2)
    dispatcher.add_handler(send_week_handler_2)
    dispatcher.add_handler(settingsConversation_handler)
    dispatcher.add_handler(notificationConversation_handler) # not working
    dispatcher.add_handler(feedbackConversation_handler) # not working
    dispatcher.add_handler(help_function_handler)
    dispatcher.add_handler(unknown_handler)
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(other_handler)

    updater.start_polling()
    updater.idle()
