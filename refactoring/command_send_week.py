# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:49:53 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, BaseFilter)
import datetime, time
from db_connection import users, event_posts

def send_week(bot, update, num_days = 7):
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

class send_week_filter(BaseFilter):
    def filter(self, message):
        return '/week' in message.text
filter_send_week = send_week_filter()

send_week_handler = CommandHandler('week', send_week)
send_week_handler_2 = MessageHandler(filter_send_week, send_week)