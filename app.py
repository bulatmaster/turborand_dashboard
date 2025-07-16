import sqlite3, random
from datetime import datetime, timezone
from typing import List, Dict
from flask import Flask, render_template, url_for

import db 

app = Flask(__name__, template_folder='templates', static_folder='static')

# ─── подключение к БД ────────────────────────────────────────────────────────
conn = db.get_conn()

# ─── планы ───────────────────────────────────────────────────────────────────
BASE_PLANS = {
    "КП":             40,
    "Звонки, мин":   1200,
    "Командировки":   10,
    "Договоры":        5,
    "Авансы":    4_000_000,
}

POSITION_PROFIT_PLAN = {
    "Стажер":                       250_000,
    "Младший менеджер":             850_000,
    "Менеджер по продажам":       2_500_000,
    "Ведущий менеджер по продажам": 5_000_000,
}
POSITIONS = list(POSITION_PROFIT_PLAN.keys())

# ─── окрашивание шкал по правилам ────────────────────────────────────────────
def css_by_metric(label: str, value: int | float) -> str:
    if label == "КП":
        if value <= 9:   return "bg-secondary"
        if value <= 19:  return "bg-danger"
        if value <= 29:  return "bg-warning"
        return "bg-success"

    if label == "Звонки, мин":
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

    if label == "Прибыль":          # одинаковые пороги для всех позиций
        if value <  50_000:  return "bg-secondary"
        if value < 100_000:  return "bg-danger"
        if value < 200_000:  return "bg-warning"
        return "bg-success"

    return "bg-secondary"

# ─── прочие утилиты ──────────────────────────────────────────────────────────
def human_int(val: int | float) -> str:
    return f"{int(val):,}".replace(",", " ")

def progress_info(label: str, value: int | float, plan: int, money: bool=False) -> Dict:
    percent = min(100, round(value / plan * 100, 1))  # ширина полосы
    css     = css_by_metric(label, value)             # цвет полосы

    txt = f"{label}:&nbsp;<span class='fw-semibold'>{human_int(value)}</span>"
    if money:
        txt += "&nbsp;₽"

    return {"display": txt, "percent": percent, "css": css}

def color_class(eff: int) -> str:
    if eff >= 80: return "text-success"
    if eff >= 50: return "text-warning"
    return "text-danger"

def bar_class(eff: int) -> str:
    if eff >= 80: return "bg-success"
    if eff >= 50: return "bg-warning"
    return "bg-danger"


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
def build_manager_data(user: sqlite3.Row, avatar: str) -> Dict:
    kp, calls_seconds, trips, dealchanges  = random.randint(0, 60), random.randint(0, 1800), \
                               random.randint(0, 13), random.randint(0, 7)
    advances   = random.randint(0, 6_000_000)

    position    = random.choice(POSITIONS)
    profit_plan = POSITION_PROFIT_PLAN[position]
    profit      = random.randint(0, profit_plan * 2)

    
    

    ################
    user_id = user['id']
    position = get_manager_position(user['date_register'])
    
    START_DATE = '2025-06-16'  # Сделать динамически 
    END_DATE = '2025-07-17'

    (kp, ) = conn.execute(
        """
        SELECT COUNT(*) FROM deals_stage_history
        WHERE new_stage_id = "PREPARATION"
        AND deal_id IN (
            SELECT id FROM deals WHERE sales_user_id = ?
        ) AND record_time BETWEEN ? AND ?
        """, (user_id, START_DATE, END_DATE)
    ).fetchone()

    (calls_seconds, ) = conn.execute(
        """
        SELECT SUM(duration) FROM calls 
        WHERE user_id = ?
        AND start_time BETWEEN ? AND ?
        """, (user_id, START_DATE, END_DATE)
    ).fetchone()
    calls = int(calls_seconds / 60) if calls_seconds else 0

    (trips, ) = conn.execute(
        """
        SELECT COUNT(*) FROM trips 
        WHERE user_id = ? 
        AND begin_time BETWEEN ? AND ?
        """, (user_id, START_DATE, END_DATE)
    ).fetchone()

    new_deal_ids = {row[0] for row in conn.execute(
        """
        SELECT deal_id FROM deals_stage_history
        WHERE record_time BETWEEN ? AND ?
        AND deal_id IN (
            SELECT id FROM deals WHERE sales_user_id = ?
        ) AND new_pipeline_id = 21
        AND old_pipeline_id = 0
        """, (START_DATE, END_DATE, user_id)
    ).fetchall()}

    new_deal_ids = [str(deal_id) for deal_id in new_deal_ids]

    (profit, ) = conn.execute(
        f"""
        SELECT SUM(profit) FROM deals WHERE id IN ({','.join(new_deal_ids)})
        """
    ).fetchone()
    if not profit:
        profit = 0

    (advances, ) = conn.execute(
        """
        SELECT SUM(amount) FROM payments 
        WHERE deal_id IN (
            SELECT id FROM deals WHERE sales_user_id = ?
        ) AND payment_type = 'Аванс'
        AND payment_time BETWEEN ? AND ?
        """, (user_id, START_DATE, END_DATE)
    ).fetchone()
    if not advances:
        advances = 0
    


    metrics = [
        progress_info("КП",            kp,      BASE_PLANS["КП"]),
        progress_info("Звонки, мин",   calls,   BASE_PLANS["Звонки, мин"]),
        progress_info("Командировки",  trips,   BASE_PLANS["Командировки"]),
        progress_info("Договоры",      len(new_deal_ids),   BASE_PLANS["Договоры"]),
        progress_info("Авансы",        advances, BASE_PLANS["Авансы"], money=True),
        progress_info("Прибыль",       profit,  profit_plan,           money=True),
    ]

    eff = random.randint(20, 100)
    return {
        "name": user["name"],
        "position": position,
        "photo_url": user["photo_url"] or avatar,
        "eff": eff,
        "eff_class": color_class(eff),
        "bar_class": bar_class(eff),
        "metrics": metrics,
    }

# ─── данные снабженцев (без изменений) ───────────────────────────────────────
def build_supply_data(row,  avatar: str) -> Dict:
    eff = random.randint(1, 100)

    total = random.randint(5, 30)
    done  = random.randint(0, total)
    percent = done / total * 100 if total else 0
    css  = "bg-success" if percent >= 100 else \
           "bg-warning" if percent >= 50 else "bg-danger"
    txt  = f"Посчитано:&nbsp;<span class='fw-semibold'>{done}</span>&nbsp;/&nbsp;<span class='fw-semibold'>{total}</span>"

    return {
        "name": row["name"],
        "photo_url": row["photo_url"] or avatar,
        "eff": eff,
        "eff_class": color_class(eff),
        "bar_class": bar_class(eff),
        "calc": {"display": txt, "percent": round(min(percent, 100), 1), "css": css},
    }

# ─── маршруты ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    avatar   = url_for("static", filename="default_avatar.jpg")
    managers = [build_manager_data(r, avatar) for r
                in conn.execute("SELECT * FROM users WHERE is_sales = 1")]
    supplies = [build_supply_data(r, avatar) for r
                in conn.execute("SELECT * FROM users WHERE is_supply = 1")]
    return render_template("index.html", managers=managers, supplies=supplies)

# ─── запуск ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3389, debug=True)
