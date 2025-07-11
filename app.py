import sqlite3
import random
from typing import List, Dict
from dataclasses import dataclass 

from flask import Flask, render_template, url_for

app = Flask(__name__, template_folder='templates', static_folder='static')

# Подключение к базе
conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row


# --- Вспомогательные функции ---
def color_class(eff: int) -> str:
    if eff >= 80:
        return "text-success"   # зелёный
    elif eff >= 50:
        return "text-warning"   # жёлтый
    return "text-danger"        # красный



def bar_class(eff: int) -> str:
    if eff >= 80:
        return "bg-success"     # зелёный
    elif eff >= 50:
        return "bg-warning"     # жёлтый
    return "bg-danger"          # красный


def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₽"


THRESHOLDS = {
    "kp":        {"plan": 40,   "zones": [(0,  9,  "bg-secondary"),   # серый
                                         (10, 19, "bg-danger"),
                                         (20, 29, "bg-warning"),
                                         (30, 40, "bg-success")]},
    "calls":     {"plan": 1200, "zones": [(0, 299,  "bg-secondary"),
                                         (300, 599, "bg-danger"),
                                         (600, 899, "bg-warning"),
                                         (900, 1200,"bg-success")]},
    "trips":     {"plan": 10,   "zones": [(0, 3,   "bg-danger"),
                                         (4, 8,    "bg-warning"),
                                         (9, 999,  "bg-success")]},
    "deals":     {"plan": 5,    "zones": [(0, 1,   "bg-danger"),
                                         (2, 3,    "bg-warning"),
                                         (4, 999,  "bg-success")]},
    "advances":  {"plan": 4_000_000, "zones": [(0, 999_999,   "bg-danger"),
                                               (1_000_000, 2_999_999, "bg-warning"),
                                               (3_000_000, 9_999_999, "bg-success")]},
}

PROFIT_TRESHOLDS = {
    "Стажер": 250_000,
    "Младший менеджер": 850_000,
    "Менеджер по продажам": 2_500_000,
    "Ведущий менеджер по продажам": 5_000_000,
}

def choose_zone(value: int | float, zones):
    """Возвращает класс Bootstrap для зоны, куда попало значение"""
    for low, high, css in zones:
        if low <= value <= high:
            return css
    return zones[-1][2]


def progress_info(metric_key: str, value: int | float):
    cfg = THRESHOLDS[metric_key]
    percent = min(100, round(value / cfg["plan"] * 100, 1))
    color   = choose_zone(value, cfg["zones"])
    return {"val": value, "plan": cfg["plan"],
            "percent": percent, "css": color}


def money_info(progress_info: dict) -> dict:
    amount = progress_info['val']
    formatted = f"{amount:,}".replace(",", " ") + " ₽"
    progress_info['val'] = formatted
    return progress_info


# ─── Формируем данные менеджера ───────────────────────────────────────────────
def build_manager_data(row, default_avatar: str) -> Dict:
    # … то, что уже было …
    kp          = random.randint(0, 60)
    calls       = random.randint(0, 1800)
    trips       = random.randint(0, 13)
    deals       = random.randint(0, 7)
    advances    = random.randint(0, 6_000_000)
    profit      = random.randint(0, 6_000_000)

    return {
        'name': row['name'],
        'position': random.choice(['Стажер', "Младший менеджер", "Менеджер по продажам", "Ведущий менеджер по продажам"]),
        'photo_url': row['photo_url'] or default_avatar,

        # метрики сразу в «расширенном» виде
        'metrics': {
            'КП':        progress_info("kp", kp),
            'Звонки, мин':progress_info("calls", calls),
            'Командировки':progress_info("trips", trips),
            'Договоры':   progress_info("deals", deals),
            'Авансы':  progress_info("advances", advances),
            #'Прибыль': progress_info("profit", profit)
        }
    }


def build_supply_data(row, default_avatar: str) -> Dict:
    eff = random.randint(1, 100)
    return {
        'name': row['name'],
        'photo_url': row['photo_url'] or default_avatar,
        'eff': eff,
        'eff_class': color_class(eff),
        'bar_class': bar_class(eff),
        'stat1': random.randint(1, 200),
        'stat2': random.randint(200, 1000),
    }


# --- Маршруты ---
@app.route('/')
def index():
    default_avatar = url_for('static', filename='default_avatar.jpg')

    db_managers = conn.execute('SELECT * FROM users WHERE is_sales = 1').fetchall()
    db_supplies = conn.execute('SELECT * FROM users WHERE is_supply = 1').fetchall()

    managers: List[Dict] = [build_manager_data(row, default_avatar) for row in db_managers]
    supplies: List[Dict] = [build_supply_data(row, default_avatar) for row in db_supplies]

    return render_template('index.html', managers=managers, supplies=supplies)


# --- Запуск ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3389, debug=True)
