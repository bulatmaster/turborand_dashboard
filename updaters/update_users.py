import sqlite3 
import requests 
import logging

import config 
from config import BX_WEBHOOK_URL
import db 


conn = db.get_conn()


def update_users():
    REQUEST_URL = f'{BX_WEBHOOK_URL}/user.get'

    r = requests.get(REQUEST_URL, {
        'FILTER[ACTIVE]': True
    })
    data = r.json()

    remaining_user_ids = {row[0] for row in conn.execute(
        'SELECT id FROM users'
    ).fetchall()}

    for user in data['result']:
        user_id = int(user['ID'])

        if user_id == 1:  # Робот Турборэнд
            continue 
        if user_id == 55:  # test user 
            continue 


        name = user['NAME']
        if 'SECOND_NAME' in user and user['SECOND_NAME']:
            name += ' ' + user['SECOND_NAME']
        if 'LAST_NAME' in user and user['LAST_NAME']:
            name += ' ' + user['LAST_NAME']

        photo_url = user['PERSONAL_PHOTO'] if 'PERSONAL_PHOTO' in user else None

        is_sales = False
        is_supply = False
        for dep_id in user['UF_DEPARTMENT']:
            if str(dep_id) == str(config.SALES_DEP_ID):
                is_sales = True
            if str(dep_id) == str(config.SUPPLY_DEP_ID):
                is_supply = True

        date_register = user['DATE_REGISTER']

        if user_id in remaining_user_ids:
            remaining_user_ids.remove(user_id)
            conn.execute(
                """
                UPDATE users SET 
                    name = ?,
                    photo_url = ?,
                    is_sales = ?,
                    is_supply = ?,
                    date_register = ?
                WHERE id = ?
                """, 
                (name, photo_url, is_sales, is_supply, date_register, user_id)
            )

        else:
            conn.execute(
                """
                INSERT INTO users 
                (id, name, photo_url, is_sales, is_supply, date_register)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, name, photo_url, is_sales, is_supply, date_register)
            )
    for user_id in remaining_user_ids:  # уволенные 
        conn.execute(
            'DELETE FROM users WHERE id = ?',
            (user_id,)
        )
    conn.commit()



if __name__ == "__main__":
    update_users()