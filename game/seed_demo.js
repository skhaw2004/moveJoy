// Run once: node game/seed_demo.js
// Creates a demo participant with a declining accuracy trend that triggers the MCI flag.

const { DatabaseSync } = require('node:sqlite');
const path = require('path');

const db = new DatabaseSync(path.join(__dirname, 'game_data.db'));

const NAME = 'margaret';

// Insert or fetch user
db.prepare('INSERT OR IGNORE INTO users (name) VALUES (?)').run(NAME);
const user = db.prepare('SELECT * FROM users WHERE name = ?').get(NAME);
console.log(`User: ${user.name} (id=${user.id})`);

// Clear any existing scores for this demo user so re-running is safe
db.prepare('DELETE FROM scores WHERE user_id = ?').run(user.id);

// Sessions: 35 days ago → today (2026-06-17)
// Baseline (first 2 weeks, 2026-05-13 – 2026-05-26): high accuracy ~72–80%
// Transition (2026-05-27 – 2026-06-03): gradual dip ~58–67%
// Recent (last 14 days, 2026-06-04 – 2026-06-17): sharp drop ~38–50%
const sessions = [
  // Baseline — strong performance
  { date: '2026-05-13 10:14:00', hits: 38, total: 50 }, // 76%
  { date: '2026-05-15 10:22:00', hits: 40, total: 50 }, // 80%
  { date: '2026-05-18 09:58:00', hits: 36, total: 50 }, // 72%
  { date: '2026-05-20 10:30:00', hits: 39, total: 50 }, // 78%
  { date: '2026-05-23 11:02:00', hits: 37, total: 50 }, // 74%
  // Transition — starting to slip
  { date: '2026-05-28 10:45:00', hits: 33, total: 50 }, // 66%
  { date: '2026-05-31 09:30:00', hits: 30, total: 50 }, // 60%
  { date: '2026-06-02 10:10:00', hits: 29, total: 50 }, // 58%
  // Recent — significant decline
  { date: '2026-06-05 10:20:00', hits: 24, total: 50 }, // 48%
  { date: '2026-06-08 09:55:00', hits: 22, total: 50 }, // 44%
  { date: '2026-06-11 10:40:00', hits: 20, total: 50 }, // 40%
  { date: '2026-06-14 11:05:00', hits: 19, total: 50 }, // 38%
  { date: '2026-06-17 10:15:00', hits: 21, total: 50 }, // 42%
];

const insert = db.prepare(
  'INSERT INTO scores (user_id, score, sequence_length, difficulty, song_id, played_at) VALUES (?, ?, ?, ?, ?, ?)'
);

for (const s of sessions) {
  insert.run(user.id, s.hits, s.total, 'easy', 'twinkle', s.date);
  const pct = Math.round((s.hits / s.total) * 100);
  console.log(`  ${s.date}  →  ${pct}%`);
}

console.log(`\nDone. ${sessions.length} sessions inserted for "${NAME}".`);
console.log('Open http://localhost:3000/admin and refresh to see the flag.');
