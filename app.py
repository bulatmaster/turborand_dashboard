import sqlite3
import random
from typing import List, Dict
from flask import Flask, render_template, url_for

app = Flask(__name__, template_folder='templates', static_folder='static')

# ─── подключение к БД ─────────────────────────────────────────────────────────
conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row

# ─── планы по метрикам ────────────────────────────────────────────────────────
BASE_PLANS = {
    "КП":            40,
    "Звонки, мин":  1200,
    "Командировки":  10,
    "Договоры":       5,
    "Авансы":   4_000_000,
}

POSITION_PROFIT_PLAN = {
    "Стажер":                     250_000,
    "Младший менеджер":           850_000,
    "Менеджер по продажам":     2_500_000,
    "Ведущий менеджер по продажам": 5_000_000,
}
POSITIONS = list(POSITION_PROFIT_PLAN.keys())

# ─── вспомогательные функции ──────────────────────────────────────────────────
def css_zone_by_percent(pct: float) -> str:
    if pct < 50:
        return "bg-danger"
    elif pct < 100:
        return "bg-warning"
    return "bg-success"

def human_int(val: int | float) -> str:
    return f"{int(val):,}".replace(",", " ")

def progress_info(label: str, value: int | float, plan: int, money: bool = False) -> Dict:
    percent = min(100, round(value / plan * 100, 1))
    css     = css_zone_by_percent(percent)

    if money:
        txt = (f"{label}:&nbsp;"
            f"<span class='fw-semibold'>{human_int(value)}</span>&nbsp;₽")
    else:
        txt = f"{label}:&nbsp;<span class='fw-semibold'>{human_int(value)}</span>"


    return {
        "display": txt,   # помечаем как безопасный HTML
        "percent": percent,
        "css": css,
    }

def color_class(eff: int) -> str:
    if eff >= 80:
        return "text-success"
    elif eff >= 50:
        return "text-warning"
    return "text-danger"

def bar_class(eff: int) -> str:
    if eff >= 80:
        return "bg-success"
    elif eff >= 50:
        return "bg-warning"
    return "bg-danger"

# ─── данные менеджеров продаж ────────────────────────────────────────────────
def build_manager_data(row, avatar: str) -> Dict:
    # демо-данные
    kp, calls, trips, deals = random.randint(0, 60), random.randint(0, 1800), \
                              random.randint(0, 13), random.randint(0, 7)
    advances = random.randint(0, 6_000_000)

    position   = random.choice(POSITIONS)
    profit_plan = POSITION_PROFIT_PLAN[position]
    profit     = random.randint(0, profit_plan * 2)

    metrics = [
        progress_info("КП",            kp,      BASE_PLANS["КП"]),
        progress_info("Звонки, мин",   calls,   BASE_PLANS["Звонки, мин"]),
        progress_info("Командировки",  trips,   BASE_PLANS["Командировки"]),
        progress_info("Договоры",      deals,   BASE_PLANS["Договоры"]),
        progress_info("Авансы",        advances,BASE_PLANS["Авансы"], money=True),
        progress_info("Прибыль",       profit,  profit_plan,           money=True),
    ]

    eff = random.randint(20, 100)
    return {
        "name": row["name"],
        "position": position,
        "photo_url": row["photo_url"] or avatar,
        "eff": eff,
        "eff_class": color_class(eff),
        "bar_class": bar_class(eff),
        "metrics": metrics,
    }

# ─── данные сотрудников снабжения ─────────────────────────────────────────────
def build_supply_data(row, avatar: str) -> Dict:
    eff = random.randint(1, 100)

    calc_total = random.randint(5, 30)
    calc_done  = random.randint(0, calc_total)

    percent = calc_done / calc_total * 100 if calc_total else 0
    css = css_zone_by_percent(percent)
    txt = f"Посчитано:&nbsp;<span class='fw-semibold'>{calc_done}</span>&nbsp;/&nbsp;<span class='fw-semibold'>{calc_total}</span>"
    calc_metric = {
        "display": txt,
        "percent": min(100, round(percent, 1)),
        "css": css,
    }

    return {
        "name": row["name"],
        "photo_url": row["photo_url"] or avatar,
        "eff": eff,
        "eff_class": color_class(eff),
        "bar_class": bar_class(eff),
        "calc": calc_metric,
    }

# ─── маршруты ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    avatar = url_for("static", filename="default_avatar.jpg")
    db_managers = conn.execute("SELECT * FROM users WHERE is_sales = 1").fetchall()
    db_supplies = conn.execute("SELECT * FROM users WHERE is_supply = 1").fetchall()

    managers: List[Dict] = [build_manager_data(r, avatar) for r in db_managers]
    supplies: List[Dict] = [build_supply_data(r, avatar) for r in db_supplies]

    return render_template("index.html", managers=managers, supplies=supplies)

# ─── запуск ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3389, debug=True)
