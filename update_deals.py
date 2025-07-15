import sqlite3 
import requests 

import config 
from config import BX_WEBHOOK_URL

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row


def update_deals():
    MAX_PER_PAGE = 50
    request_url = f'{BX_WEBHOOK_URL}/crm.deal.list'
    
    start = 0

    while True:

        r = requests.get(request_url, {
            'order[DATE_MODIFY]': 'ASC',
            #'filter[>DATE_MODIFY]': '2025-04-23T14:12:50+00:00',
            'start': start
        })

    
        data = r.json()

        if data['total'] - start <= MAX_PER_PAGE:
            break 
        
        print(f'{start} / {data["total"]}')
        
        start += 50


        
        
    

def main():
    update_deals()


if __name__ == "__main__":
    main()