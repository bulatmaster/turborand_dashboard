# https://apidocs.bitrix24.ru/api-reference/telephony/voximplant-statistic-get.html

import requests 

import config 
import db 


conn = db.get_conn()


def update_calls():
    method = 'voximplant.statistic.get'

    request_url = f'{config.BX_WEBHOOK_URL}/{method}'

    highest_id_call = conn.execute('SELECT id FROM calls ORDER BY id DESC LIMIT 1').fetchone()
    highest_id = highest_id_call[0] if highest_id_call else 80000  # ~29 дек 2024

    offset = 0

    while True:
        
        r = requests.get(request_url, params={
            "FILTER[>ID]": highest_id,
            "start": offset
        })
        data = r.json()

        to_insert = []
        for call in data['result']:
            call_id = call['ID']
            user_id = call['PORTAL_USER_ID']
            duration = call['CALL_DURATION']
            start_time = call['CALL_START_DATE']

            to_insert.append((call_id, user_id, duration, start_time))
        
        if to_insert:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO calls 
                    (id, user_id, duration, start_time) VALUES 
                    (?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                    """, to_insert
                )
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_calls()