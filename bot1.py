import telebot
import requests
import psycopg2
from telebot import types
from geopy import geocoders
from deep_translator import GoogleTranslator
from config import *

bot = telebot.TeleBot(api_bot)

connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)
connection.autocommit = True


def city_setting(message):
    if message.text == '/start' or message.text == 'Город' or message.text == 'город' or message.text == '/city' or message.text == '/weather' or message.text == '/time':
        msg = bot.send_message(message.chat.id,
                               "Такого города я не знаю, будьте внимательней и попробуйте ввести название города снова.")
        bot.register_next_step_handler(msg, finally_city)
    else:
        try:
            en_city_name = GoogleTranslator(source='ru', target='en').translate(message.text)
            geolocator = geocoders.Nominatim(user_agent="telebot")
            latitude = str(geolocator.geocode(en_city_name).latitude)
            longitude = str(geolocator.geocode(en_city_name).longitude)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users_data (users_id, city, latitude, longitude) VALUES (%s, %s, %s, %s)",
                        (message.from_user.id, message.text.capitalize(), latitude, longitude)
                    )
            except:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users_data SET city = %s, latitude = %s, longitude = %s WHERE users_id = %s",
                        (message.text.capitalize(), latitude, longitude, message.from_user.id)
                    )
            bot.send_message(message.chat.id,
                             f'Хорошо, в дальнейшем я буду присылать вам погоду в городе {message.text.capitalize()}.',
                             parse_mode='html')
        except:
            msg = bot.send_message(message.chat.id, f"Город {message.text} не найден! Попробуйте еще раз.")
            bot.register_next_step_handler(msg, finally_city)


@bot.message_handler(commands=['start'])
def start(message):
    msg = bot.send_message(message.chat.id, f'Доброго времени суток, <b>{message.from_user.first_name} {message.from_user.last_name}</b>!\n'
                                            'Каждый день я автоматически буду присылать вам погоду в указанное время (при желании), а также в любое другое.\n'
                                            'Для успешного начала моей работы необходимо выполнить 2 действия:\n'
                                            '- Во-первых, <u>напишите город</u>, погода в котором вам интересна. Пример: Москва', parse_mode='html')
    bot.register_next_step_handler(msg, first_city_setting)

def first_city_setting(message):
    city_setting(message)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT time FROM users_data WHERE users_id = %s", (message.from_user.id,)
        )
        data = cursor.fetchone()
        if None in data:
            msg = bot.send_message(message.chat.id,
                                   '- Во-вторых, <u>укажите время</u>, в которое я каждый день буду присылать вам сводку погоды. '
                                   'Пример: 07:00, 22:33 \n'
                                   'Если же получать сводку не хочется, просто напишите слово \'стоп\' (крайне не приветствуется!!!)',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, set_time)


@bot.message_handler(commands=['city'])
def city(message):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT city FROM users_data WHERE users_id = %s", (message.from_user.id,)
        )
        data = cursor.fetchone()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('\U0001F44D Было бы неплохо')
    button2 = types.KeyboardButton('\U0001F645 Пока не нужно')
    markup.add(button1, button2)
    bot.send_message(message.chat.id,
                     f'Каждый раз я смотрю погоду в городе {data[0]}. Хотели бы его изменить?', reply_markup=markup)


def finally_city(message):
    city_setting(message)


@bot.message_handler(commands=['time'])
def time(message):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT time FROM users_data WHERE users_id = %s", (message.from_user.id,)
        )
        data = cursor.fetchone()
    if None in data:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton('\U0001F44D Конечно же да')
        button2 = types.KeyboardButton('\U0001F645 Пожалуй не стоит')
        markup.add(button1, button2)
        bot.send_message(message.chat.id, 'Время не установлено. Хотели бы его установить?', reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button1 = types.KeyboardButton('\U0001F44D Конечно же да')
        button2 = types.KeyboardButton('\U0001F645 Пожалуй не стоит')
        button3 = types.KeyboardButton('Отключить отправку сводки по расписанию')
        markup.add(button1, button2, button3)
        bot.send_message(message.chat.id,
                         f'Отправка сводки у вас установлена на {data[0]}. Хотели бы изменить?', reply_markup=markup)


def set_time(message):
    try:
        if message.text == 'стоп' or message.text == 'Стоп':
            bot.send_message(message.chat.id, 'Не очень то и хотелось что-то менять \U0001F611')

        elif (0 <= int(message.text[0:2]) <= 23 or message.text[0:2] == '00')\
            and (0 <= int(message.text[3:5]) <= 59 or message.text[3:5] == '00'):
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users_data (time) VALUES (%s) WHERE users_id = %s", (message.text, message.from_user.id)
                    )
            except:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users_data SET time = %s WHERE users_id = %s", (message.text, message.from_user.id)
                    )
            bot.send_message(message.chat.id,
                             f'Отлично! В дальнейшем буду присылать вам сводку в {message.text}')
        else:
            msg = bot.send_message(message.chat.id,
                                   'Время необходимо писать в формате ЧЧ:ММ. Пример: 22:34. Для отмены изменений напишите \'стоп\'')
            bot.register_next_step_handler(msg, set_time)
    except:
        msg = bot.send_message(message.chat.id,
                               'Время необходимо писать в формате ЧЧ:ММ. Пример: 22:34. Для отмены изменений напишите \'стоп\'')
        bot.register_next_step_handler(msg, set_time)

@bot.message_handler(commands=['weather'])
def weather(message):
    condition = {
        'clear': 'ясно \U00002600', 'partly-cloudy': 'малооблачно \U00002601',
        'cloudy': 'облачно с прояснениями \U00002601',
        'overcast': 'пасмурно \U00002601', 'drizzle': 'морось \U00002614', 'light-rain': 'небольшой дождь \U00002614',
        'rain': 'дождь \U00002614', 'moderate-rain': 'умеренно-сильный дождь \U00002614',
        'heavy-rain': 'сильный дождь \U00002614',
        'continuous-heavy-rain': 'длительный сильный дождь \U00002614', 'showers': 'ливень \U00002614',
        'wet-snow': 'дождь со снегом \U00002614', 'light-snow': 'небольшой снег \U0001F328', 'snow': 'снег \U0001F328',
        'snow-showers': 'снегопад \U0001F328', 'hail': 'град \U0001F328', 'thunderstorm': 'гроза \U000026A1',
        'thunderstorm-with-rain': 'дождь с грозой \U000026A1', 'thunderstorm-with-hail': 'гроза с градом \U000026A1'
    }
    wind_dir = {
        'nw': 'северо-западное', 'n': 'северное', 'ne': 'северо-восточное', 'e': 'восточное',
                'se': 'юго-восточное', 's': 'южное', 'sw': 'юго-западное', 'w': 'западное', 'с': 'штиль'
    }
    part_name = {
        'night': '\U0001F31B Ночью', 'morning': '🌅 Утром', 'day': '\U0001F31E Днём', 'evening': '🌇 Вечером'
    }

    try:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT city, latitude, longitude FROM users_data WHERE users_id = %s", (message.from_user.id,)
                )
                database_data = cursor.fetchone()
            bot.send_message(message.chat.id, 'Данные успешно получены.')
        except:
            bot.send_message(message.chat.id, 'Проблемы с данными из базы данных.')
        site = f'https://api.weather.yandex.ru/v2/informers?lat={database_data[1]}&lon={database_data[2]}&lang=ru_RU'
        r = requests.get(site, headers={'X-Yandex-API-Key': api_weather})
        data = r.json()
        cur_temp = data['fact']['temp']
        feels_like = data['fact']['feels_like']
        ws = data['fact']['wind_speed']
        wd = data['fact']['wind_dir']
        sunrise = data['forecast']['sunrise']
        sunset = data['forecast']['sunset']
        cond = data['fact']['condition']
        fact_pres = data['fact']['pressure_mm']
        first_part = data['forecast']['parts'][0]['part_name']
        fp_max_temp = data['forecast']['parts'][0]['temp_max']
        fp_min_temp = data['forecast']['parts'][0]['temp_min']
        fp_cond = data['forecast']['parts'][0]['condition']
        fp_prec_prob = data['forecast']['parts'][0]['prec_prob']
        fp_wind_speed = data['forecast']['parts'][0]['wind_speed']
        fp_wind_dir = data['forecast']['parts'][0]['wind_dir']
        fp_pressure = data['forecast']['parts'][0]['pressure_mm']
        sec_part = data['forecast']['parts'][1]['part_name']
        sp_max_temp = data['forecast']['parts'][1]['temp_max']
        sp_min_temp = data['forecast']['parts'][1]['temp_min']
        sp_cond = data['forecast']['parts'][1]['condition']
        sp_prec_prob = data['forecast']['parts'][1]['prec_prob']
        sp_wind_speed = data['forecast']['parts'][1]['wind_speed']
        sp_wind_dir = data['forecast']['parts'][1]['wind_dir']
        sp_pressure = data['forecast']['parts'][1]['pressure_mm']
        text = f'   На данный момент температура в городе {database_data[0]} {cur_temp}°С (ощущается как {feels_like}°С), {condition[cond]}.\n' \
               f'Скорость ветра {ws} м/с, направление {wind_dir[wd]}\n' \
               f'Атмосферное давление ровняется {fact_pres} мм рт.ст.\n\n' \
               f'   Восход сегодня в {sunrise}, закат в {sunset}.\n\n' \
               f'   {part_name[first_part]} температура поднимется до {fp_max_temp}°С, минимальное ее значение составит {fp_min_temp}°С, {condition[fp_cond]}\n' \
               f'Вероятность выпадения осадков будет равна {fp_prec_prob}%\n' \
               f'Скорость ветра {fp_wind_speed} м/с, направление {wind_dir[fp_wind_dir]}\n' \
               f'Атмосферное давление составит {fp_pressure} мм рт.ст.\n\n' \
               f'   {part_name[sec_part]} температура поднимется до {sp_max_temp}°С, минимальное ее значение составит {sp_min_temp}°С, {condition[sp_cond]}\n' \
               f'Вероятность выпадения осадков будет равна {sp_prec_prob}%\n' \
               f'Скорость ветра {sp_wind_speed} м/с, направление {sp_wind_dir}\n' \
               f'Атмосферное давление составит {sp_pressure} мм рт.ст.\n'
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, 'Кажется со сводкой погоды какие-то проблемы. Пожалуйста, обратитесь к Диме.')

@bot.message_handler(content_types=['text'])
def text(message):
    if message.text == 'город' or message.text == 'Город':
        msg = bot.send_message(message.chat.id, "Введите название города, погода в котором вам интересна.")
        bot.register_next_step_handler(msg, finally_city)

    elif message.text == 'погода' or message.text == 'Погода':
        weather(message)

    elif message.text == 'тест':
        bot.send_message(message.chat.id, message)

    elif message.text == '\U0001F44D Конечно же да':
        msg = bot.send_message(message.chat.id, 'Укажите новое время для автоматической отправки сводки погоды. '
                                                'Вы можете написать слово \'стоп\' и отменить изменения', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, set_time)

    elif message.text == '\U0001F645 Пожалуй не стоит':
        bot.send_message(message.chat.id, 'Нууу... На нет и суда нет \U0001F611', reply_markup=types.ReplyKeyboardRemove())

    elif message.text == 'Отключить отправку сводки по расписанию':
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users_data SET time = Null WHERE users_id = %s", (message.from_user.id,)
            )
        bot.send_message(message.chat.id, 'Автоматическая отправка успешно отключена \U00002705', reply_markup=types.ReplyKeyboardRemove())

    elif message.text == '\U0001F44D Было бы неплохо':
        msg = bot.send_message(message.chat.id, 'Введите название города, погода в котором вам интересна.', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, finally_city)

    elif message.text == '\U0001F645 Пока не нужно':
        bot.send_message(message.chat.id, 'Я бы на вашем месте подумал о том, чтобы сменить город... Город проживания \U0001F605', reply_markup=types.ReplyKeyboardRemove())


if __name__ == '__main__':
    bot.polling(none_stop=True)