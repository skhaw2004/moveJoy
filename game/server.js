const express = require('express');
const path    = require('path');
const {
  registerUser, saveScore, getLeaderboard, getAllUsers, getUserStats,
  getPet, setPet,
  getBoss, applyBossDamage,
  getAllPets,
  getAdminDashboard,
} = require('./db');

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

// ── Users ─────────────────────────────────────────────────────
app.post('/api/users', (req, res) => {
  const { name } = req.body;
  if (!name || !name.trim()) return res.status(400).json({ error: 'Name required' });
  const user = registerUser(name.trim());
  res.json(user);
});

// ── Scores (kept for admin / legacy) ─────────────────────────
app.post('/api/scores', (req, res) => {
  const { name, score, sequenceLength, difficulty, songId } = req.body;
  if (!name || score == null || !sequenceLength || !difficulty)
    return res.status(400).json({ error: 'Missing fields' });
  saveScore(name.trim(), score, sequenceLength, difficulty, songId || 'unknown');
  res.json({ ok: true });
});

app.get('/api/leaderboard', (req, res) => {
  res.json(getLeaderboard());
});

// ── Pets ──────────────────────────────────────────────────────
app.get('/api/pets/all', (req, res) => {
  res.json(getAllPets());
});

app.get('/api/pet/:name', (req, res) => {
  const pet = getPet(req.params.name);
  res.json(pet || { petId: 'cat' });
});

app.post('/api/pet', (req, res) => {
  const { name, petId } = req.body;
  if (!name || !petId) return res.status(400).json({ error: 'Missing fields' });
  setPet(name.trim(), petId);
  res.json({ ok: true });
});

// ── Boss ──────────────────────────────────────────────────────
app.get('/api/boss', (req, res) => {
  res.json(getBoss());
});

app.post('/api/boss/damage', (req, res) => {
  const { damage } = req.body;
  if (!damage || damage <= 0) return res.status(400).json({ error: 'Invalid damage' });
  const result = applyBossDamage(Math.floor(damage));
  res.json(result);
});

// ── Admin ─────────────────────────────────────────────────────
app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'admin.html'));
});

app.get('/api/admin/dashboard', (req, res) => {
  res.json(getAdminDashboard());
});

app.get('/api/users', (req, res) => {
  res.json(getAllUsers());
});

app.get('/api/users/:id/stats', (req, res) => {
  const data = getUserStats(Number(req.params.id));
  if (!data) return res.status(404).json({ error: 'User not found' });
  res.json(data);
});

const PORT = 3000;
app.listen(PORT, () => console.log(`MoveJoy running at http://localhost:${PORT}`));
