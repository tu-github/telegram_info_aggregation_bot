# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:30:27 2019

@author: HP
"""


from pymongo import MongoClient
client = MongoClient("")

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
event_themes_russian = list(event_themes_dict_reverse.values())
