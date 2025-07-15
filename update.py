import time 
import logging 

from update_calls import update_calls
from update_deals import update_deals
from update_payments import update_payments
from update_stage_history import update_stage_history
from update_trips import update_trips
from update_users import update_users 
from utils import emergency_report




def main():
    while True:
        try:
            update_calls()
            update_deals()
            update_payments()
            update_stage_history()
            update_trips()
            update_users ()
        except Exception as e:
            emergency_report(f'turbodesk updater: {e.__class__.__name__}: {e}')
            logging.exception(e)
        finally:
            time.sleep(300)


if __name__ == '__main__':
    main()
            
