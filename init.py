import sqlite3
import os 

try:
    os.remove('database.db')
except FileNotFoundError:
    pass 

conn = sqlite3.connect('database.db')
with open('schema.sql') as f:
    with conn:
        conn.executescript(f.read())

print('ok')