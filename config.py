from os import getenv
import dotenv

dotenv.load_dotenv(override=True)


# MYSQL (сервер c битрикс24)
MYSQL_HOST =     getenv("MYSQL_HOST")
MYSQL_PORT =     int(getenv("MYSQL_PORT", 3306))
MYSQL_USER =     getenv("MYSQL_USER")
MYSQL_PASSWORD = getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = getenv("MYSQL_DATABASE")


# TG Error Notitications 
EMERGENCY_BOT_TOKEN = getenv('EMERGENCY_BOT_TOKEN')
EMERGENCY_CONTACT_IDS = [5309563931]  # @bulatmaster 


BX_WEBHOOK_URL = getenv('BX_WEBHOOK_URL')

SALES_DEP_ID = 54  # ID  отдела продаж
SUPPLY_DEP_ID = 15  # ID отдела снабжения 



ALL_STAGES = ('NEW', 'UC_O9A0TT', 'UC_WJYSPC', '15', 'PREPARATION', 'UC_Q1P82J', 'UC_3QF7OY', 'UC_Q08ZUN', '17', 'UC_CRI622', '18', 'WON', 'LOSE', 'C20:NEW', 'C20:PREPARATION', 'C20:PREPAYMENT_INVOIC', 'C20:UC_XRMVHI', 'C20:WON', 'C20:LOSE', 'C21:NEW', 'C21:PREPARATION', 'C21:UC_6XX9P7', 'C21:PREPAYMENT_INVOIC', 'C21:EXECUTING', 'C21:FINAL_INVOICE', 'C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY', 'C4:NEW', 'C4:PREPARATION', 'C4:PREPAYMENT_INVOICE', 'C4:EXECUTING', 'C4:FINAL_INVOICE', 'C4:1', 'C4:2', 'C4:3', 'C4:9', 'C4:4', 'C4:5', 'C4:WON', 'C4:LOSE', 'C4:6', 'C4:7', 'C4:8')
KP_SENT_STAGES = ('PREPARATION', 'UC_Q1P82J', 'UC_3QF7OY', 'UC_Q08ZUN', '17', 'UC_CRI622', '18', 'WON', 'LOSE', 'C21:NEW', 'C21:PREPARATION', 'C21:UC_6XX9P7', 'C21:PREPAYMENT_INVOIC', 'C21:EXECUTING', 'C21:FINAL_INVOICE', 'C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY', 'C4:NEW', 'C4:PREPARATION', 'C4:PREPAYMENT_INVOICE', 'C4:EXECUTING', 'C4:FINAL_INVOICE', 'C4:1', 'C4:2', 'C4:3', 'C4:9', 'C4:4', 'C4:5', 'C4:WON', 'C4:LOSE', 'C4:6', 'C4:7', 'C4:8')
CONTRACT_STAGES = ('C21:NEW', 'C21:PREPARATION', 'C21:UC_6XX9P7', 'C21:PREPAYMENT_INVOIC', 'C21:EXECUTING', 'C21:FINAL_INVOICE', 'C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY', 'C4:NEW', 'C4:PREPARATION', 'C4:PREPAYMENT_INVOICE', 'C4:EXECUTING', 'C4:FINAL_INVOICE', 'C4:1', 'C4:2', 'C4:3', 'C4:9', 'C4:4', 'C4:5', 'C4:WON', 'C4:LOSE', 'C4:6', 'C4:7', 'C4:8')
SUPPLY_IN_PROGRESS_STAGES = ('C20:PREPARATION', 'C20:PREPAYMENT_INVOIC', 'C20:UC_XRMVHI', 'C20:WON', 'C20:LOSE')
CARGO_CLEARED_STAGES = ('C21:UC_YU26O5', 'C21:UC_KR9EHV', 'C21:UC_78XHX0', 'C21:UC_FOAJK1', 'C21:UC_CAJFEH', 'C21:UC_1A0H14', 'C21:WON', 'C21:LOSE', 'C21:APOLOGY')



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
        "id": 4,
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

# Снабжение (4)
[
    {
      "NAME": "Выбор поставщика",
      "STATUS_ID": "C4:NEW"
    },
    {
      "NAME": "Заключение договора",
      "STATUS_ID": "C4:PREPARATION"
    },
    {
      "NAME": "Ожидание оплаты от клиента",
      "STATUS_ID": "C4:PREPAYMENT_INVOICE"
    },
    {
      "NAME": "Счет передан на оплату",
      "STATUS_ID": "C4:EXECUTING"
    },
    {
      "NAME": "ДС получены поставщиком",
      "STATUS_ID": "C4:FINAL_INVOICE"
    },
    {
      "NAME": "Отгрузка товара",
      "STATUS_ID": "C4:1"
    },
    {
      "NAME": "Согласование документа с брокером",
      "STATUS_ID": "C4:2"
    },
    {
      "NAME": "Товар в пути",
      "STATUS_ID": "C4:3"
    },
    {
      "NAME": "Растаможка",
      "STATUS_ID": "C4:9"
    },
    {
      "NAME": "Товар на нашем складе",
      "STATUS_ID": "C4:4"
    },
    {
      "NAME": "Товар в пути к клиенту",
      "STATUS_ID": "C4:5"
    },
    {
      "NAME": "Товар получен",
      "STATUS_ID": "C4:WON"
    },
    {
      "NAME": "Поставщик не нашелся",
      "STATUS_ID": "C4:LOSE"
    },
    {
      "NAME": "Не заключили договор",
      "STATUS_ID": "C4:6"
    },
    {
      "NAME": "Товар не прошел таможню",
      "STATUS_ID": "C4:7"
    },
    {
      "NAME": "Клиент не принял товар",
      "STATUS_ID": "C4:8"
    }
]