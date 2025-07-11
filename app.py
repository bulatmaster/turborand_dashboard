import sqlite3
import random
from typing import List, Dict

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


def build_manager_data(row, default_avatar: str) -> Dict:
    eff = random.randint(20, 100)
    return {
        'name': row['name'],
        'position': random.choice(['Стажер ', 'Младший менеджер', 'Менеджер по продажам', 'Ведущий менеджер по продажам']),
        'photo_url': row['photo_url'] or default_avatar,
        'eff': eff,
        'eff_class': color_class(eff),
        'bar_class': bar_class(eff),
        'kp_count': random.randint(0, 60),
        'calls_minutes': random.randint(0, 1800),
        'trips_count': random.randint(0, 13),
        'success_deals': random.randint(0, 7),
        'advances_rub': format_money(random.randint(0, 6_000_000)),
        'profit_rub': format_money(random.randint(0, 6_000_000)),
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
