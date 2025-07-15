
import requests 

import config 
import db 
from utils import money_to_int


conn = db.get_conn()


def update_payments():
    method = 'crm.item.list'

    request_url = f'{config.BX_WEBHOOK_URL}/{method}'

    highest_id_payment = conn.execute('SELECT id FROM payments ORDER BY id DESC LIMIT 1').fetchone()
    highest_id = highest_id_payment[0] if highest_id_payment else 0

    offset = 0

    while True:
        
        r = requests.get(request_url, params={
            "entityTypeId": 1048,  # Приходы 
            "FILTER[>ID]": highest_id,
            "start": offset
        })
        data = r.json()

        to_insert = []
        for payment in data['result']['items']:
            payment_id = payment['id']
            deal_id = payment['ufCrm23Iddeal']
            amount = money_to_int(payment['ufCrm23Summa'])
            payment_time = payment['ufCrm23Data']
            payment_type = payment['ufCrm23Kpalteg']

            to_insert.append((payment_id, deal_id, amount, payment_time, payment_type))
        
        if to_insert:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO payments 
                    (id, deal_id, amount, payment_time, payment_type) 
                    VALUES (?, ?, ?, ?, ?)
                    """, to_insert
                )
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_payments()