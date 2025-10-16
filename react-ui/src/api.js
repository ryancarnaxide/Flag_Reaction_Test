// src/api.js

// Prefer env override; fallback to localhost.
const BASE =
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_BASE) ||
  "http://127.0.0.1:8000";

// Generic request helper with timeout + better errors
async function request(path, { method = "GET", headers = {}, body, timeoutMs = 10000 } = {}) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body,
      signal: controller.signal,
    });

    const ct = res.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");

    if (!res.ok) {
      const errPayload = isJson ? await res.json().catch(() => ({})) : await res.text().catch(() => "");
      const message =
        (errPayload && (errPayload.detail || errPayload.message)) ||
        (typeof errPayload === "string" ? errPayload : `HTTP ${res.status}`);
      throw new Error(message);
    }

    return isJson ? res.json() : res.blob();
  } finally {
    clearTimeout(id);
  }
}

// ---------- Players ----------
export async function listPlayers() {
  return request("/players");
}

export async function createPlayer(name, position = null, side = null) {
  return request("/players", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, position, side }),
  });
}

export async function deletePlayer(id) {
  return request(`/players/${id}`, { method: "DELETE" });
}

// ---------- Sessions ----------
export async function addSession({ player_id, difficulty, catches }) {
  return request("/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_id, difficulty, catches }),
  });
}

// ---------- CSV ----------
export async function exportCSVSimple(filename = "players_scores.csv") {
  const blob = await request("/export-simple");
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function importCSVSimple(file) {
  const fd = new FormData();
  fd.append("file", file);
  return request("/import-simple", { method: "POST", body: fd });
}

// ---------- Leaderboard ----------
export async function getLeaderboard(topN = 10) {
  // FastAPI returns: [{name, difficulty, catches, played_at}]
  return request(`/leaderboard?top_n=${topN}`);
}

export { BASE };
