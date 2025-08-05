import sqlite3 
import logging


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.set_trace_callback(logging.debug)
    return conn 