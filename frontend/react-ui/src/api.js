// src/api.js
//const BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const BASE = import.meta.env.VITE_API_BASE;

async function j(r) {
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ---------- Players ----------
export async function listPlayers() {
  return j(await fetch(`${BASE}/players`));
}

export async function createPlayer(name, position = null, side = null) {
  return j(
    await fetch(`${BASE}/players`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, position, side }),
    })
  );
}

export async function deletePlayer(id) {
  return j(await fetch(`${BASE}/players/${id}`, { method: "DELETE" }));
}

// ---------- Sessions ----------
export async function addSession({ player_id, difficulty, catches }) {
  return j(
    await fetch(`${BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id, difficulty, catches }),
    })
  );
}

// ---------- CSV ----------
export async function exportCSVSimple() {
  const r = await fetch(`${BASE}/export-simple`);
  if (!r.ok) throw new Error(await r.text());
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "players_scores.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function importCSVSimple(file) {
  const fd = new FormData();
  fd.append("file", file);
  return j(
    await fetch(`${BASE}/import-simple`, {
      method: "POST",
      body: fd,
    })
  );
}

// ---------- Leaderboard ----------
export async function getLeaderboard(topN = 10) {
  return j(await fetch(`${BASE}/leaderboard?top_n=${topN}`));
}

// ---------- Hardware Control ----------
export async function getHardwareStatus() {
  return j(await fetch(`${BASE}/hardware/status`));
}

export async function turnMagnetsOn() {
  return j(
    await fetch(`${BASE}/hardware/magnets/on`, {
      method: "POST",
    })
  );
}

export async function turnMagnetsOff() {
  return j(
    await fetch(`${BASE}/hardware/magnets/off`, {
      method: "POST",
    })
  );
}

export async function startDropSequence(difficulty) {
  return j(
    await fetch(`${BASE}/hardware/drop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ difficulty }),
    })
  );
}