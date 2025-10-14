// src/api.js
const BASE = "http://127.0.0.1:8000";


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


