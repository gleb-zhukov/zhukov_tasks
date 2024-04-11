from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from ydb_func import *
from static import *


# клавиатура задачи
def build_task_markup(user_id, data = None, task_id = None):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1

    # если task_id можно вытащить из callback data - вытаскиваем, иначе - берём из строки юзера в ydb
    if (data is None) and (task_id is None):
        result = ydb_get_user_data(user_id, user_task_id = True)
        for item in result:
            user_task_id = item['user_task_id']
        task_id = user_task_id
    elif data != None:
        start = len('task_id_')
        end = len(data)
        task_id = data[start:end]

    
    result = ydb_get_task_data(task_id, task_deadline = True, task_status = True)
    for item in result:
        task_deadline = item['task_deadline']
        task_status = item['task_status']

    if task_status == 'active':
        markup.add(InlineKeyboardButton('Задача выполнена!', callback_data='set_status_done'))
        if task_deadline == None:
            markup.add(InlineKeyboardButton('Назначить дедлайн', callback_data='set_deadline'))
        elif task_deadline != None:
            markup.add(InlineKeyboardButton('Изменить дедлайн', callback_data='set_deadline'))
        markup.add(InlineKeyboardButton('Удалить задачу', callback_data='delete_task'))
        markup.add(InlineKeyboardButton('Назад', callback_data='term_today'))
    elif task_status == 'done':
        markup.add(InlineKeyboardButton('Вернуть задачу в работу', callback_data='set_status_active'))
        markup.add(InlineKeyboardButton('Назад', callback_data='term_today'))
       
    return markup


# клавиатура выбора статуса задач
def build_task_terms_markup():    

    markup = InlineKeyboardMarkup()
    markup.row_width = 2
        
    callback = 'term_all'
    markup.add(InlineKeyboardButton('Все задачи 🌐', callback_data=callback))
    callback = 'term_expired'
    markup.add(InlineKeyboardButton('Просроченные ⌛️👀⚠️', callback_data=callback))
    callback = 'term_today'
    markup.add(InlineKeyboardButton('Сегодня ⚓️', callback_data=callback))
    callback = 'term_tomorrow'
    markup.add(InlineKeyboardButton('Завтра 🏄', callback_data=callback))
    callback = 'term_week'
    markup.add(InlineKeyboardButton('Ближайшие 7 дней 🗓', callback_data=callback))
    callback = 'term_later'
    markup.add(InlineKeyboardButton('Позже 🧘', callback_data=callback))
    markup.add(InlineKeyboardButton(' ', callback_data=' '))
    markup.add(InlineKeyboardButton(' ', callback_data=' '))
    markup.add(InlineKeyboardButton(' ', callback_data=' '))
    callback = 'term_archive'
    markup.add(InlineKeyboardButton('Архив ☑️', callback_data=callback))

    return markup

def build_task_headers(user_id, data):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3

    start = len('term_')
    end = len(data)
    term = data[start:end]

    task_id, task_header = ydb_get_tasks_by_term(user_id = user_id, term = term)


    butt = []
    if term == 'all':
        callback = 'term_archive'
        butt.append(InlineKeyboardButton('<<<', callback_data=callback))
        text = task_terms.get(term)
        butt.append(InlineKeyboardButton(text, callback_data=' '))
        callback = 'term_expired'
        butt.append(InlineKeyboardButton('>>>', callback_data=callback))

    if term == 'expired':
        callback = 'term_all'
        butt.append(InlineKeyboardButton('<<<', callback_data=callback))
        text = task_terms.get(term)
        butt.append(InlineKeyboardButton(text, callback_data=' '))
        callback = 'term_today'
        butt.append(InlineKeyboardButton('>>>', callback_data=callback))
        
    elif term == 'today':
        callback = 'term_expired'
        butt.append(InlineKeyboardButton('<<<', callback_data=callback))
        text = task_terms.get(term)
        butt.append(InlineKeyboardButton(text, callback_data=' '))
        callback = 'term_tomorrow'
        butt.append(InlineKeyboardButton('>>>', callback_data=callback))
    
    elif term == 'tomorrow':
        callback = 'term_today'
        butt.append(InlineKeyboardButton('<<<', callback_data=callback))
        text = task_terms.get(term)
        butt.append(InlineKeyboardButton(text, callback_data=' '))
        callback = 'term_week'
        butt.append(InlineKeyboardButton('>>>', callback_data=callback))

    elif term == 'week':
        callback = 'term_tomorrow'
        butt.append(InlineKeyboardButton('<<<', callback_data=callback))
        text = task_terms.get(term)
        butt.append(InlineKeyboardButton(text, callback_data=' '))
        callback = 'term_later'
        butt.append(InlineKeyboardButton('>>>', callback_data=callback))

    elif term == 'later':
        callback = 'term_week'
        butt.append(InlineKeyboardButton('<<<', callback_data=callback))
        text = task_terms.get(term)
        butt.append(InlineKeyboardButton(text, callback_data=' '))
        callback = 'term_archive'
        butt.append(InlineKeyboardButton('>>>', callback_data=callback))
    
    elif term == 'archive':
        callback = 'term_later'
        butt.append(InlineKeyboardButton('<<<', callback_data=callback))
        text = task_terms.get(term)
        butt.append(InlineKeyboardButton(text, callback_data=' '))
        callback = 'term_all'
        butt.append(InlineKeyboardButton('>>>', callback_data=callback))

    markup.add(*butt)

    for i in range(0, len(task_id)):
        callback = 'task_id_' + task_id[i]
        markup.add(InlineKeyboardButton(task_header[i], callback_data=callback))

    # если задач меньше 8, забиваем пустыми клавишами чтобы меню не было маленьким
    if len(task_id) < 8:
        for i in range(0, 8 - len(task_id)):
            markup.add(InlineKeyboardButton(' ', callback_data=' '))


    

    
    markup.add(InlineKeyboardButton('Назад', callback_data='main_menu'))
    return markup

