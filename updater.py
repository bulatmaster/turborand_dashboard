import time 
import logging 
from datetime import datetime
from zoneinfo import ZoneInfo  # use pytz if Python < 3.9

from update_calls import update_calls
from update_deals import update_deals
from update_payments import update_payments
from update_stage_history import update_stage_history
from update_trips import update_trips
from update_users import update_users 
from utils import emergency_report

import db 


conn = db.get_conn()


def update_last_updated():
    now_moscow = datetime.now(ZoneInfo("Europe/Moscow"))
    ts = now_moscow.strftime("%d.%m.%Y %H:%M")
    with conn:
        conn.execute(
            """
            UPDATE metadata SET value = ? WHERE key = "last_updated"
            """, (ts,)
        )



def update_stage_history():
    while True:
        try:
            update_users()
            update_deals()
            update_calls()
            update_payments()
            update_stage_history()
            update_trips()
            update_last_updated()
        except Exception as e:
            emergency_report(f'turbodesk updater: {e.__class__.__name__}: {e}')
            logging.exception(e)
        finally:
            time.sleep(300)


if __name__ == '__main__':
    update_stage_history()
            
