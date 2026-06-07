import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "/tmp/bot.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        query TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    try:
        yield cur
        conn.commit()
    finally:
        conn.close()

def add_user(user_id, username=None, first_name=None):
    with get_db() as cur:
        cur.execute("INSERT OR IGNORE INTO users(user_id, username, first_name) VALUES(?,?,?)",
                    (user_id, username, first_name))

def log_query(user_id, query):
    with get_db() as cur:
        cur.execute("INSERT INTO logs(user_id, query) VALUES(?,?)", (user_id, query))

def get_stats():
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM logs")
        total_requests = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM logs WHERE date(timestamp) = date('now')")
        today_requests = cur.fetchone()[0]
    return users, total_requests, today_requests

def get_all_users():
    with get_db() as cur:
        cur.execute("SELECT user_id, username, first_name FROM users")
        return cur.fetchall()

def get_logs(limit=50):
    with get_db() as cur:
        cur.execute("SELECT user_id, query, timestamp FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()