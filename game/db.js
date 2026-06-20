const { DatabaseSync } = require('node:sqlite');
const path = require('path');

const db = new DatabaseSync(path.join(__dirname, 'game_data.db'));

const BOSS_MAX_HP = 60000;

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
    song_id         TEXT NOT NULL DEFAULT 'unknown',
    played_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
  CREATE TABLE IF NOT EXISTS pets (
    user_id INTEGER PRIMARY KEY,
    pet_id  TEXT NOT NULL DEFAULT 'cat',
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
  CREATE TABLE IF NOT EXISTS boss (
    id         INTEGER PRIMARY KEY,
    hp         INTEGER NOT NULL,
    max_hp     INTEGER NOT NULL,
    generation INTEGER NOT NULL DEFAULT 1
  );
`);

// Ensure the shared boss row exists
if (!db.prepare('SELECT id FROM boss WHERE id = 1').get()) {
  db.prepare('INSERT INTO boss (id, hp, max_hp, generation) VALUES (1, ?, ?, 1)')
    .run(BOSS_MAX_HP, BOSS_MAX_HP);
}

// ── User helpers ──────────────────────────────────────────────
function registerUser(name) {
  const normalized = name.trim().toLowerCase();
  db.prepare('INSERT OR IGNORE INTO users (name) VALUES (?)').run(normalized);
  return db.prepare('SELECT * FROM users WHERE name = ?').get(normalized);
}

function saveScore(name, score, sequenceLength, difficulty, songId = 'unknown') {
  const user = registerUser(name);
  db.prepare(
    'INSERT INTO scores (user_id, score, sequence_length, difficulty, song_id) VALUES (?, ?, ?, ?, ?)'
  ).run(user.id, score, sequenceLength, difficulty, songId);
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
    SELECT score, sequence_length, difficulty, song_id, played_at
    FROM scores WHERE user_id = ?
    ORDER BY played_at ASC
  `).all(userId);

  if (sessions.length === 0) return { user, sessions: [], stats: null };

  const accuracies = sessions.map(s => s.score / s.sequence_length);
  const avgAccuracy = accuracies.reduce((a, b) => a + b, 0) / accuracies.length;
  const bestScore = Math.max(...sessions.map(s => s.score));

  let trend = 'Stable';
  if (sessions.length >= 4) {
    const recentAvg  = accuracies.slice(-3).reduce((a, b) => a + b, 0) / 3;
    const earlierAvg = accuracies.slice(0, -3).reduce((a, b) => a + b, 0) / (accuracies.length - 3);
    const diff = recentAvg - earlierAvg;
    if (diff > 0.1)       trend = 'Improving';
    else if (diff < -0.1) trend = 'Declining';
  }

  return { user, sessions, stats: { avgAccuracy, bestScore, totalSessions: sessions.length, trend } };
}

// ── Pet helpers ───────────────────────────────────────────────
function getPet(name) {
  const normalized = name.trim().toLowerCase();
  const user = db.prepare('SELECT id FROM users WHERE name = ?').get(normalized);
  if (!user) return null;
  return db.prepare('SELECT pet_id AS petId FROM pets WHERE user_id = ?').get(user.id);
}

function setPet(name, petId) {
  const user = registerUser(name);
  db.prepare('INSERT OR REPLACE INTO pets (user_id, pet_id) VALUES (?, ?)').run(user.id, petId);
}

// ── Boss helpers ──────────────────────────────────────────────
function getBoss() {
  const row = db.prepare('SELECT hp, max_hp, generation FROM boss WHERE id = 1').get();
  return { hp: row.hp, maxHp: row.max_hp, generation: row.generation };
}

function applyBossDamage(damage) {
  const boss  = getBoss();
  const newHp = Math.max(0, boss.hp - damage);

  let wasDefeated = false;
  let newGen      = boss.generation;

  if (newHp <= 0) {
    wasDefeated = true;
    newGen      = boss.generation + 1;
    db.prepare('UPDATE boss SET hp = ?, generation = ? WHERE id = 1').run(BOSS_MAX_HP, newGen);
  } else {
    db.prepare('UPDATE boss SET hp = ? WHERE id = 1').run(newHp);
  }

  return {
    hp:          wasDefeated ? BOSS_MAX_HP : newHp,
    maxHp:       BOSS_MAX_HP,
    generation:  newGen,
    wasDefeated,
  };
}

// Returns all users that have chosen a pet (for the ranch)
function getAllPets() {
  return db.prepare(`
    SELECT u.name, p.pet_id AS petId
    FROM pets p
    JOIN users u ON u.id = p.user_id
    ORDER BY u.name ASC
  `).all();
}

function getAdminDashboard() {
  const users = db.prepare(`
    SELECT u.id, u.name, u.created_at,
      COUNT(s.id)    AS session_count,
      MAX(s.played_at) AS last_played,
      MIN(s.played_at) AS first_played
    FROM users u
    LEFT JOIN scores s ON s.user_id = u.id
    GROUP BY u.id
    ORDER BY last_played DESC NULLS LAST
  `).all();

  const now = Date.now();

  return users.map(user => {
    const sessions = db.prepare(`
      SELECT score, sequence_length, played_at
      FROM scores WHERE user_id = ?
      ORDER BY played_at ASC
    `).all(user.id);

    const sessionData = sessions.map(s => ({
      accuracy:  s.sequence_length > 0 ? Math.round((s.score / s.sequence_length) * 100) : 0,
      played_at: s.played_at,
    }));

    const firstPlayed    = user.first_played ? new Date(user.first_played).getTime() : now;
    const daysSinceFirst = (now - firstPlayed) / 86400000;

    let status = 'building_baseline';
    let statusLabel = 'Building Baseline';
    let change = null;

    if (daysSinceFirst >= 28 && sessionData.length >= 8) {
      const baselineCutoff = new Date(firstPlayed + 14 * 86400000).toISOString();
      const recentCutoff   = new Date(now        - 14 * 86400000).toISOString();
      const baseline = sessionData.filter(s => s.played_at <  baselineCutoff);
      const recent   = sessionData.filter(s => s.played_at >= recentCutoff);

      if (baseline.length >= 3 && recent.length >= 3) {
        const avg = arr => arr.reduce((a, b) => a + b.accuracy, 0) / arr.length;
        change = Math.round(avg(recent) - avg(baseline));
        if      (change <= -20) { status = 'flag';  statusLabel = 'Recommend Review'; }
        else if (change <= -10) { status = 'watch'; statusLabel = 'Watch'; }
        else                    { status = 'ok';    statusLabel = 'No Concerns'; }
      } else {
        status = 'monitoring'; statusLabel = 'Monitoring';
      }
    } else if (daysSinceFirst >= 14) {
      status = 'monitoring'; statusLabel = 'Monitoring';
    }

    const avgAccuracy = sessionData.length > 0
      ? Math.round(sessionData.reduce((a, b) => a + b.accuracy, 0) / sessionData.length)
      : null;

    return {
      id:            user.id,
      name:          user.name,
      session_count: user.session_count || 0,
      last_played:   user.last_played,
      first_played:  user.first_played,
      days_active:   Math.floor(daysSinceFirst),
      avg_accuracy:  avgAccuracy,
      status,
      status_label:  statusLabel,
      change,
      sessions:      sessionData,
    };
  });
}

module.exports = {
  registerUser, saveScore, getLeaderboard, getAllUsers, getUserStats,
  getPet, setPet,
  getBoss, applyBossDamage,
  getAllPets,
  getAdminDashboard,
};
