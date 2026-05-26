import sqlite3

DB_NAME = "game_data.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            sequence_length INTEGER NOT NULL,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()


def register_user(user_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users (user_id)
        VALUES (?)
    """, (user_id,))

    conn.commit()
    conn.close()


def save_session(user_id: str, score: int, sequence_length: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO game_sessions (user_id, score, sequence_length)
        VALUES (?, ?, ?)
    """, (user_id, score, sequence_length))

    conn.commit()
    conn.close()