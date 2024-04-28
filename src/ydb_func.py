import os
import ydb
import ydb.iam
from datetime import datetime, timezone, timedelta
from static import code_mode

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

def delete_task(user_id):
    result = ydb_get_user_data(user_id, user_task_id = True)
    for item in result:
        user_task_id = item['user_task_id']
    task_id = user_task_id
    ydb_request = f'DELETE from tasks where id = "{task_id}"'
    session.transaction().execute(ydb_request, commit_tx=True)
    return
#получаем заголовки задач в зависимости от срока (дедлайна)
def ydb_get_tasks_by_term(user_id, term):

    ydb_request = ''

    if term == 'all':
        time_now = datetime.now(timezone(timedelta(hours=3))).timestamp()

        ydb_request = f'SELECT id, task_header FROM tasks WHERE task_owner_id == {user_id} AND task_status == "active"'
    
    elif term == 'expired':
        time_now = datetime.now(timezone(timedelta(hours=3))).timestamp()

        ydb_request = f'SELECT id, task_header FROM tasks WHERE task_owner_id == {user_id} AND task_deadline < {time_now}'

    elif term == 'today':
        today = datetime.now(timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)
        today_from = today.timestamp()
        today_to = today_from + 86340

        ydb_request = f'SELECT id, task_header FROM tasks WHERE task_owner_id == {user_id} AND task_deadline BETWEEN {today_from} AND {today_to}'

    elif term == 'tomorrow':
        today = datetime.now(timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)
        today_from = today.timestamp()
        tomorrow_from = today_from + 86400
        tomorrow_to = tomorrow_from + 86340

        ydb_request = f'SELECT id, task_header FROM tasks WHERE task_owner_id == {user_id} AND task_deadline BETWEEN {tomorrow_from} AND {tomorrow_to}'

    elif term == 'week':
        today = datetime.now(timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)
        today_from = today.timestamp()
        week_from = today_from + 172800
        week_to = week_from + 604740 

        ydb_request = f'SELECT id, task_header FROM tasks WHERE task_owner_id == {user_id} AND task_deadline BETWEEN {week_from} AND {week_to}'

    elif term == 'later':
        today = datetime.now(timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)
        today_from = today.timestamp()
        later = today_from + 691200

        ydb_request = f'SELECT id, task_header FROM tasks WHERE task_owner_id == {user_id} AND task_deadline > {later}'

    elif term == 'archive':
        ydb_request = f'SELECT id, task_header FROM tasks WHERE task_owner_id == {user_id} AND task_status = "done"'


    result_sets = session.transaction().execute(ydb_request, commit_tx=True)
    task_id = list()
    task_header = list()
    if not result_sets[0].rows: # если ответ пустой
        print('error, no data in ydb, func ydb_get_tasks_by_term')
        return task_id, task_header
    else: # иначе если ответ есть, отдаем 
        for row in result_sets[0].rows:
            task_id.append(row.id)
            task_header.append(row.task_header)
        
        return task_id, task_header
            

    return

# получаем данные пользователя по id 
def ydb_get_user_data(user_id, **data):
    
    ydb_request = 'SELECT '
    for key, value in data.items():
        if value == True:
            ydb_request = ydb_request + str(key) + ', '

    # убираем последнюю запятую
    str_len = len(ydb_request)
    ydb_request = ydb_request[:str_len-2] + ' ' + ydb_request[str_len:] + f'FROM users WHERE id == {user_id}'

    result_sets = session.transaction().execute(ydb_request, commit_tx=True)

    result = list()
    if not result_sets[0].rows:
        result = False
        return result
    else:
        for row in result_sets[0].rows:
            result.append(row)
            return result

# получаем данные о задаче по id
def ydb_get_task_data(task_id, **data):
    
    ydb_request = 'SELECT '
    for key, value in data.items():
        if value == True:
            ydb_request = ydb_request + str(key) + ', '

    # убираем последнюю запятую
    str_len = len(ydb_request)
    ydb_request = ydb_request[:str_len-2] + ' ' + ydb_request[str_len:] + f'FROM tasks WHERE id == "{task_id}"'

    result_sets = session.transaction().execute(ydb_request, commit_tx=True)

    result = list()
    for row in result_sets[0].rows:
        result.append(row)
    return result

def ydb_update_task_status(task_id, task_status):
    # удаляем task_deadline через null
    ydb_request = f'upsert into tasks (id, task_status, task_deadline) values ("{task_id}", "{task_status}", null)'
    print(ydb_request)
    session.transaction().execute(ydb_request, commit_tx=True)
    return


def ydb_update_task_data(task_id, task_header = None, task_body = None, task_owner_id = None, task_status = None, task_deadline = False):

    ydb_request = 'upsert into tasks (id'

    if task_header != None:
        ydb_request = ydb_request + ',task_header'
    if task_body != None:
        ydb_request = ydb_request + ',task_body'
    if task_owner_id != None:
        ydb_request = ydb_request + ',task_owner_id'
    if task_status != None:
        ydb_request = ydb_request + ',task_status'
    if task_deadline != False:
        ydb_request = ydb_request + ',task_deadline'

    ydb_request = ydb_request + f') values ("{task_id}"'

    if task_header != None:
        ydb_request = ydb_request + f',"{task_header}"'
    if task_body != None:
        ydb_request = ydb_request + f',"{task_body}"'
    if task_owner_id != None:
        ydb_request = ydb_request + f',{task_owner_id}'
    if task_status != None:
        ydb_request = ydb_request + f',"{task_status}"'
    if task_deadline != False:
        ydb_request = ydb_request + f',{task_deadline}'
    elif task_deadline == None:
        ydb_request = ydb_request + f',{task_deadline}'
    ydb_request = ydb_request + ')'

    session.transaction().execute(ydb_request, commit_tx=True)

    return

def ydb_update_user_data(user_id, user_task_id = None, user_full_name = None, user_mode = None):
    
    ydb_request = 'upsert into users (id'
    if user_task_id != None:
        ydb_request = ydb_request + ',user_task_id'
    if user_full_name != None:
        ydb_request = ydb_request + ',user_full_name'
    if user_mode != None:
        ydb_request = ydb_request + ',user_mode'

    ydb_request = ydb_request + f') values ({user_id}'

    if user_task_id != None:
        ydb_request = ydb_request + f',"{user_task_id}"'
    if user_full_name != None:
        ydb_request = ydb_request + f',"{user_full_name}"'
    if user_mode != None:
        ydb_request = ydb_request + f',{user_mode}'

    ydb_request = ydb_request + ')'

    session.transaction().execute(ydb_request, commit_tx=True)
    return
