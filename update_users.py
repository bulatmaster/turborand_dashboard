import sqlite3 
import requests 

import config 
from config import BX_WEBHOOK_URL
import db 


conn = db.get_conn()


def update_users():
    request_url = f'{BX_WEBHOOK_URL}/user.get'

    r = requests.get(request_url, {
        'FILTER[ACTIVE]': True
    })
    data = r.json()

    for user in data['result']:
        user_id = user['ID']

        name = user['NAME']
        if 'LAST_NAME' in user and user['LAST_NAME']:
            name += ' ' + user['LAST_NAME']
        if 'SECOND_NAME' in user and user['SECOND_NAME']:
            name += ' ' + user['SECOND_NAME']

        photo_url = user['PERSONAL_PHOTO'] if 'PERSONAL_PHOTO' in user else None

        is_sales = False
        is_supply = False
        for dep_id in user['UF_DEPARTMENT']:
            if str(dep_id) == str(config.SALES_DEP_ID):
                is_sales = True
            if str(dep_id) == str(config.SUPPLY_DEP_ID):
                is_supply = True

        date_register = user['DATE_REGISTER']

        with conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO users 
                (id, name, photo_url, is_sales, is_supply, date_register)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, name, photo_url, is_sales, is_supply, date_register)
            )



if __name__ == "__main__":
    update_users()