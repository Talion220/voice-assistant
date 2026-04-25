import os
import webbrowser
import sys
import subprocess
import datetime

import voice

try:
    import requests		#pip install requests
except:
    pass

def browser():

    webbrowser.open('https://ya.ru', new=2)


def game():
    try:
        subprocess.Popen('C:/Windows/system32/mspaint.exe')
    except:
        voice.speaker('Путь к файлу не найден, проверьте, правильный ли он')

def time():
    now = datetime.datetime.now()
    hours = now.hour
    minutes = now.minute
    voice.speaker(f"Текущее время: {hours} часов {minutes} минут")

def offpc():
    #отключает ПК под управлением Windows

    #os.system('shutdown \s')
    print('пк был бы выключен, но команде # в коде мешает;)))')


def weather():
    '''Для работы нужно зарегистрироваться на сайте https://openweathermap.org '''
    try:
        params = {'q': 'Krasnoyarsk', 'units': 'metric', 'lang': 'ru', 'appid': 'f5b76d1ea4b8a6b22819e0fd530612ec'}
        response = requests.get(f'https://api.openweathermap.org/data/2.5/weather', params=params)
        if not response:
            raise
        w = response.json()
        voice.speaker(f"На улице {w['weather'][0]['description']} {round(w['main']['temp'])} градусов")

    except:
        voice.speaker('Произошла ошибка при попытке запроса к ресурсу API, проверь код')


def offBot():
    voice.speaker("Пока")
    os._exit(0)

def passive():
    '''Функция заглушка при простом диалоге с ботом'''
    pass

