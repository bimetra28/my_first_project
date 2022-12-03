import psycopg2
import requests
import telebot
import time
from config import *

bot = telebot.TeleBot(api_bot)

connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)

def schedule_checker():
    id = 0
    while True:
        cur_time = time.strftime('%H:%M', time.localtime())
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT time, users_id FROM users_data"
            )
            data = cursor.fetchall()
        for i in data:
            if i[0] == cur_time:
                id = i[1]
                weather(id)
        time.sleep(60)

def weather(id):
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
                    "SELECT city, latitude, longitude FROM users_data WHERE users_id = %s", (id,)
                )
                database_data = cursor.fetchone()
            bot.send_message(id, 'Данные успешно получены.')
        except:
            bot.send_message(id, 'Проблемы с данными из базы данных.')
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
               f'Атмосферное давление ровняется {fact_pres} мм рт.ст.\n' \
               f'   Восход сегодня в {sunrise}, закат в {sunset}.\n\n' \
               f'   {part_name[first_part]} температура поднимется до {fp_max_temp}°С, минимальное ее значение составит {fp_min_temp}°С, {condition[fp_cond]}\n' \
               f'Вероятность выпадения осадков будет равна {fp_prec_prob}%\n' \
               f'Скорость ветра {fp_wind_speed} м/с, направление {wind_dir[fp_wind_dir]}\n' \
               f'Атмосферное давление составит {fp_pressure} мм рт.ст.\n\n' \
               f'   {part_name[sec_part]} температура поднимется до {sp_max_temp}°С, минимальное ее значение составит {sp_min_temp}°С, {condition[sp_cond]}\n' \
               f'Вероятность выпадения осадков будет равна {sp_prec_prob}%\n' \
               f'Скорость ветра {sp_wind_speed} м/с, направление {sp_wind_dir}\n' \
               f'Атмосферное давление составит {sp_pressure} мм рт.ст.\n'
        bot.send_message(id, text)
    except:
        bot.send_message(id, 'Кажется со сводкой погоды какие-то проблемы. Пожалуйста, обратитесь к Диме.')


if __name__ == '__main__':
    schedule_checker()
