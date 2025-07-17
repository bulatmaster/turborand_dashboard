import requests

import config 


def money_to_int(value: str) -> int:
    if not value:
        return None
    # Отделим число от возможных суффиксов (например, |RUB)
    number_part = value.split('|')[0]
    # Преобразуем к float и затем к int (отбрасывается дробная часть)
    return int(float(number_part))


def emergency_report(message: str):
    """
    Оповещения в телеграм об ошибках 
    """

    DEFAULT_MESSAGE = 'Ошибка в ботах'

    if not message:
        message = DEFAULT_MESSAGE

    token = config.EMERGENCY_BOT_TOKEN
    for chat_id in config.EMERGENCY_CONTACT_IDS:
        url = f'https://api.telegram.org/bot{token}/'   
        requests.get(url + 'sendMessage', params = {
            'chat_id': chat_id,
            'text': message
        })


