import os 
from os import getenv
import dotenv

dotenv.load_dotenv(override=True)


# MYSQL (главный сервер)
MYSQL_HOST =     getenv("MYSQL_HOST")
MYSQL_PORT =     int(getenv("MYSQL_PORT", 3306))
MYSQL_USER =     getenv("MYSQL_USER")
MYSQL_PASSWORD = getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = getenv("MYSQL_DATABASE")


MYSQL_CONFIG = {
    "host": MYSQL_HOST,
    "port": MYSQL_PORT,
    "user": MYSQL_USER,
    "password": MYSQL_PASSWORD,
    "database": MYSQL_DATABASE,
    "charset":  "utf8mb4",
    "autocommit": False,      # будем коммитить сами после каждого батча
}


HTTP_PROXY_URL = getenv('HTTP_PROXY_URL')
OPENAI_KEY  = getenv('OPENAI_KEY')
ASST_ID = getenv('ASST_ID')

# Telegram Уведомления об ошибках
EMERGENCY_BOT_TOKEN = getenv('EMERGENCY_BOT_TOKEN')
EMERGENCY_CONTACT_IDS = [5309563931]   # @bulatmaster 


BX_WEBHOOK_URL = getenv('BX_WEBHOOK_URL')


SALES_DEP_ID = 54  # ID  отдела продаж
SUPPLY_DEP_ID = 15  # ID отдела снабжения 


# Все названия стадий уникальны (между разными воронками не пересекаются)

ALL_STAGES = ('NEW', 'UC_O9A0TT', 'UC_WJYSPC', '15', 'PREPARATION', 'UC_Q1P82J', 'UC_3QF7OY', 'UC_Q08ZUN', '17', 'UC_CRI622', '18', 'WON', 'LOSE', 'C20:NEW', 'C20:PREPARATION', 'C20:PREPAYMENT_INVOIC', 'C20:UC_XRMVHI', 'C20:WON', 'C20:LOSE', 'C21:NEW', 'C21:PREPARATION', 'C21:UC_6XX9P7', 'C21:PREPAYMENT_INVOIC', 'C21:EXECUTING', 'C21:FINAL_INVOICE', 'C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY', 'C4:NEW', 'C4:PREPARATION', 'C4:PREPAYMENT_INVOICE', 'C4:EXECUTING', 'C4:FINAL_INVOICE', 'C4:1', 'C4:2', 'C4:3', 'C4:9', 'C4:4', 'C4:5', 'C4:WON', 'C4:LOSE', 'C4:6', 'C4:7', 'C4:8')

# Все стадии всех воронок, на которых КП отправлено 
KP_SENT_STAGES = ('PREPARATION', 'UC_Q1P82J', 'UC_3QF7OY', 'UC_Q08ZUN', '17', 'UC_CRI622', '18', 'WON', 'LOSE', 'C21:NEW', 'C21:PREPARATION', 'C21:UC_6XX9P7', 'C21:PREPAYMENT_INVOIC', 'C21:EXECUTING', 'C21:FINAL_INVOICE', 'C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY', 'C4:NEW', 'C4:PREPARATION', 'C4:PREPAYMENT_INVOICE', 'C4:EXECUTING', 'C4:FINAL_INVOICE', 'C4:1', 'C4:2', 'C4:3', 'C4:9', 'C4:4', 'C4:5', 'C4:WON', 'C4:LOSE', 'C4:6', 'C4:7', 'C4:8')
# Все стадии всех воронок, на которых договор заключен (по сути воронка "Исп. договора")
CONTRACT_STAGES = ('C21:NEW', 'C21:PREPARATION', 'C21:UC_6XX9P7', 'C21:PREPAYMENT_INVOIC', 'C21:EXECUTING', 'C21:FINAL_INVOICE', 'C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY', 'C4:NEW', 'C4:PREPARATION', 'C4:PREPAYMENT_INVOICE', 'C4:EXECUTING', 'C4:FINAL_INVOICE', 'C4:1', 'C4:2', 'C4:3', 'C4:9', 'C4:4', 'C4:5', 'C4:WON', 'C4:LOSE', 'C4:6', 'C4:7', 'C4:8')

# Стадии воронки "Снабжение для КП", на которых снабженец считает заявку 
# Первая стадия "Новый запрос" сюда не входит, т.к. заявки на ней еще не распределены по менеджерам
SUPPLY_CALCULATION_IN_PROGRESS_STAGES = ('C20:PREPARATION', 'C20:PREPAYMENT_INVOIC', 'C20:UC_XRMVHI', 'C20:WON', 'C20:LOSE')

# Стадии на которых груз растаможен 
CARGO_CLEARED_STAGES = ('C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY')

STATUS_TYPES = {
    "SALE": "Прямая продажа",
    "UC_MBAY1E": "Прямая закупка",
    "UC_KROLC6": "Тендер не под нас",
    "UC_BYNIUH": "Тендер под нас",
    "UC_HP3VTF": "Внутренний конкурс",
    "UC_MVUG9F": "Мониторинг цен",
    "UC_MT07DI": "Непонятная заявка",
}



STATUS_IDS = {
    "NEW": "Новая сделка",
    "UC_O9A0TT": "Запрос сервисникам",
    "UC_WJYSPC": "Расчет КП (поиск цен)",
    "15": "Подготовка КП",
    "PREPARATION": "КП отправлено",
    "UC_Q1P82J": "Подготовка тендера",
    "UC_3QF7OY": "Ожидание результата тендера",
    "UC_Q08ZUN": "Замороженные КП",
    "17": "Заключение договора",
    "UC_CRI622": "Согласование БГ",
    "18": "Исполнение договора",
    "WON": "Сделка завершена",
    "LOSE": "Сделка провалена",

    "C20:NEW": "Новый запрос",
    "C20:PREPARATION": "Отправить запрос менеджеру ОП",
    "C20:PREPAYMENT_INVOIC": "Подготовка расчёта",
    "C20:UC_XRMVHI": "Завершить расчет",
    "C20:WON": "Поставщик найден, расчёт произведен",
    "C20:LOSE": "Сделка провалена",

    "C21:NEW": "Ожидание предоплаты",
    "C21:PREPARATION": "Выбор поставщика",
    "C21:UC_6XX9P7": "Предоплата поставщику",
    "C21:PREPAYMENT_INVOIC": "Поставка запчастей (Вне РФ)",
    "C21:EXECUTING": "Поставка запчастей (в РФ)",
    "C21:FINAL_INVOICE": "Растаможка",
    "C21:UC_YU26O5": "Постоплата поставщику",
    "C21:UC_KR9EHV": "Доставка запчастей клиенту по РФ",
    "C21:UC_78XHX0": "Выезд сервисного инженера",
    "C21:UC_FOAJK1": "Ожидание закрывающих документов",
    "C21:UC_CAJFEH": "Ожидание окончательной оплаты",
    "C21:UC_1A0H14": "Рекламация",
    "C21:WON": "Сделка успешна",
    "C21:LOSE": "Сделка провалена",
    "C21:APOLOGY": "Анализ причины провала"
}




############ СПРАВОЧНИК ################


# crm.category.list?entityTypeId=2
# ID воронок 
[
    {
        "id": 0,
        "name": "Продажа",
      },
      {
        "id": 20,
        "name": "Снабжение для КП",
      },
      {
        "id": 21,
        "name": "Исполнение договора",
      },
      {
        "id": 4,  # не используется 
        "name": "Снабжение",
      },
      {
        "id": 3,   # не используется  
        "name": "Тендеры_1",
      }
]



# Этапы воронок

# crm.dealcategory.stage.list?id=<pipeline_id>
# Продажа (0)
[
    {
      "NAME": "Новая сделка",
      "STATUS_ID": "NEW"
    },
    {
      "NAME": "Запрос сервисникам",
      "STATUS_ID": "UC_O9A0TT"
    },
    {
      "NAME": "Расчет КП (поиск цен)",
      "STATUS_ID": "UC_WJYSPC"
    },
    {
      "NAME": "Подготовка КП",
      "STATUS_ID": "15"
    },
    {
      "NAME": "КП отправлено",
      "STATUS_ID": "PREPARATION"
    },
    {
      "NAME": "Подготовка тендера",
      "STATUS_ID": "UC_Q1P82J"
    },
    {
      "NAME": "Ожидание результата тендера",
      "STATUS_ID": "UC_3QF7OY"
    },
    {
      "NAME": "Замороженные КП",
      "STATUS_ID": "UC_Q08ZUN"
    },
    {
      "NAME": "Заключение договора",
      "STATUS_ID": "17"
    },
    {
      "NAME": "Согласование БГ",
      "STATUS_ID": "UC_CRI622"
    },
    {
      "NAME": "Исполнение договора",
      "STATUS_ID": "18"
    },
    {
      "NAME": "Сделка завершена",
      "STATUS_ID": "WON"
    },
    {
      "NAME": "Сделка провалена",
      "STATUS_ID": "LOSE"
    }
]


# Этапы воронки Снабжение для КП (20)
[
    {
      "NAME": "Новый запрос",
      "STATUS_ID": "C20:NEW"
    },
    {
      "NAME": "Отправить запрос менеджеру ОП",
      "STATUS_ID": "C20:PREPARATION"
    },
    {
      "NAME": "Подготовка расчёта",
      "STATUS_ID": "C20:PREPAYMENT_INVOIC"
    },
    {
      "NAME": "Завершить расчет",
      "STATUS_ID": "C20:UC_XRMVHI"
    },
    {
      "NAME": "Поставщик найден, расчёт произведен",
      "STATUS_ID": "C20:WON"
    },
    {
      "NAME": "Сделка провалена",
      "STATUS_ID": "C20:LOSE"
    }
]

# Исполнение договора  (21)
[
    {
      "NAME": "Ожидание предоплаты",
      "STATUS_ID": "C21:NEW"
    },
    {
      "NAME": "Выбор поставщика",
      "STATUS_ID": "C21:PREPARATION"
    },
    {
      "NAME": "Предоплата поставщику",
      "STATUS_ID": "C21:UC_6XX9P7"
    },
    {
      "NAME": "Поставка запчастей (Вне РФ)",
      "STATUS_ID": "C21:PREPAYMENT_INVOIC"
    },
    {
      "NAME": "Поставка запчастей (в РФ)",
      "STATUS_ID": "C21:EXECUTING"
    },
    {
      "NAME": "Растаможка",
      "STATUS_ID": "C21:FINAL_INVOICE"
    },
    {
      "NAME": "Постоплата поставщику",
      "STATUS_ID": "C21:UC_YU26O5"
    },
    {
      "NAME": "Доставка запчастей клиенту по РФ",
      "STATUS_ID": "C21:UC_KR9EHV"
    },
    {
      "NAME": "Выезд сервисного инженера",
      "STATUS_ID": "C21:UC_78XHX0"
    },
    {
      "NAME": "Ожидание закрывающих документов",
      "STATUS_ID": "C21:UC_FOAJK1"
    },
    {
      "NAME": "Ожидание окончательной оплаты",
      "STATUS_ID": "C21:UC_CAJFEH"
    },
    {
      "NAME": "Рекламация",
      "STATUS_ID": "C21:UC_1A0H14"
    },
    {
      "NAME": "Сделка успешна",
      "STATUS_ID": "C21:WON"
    },
    {
      "NAME": "Сделка провалена",
      "STATUS_ID": "C21:LOSE"
    },
    {
      "NAME": "Анализ причины провала",
      "STATUS_ID": "C21:APOLOGY"
    }
]
