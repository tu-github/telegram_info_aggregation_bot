# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:23:52 2019
@author: HP
"""
from telegram.ext import Updater
from telegram.utils.request import Request
from MQBot import MQBot
from telegram.ext import messagequeue as mq

from command_start import start_handler
from command_send_today import send_today_handler, send_today_handler_2
from command_send_tomorrow import send_tomorrow_handler, send_tomorrow_handler_2
from command_send_week import send_week_handler, send_week_handler_2
from command_helpers import help_function_handler, unknown_handler, error_handler, other_handler

from conversation_subscribe import subscribeConversation_handler
from conversation_feedback import feedbackConversation_handler
from conversation_post import postConversation_handler
from conversation_settings import settingsConversation_handler
from conversation_processing import processingConversation_handler
from conversation_notification import notificationConversation_handler


if __name__ == '__main__':
    # token real bot - ''
    # token test bot - '722203998:AAEbkJlsVsL6GEtoaM1P5uOwEO1cp59Jii0'
    token = '' #test
    
    queue = mq.MessageQueue(all_burst_limit = 29, all_time_limit_ms = 1017)
    request = Request(con_pool_size = 8)
    MQBot_test = MQBot(token, request = request, mqueue = queue)
    updater = Updater(bot = MQBot_test)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(send_today_handler)
    dispatcher.add_handler(send_tomorrow_handler)
    dispatcher.add_handler(send_week_handler)
    dispatcher.add_handler(send_today_handler_2)
    dispatcher.add_handler(send_tomorrow_handler_2)
    dispatcher.add_handler(send_week_handler_2)

    dispatcher.add_handler(subscribeConversation_handler)
    dispatcher.add_handler(postConversation_handler)
    dispatcher.add_handler(processingConversation_handler)
    dispatcher.add_handler(settingsConversation_handler)
    dispatcher.add_handler(notificationConversation_handler)
    dispatcher.add_handler(feedbackConversation_handler)

    dispatcher.add_handler(help_function_handler)
    dispatcher.add_handler(unknown_handler)
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(other_handler)

    updater.start_polling()
    #updater.idle()
