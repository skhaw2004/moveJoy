const express = require('express');
const path = require('path');
const { registerUser, saveScore, getLeaderboard, getAllUsers, getUserStats } = require('./db');

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

app.post('/api/users', (req, res) => {
  const { name } = req.body;
  if (!name || !name.trim()) return res.status(400).json({ error: 'Name required' });
  const user = registerUser(name.trim());
  res.json(user);
});

app.post('/api/scores', (req, res) => {
  const { name, score, sequenceLength, difficulty } = req.body;
  if (!name || score == null || !sequenceLength || !difficulty)
    return res.status(400).json({ error: 'Missing fields' });
  saveScore(name.trim(), score, sequenceLength, difficulty);
  res.json({ ok: true });
});

app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'admin.html'));
});

app.get('/api/leaderboard', (req, res) => {
  res.json(getLeaderboard());
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
