import os 
import json
import telebot
from telebot.types import ReplyKeyboardRemove
from build_date_func import *
from static import *
from task_func import *
from ydb_func import *
from all_keyboards import *

if code_mode == 'dev':
    from dotenv import load_dotenv
    load_dotenv()

tg_token = os.getenv('TG_TOKEN')
bot = telebot.TeleBot(tg_token)

@bot.message_handler(func=lambda message: True)
def message_handler(message):
    # если пользователь ранее решил создать задачу или проект и есть отметка в ydb, забираем его сообщение в качестве текста задачи
    result = ydb_get_user_data(message.chat.id, user_mode = True)
    
    if result != False:
        for item in result:
            user_mode = item['user_mode']

        if user_mode == 1:
            create_task(message.chat.id, data = message.text, user_mode = user_mode)
            bot.send_message(message.chat.id, 'Напишите текст задачи:')
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(message.chat.id, message.message_id-1)
            return
        elif user_mode == 2:
            text = create_task(message.chat.id, data = message.text, user_mode = user_mode)
            bot.send_message(message.chat.id, text = text, reply_markup=build_task_markup(message.chat.id))
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(message.chat.id, message.message_id-1)
            return
    elif result == False:
        new_user(message)
        bot.send_message(message.chat.id, text = start_text, reply_markup=ReplyKeyboardRemove())
        return

    if message.text == '/new_task':
        create_task(message.chat.id)
        bot.send_message(message.chat.id, 'Напишите название задачи:')
        bot.delete_message(message.chat.id, message.message_id)
        return
    
    elif message.text == '/main_menu':
        bot.send_message(message.chat.id, 'Мои задачи', reply_markup=build_task_terms_markup())
        bot.delete_message(message.chat.id, message.message_id)
        return

    else: 
        bot.send_message(message.chat.id, 'О, это ты? Привет!')
        return

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if 'main_menu' in call.data:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Мои задачи', reply_markup=build_task_terms_markup())
        return
    elif 'task_id_' in call.data:
        set_user_task(call.message.chat.id, data = call.data)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = build_task_text(call.message.chat.id, data = call.data), reply_markup=build_task_markup(call.from_user.id, data = call.data))
        return
    elif 'delete_task' in call.data:
        delete_task(call.message.chat.id)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Мои задачи', reply_markup=build_task_terms_markup())
        bot.answer_callback_query(call.id, 'Задача удалена')
        return
    elif 'switch_month_' in call.data:
        bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=build_days(call.data))
        return
    elif 'day_' in call.data:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выберите час:', reply_markup=build_hours(call.data))
        return
    elif 'hour_' in call.data:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выберите минуты:', reply_markup=build_minutes(call.data))
        return    
    elif 'date_' in call.data:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=set_deadline(call.message.chat.id, call.data), reply_markup=build_task_markup(call.message.chat.id))
        return
    elif 'set_deadline' in call.data:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выберите день:', reply_markup=build_days())
        return
    elif 'set_status' in call.data:
        set_task_status(call.message.chat.id, call.data)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = build_task_text(call.message.chat.id), reply_markup=build_task_markup(call.from_user.id))
        bot.answer_callback_query(call.id, 'Статус задачи успешно изменён')
    elif 'term_' in call.data:
        text = 'Мои задачи'
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=build_task_headers(call.message.chat.id, call.data))
        return
    else:
        bot.answer_callback_query(call.id)

if code_mode == 'dev':
    bot.infinity_polling()

# use in YC
def handler(event,context):
    body = json.loads(event['body'])
    update = telebot.types.Update.de_json(body)
    bot.process_new_updates([update])
    return {
    'statusCode': 200,
    'body': 'ok',
    }
