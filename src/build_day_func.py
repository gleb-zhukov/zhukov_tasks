from calendar import Calendar
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone, timedelta
from static import *

def build_minutes(data):
    markup = InlineKeyboardMarkup()
    markup.row_width = 6
    butt = []
    data = data.replace("hour_", "date_")
    for i in range(0, 6):
        callback = data + '_' + minutes_name[i]
        butt.append(InlineKeyboardButton(minutes_name[i], callback_data=callback))

    markup.add(*butt)
    return markup

def build_hours(data):
    markup = InlineKeyboardMarkup()
    markup.row_width = 6
    butt = []
    data = data.replace("day_", "hour_")
    current_hour = datetime.now(timezone(timedelta(hours=3))).hour

    for i in range(0, 24):
        if i < current_hour:
            butt.append(InlineKeyboardButton(' ', callback_data= ' '))
        else:
            callback = data + '_' + hours_name[i]
            butt.append(InlineKeyboardButton(hours_name[i], callback_data=callback))

    markup.add(*butt)
    return markup

def build_days(data=None):
    markup = InlineKeyboardMarkup()
    markup.row_width = 7

    current_year = datetime.now(timezone(timedelta(hours=3))).year
    current_month = datetime.now(timezone(timedelta(hours=3))).month
    current_day = datetime.now(timezone(timedelta(hours=3))).day

    if data == None:
        data_year = current_year
        data_month = current_month
    elif data != None:
        start = len('switch_month_')
        end = start + 4
        data_year = data[start:end]
        data_year = int(data_year)
        data_month = data[end+1:len(data)]
        data_month = int(data_month)

    cal = Calendar()
    days = cal.monthdayscalendar(data_year, data_month)
    butt = []
    butt2 = []

    for x in range(0, 7):
        butt.append(InlineKeyboardButton(days_name[x], callback_data=" "))
    for i in range(0, len(days)):
        for k in range(0, 7):
            day = days[i][k]
            if ((day < current_day) and (data_month == current_month) and (data_year == current_year)) or (day == 0):
                day = ' '
            callback = 'day_' + str(data_year) + '_' + str(data_month) + '_' + str(day)
            butt.append(InlineKeyboardButton(day, callback_data=callback))

    if (data_year <= current_year) and (data_month <= current_month):
        butt2.append(InlineKeyboardButton(' ', callback_data=' '))
    elif (data_year > current_year) or (data_month > current_month):
        if (data_month - 1) < 1:
            callback_switch_month = 'switch_month_' + str(data_year - 1) + '_' + str(12)
            butt2.append(InlineKeyboardButton('<<', callback_data=callback_switch_month))
        elif (data_month - 1) > 0:
            callback_switch_month = 'switch_month_' + str(data_year) + '_' + str(data_month - 1)
            butt2.append(InlineKeyboardButton('<<', callback_data=callback_switch_month))

    month_year = months_name[data_month-1]+ ' ' + str(data_year)
    butt2.append(InlineKeyboardButton(month_year, callback_data=' '))

    if (data_month + 1) <= 12:
            callback_switch_month = 'switch_month_' + str(data_year) + '_' + str(data_month + 1)
            butt2.append(InlineKeyboardButton('>>', callback_data=callback_switch_month))
    elif (data_month + 1) > 12:
        callback_switch_month = 'switch_month_' + str(data_year + 1) + '_' + str(1)
        butt2.append(InlineKeyboardButton('>>', callback_data=callback_switch_month))

    markup.add(*butt)
    markup.add(*butt2)
    return markup
