import sqlite3
import random
from calendar import monthrange
from datetime import datetime, timezone, date
from typing import List, Dict
from dataclasses import dataclass
from statistics import mean

from flask import Flask, render_template, url_for, send_from_directory, request

import db 
import config 


app = Flask(__name__, template_folder='templates', static_folder='static')

months = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
]

conn = db.get_conn()


PLANS = {
    "КП": 40,
    "Звонки": 1200,
    "Командировки": 10,
    "Договоры": 5,
    "Авансы": 4_000_000,
    "Прибыль": {
        "Стажер": 250_000,
        "Младший менеджер": 850_000,
        "Менеджер по продажам": 2_500_000,
        "Ведущий менеджер по продажам": 5_000_000,
    }
}


def css_by_metric(label: str, value: int | float) -> str:
    ### Продажи 
    if label == "КП":
        if value <= 9:   return "bg-secondary"
        if value <= 19:  return "bg-danger"
        if value <= 29:  return "bg-warning"
        return "bg-success"

    if label == "Звонки":
        if value <= 299:  return "bg-secondary"
        if value <= 599:  return "bg-danger"
        if value <= 899:  return "bg-warning"
        return "bg-success"

    if label == "Командировки":
        if value <= 3:   return "bg-danger"
        if value <= 8:   return "bg-warning"
        return "bg-success"

    if label == "Договоры":
        if value <= 1:   return "bg-danger"
        if value <= 3:   return "bg-warning"
        return "bg-success"

    if label == "Авансы":
        if value < 1_000_000:   return "bg-danger"
        if value < 3_000_000:   return "bg-warning"
        return "bg-success"

    if label == "Прибыль":  # проценты от плана
        if value < 20:  return "bg-secondary"
        if value < 40:  return "bg-danger"
        if value < 80:  return "bg-warning"
        return "bg-success"
 
    if label == "Заявки в снабжение":   # проценты (конверсия)
        if value < 20: return "bg-secondary"
        if value < 40: return "bg-danger"
        if value < 70: return "bg-warning"
        return "bg-success"
    
    ### Снабжение
    if label == "Заявки":
        if value < 20: return "bg-secondary"
        if value < 40: return "bg-danger"
        if value < 70: return "bg-warning"
        return "bg-success"

    if label == "Растаможено":
        return "bg-secondary"
        

    #
    return "bg-secondary"



@dataclass 
class Metric:
    html_text: str  # надпись 
    percent: int  # % заполнения шкалы 
    css: str  # цвет шкалы 

@dataclass
class ManagerInfo:
    name: str 
    position: str 
    photo_url: str
    metrics: Metric

def safe_percent(x: int | float, y: int | float) -> int:
    if not y:
        return 0
    return int(x / y * 100)

def format_money(val: int | float) -> str:
    """
    Форматирует число с разделением тысяч пробелами
    """
    return f"{int(val):,}".replace(",", "&nbsp;")


def get_manager_position(start_date_str):
    start_date = datetime.fromisoformat(start_date_str)
    now = datetime.now(timezone.utc)
    months_passed = (now.year - start_date.year) * 12 + now.month - start_date.month

    if months_passed < 4:
        return "Стажер"
    elif months_passed < 7:
        return "Младший менеджер"
    elif months_passed <= 12:
        return "Менеджер по продажам"
    else:
        return "Ведущий менеджер по продажам"


# ─── данные менеджеров ───────────────────────────────────────────────────────
def build_manager_data(user: sqlite3.Row, default_avatar: str, start_date: str, end_date: str) -> ManagerInfo:
    user_id = user['id']

    # Категория менеджера (стажёр, младший менеджер и тд) (влияет на план по прибыли)
    position = get_manager_position(user['date_register'])

    # Отправлено КП 
    (kp, ) = conn.execute(
        f"""
        SELECT COUNT(DISTINCT deal_id) FROM deals_stage_history
        WHERE new_stage_id IN {config.KP_SENT_STAGES}
        AND old_stage_id NOT IN {config.KP_SENT_STAGES}
        AND deal_id IN (SELECT id FROM deals WHERE sales_user_id = {user_id}) 
        AND record_time BETWEEN '{start_date}' AND '{end_date}'
        """
    ).fetchone()
    kp_metric = Metric(
        html_text=f"КП:&nbsp;<span class='fw-semibold'>{kp}</span>",
        percent=safe_percent(kp, PLANS['КП']),
        css=css_by_metric("КП", kp),
    )

    # Минут звонков 
    (calls_seconds, ) = conn.execute(
        """
        SELECT SUM(duration) FROM calls 
        WHERE user_id = ?
        AND start_time BETWEEN ? AND ?
        """, (user_id, start_date, end_date)
    ).fetchone()
    calls = int(calls_seconds / 60) if calls_seconds else 0
    calls_metric = Metric(
        html_text=f"Звонки:&nbsp;<span class='fw-semibold'>{calls}</span>&nbsp;мин",
        percent=safe_percent(calls, PLANS['Звонки']),
        css=css_by_metric('Звонки', calls)
    )

     # Расходы по командировкам 
    (trip_expenses, ) = conn.execute(
        """
        SELECT SUM(amount) FROM trip_expenses
        WHERE trip_id IN (
            SELECT id FROM trips 
            WHERE user_id = ? 
            AND begin_time BETWEEN ? AND ?
        )
        """, (user_id, start_date, end_date)
    ).fetchone()
    if not trip_expenses:
        trip_expenses = 0
    
    trip_expenses_metric = Metric(
        html_text=f"Расходы по командировкам:&nbsp;<span class='fw-semibold'>{format_money(trip_expenses)}</span>&nbsp;₽",
        percent=0,
        css=css_by_metric('Расходы по командировкам', 0)
    )

    # Командировки 
    (trips, ) = conn.execute(
        """
        SELECT COUNT(*) FROM trips 
        WHERE user_id = ? 
        AND begin_time BETWEEN ? AND ?
        """, (user_id, start_date, end_date)
    ).fetchone()

    if trip_expenses:
        expenses_str = f"<span class='text-muted text-green'>&nbsp;&nbsp;&nbsp;{format_money(trip_expenses)}&nbsp₽</span>"
    else:
        expenses_str = ''

    trips_metric = Metric(
        html_text=f"Командировки:&nbsp;<span class='fw-semibold'>{trips}</span>{expenses_str}",
        percent=safe_percent(trips, PLANS['Командировки']),
        css=css_by_metric('Командировки', trips)
    )

    # Заявки в снабжение
    supply_request_ids = {row[0] for row in conn.execute(
        f"""
        SELECT deal_id FROM deals_stage_history
        WHERE deal_id IN (SELECT id FROM deals WHERE sales_user_id = {user_id}) 
        AND record_time BETWEEN '{start_date}' AND '{end_date}'
        AND old_pipeline_id = 0 AND new_pipeline_id = 20
        """
    ).fetchall()}
    supply_requests_total = len(supply_request_ids)

    if not supply_request_ids:
        supply_requests_processed = 0
    else:
        deals_str = [str(deal_id) for deal_id in supply_request_ids]
        (supply_requests_processed, ) = conn.execute(
            f"""
            SELECT COUNT(DISTINCT deal_id) FROM deals_stage_history
            WHERE deal_id IN ({','.join(deals_str)})
            AND record_time BETWEEN '{start_date}' AND '{end_date}'
            AND old_pipeline_id = 20 AND new_pipeline_id = 0
            """
        ).fetchone()
    
    supply_requests_percent = safe_percent(supply_requests_processed, supply_requests_total)
    supply_requests_metric = Metric(
        html_text=f"Заявки в снабжение:&nbsp;<span class='fw-semibold'>{supply_requests_processed}</span>&nbsp;из&nbsp;<span class='fw-semibold'>{supply_requests_total}</span>",
        percent=supply_requests_percent,
        css=css_by_metric('Заявки в снабжение', supply_requests_percent)
    )

    # Время расчёта заявки 
    deltas = []
    current_datetime = datetime.now(timezone.utc)
    for deal_id in supply_request_ids:
        (start_time_str,) = conn.execute(
            f"""
            SELECT record_time FROM deals_stage_history
            WHERE deal_id = {deal_id}
            AND old_pipeline_id = 0
            AND new_pipeline_id = 20
            ORDER BY id 
            LIMIT 1
            """
        ).fetchone()
        start_time = datetime.fromisoformat(start_time_str)

        deal = conn.execute(f'SELECT * FROM deals WHERE id = {deal_id}').fetchone()

        if deal['pipeline_id'] == 20:  # Снабжение для КП  (заявка ещё считается)
            end_time = current_datetime

        else:
            (end_time_str, ) = conn.execute(
                f"""
                SELECT record_time FROM deals_stage_history
                WHERE deal_id = {deal_id}
                AND old_pipeline_id = 20
                AND new_pipeline_id = 0
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            end_time = datetime.fromisoformat(end_time_str)
            
        duration_hours = (end_time - start_time).total_seconds() / 3600
        deltas.append(duration_hours)
    
    if deltas:
        avg_proc_hrs = round(mean(deltas), 1)
        avg_proc_days = round(avg_proc_hrs/24, 1)

        avg_time_str = f'{avg_proc_days} дн.'
    
    else:
        avg_time_str = 'N/A'

    supply_processing_time_metric = Metric(
        html_text=f"Среднее время расчёта:&nbsp;<span class='fw-semibold'>{avg_time_str}</span>",
        percent=0,
        css=css_by_metric(0, 'Среднее время расчёта')
    )

    # Договоры 
    contract_deal_ids = {row[0] for row in conn.execute(
        f"""
        SELECT deal_id FROM deals_stage_history
        WHERE record_time BETWEEN '{start_date}' AND '{end_date}'
        AND deal_id IN (SELECT id FROM deals WHERE sales_user_id = {user_id}) 
        AND new_pipeline_id = 21 AND old_pipeline_id = 0
        """, 
    ).fetchall()}
    contracts = len(contract_deal_ids)
    contracts_metric = Metric(
        html_text=f"Договоры:&nbsp;<span class='fw-semibold'>{contracts}</span>",
        percent=safe_percent(contracts, PLANS["Договоры"]),
        css=css_by_metric('Договоры', contracts)
    )


    # Авансы 
    (advances, ) = conn.execute(
        f"""
        SELECT SUM(amount) FROM payments 
        WHERE deal_id IN (SELECT id FROM deals WHERE sales_user_id = {user_id}) 
        AND payment_type = 'Аванс'
        AND payment_time BETWEEN ? AND ?
        """, (start_date, end_date)
    ).fetchone()
    if not advances:
        advances = 0
    advances_metric = Metric(
        html_text=f"Авансы:&nbsp;<span class='fw-semibold'>{format_money(advances)}</span>&nbsp;₽",
        percent=safe_percent(advances, PLANS["Авансы"]),
        css=css_by_metric('Авансы', advances)
    )    


    # Прибыль = сумма входящих платежей минус себестоимость для заключенных сделок за период 
    (profit, ) = conn.execute(
        f"""
        SELECT SUM(amount) FROM payments 
        WHERE payment_time BETWEEN ? AND ?
        AND deal_id IN (SELECT id FROM deals WHERE sales_user_id = ?)
        """, (start_date, end_date, user_id)
    ).fetchone()
    if not profit:
        profit = 0

    profit_percent = safe_percent(profit, PLANS["Прибыль"][position])
    profit_metric = Metric(
        html_text=f"Прибыль:&nbsp;<span class='fw-semibold'>{format_money(profit)}</span>&nbsp;₽",
        percent=profit_percent,
        css=css_by_metric('Прибыль', profit_percent)
    ) 

    metrics = [
        kp_metric,
        calls_metric,
        trips_metric,
        supply_requests_metric,
        supply_processing_time_metric,
        contracts_metric,
        advances_metric,
        profit_metric,
    ]

    return ManagerInfo(
        name=user["name"],
        position=position,
        photo_url=user["photo_url"] or default_avatar,
        metrics=metrics,
    )

def build_supply_data(user: sqlite3.Row,  default_avatar: str, start_date: str, 
                      end_date: str) -> ManagerInfo:

    user_id = user['id']

    position = 'Менеджер по снабжению'

    # Количество полученных заявок
    requests_deal_ids = {row[0] for row in conn.execute(
        f"""
        SELECT deal_id FROM deals_stage_history
        WHERE new_stage_id IN {config.SUPPLY_CALCULATION_IN_PROGRESS_STAGES}
        AND record_time BETWEEN '{start_date}' AND '{end_date}'
        AND deal_id IN (SELECT id FROM deals WHERE supply_user_id = {user_id})
        """
    ).fetchall()}
    requests_count = len(requests_deal_ids)

    if not requests_count:
        complete_requests_count = 0
    else:
        deals_str = [str(deal_id) for deal_id in requests_deal_ids]
        (complete_requests_count, ) = conn.execute(
            f"""
            SELECT COUNT(DISTINCT deal_id) FROM deals_stage_history
            WHERE record_time BETWEEN '{start_date}' AND '{end_date}'
            AND old_pipeline_id = 20 AND new_pipeline_id = 0
            AND deal_id IN ({','.join(deals_str)})
            """
        ).fetchone()

    requests_percent = safe_percent(complete_requests_count, requests_count)
    requests_metric = Metric(
        html_text=f"Посчитано заявок:&nbsp;<span class='fw-semibold'>{complete_requests_count}</span>&nbsp;из&nbsp;<span class='fw-semibold'>{requests_count}</span>",
        percent=requests_percent,
        css=css_by_metric('Заявки', requests_percent)
    )

    # Среднее время расчета заявки 
    deltas = []
    current_datetime = datetime.now(timezone.utc)
    for deal_id in requests_deal_ids:
        (start_time_str,) = conn.execute(
            f"""
            SELECT record_time FROM deals_stage_history
            WHERE deal_id = {deal_id}
            AND old_stage_id = "C20:NEW"
            AND new_stage_id IN {config.SUPPLY_CALCULATION_IN_PROGRESS_STAGES}
            ORDER BY id 
            LIMIT 1
            """
        ).fetchone()
        start_time = datetime.fromisoformat(start_time_str)

        deal = conn.execute(f'SELECT * FROM deals WHERE id = {deal_id}').fetchone()

        if deal['pipeline_id'] == 20:  # Снабжение для КП  (заявка ещё считается)
            end_time = current_datetime

        else:
            (end_time_str, ) = conn.execute(
                f"""
                SELECT record_time FROM deals_stage_history
                WHERE deal_id = {deal_id}
                AND old_pipeline_id = 20
                AND new_pipeline_id = 0
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            end_time = datetime.fromisoformat(end_time_str)
            
        duration_hours = (end_time - start_time).total_seconds() / 3600
        deltas.append(duration_hours)
    
    if deltas:
        avg_proc_hrs = round(mean(deltas), 1)
        avg_proc_days = round(avg_proc_hrs/24, 1)

        avg_time_str = f'{avg_proc_days} дн.'
    
    else:
        avg_time_str = 'N/A'

    processing_time_metric = Metric(
        html_text=f"Среднее время расчёта:&nbsp;<span class='fw-semibold'>{avg_time_str}</span>",
        percent=0,
        css=css_by_metric(0, 'Среднее время расчёта')
    )

    (request_in_progress, ) = conn.execute(
        f"""
        SELECT COUNT(*) FROM deals 
        WHERE supply_user_id = {user_id}
        AND stage_id = "C20:PREPAYMENT_INVOIC"
        """
    ).fetchone()
    request_in_processing_metric = Metric(
        html_text=f"Заявок в работе:&nbsp;<span class='fw-semibold'>{request_in_progress}</span>",
        percent=0,
        css=css_by_metric(0, 'Заявок в работе')
    )

    # Количество растаможенных грузов 
    (cleared_cargo, ) = conn.execute(
        f"""
        SELECT COUNT(*) FROM deals_stage_history
        WHERE deal_id IN (SELECT id FROM deals WHERE supply_user_id = {user_id})
        AND record_time BETWEEN '{start_date}' AND '{end_date}'
        AND old_stage_id = 'C21:FINAL_INVOICE'
        AND new_stage_id IN {config.CARGO_CLEARED_STAGES}
        """
    ).fetchone()
    cargo_metric = Metric(
        html_text=f"Растаможено грузов:&nbsp;<span class='fw-semibold'>{cleared_cargo}</span>",
        percent=0,
        css=css_by_metric('Растаможено', cleared_cargo)
    )

    placeholder1 = Metric(
        '<span class="text-muted">[Размещенных заказов поставщикам]</span>',
        0,
        css_by_metric('_', 0)
    )
    placeholder2 = Metric(
        '<span class="text-muted">[Найдено новых поставщиков]</span>',
        0,
        css_by_metric('__', 0)
    )
    placeholder3 = Metric(
        '<span class="text-muted">[Сэкономлено ДС]</span>',
        0,
        css_by_metric('___', 0)
    )

    metrics = [
        requests_metric,
        processing_time_metric,
        request_in_processing_metric,
        cargo_metric,
        placeholder1,
        placeholder2,
        placeholder3
    ]

    return ManagerInfo(
        name=user["name"],
        position=position,
        photo_url=user["photo_url"] or default_avatar,
        metrics=metrics,
    )

# ─── маршруты ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    tv_mode = request.args.get("tv") == "1"

    # ---------- список из 6 периодов (текущий + 5 предыдущих) ----------
    today = date.today()

    def prev_month(dt: date, back: int) -> date:
        y, m = dt.year, dt.month - back
        while m <= 0:
            y -= 1
            m += 12
        return date(y, m, 1)

    period_options = []
    for i in range(6):                        # 0..5 месяцев назад
        d = prev_month(today, i)
        period_options.append({
            "value": d.strftime("%Y-%m"),     # например  «2025-07»
            "label": f"{months[d.month-1].capitalize()} {d.year}"
        })

    selected_period = request.args.get("period",
                                       period_options[0]["value"])

    sel_year, sel_month = map(int, selected_period.split("-"))
    first_day = date(sel_year, sel_month, 1)
    last_day  = monthrange(sel_year, sel_month)[1]

    start_date = f"{first_day:%Y-%m-%d}T00:00:00"
    end_date   = f"{first_day.replace(day=last_day):%Y-%m-%d}T23:59:59"


    avatar = url_for("static", filename="default_avatar.jpg")

    sales = [build_manager_data(r, avatar, start_date, end_date) for r
                in conn.execute("SELECT * FROM users WHERE is_sales = 1").fetchall()]
    
    supplies = [build_supply_data(r, avatar, start_date, end_date) for r
                in conn.execute("SELECT * FROM users WHERE is_supply = 1").fetchall()]
    
    (last_updated, ) = conn.execute("SELECT value FROM metadata WHERE key = 'last_updated'").fetchone()
    
    refresh_url = '/?tv=1' if tv_mode else '/'

    return render_template(
        "index.html",
        sales=sales,
        supplies=supplies,
        tv_mode=tv_mode,
        last_updated=last_updated,
        period_options=period_options,
        selected_period=selected_period,
        refresh_url=refresh_url
    )



@app.route("/kp")
def kps():
    selected_filter = request.args.get('filter', '')  # '' если ничего не выбрано
    selected_manager = request.args.get('manager', '')

    if selected_filter == 'success':
        where1 = 'AND deal_id IN (SELECT id FROM deals WHERE pipeline_id = 21)'
    elif selected_filter == 'failed':
        where1 = 'AND deal_id IN (SELECT id FROM deals WHERE stage_semantic_id = "F")'
    elif selected_filter == 'kp_sent':
        where1 = 'AND deal_id IN (SELECT id FROM deals WHERE stage_id = "PREPARATION")'
    elif selected_filter == 'kp_frozen':
        where1 = 'AND deal_id IN (SELECT id FROM deals WHERE stage_id = "UC_Q08ZUN")'
    elif selected_filter == 'signing':
        where1 = 'AND deal_id IN (SELECT id FROM deals WHERE stage_id IN ("17", "UC_CRI622"))'
    elif selected_filter == 'deal_in_progress':
        where1 = """
        AND deal_id NOT IN (SELECT id FROM deals WHERE pipeline_id = 21)
        AND deal_id NOT IN (SELECT id FROM deals WHERE stage_semantic_id = "F")
        AND deal_id NOT IN (SELECT id FROM deals WHERE stage_id = "PREPARATION")
        AND deal_id NOT IN (SELECT id FROM deals WHERE stage_id = "UC_Q08ZUN")
        AND deal_id NOT IN (SELECT id FROM deals WHERE stage_id IN ("17", "UC_CRI622"))
        """
    else:
        where1 = ''
    
    where2 = ''
    selected_manager_safe = None
    if selected_manager:
        manager_str_ids = {str(row[0]) for row in conn.execute('SELECT id FROM users').fetchall()}
        if str(selected_manager) in manager_str_ids:
            where2 = f'AND deal_id IN (SELECT id FROM deals WHERE sales_user_id = {selected_manager})'
            selected_manager_safe = int(selected_manager)

    files = conn.execute(
        f"""
        SELECT * FROM kp_files 
        WHERE kp_date > "2025-05"
        {where1} {where2}
        ORDER BY kp_date DESC 
        """
    ).fetchall()

    kps = []

    for file in files:
        deal_id = file['deal_id']
        deal = conn.execute(f'SELECT * FROM deals WHERE id = {deal_id}').fetchone()

        user_id = deal['sales_user_id']

        # Название сделки  (кликабельное)
        deal_title = deal['title']
        deal_url = f'https://crm.turborand.ru/crm/deal/details/{deal_id}/'

        # Название файла КП (кликабельное)
        if file['original_file_name']:
            file_name = file['original_file_name']
            file_url = f'https://crm.turborand.ru{file["download_url"]}'
        else:
            file_name = ''
            file_url = ''

        # Сумма сделки 
        opportunity_raw  = deal['opportunity']
        opportunity_formatted  = f'{format_money(opportunity_raw)}&nbsp;₽'

        # Тип сделки 
        deal_type = config.STATUS_TYPES[deal['type_id']]

        # Менеджер
        manager = conn.execute(
            'SELECT name FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        manager_name = manager['name'] if manager else '[уволенный сотрудник]'

        # Результат сделки + выделение строки цветом 
        if deal['pipeline_id'] == 21:  # Исп. договора
            result = 'Договор заключен'
            row_color = 'table-success'

        elif deal['stage_id'] in ('17', 'UC_CRI622'):
            result = 'Заключаем договор'
            row_color = 'table-primary'

        elif deal['stage_semantic_id'] == 'F':  # Fail
            if deal['fail_reason']:
                result = f"<b>{deal['fail_reason']}</b>"
            else:
                result = 'Сделка провалена'
            row_color = 'table-danger'

        elif deal['stage_id'] == 'PREPARATION':  # КП отправлено 
            (kp_sent_dt, ) = conn.execute(
                f"""
                SELECT record_time FROM deals_stage_history 
                WHERE deal_id = {deal_id} AND new_stage_id = "PREPARATION"
                ORDER BY id DESC LIMIT 1
                """
            ).fetchone()
            days_ago = (datetime.now(timezone.utc) - datetime.fromisoformat(kp_sent_dt)).days
            result = f'КП отправлено ({days_ago} дн.)'
            row_color = 'table-warning' if days_ago >= 7 else 'table-secondary'

        elif deal['stage_id'] == 'UC_Q08ZUN':  # Замороженные КП 
            (kp_frozen_dt, ) = conn.execute(
                f"""
                SELECT record_time FROM deals_stage_history 
                WHERE deal_id = {deal_id} AND new_stage_id = "UC_Q08ZUN"
                ORDER BY id DESC LIMIT 1
                """
            ).fetchone()
            days_ago = (datetime.now(timezone.utc) - datetime.fromisoformat(kp_frozen_dt)).days
            result = f'КП заморожено ({days_ago} дн.)'
            row_color = ''

        else:
            stage_id = deal['stage_id']
            (stage_dt, ) = conn.execute(
                f"""
                SELECT record_time FROM deals_stage_history 
                WHERE deal_id = {deal_id} AND new_stage_id = "{stage_id}"
                ORDER BY id DESC LIMIT 1
                """
            ).fetchone()
            days_ago = (datetime.now(timezone.utc) - datetime.fromisoformat(stage_dt)).days
            stage_name = config.STATUS_IDS[stage_id]
            result = f'{stage_name} ({days_ago} дн.)'
            row_color = ''

        # Время в стадии (дубль)
        stage_id = deal['stage_id']
        (stage_dt, ) = conn.execute(
            f"""
            SELECT record_time FROM deals_stage_history 
            WHERE deal_id = {deal_id} AND new_stage_id = "{stage_id}"
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
        days_in_stage = (datetime.now(timezone.utc) - datetime.fromisoformat(stage_dt)).days

        # Время обработки 
        try:
            (start_time_str,) = conn.execute(
                f"""
                SELECT record_time FROM deals_stage_history
                WHERE deal_id = {deal_id}
                AND old_pipeline_id = 0
                AND new_pipeline_id = 20
                ORDER BY id 
                LIMIT 1
                """
            ).fetchone()
            start_time = datetime.fromisoformat(start_time_str)

            (end_time_str, ) = conn.execute(
                f"""
                SELECT record_time FROM deals_stage_history
                WHERE deal_id = {deal_id}
                AND old_pipeline_id = 20
                AND new_pipeline_id = 0
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            end_time = datetime.fromisoformat(end_time_str)
                
            duration_hours = (end_time - start_time).total_seconds() / 3600
        
            if duration_hours < 72:
                processing_time = f'{int(duration_hours)} ч.'
                processing_time_raw = duration_hours

            else:
                duration_days = int(duration_hours/24)
                processing_time = f'{duration_days} дн.'
                processing_time_raw = duration_hours 
        
        except Exception:  # не найдена строка в ДБ и т.д.
            processing_time = ''
            processing_time_raw = None

        # Summary 
        summary = file['summary'] if file['summary'] else ''

        kps.append({
            'date': file['kp_date'][:10],
            'deal': deal_title,
            'deal_url': deal_url,
            'deal_type': deal_type,
            'manager': manager_name, 
            'file_name': file_name,
            'file_url': file_url,
            'summary': summary,
            'opportunity': opportunity_formatted,
            'opportunity_raw': opportunity_raw,
            'result': result,
            'row_color': row_color,
            'processing_time': processing_time,
            'processing_time_raw': processing_time_raw,
            'days_in_stage': days_in_stage,
        })


    (last_updated, ) = conn.execute("SELECT value FROM metadata WHERE key = 'last_updated'").fetchone()

    managers = [{'id': m['id'], 'name': m['name']} for m in conn.execute(
        'SELECT * FROM users WHERE is_sales = 1'
    ).fetchall()]

    return render_template(
        'kps.html',
        kps=kps,
        last_updated=last_updated,
        selected_filter=selected_filter,
        managers=managers,
        selected_manager=selected_manager_safe,
    )



# ─── запуск ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3389, debug=True)
