# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 15:19:19 2019

@author: HP
"""

from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter)
from command_helpers import support_handlers
from db_connection import feedback_data
from command_helpers import help_function

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

class feedback_filter(BaseFilter):
    def filter(self, message):
        return '/feedback' in message.text
filter_feedback = feedback_filter()

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