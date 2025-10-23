import { useEffect, useRef, useState } from "react";
import "./App.css";
import {
  listPlayers,
  createPlayer,
  deletePlayer,
  exportCSVSimple,
  importCSVSimple,
  getLeaderboard,
  addSession, // <-- save sessions
} from "./api";

function Screen({ view, children }) {
  return (
    <div key={view} className="screen animate-in">
      {children}
    </div>
  );
}

export default function App() {
  // Views: home | select | difficulty | countdown | flash | ready | capture | leaderboard | admin
  const [view, setView] = useState("home");

  // Shared state
  const [players, setPlayers] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  // Admin: create player fields
  const [newName, setNewName] = useState("");
  const [newPosition, setNewPosition] = useState("");
  const [newSide, setNewSide] = useState("");

  const [msg, setMsg] = useState("");

  // Difficulty and catch count (capture)
  const [difficulty, setDifficulty] = useState(null);
  const [catches, setCatches] = useState(null);

  // Countdown
  const [count, setCount] = useState(3);

  // Leaderboard
  const [board, setBoard] = useState([]);

  // -------- data helpers --------
  const fetchingRef = useRef(false);
  async function refreshPlayers() {
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    try {
      const p = await listPlayers();
      setPlayers(p);
    } catch (e) {
      setMsg(`Load failed: ${e.message}`);
    } finally {
      fetchingRef.current = false;
    }
  }

  useEffect(() => {
    if (view === "admin" || view === "select") refreshPlayers();
  }, [view]);

  // -------- admin handlers --------
  async function handleCreate() {
    const name = newName.trim();
    const position = newPosition.trim();
    const side = newSide.trim();
    if (!name) return setMsg("Please enter a player name.");
    if (!position) return setMsg("Please enter the player's position.");
    if (!side) return setMsg("Please select a side (Offense/Defense/Special Teams).");

    try {
      await createPlayer(name, position, side);
      setMsg(`Created player: ${name}`);
      setNewName("");
      setNewPosition("");
      setNewSide("");
      await refreshPlayers();
    } catch (e) {
      setMsg(`Create failed: ${e.message}`);
    }
  }

  async function handleDelete() {
    if (!selectedId) return setMsg("Choose a player to delete.");
    const picked = players.find((p) => p.id === selectedId);
    if (!picked) return;
    if (!confirm(`Delete ${picked.name}? This also deletes their sessions.`))
      return;
    try {
      await deletePlayer(selectedId);
      setMsg(`Deleted: ${picked.name}`);
      setSelectedId(null);
      await refreshPlayers();
    } catch (e) {
      setMsg(`Delete failed: ${e.message}`);
    }
  }

  async function handleExport() {
    try {
      await exportCSVSimple();
      setMsg("Exported: players_scores.csv");
    } catch (e) {
      setMsg(`Export failed: ${e.message}`);
    }
  }

  async function handleImport(file) {
    if (!file) return;
    try {
      const res = await importCSVSimple(file);
      setMsg(
        `Import complete — Imported: ${res.imported}, Skipped: ${res.skipped}`
      );
      await refreshPlayers();
    } catch (e) {
      setMsg(`Import failed: ${e.message}`);
    }
  }

  // Secondary line for player meta
  function renderMeta(p) {
    const pos = (p.position || "").trim();
    const side = (p.side || "").trim();
    if (!pos && !side) return null;
    if (pos && side) return `${pos} · ${side}`;
    return pos || side;
  }

  // Countdown 3→0 then go to green flash
  useEffect(() => {
    if (view !== "countdown") return;
    setCount(3);
    const t = setInterval(() => {
      setCount((c) => {
        if (c <= 1) {
          clearInterval(t);
          setView("flash");
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [view]);

  // Green flash for 1s, then go to the "ready" click-to-proceed screen
  useEffect(() => {
    if (view !== "flash") return;
    const t = setTimeout(() => {
      setView("ready");
    }, 1000);
    return () => clearTimeout(t);
  }, [view]);

  // -------- screens --------
  return (
    <div className="page">
      {/* TOP-LEFT LOGO (non-interactive) */}
      <div className="brand brand-static" aria-hidden="true">
        <img src="/psu-logo.png" alt="Penn State logo" />
      </div>

      {view === "home" && (
        <Screen view={view}>
          <div className="home">
            <h1 className="title">FLAG REACTION TEST</h1>
            <p className="subtitle">WELCOME,</p>

            <div className="menu">
              <button
                className="btn"
                onClick={() => {
                  setSelectedId(null);
                  setView("select");
                }}
              >
                Player Select
              </button>
              <button
                className="btn"
                onClick={async () => {
                  try {
                    const data = await getLeaderboard(10);
                    setBoard(data);
                    setView("leaderboard");
                  } catch (e) {
                    setMsg(`Leaderboard failed: ${e.message}`);
                  }
                }}
              >
                Leaderboard
              </button>
              <button className="btn" onClick={() => setView("admin")}>
                Admin
              </button>
            </div>
          </div>
        </Screen>
      )}

      {view === "select" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>Select Player</h2>
              <p className="muted">Tap a name, then proceed.</p>
            </header>

            {msg && <div className="toast animate-in">{msg}</div>}

            <section className="section">
              {players.length === 0 ? (
                <div className="empty">No players yet. Add some in Admin.</div>
              ) : (
                <ul
                  className="list"
                  style={{ maxHeight: 380, overflowY: "auto" }}
                >
                  {players
                    .slice()
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((p) => {
                      const meta = renderMeta(p);
                      return (
                        <li
                          key={p.id}
                          className={`list-item ${
                            selectedId === p.id ? "selected" : ""
                          }`}
                          onClick={() => setSelectedId(p.id)}
                          aria-selected={selectedId === p.id}
                        >
                          <div className="list-main">
                            <div className="name">{p.name}</div>
                            {meta && <div className="meta">{meta}</div>}
                          </div>
                        </li>
                      );
                    })}
                </ul>
              )}
            </section>

            <div className="actions">
              <button
                className="btn small danger"
                onClick={() => setView("home")}
              >
                ← Back
              </button>
              <button
                className="btn small"
                disabled={!selectedId}
                onClick={() => {
                  setCatches(null);
                  setDifficulty(null);
                  setView("difficulty");
                }}
              >
                Proceed
              </button>
            </div>
          </div>
        </Screen>
      )}

      {view === "difficulty" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>Select Difficulty</h2>
              <p className="muted">Choose one to begin the countdown.</p>
            </header>

            <section className="section">
              <div className="choices vertical">
                {["Easy", "Medium", "Hard", "Very Hard"].map((d) => (
                  <button
                    key={d}
                    className={`chip ${difficulty === d ? "active" : ""}`}
                    onClick={() => setDifficulty(d)}
                    type="button"
                  >
                    {d}
                  </button>
                ))}
              </div>
            </section>

            <div className="actions">
              <button
                className="btn small danger"
                onClick={() => setView("select")}
              >
                ← Back
              </button>
              <button
                className="btn small"
                disabled={!difficulty}
                onClick={() => setView("countdown")}
              >
                Proceed
              </button>
            </div>
          </div>
        </Screen>
      )}

      {view === "countdown" && (
        <Screen view={view}>
          <div className="panel center">
            <div className="countdown">{count > 0 ? count : 0}</div>
            <p className="muted" style={{ marginTop: 12 }}>
              Get ready…
            </p>
          </div>
        </Screen>
      )}

      {view === "flash" && <div className="green-screen" aria-hidden="true" />}

      {view === "ready" && (
        <Screen view={view}>
          <div className="panel center">
            <div
              className="big-cta"
              onClick={() => setView("capture")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) =>
                (e.key === "Enter" || e.key === " ") && setView("capture")
              }
            >
              Click to proceed
            </div>
            <div className="hint muted">(Tap anywhere on the card)</div>
          </div>
        </Screen>
      )}

      {view === "capture" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>How many flags did you catch?</h2>
              <p className="muted">Choose 0–10 below.</p>
            </header>

            <section className="section">
              <div className="nums-vertical">
                {Array.from({ length: 11 }, (_, i) => i).map((n) => (
                  <button
                    key={n}
                    type="button"
                    className={`num-vert ${catches === n ? "active" : ""}`}
                    onClick={() => setCatches(n)}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </section>

            <div className="actions" style={{ justifyContent: "flex-end" }}>
              <button
                className="btn small"
                disabled={catches == null}
                onClick={async () => {
                  try {
                    if (!selectedId) {
                      setMsg(
                        "No player selected — go back and choose a player."
                      );
                      return;
                    }
                    if (!difficulty) {
                      setMsg("Please select a difficulty first.");
                      return;
                    }
                    // SAVE the session
                    await addSession({
                      player_id: selectedId,
                      difficulty,
                      catches,
                    });
                    // Then fetch leaderboard
                    const data = await getLeaderboard(10);
                    setBoard(data);
                    setView("leaderboard");
                  } catch (e) {
                    setMsg(`Save/Leaderboard failed: ${e.message}`);
                  }
                }}
              >
                Proceed
              </button>
            </div>
          </div>
        </Screen>
      )}

      {view === "leaderboard" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>Leaderboard (Top 10)</h2>
              <p className="muted">Balanced by difficulty multiplier.</p>
            </header>

            {board.length === 0 ? (
              <div className="empty">No sessions recorded yet.</div>
            ) : (
              <section className="section">
                <table className="table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Player</th>
                      <th>Difficulty</th>
                      <th>Catches</th>
                      <th>Score</th>
                      <th>Played</th>
                    </tr>
                  </thead>
                  <tbody>
                    {board.slice(0, 10).map((row, i) => (
                      <tr key={i}>
                        <td>{i + 1}</td>
                        <td>{row.name}</td>
                        <td>{row.difficulty}</td>
                        <td>{row.catches}</td>
                        <td>{row.score}</td>
                        <td>{row.played_at ? new Date(row.played_at).toLocaleString() : ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            )}

            <div className="actions">
              <button
                className="btn small"
                onClick={() => {
                  setCatches(null);
                  setDifficulty(null);
                  setView("select");
                }}
              >
                Play Again
              </button>
              <button
                className="btn small ghost"
                onClick={() => setView("home")}
              >
                Return to Start
              </button>
            </div>
          </div>
        </Screen>
      )}

      {view === "admin" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>Admin</h2>
              <p className="muted">Manage players & data</p>
            </header>

            {msg && <div className="toast animate-in">{msg}</div>}

            <section className="section">
              <h3>Create Player</h3>
              <div className="row" style={{ flexWrap: "wrap", gap: "8px" }}>
                <input
                  className="input"
                  placeholder="Name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
                <input
                  className="input"
                  placeholder="Position"
                  value={newPosition}
                  onChange={(e) => setNewPosition(e.target.value)}
                />
                <select
                  className="input"
                  value={newSide}
                  onChange={(e) => setNewSide(e.target.value)}
                >
                  <option value="">Select Side</option>
                  <option value="Offense">Offense</option>
                  <option value="Defense">Defense</option>
                  <option value="Special Teams">Special Teams</option>
                </select>
                <button className="btn small" onClick={handleCreate}>
                  Create
                </button>
              </div>
            </section>

            <section className="section">
              <h3>Players</h3>
              {players.length === 0 ? (
                <div className="empty">No players yet.</div>
              ) : (
                <ul
                  className="list"
                  style={{ maxHeight: 340, overflowY: "auto" }}
                >
                  {players.map((p) => {
                    const meta = renderMeta(p);
                    return (
                      <li
                        key={p.id}
                        className={`list-item ${
                          selectedId === p.id ? "selected" : ""
                        }`}
                        onClick={() => setSelectedId(p.id)}
                        aria-selected={selectedId === p.id}
                      >
                        <div className="list-main">
                          <div className="name">{p.name}</div>
                          {meta && <div className="meta">{meta}</div>}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
              <div className="row" style={{ marginTop: 10 }}>
                <button
                  className="btn small danger"
                  onClick={handleDelete}
                  disabled={!selectedId}
                >
                  Delete Selected
                </button>
                <button className="btn small ghost" onClick={refreshPlayers}>
                  Refresh
                </button>
              </div>
            </section>

            <section className="section">
              <h3>Import / Export</h3>
              <div className="row">
                <label className="file-btn">
                  Import
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    onChange={(e) =>
                      e.target.files?.[0] && handleImport(e.target.files[0])
                    }
                  />
                </label>
                <button className="btn small" onClick={handleExport}>
                  Export
                </button>
              </div>
            </section>

            <div className="row" style={{ marginTop: 12 }}>
              <button
                className="btn small ghost"
                onClick={() => setView("home")}
              >
                ← Back
              </button>
            </div>
          </div>
        </Screen>
      )}
    </div>
  );
}
