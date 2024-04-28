import uuid
import os
from ydb_func import *
from datetime import datetime, timezone, timedelta
import telebot
from all_keyboards import *
from static import *

if code_mode == 'dev':
    from dotenv import load_dotenv
    load_dotenv()


tg_token = os.getenv('TG_TOKEN')
bot = telebot.TeleBot(tg_token)

def new_user(message):

    user_id = message.from_user.id
    
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    user_username = message.from_user.username

    if user_first_name != None:
        full_name = user_first_name + ' ' 
    if user_last_name != None:
        full_name = full_name + user_last_name
    if (user_first_name == None) and (user_last_name == None):
        full_name = user_username

    ydb_update_user_data(user_id, user_full_name = full_name, user_mode = 0)

    return 

# user_mode: 0 - default, 1 - ввод заголовка задачи, 2 - ввод текста задачи
#создание задачи
def create_task(user_id, data = None, user_mode = 0):
    # если пользователь только начал создавать задачу
    if (data == None) and (user_mode == 0):
        # вносим отметку что юзер создает задачу
        ydb_update_user_data(user_id, user_mode = 1)
        return
    
    # если пользователь внес заголовок задачи
    elif (data != None) and (user_mode == 1):
        task_header = data

        task_id = uuid.uuid4()
        task_id = str(task_id)
        ydb_update_user_data(user_id, user_task_id = task_id, user_mode = 2)
        ydb_update_task_data(task_id, task_owner_id = user_id, task_header = task_header)

    # если пользователь внес текст задачи
    elif (data != None) and (user_mode == 2):
        task_body = data

        result = ydb_get_user_data(user_id, user_task_id = True)
        for item in result:
            user_task_id = item['user_task_id']

        task_id = user_task_id

        status = 'active'

        ydb_update_user_data(user_id, user_mode = 0)
        ydb_update_task_data(task_id, task_owner_id = user_id, task_body = task_body, task_status = status)

        text = build_task_text(user_id, task_id = task_id)
        return text


# текст задачи
def build_task_text(user_id, data = None, task_id = None):
    text = ''

    # если есть data
    if (data is not None):
        start = len('task_id_')
        end = len(data)
        task_id = data[start:end]
    # если нет data и нет task_id
    elif (data is None) and (task_id is None):
        result = ydb_get_user_data(user_id, user_task_id = True)
        for item in result:
            user_task_id = item['user_task_id']
            task_id = user_task_id

    
    result = ydb_get_task_data(task_id, task_header = True, task_body = True, task_deadline = True)
    for item in result:
        task_header = item['task_header']
        task_body = item['task_body']
        task_deadline = item['task_deadline']

    text = task_header + '\n\n' + task_body

    if task_deadline is not None:
        deadline_text = deadline_calculator(task_deadline)
        text = text + '\n\n' + deadline_text

    return text

def deadline_calculator(task_deadline):

    unix = task_deadline

    date_now = datetime.now(timezone(timedelta(hours=3)))
    unix2 = date_now.timestamp()
    
    seconds = unix-unix2
    
    task_date = datetime.fromtimestamp(unix).strftime('%d.%m.%Y %H:%M')

    text = 'Выполнить до: ' + task_date + '\n'

    if seconds < 0:
        seconds = abs(seconds)
        text = text + 'Просрочено на: '
    elif seconds > 0:
        text = text + 'Осталось: '  

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24) 
    days = int(days)
    hours = int(hours)
    minutes = int(minutes)

    if days != 0:
        text = text + str(days) + ' д '
    if hours != 0:
        text = text + str(hours) + ' ч '
    text = text + str(minutes) + ' мин'
    return text


def set_deadline(user_id, data):
    start = len('date_')
    end = start + 4
    data_year = data[start:end]

    start = end+1
    end = data.find('_', start)
    data_month = data[start:end]
    if int(data_month) < 10:
        data_month = '0' + str(data_month)

    start = end+1
    end = data.find('_', start)
    data_day = data[start:end]
    if int(data_day) < 10:
        data_day = '0' + str(data_day)

    start = end+1
    end = data.find('_', start)
    data_hour = data[start:end]

    start = end+1
    end = len(data)
    data_minute = data[start:end]

    deadline  = data_year + '-' + data_month + '-' + data_day + ' ' + data_hour + ':' + data_minute + ':00' + '+0300'
    result = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S%z')
    unix_deadline = result.timestamp()   

    result = ydb_get_user_data(user_id, user_task_id = True)
    for item in result:
        user_task_id = item['user_task_id']

    task_id = user_task_id
    
    ydb_update_task_data(task_id, task_deadline = int(unix_deadline))
    
    text = build_task_text(user_id, task_id = task_id)
    return text



def set_task_status(user_id, data):

    # получаем task_id по user_id из users
    result = ydb_get_user_data(user_id, user_task_id = True)
    for item in result:
        user_task_id = item['user_task_id']
    task_id = user_task_id     

    # получаем новый status из data сообщения
    start = len('set_status_')
    end = len(data)
    new_task_status = data[start:end]
    
    # task_deadline в данной функции обнуляется (null)
    ydb_update_task_status(task_id, task_status = new_task_status)

    return

def set_user_task(user_id, data):

    start = len('task_id_')
    end = len(data)
    task_id = data[start:end]

    ydb_update_user_data(user_id, user_task_id = task_id)

    return
