import requests 

import config 
import db 


conn = db.get_conn()


def update_trips():
    method = 'crm.item.list'

    request_url = f'{config.BX_WEBHOOK_URL}/{method}'

    highest_id_rec = conn.execute('SELECT id FROM trips ORDER BY id DESC LIMIT 1').fetchone()
    highest_id = highest_id_rec[0] if highest_id_rec else 0

    offset = 0

    while True:
        
        r = requests.get(request_url, params={
            "entityTypeId": 176,  # Смарт процесс Командировки 
            "FILTER[>ID]": highest_id,
            "start": offset
        })
        data = r.json()

        to_insert = []
        for trip in data['result']['items']:
            trip_id = trip['id']
            user_id = trip['assignedById']
            stage_id = trip['stageId']
            start_time = trip['begindate']
            end_time = trip['closedate']

            to_insert.append((trip_id, user_id, stage_id, start_time, end_time))
        
        if to_insert:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO trips 
                    (id, user_id, stage_id, begin_time, end_time) 
                    VALUES (?, ?, ?, ?, ?)
                    """, to_insert
                )
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_trips()