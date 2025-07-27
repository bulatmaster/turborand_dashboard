
import requests 

import config 
import db 
from utils import money_to_int


conn = db.get_conn()


def update_trip_expenses():
    method = 'crm.item.list'

    request_url = f'{config.BX_WEBHOOK_URL}/{method}'

    highest_id_rec = conn.execute('SELECT id FROM trip_expenses ORDER BY id DESC LIMIT 1').fetchone()
    highest_id = highest_id_rec[0] if highest_id_rec else 0

    offset = 0

    while True:
        
        r = requests.get(request_url, params={
            "entityTypeId": 1078,  # "Принимающие компании" - тут суммируются отдельные расходы по командировкам 
            "FILTER[>ID]": highest_id,
            "start": offset
        })
        data = r.json()

        to_insert = []
        for payment in data['result']['items']:
            rec_id = payment['id']
            trip_id = payment['parentId176']
            amount = money_to_int(payment['ufCrm30Budjet'])
            
            to_insert.append((rec_id, trip_id, amount))
        
        if to_insert:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO trip_expenses
                    (id, trip_id, amount) 
                    VALUES (?, ?, ?)
                    ON CONFLICT DO NOTHING
                    """, to_insert
                )
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_trip_expenses()