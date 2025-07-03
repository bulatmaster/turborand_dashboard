from os import getenv
import dotenv

dotenv.load_dotenv(override=True)


BX_WEBHOOK_URL = getenv('BX_WEBHOOK_URL')

SALES_DEP_ID = getenv('SALES_DEP_ID')
SUPPLY_DEP_ID = getenv('SUPPLY_DEP_ID')