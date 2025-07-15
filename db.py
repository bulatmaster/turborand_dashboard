import sqlite3 


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    conn.set_trace_callback(print)
    return conn 