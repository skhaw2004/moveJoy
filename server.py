"""
MoveJoy v2 — Player Database Server
--------------------------------------
Flask + SQLite API for player registration, progress and scores.
Runs alongside gesture_server.py on the Pi.

Endpoints:
  GET  /player?name=<name>          → player data or 404
  POST /player                      → create player { name }
  GET  /player/<id>/progress        → all level progress for player
  PUT  /player/<id>/progress        → save level progress { level_id, stars, score, completed }

Usage:
  python3 server.py
Runs on http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os, datetime

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'movejoy.db')


# ── Database setup ─────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            created_at TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS progress (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id  INTEGER NOT NULL REFERENCES players(id),
            level_id   INTEGER NOT NULL,
            stars      INTEGER NOT NULL DEFAULT 0,
            score      INTEGER NOT NULL DEFAULT 0,
            completed  INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT    NOT NULL,
            UNIQUE(player_id, level_id)
        );
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Initialised at {DB_PATH}")


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/player', methods=['GET'])
def get_player():
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400

    conn = get_db()
    row = conn.execute('SELECT * FROM players WHERE name = ?', (name,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'not found'}), 404

    progress = conn.execute(
        'SELECT level_id, stars, score, completed FROM progress WHERE player_id = ?',
        (row['id'],)
    ).fetchall()
    conn.close()

    return jsonify({
        'id':         row['id'],
        'name':       row['name'],
        'created_at': row['created_at'],
        'progress':   [dict(p) for p in progress]
    })


@app.route('/player', methods=['POST'])
def create_player():
    data = request.get_json()
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400

    now = datetime.datetime.utcnow().isoformat()
    conn = get_db()
    try:
        cur = conn.execute('INSERT INTO players (name, created_at) VALUES (?, ?)', (name, now))
        conn.commit()
        player_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'name already exists'}), 409
    conn.close()

    return jsonify({'id': player_id, 'name': name, 'created_at': now, 'progress': []}), 201


@app.route('/player/<int:player_id>/progress', methods=['GET'])
def get_progress(player_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT level_id, stars, score, completed FROM progress WHERE player_id = ?',
        (player_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/player/<int:player_id>/progress', methods=['PUT'])
def save_progress(player_id):
    data       = request.get_json()
    level_id   = data.get('level_id')
    stars      = data.get('stars', 0)
    score      = data.get('score', 0)
    completed  = 1 if data.get('completed') else 0
    now        = datetime.datetime.utcnow().isoformat()

    if level_id is None:
        return jsonify({'error': 'level_id required'}), 400

    conn = get_db()
    conn.execute("""
        INSERT INTO progress (player_id, level_id, stars, score, completed, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_id, level_id) DO UPDATE SET
            stars      = MAX(stars, excluded.stars),
            score      = MAX(score, excluded.score),
            completed  = excluded.completed,
            updated_at = excluded.updated_at
    """, (player_id, level_id, stars, score, completed, now))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("[Server] Running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5001, debug=False)
