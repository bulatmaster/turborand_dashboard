import sqlite3 
from random import randint
import random 

from flask import Flask, render_template, url_for




app = Flask(__name__, template_folder='templates', static_folder='static')

conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row


def color_class(eff: int) -> str:
    if eff >= 80:
        return "text-success"     # зелёный (Bootstrap)
    elif eff >= 50:
        return "text-warning"     # жёлтый
    elif eff >= 30:
        return "text-orange"      # добавим свой
    else:
        return "text-danger"      # красный


def bar_class(eff: int) -> str:
    if eff >= 80:
        return "bg-success"
    elif eff >= 50:
        return "bg-warning"
    elif eff >= 30:
        return "bg-orange"
    else:
        return "bg-danger"


@app.route('/')
def index():
    default_avatar = url_for('static', filename='default_avatar.jpg')

    db_managers = conn.execute('SELECT * FROM users WHERE is_sales = 1').fetchall()
    managers = []
    for db_man in db_managers:

        eff = randint(20, 100)


        profit = random.randint(0, 1_000_000)
        managers.append({
            'name': db_man['name'],
            'photo_url': db_man['photo_url'] if db_man['photo_url'] else default_avatar,
            'eff': eff,
            'eff_class': color_class(eff),
            'bar_class': bar_class(eff),
            'kp_count': randint(2, 100),
            'calls_count': randint(20, 500),
            'success_deals': randint(0, 50),
            'profit_money': f"{profit:,}".replace(",", " ") + " ₽"
        })
    
    supplies = []
    db_supplies = conn.execute('SELECT * FROM users WHERE is_supply = 1').fetchall()
    for db_man in db_supplies:
        eff = randint(1, 100)
        supplies.append({
            'name': db_man['name'],
            'photo_url': db_man['photo_url'] if db_man['photo_url'] else default_avatar,
            'eff': eff,
            'eff_class': color_class(eff),
            'bar_class': bar_class(eff),
            'stat1': randint(1, 200),
            'stat2': randint(200, 1000),
        })
    
    return render_template('index.html', managers=managers, supplies=supplies)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3389, debug=True)
    
