const { DatabaseSync } = require('node:sqlite');
const path = require('path');

const db = new DatabaseSync(path.join(__dirname, 'game_data.db'));

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
  CREATE TABLE IF NOT EXISTS scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    score           INTEGER NOT NULL,
    sequence_length INTEGER NOT NULL,
    difficulty      TEXT NOT NULL,
    played_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
`);

function registerUser(name) {
  const normalized = name.trim().toLowerCase();
  db.prepare('INSERT OR IGNORE INTO users (name) VALUES (?)').run(normalized);
  return db.prepare('SELECT * FROM users WHERE name = ?').get(normalized);
}

function saveScore(name, score, sequenceLength, difficulty) {
  const user = registerUser(name);
  db.prepare(
    'INSERT INTO scores (user_id, score, sequence_length, difficulty) VALUES (?, ?, ?, ?)'
  ).run(user.id, score, sequenceLength, difficulty);
}

function getLeaderboard(limit = 10) {
  return db.prepare(`
    SELECT u.name, s.score, s.sequence_length, s.difficulty, s.played_at
    FROM scores s
    JOIN users u ON u.id = s.user_id
    ORDER BY s.score DESC, s.played_at DESC
    LIMIT ?
  `).all(limit);
}

function getAllUsers() {
  return db.prepare(`
    SELECT u.id, u.name, COUNT(s.id) as session_count, MAX(s.played_at) as last_played
    FROM users u
    LEFT JOIN scores s ON s.user_id = u.id
    GROUP BY u.id
    ORDER BY last_played DESC NULLS LAST
  `).all();
}

function getUserStats(userId) {
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
  if (!user) return null;

  const sessions = db.prepare(`
    SELECT score, sequence_length, difficulty, played_at
    FROM scores WHERE user_id = ?
    ORDER BY played_at ASC
  `).all(userId);

  if (sessions.length === 0) return { user, sessions: [], stats: null };

  const accuracies = sessions.map(s => s.score / s.sequence_length);
  const avgAccuracy = accuracies.reduce((a, b) => a + b, 0) / accuracies.length;
  const bestScore = Math.max(...sessions.map(s => s.score));

  let trend = 'Stable';
  if (sessions.length >= 4) {
    const recentAvg = accuracies.slice(-3).reduce((a, b) => a + b, 0) / 3;
    const earlierAvg = accuracies.slice(0, -3).reduce((a, b) => a + b, 0) / (accuracies.length - 3);
    const diff = recentAvg - earlierAvg;
    if (diff > 0.1) trend = 'Improving';
    else if (diff < -0.1) trend = 'Declining';
  }

  return { user, sessions, stats: { avgAccuracy, bestScore, totalSessions: sessions.length, trend } };
}

module.exports = { registerUser, saveScore, getLeaderboard, getAllUsers, getUserStats };
