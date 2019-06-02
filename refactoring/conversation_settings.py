# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 15:25:14 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler)
from command_helpers import support_handlers
from telegram import ReplyKeyboardMarkup
from db_connection import users, locations, event_themes_dict, organizations

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