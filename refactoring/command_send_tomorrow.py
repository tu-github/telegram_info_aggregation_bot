# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:49:19 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, BaseFilter)
import datetime
from db_connection import users, event_posts

def send_tomorrow(bot, update):
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

class send_tomorrow_filter(BaseFilter):
    def filter(self, message):
        return '/tomorrow' in message.text
filter_send_tomorrow = send_tomorrow_filter()


send_tomorrow_handler = CommandHandler('tomorrow', send_tomorrow)
send_tomorrow_handler_2 = MessageHandler(filter_send_tomorrow, send_tomorrow)