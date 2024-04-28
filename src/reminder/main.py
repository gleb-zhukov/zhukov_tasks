# use 'prod' in YC
code_mode = 'dev'

import os
import ydb
import ydb.iam
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

if code_mode == 'dev':
    from dotenv import load_dotenv
    load_dotenv()

    ydb_endpoint=os.getenv('YDB_ENDPOINT')
    ydb_database=os.getenv('YDB_DATABASE')
    ydb_token=os.getenv('YDB_TOKEN')

    driver = ydb.Driver(endpoint=ydb_endpoint, database=ydb_database, credentials=ydb.AccessTokenCredentials(ydb_token))

elif code_mode == 'prod':
    ydb_endpoint=os.getenv('YDB_ENDPOINT')
    ydb_database=os.getenv('YDB_DATABASE')

    driver = ydb.Driver(endpoint=ydb_endpoint,database=ydb_database, credentials=ydb.iam.MetadataUrlCredentials())

driver.wait(fail_fast=True, timeout=5)
session = driver.table_client.session().create()

tg_token = os.getenv('TG_TOKEN')
bot = telebot.TeleBot(tg_token)

timestamp = datetime.now().timestamp()

day_to = timestamp + 86340
day_from = day_to - 600

hour_to = timestamp + 3600
hour_from = hour_to - 600


def ydb_get_task(val):

    if val == 'hour':
        ydb_request = f'SELECT id, task_header, task_owner_id FROM tasks WHERE task_deadline BETWEEN {hour_from} AND {hour_to}'
    elif val == 'day':
        ydb_request = f'SELECT id, task_header, task_owner_id FROM tasks WHERE task_deadline BETWEEN {day_from} AND {day_to}'
    elif val == 'expired':
        ydb_request = f'SELECT id, task_header, task_owner_id FROM tasks WHERE task_deadline < {timestamp}'

    result_sets = session.transaction().execute(ydb_request, commit_tx=True)
    task_id = list()
    task_owner_id = list()
    task_header = list()
    if not result_sets[0].rows: # если ответ пустой
        print('error, no data in ydb, func ydb_get_day_task')
        return task_owner_id, task_header
    else: # иначе если ответ есть, отдаем 
        for row in result_sets[0].rows:
            task_id.append(row.id)
            task_owner_id.append(row.task_owner_id)
            task_header.append(row.task_header)
        
        return task_id, task_owner_id, task_header

def send_notification(task_id, task_owner_id, task_header, msg):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    callback = 'task_id_' + task_id
    markup.add(InlineKeyboardButton(task_header, callback_data=callback))
    bot.send_message(task_owner_id, text = msg, reply_markup=markup)
    
def send_day_notification():
    task_id, task_owner_id, task_header = ydb_get_task('day')
    if task_id != None:
        msg = f'Дедлайн задачи близок ⏰\n\nОсталось менее суток!'
        for i in range(0, len(task_id)):
            send_notification(task_id[i], task_owner_id[i], task_header[i], msg)


def send_hour_notification():
    task_id, task_owner_id, task_header = ydb_get_task('hour')
    if task_id != None:
        msg = f'Дедлайн задачи близок ⏰\n\nОсталось менее часа!'
        for i in range(0, len(task_id)):
            send_notification(task_id[i], task_owner_id[i], task_header[i], msg)


# уведомление о просроченных задачах (раз в час)
def send_expired_notification():

    # получаем метку часа, когда было прошлое уведомление 
    ydb_request = 'SELECT hour FROM reminder WHERE id = 0'
    result_sets = session.transaction().execute(ydb_request, commit_tx=True)
    for row in result_sets[0].rows:
            hour = row.hour
    
    now_hour = datetime.now().hour

    # если наступил следующий час
    if hour != now_hour:
        # заменяем час в ydb
        ydb_request = f'UPSERT into reminder (id, hour) values (0, {now_hour})'
        result_sets = session.transaction().execute(ydb_request, commit_tx=True)

        task_id, task_owner_id, task_header = ydb_get_task('expired')
        if task_id != None:
            msg = f'Кажется, у вас сроки летят ⏰✈️\n\nЗадача просрочена ⚠️'
            for i in range(0, len(task_id)):
                send_notification(task_id[i], task_owner_id[i], task_header[i], msg)


send_day_notification()
send_hour_notification()
send_expired_notification()
