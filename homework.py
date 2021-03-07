import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    filemode='w',
    datefmt='%Y-%m-%d,%H:%M:%S',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = 'unknown_status'
    if homework_name is None or homework_status is None:
        logging.error('homework_name is None OR homework_status is None')
        return f'{homework_name}: ' \
               f'homework_name is None OR homework_status is None'
    elif homework_status == 'reviewing':
        verdict = 'Проект на ревью.'
    elif homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'approved':
        verdict = 'Ревьюеру всё понравилось, ' \
                  'можно приступать к следующему уроку.'
    elif verdict == 'unknown_status':
        logging.error('unknown review status')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    homework_statuses = {}
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    try:
        homework_statuses = requests.get(
            url=URL,
            headers=headers,
            params=params
        )

        """ пример request с ошибкой 401 """
        # homework_statuses = requests.get(URL, data={
        #     'Authorization': PRAKTIKUM_TOKEN,
        #     'from_date': current_timestamp
        # })
        # .raise_for_status() не пропускает pytest
        # AttributeError: 'MockResponseGET' object has no attribute
        # 'raise_for_status'
        # хотя с ним ошибки HTTPError попадают в .log (!)
        # homework_statuses.raise_for_status()

        if 'error' in homework_statuses.json():
            logging.error(f'{homework_statuses.json().get("error")}')
    except requests.exceptions.RequestException:
        logging.error('Exception occurred', exc_info=True)
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.debug('logging is started')
    bot_client = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                last_hw = new_homework.get('homeworks')[0]
                send_message((parse_homework_status(last_hw)), bot_client)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)

        except requests.exceptions.RequestException:
            logging.error('Exception occurred', exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    main()
