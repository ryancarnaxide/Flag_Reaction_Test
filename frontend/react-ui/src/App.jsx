import { useEffect, useRef, useState } from "react";
import "./App.css";
import {
  listPlayers,
  createPlayer,
  deletePlayer,
  exportCSVSimple,
  importCSVSimple,
  getLeaderboard,
  addSession,
  getHardwareStatus,
  turnMagnetsOn,
  turnMagnetsOff,
  startDropSequence,
} from "./api";

// Background Slideshow Component (Simple & Consistent)
function BackgroundSlideshow() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const images = [
    '/bg1.jpg',
    '/bg2.jpg',
    '/bg3.jpg',
    '/bg4.jpg',
    '/bg5.jpg',
    '/bg6.jpg',
    '/bg7.jpg',
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % images.length);
    }, 6000); // Change image every 6 seconds

    return () => clearInterval(interval);
  }, [images.length]);

  return (
    <div className="background-slideshow">
      {images.map((src, index) => (
        <div
          key={index}
          className={`slideshow-image ${index === currentIndex ? 'active' : ''}`}
          style={{ backgroundImage: `url(${src})` }}
        />
      ))}
      <div className="slideshow-overlay" />
    </div>
  );
}

// Reusable Screen wrapper with animation
function Screen({ view, children }) {
  return (
    <div key={view} className="screen animate-in">
      {children}
    </div>
  );
}

// Toast notification component
function Toast({ message, onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="toast animate-in">
      <span>{message}</span>
      <button className="toast-close" onClick={onClose} aria-label="Close notification">
        ✕
      </button>
    </div>
  );
}

export default function App() {
  // View management
  const [view, setView] = useState("home");
  
  // Player state
  const [players, setPlayers] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  
  // Admin form state
  const [newName, setNewName] = useState("");
  const [newPosition, setNewPosition] = useState("");
  const [newSide, setNewSide] = useState("");
  
  // Game mode toggle
  const [useReactionGame, setUseReactionGame] = useState(() => {
    // Load from localStorage
    const saved = localStorage.getItem("useReactionGame");
    return saved === "true";
  });
  
  // Hardware status
  const [hardwareAvailable, setHardwareAvailable] = useState(false);
  
  // Notification state
  const [msg, setMsg] = useState("");
  
  // Game state
  const [difficulty, setDifficulty] = useState(null);
  const [catches, setCatches] = useState(null);
  const [count, setCount] = useState(3);
  
  // Reaction game state
  const [currentCircle, setCurrentCircle] = useState(null);
  const [circleStartTime, setCircleStartTime] = useState(null);
  const [floatingTimes, setFloatingTimes] = useState([]);
  const [circlesShown, setCirclesShown] = useState(0); // Track how many circles have been shown
  const maxCircles = 10;

  // Admin state
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminPassword, setAdminPassword] = useState("");
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const passwordRef = useRef(null);
  
  // Leaderboard state
  const [board, setBoard] = useState([]);
  
  // Fetching guard
  const fetchingRef = useRef(false);
  const gameContainerRef = useRef(null);

  // Difficulty settings for circle game
  const difficultySettings = {
    Easy: { size: 100 },
    Medium: { size: 80 },
    Hard: { size: 60 },
    "Very Hard": { size: 45 },
  };

  // Helper: Get selected player info
  const selectedPlayer = players.find((p) => p.id === selectedId);

  // Helper: Format player metadata
  function renderMeta(player) {
    const pos = (player.position || "").trim();
    const side = (player.side || "").trim();
    if (!pos && !side) return null;
    if (pos && side) return `${pos} · ${side}`;
    return pos || side;
  }

  // Helper: Show temporary message
  function showMessage(message) {
    setMsg(message);
  }

  // Fetch players from API
  async function refreshPlayers() {
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    try {
      const data = await listPlayers();
      setPlayers(data);
    } catch (error) {
      showMessage(`Failed to load players: ${error.message}`);
    } finally {
      fetchingRef.current = false;
    }
  }

  // Auto-fetch players when needed
  useEffect(() => {
    if (view === "admin" || view === "select") {
      refreshPlayers();
    }
  }, [view]);

  // Check hardware status on mount
  useEffect(() => {
    async function checkHardware() {
      try {
        const status = await getHardwareStatus();
        setHardwareAvailable(status.available);
        if (status.available) {
          showMessage("✓ Hardware connected");
        }
      } catch (error) {
        console.log("Hardware not available:", error);
      }
    }
    checkHardware();
  }, []);

  // Handle player creation
  async function handleCreatePlayer() {
    const name = newName.trim();
    const position = newPosition.trim();
    const side = newSide.trim();

    if (!name) return showMessage("Please enter a player name");
    if (!position) return showMessage("Please enter a position");
    if (!side) return showMessage("Please select a side");

    try {
      await createPlayer(name, position, side);
      showMessage(`✓ Created player: ${name}`);
      setNewName("");
      setNewPosition("");
      setNewSide("");
      await refreshPlayers();
    } catch (error) {
      showMessage(`Failed to create player: ${error.message}`);
    }
  }

  // Handle player deletion
  async function handleDeletePlayer() {
    if (!selectedId || !selectedPlayer) {
      return showMessage("Please select a player to delete");
    }

    const confirmDelete = window.confirm(
      `Delete ${selectedPlayer.name}?\n\nThis will also delete all their sessions.`
    );
    
    if (!confirmDelete) return;

    try {
      await deletePlayer(selectedId);
      showMessage(`✓ Deleted: ${selectedPlayer.name}`);
      setSelectedId(null);
      await refreshPlayers();
    } catch (error) {
      showMessage(`Failed to delete player: ${error.message}`);
    }
  }

  // Handle CSV export
  async function handleExportCSV() {
    try {
      await exportCSVSimple();
      showMessage("✓ Exported: players_scores.csv");
    } catch (error) {
      showMessage(`Export failed: ${error.message}`);
    }
  }

  // Handle CSV import
  async function handleImportCSV(file) {
    if (!file) return;
    
    try {
      const result = await importCSVSimple(file);
      showMessage(
        `✓ Import complete — Added: ${result.imported}, Skipped: ${result.skipped}`
      );
      await refreshPlayers();
    } catch (error) {
      showMessage(`Import failed: ${error.message}`);
    }
  }

  // Handle session save and show leaderboard
  async function handleSaveSession() {
    if (!selectedId) {
      return showMessage("No player selected");
    }
    if (!difficulty) {
      return showMessage("No difficulty selected");
    }
    if (catches == null) {
      return showMessage("Please select number of catches");
    }

    try {
      await addSession({
        player_id: selectedId,
        difficulty,
        catches,
      });
      
      const data = await getLeaderboard(10);
      setBoard(data);
      setView("leaderboard");
    } catch (error) {
      showMessage(`Failed to save session: ${error.message}`);
    }
  }

  // Toggle game mode (reaction game on/off)
  function handleToggleGameMode(enabled) {
    setUseReactionGame(enabled);
    localStorage.setItem("useReactionGame", enabled.toString());
    showMessage(enabled ? "✓ Reaction game enabled" : "✓ Reaction game disabled");
  }

  // Countdown effect (3, 2, 1, 0 → flash)
  useEffect(() => {
    if (view !== "countdown") return;
    
    setCount(3);
    const interval = setInterval(() => {
      setCount((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          setView("flash");
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [view]);

  // Flash effect (hold for 1s → ready OR capture depending on mode)
  useEffect(() => {
    if (view !== "flash") return;
    
    const timer = setTimeout(async () => {
      if (useReactionGame) {
        // New mode: go to reaction game (software circles)
        setView("ready");
      } else {
        // Old mode: trigger hardware drop sequence
        if (hardwareAvailable) {
          try {
            await startDropSequence(difficulty);
            showMessage("🔧 Hardware sequence started");
          } catch (error) {
            showMessage("Hardware error: " + error.message);
          }
        }
        // Go to capture screen after flash
        setView("capture");
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [view, useReactionGame, hardwareAvailable, difficulty]);

  // Start spawning circles when ready view loads
  useEffect(() => {
    if (view !== "ready") return;
    
    // Reset counter and start first circle
    setCirclesShown(0);
    const timer = setTimeout(() => {
      spawnCircle();
    }, 100);

    return () => clearTimeout(timer);
  }, [view]);

  // Spawn a circle at random position
  function spawnCircle() {
    if (view !== "ready" || !gameContainerRef.current || !difficulty) return;

    // Check if we've shown 10 circles already
    if (circlesShown >= maxCircles) {
      // Move to capture screen after showing all circles
      setTimeout(() => {
        setView("capture");
      }, 500);
      return;
    }

    const container = gameContainerRef.current;
    const settings = difficultySettings[difficulty];
    const size = settings.size;

    // Random position
    const maxX = window.innerWidth - size - 40;
    const maxY = window.innerHeight - size - 40;
    const x = Math.random() * maxX + 20;
    const y = Math.random() * maxY + 20;

    setCurrentCircle({ x, y, size });
    setCircleStartTime(Date.now());
    setCirclesShown((prev) => prev + 1); // Increment counter
  }

  // Handle circle click
  function handleCircleClick(e) {
    if (!circleStartTime) return;

    const reactionTime = Date.now() - circleStartTime;

    // Add floating time popup
    const id = Date.now();
    setFloatingTimes((prev) => [
      ...prev,
      { id, time: reactionTime, x: e.clientX, y: e.clientY },
    ]);

    // Remove floating time after animation
    setTimeout(() => {
      setFloatingTimes((prev) => prev.filter((ft) => ft.id !== id));
    }, 1200);

    // Remove current circle
    setCurrentCircle(null);
    setCircleStartTime(null);

    // Spawn next circle immediately
    setTimeout(() => {
      spawnCircle();
    }, 100);
  }

  // Auto-remove circle after 1 second if not clicked
  useEffect(() => {
    if (!currentCircle || view !== "ready") return;

    const timer = setTimeout(() => {
      // Circle timed out - remove it and spawn new one
      setCurrentCircle(null);
      setCircleStartTime(null);
      
      setTimeout(() => {
        spawnCircle();
      }, 100);
    }, 1000);

    return () => clearTimeout(timer);
  }, [currentCircle, view]);

  // Reset game state
  function resetGame() {
    setSelectedId(null);
    setDifficulty(null);
    setCatches(null);
    setCurrentCircle(null);
    setCircleStartTime(null);
    setFloatingTimes([]);
    setCirclesShown(0);
  }

  return (
    <div className="page">
      {/* Background Slideshow */}
      <BackgroundSlideshow />
      
      {/* Penn State Logo */}
      <div className="brand brand-static" aria-hidden="true">
        <img src="/psu-logo.png" alt="Penn State" />
      </div>

      {/* Notification Toast */}
      {msg && <Toast message={msg} onClose={() => setMsg("")} />}

      {/* HOME SCREEN */}
      {view === "home" && (
        <Screen view={view}>
          <div className="home">
            {/* 🔴 TOP-RIGHT POWER BUTTON */}
            <div className="top-right">
              <button
                className="btn btn-nav ghost"
                onClick={async () => {
                  try {
                    await turnMagnetsOff();
                    showMessage("✓ All magnets OFF");
                  } catch (error) {
                    showMessage("Error: " + error.message);
                  }
                }}
              >
                🔴 All Magnets OFF
              </button>
            </div>

            <p className="home-header">Penn State Athletics</p>
            <h1 className="title">Flag Reaction Test</h1>
            <p className="subtitle">Select an option to begin</p>

            <nav className="menu">
              <button
                className="btn btn-nav"
                onClick={() => {
                  resetGame();
                  setView("select");
                }}
              >
                Start Test
              </button>
              
              <button
                className="btn btn-nav"
                onClick={async () => {
                  try {
                    const data = await getLeaderboard(10);
                    setBoard(data);
                    setView("leaderboard");
                  } catch (error) {
                    showMessage(`Failed to load leaderboard: ${error.message}`);
                  }
                }}
              >
                View Leaderboard
              </button>

              <button
                className="btn btn-nav"
                onClick={() => setShowAdminLogin(true)}
              >
                Admin Panel
              </button>

              {/* INLINE ADMIN LOGIN FORM */}
              {showAdminLogin && (
                <div className="admin-login">
                  <input
                    type="password"
                    placeholder="Enter admin password"
                    value={adminPassword}
                    onChange={(e) => setAdminPassword(e.target.value)}
                    ref={passwordRef}
                    className="input"
                  />
                  <button
                    className="btn btn-nav"
                    onClick={async () => {
                      try {
                        const res = await fetch("http://127.0.0.1:8000/admin-check", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ password: adminPassword }),
                        });

                        if (!res.ok) throw new Error("Unauthorized");

                        const data = await res.json();
                        console.log(data.message);
                        setIsAdmin(true);
                        setView("admin");
                        setShowAdminLogin(false);
                        setAdminPassword("");
                      } catch (err) {
                        alert("Incorrect password");
                        setAdminPassword("");         // reset input
                        passwordRef.current?.focus(); // focus password box
                      }
                    }}
                  >
                    Login
                  </button>
                  <button
                    className="btn btn-nav ghost"
                    onClick={() => {
                      setShowAdminLogin(false);
                      setAdminPassword("");
                    }}
                  >
                    Cancel
                  </button>
                </div>
              )}
            </nav>
          </div>
        </Screen>
      )}

      {/* PLAYER SELECT SCREEN */}
      {view === "select" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>Select Player</h2>
              <p className="muted">Choose a player to begin the test</p>
            </header>

            <section className="section">
              {players.length === 0 ? (
                <div className="empty">
                  No players available. Please add players in the Admin Panel.
                </div>
              ) : (
                <ul className="list" role="listbox" aria-label="Player list">
                  {players
                    .slice()
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((player) => {
                      const meta = renderMeta(player);
                      const isSelected = selectedId === player.id;
                      
                      return (
                        <li
                          key={player.id}
                          className={`list-item ${isSelected ? "selected" : ""}`}
                          onClick={() => setSelectedId(player.id)}
                          role="option"
                          aria-selected={isSelected}
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              setSelectedId(player.id);
                            }
                          }}
                        >
                          <div className="list-main">
                            <div className="name">{player.name}</div>
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
                onClick={async () => {
                  try {
                    await turnMagnetsOn();
                    showMessage("✓ All magnets ON");
                  } catch (error) {
                    showMessage("Error: " + error.message);
                  }
                  setView("difficulty");
                }}
              >
                Continue →
              </button>
            </div>
          </div>
        </Screen>
      )}

      {/* DIFFICULTY SELECT SCREEN */}
      {view === "difficulty" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>Select Difficulty</h2>
              <p className="muted">
                {selectedPlayer && (
                  <span>
                    Testing: <strong>{selectedPlayer.name}</strong>
                  </span>
                )}
              </p>
            </header>

            <section className="section">
              <div className="choices">
                {[
                  { level: "Easy", multiplier: "×1" },
                  { level: "Medium", multiplier: "×2" },
                  { level: "Hard", multiplier: "×3" },
                  { level: "Very Hard", multiplier: "×5" },
                ].map(({ level, multiplier }) => (
                  <button
                    key={level}
                    className={`chip ${difficulty === level ? "active" : ""}`}
                    onClick={() => setDifficulty(level)}
                    type="button"
                  >
                    <span className="chip-label">{level}</span>
                    <span className="chip-badge">{multiplier}</span>
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
                Begin Test →
              </button>
            </div>
          </div>
        </Screen>
      )}

      {/* COUNTDOWN SCREEN */}
      {view === "countdown" && (
        <Screen view={view}>
          <div className="panel center">
            <div className="countdown">{count > 0 ? count : "GO!"}</div>
            <p className="muted countdown-hint">Get ready...</p>
          </div>
        </Screen>
      )}

      {/* GREEN FLASH SCREEN */}
      {view === "flash" && (
        <Screen view={view}>
          <div className="panel center">
            <div className="green-screen">
              <span className="go-text">GO</span>
            </div>
          </div>
        </Screen>
      )}

      {/* READY/GAME SCREEN - Click circles as they appear */}
      {view === "ready" && (
        <div className="game-screen" ref={gameContainerRef}>
          {/* Circle Target */}
          {currentCircle && (
            <div
              className="reaction-circle"
              style={{
                position: 'absolute',
                left: currentCircle.x,
                top: currentCircle.y,
                width: currentCircle.size,
                height: currentCircle.size,
                borderRadius: '50%',
                background: '#17c964',
                cursor: 'pointer',
                boxShadow: '0 8px 24px rgba(23, 201, 100, 0.4)',
              }}
              onClick={handleCircleClick}
            />
          )}

          {/* Floating Time Displays */}
          {floatingTimes.map((ft) => (
            <div
              key={ft.id}
              className="time-popup"
              style={{
                position: 'fixed',
                left: ft.x,
                top: ft.y,
                fontSize: '28px',
                fontWeight: '900',
                color: '#17c964',
                textShadow: '0 2px 8px rgba(0, 0, 0, 0.6)',
                pointerEvents: 'none',
                zIndex: 1000,
                animation: 'floatUp 1.2s ease-out forwards',
              }}
            >
              {ft.time}ms
            </div>
          ))}

          {/* Progress Counter */}
          <div style={{
            position: 'fixed',
            top: '100px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(255, 255, 255, 0.08)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '12px',
            padding: '16px 28px',
            color: '#EAF1FF',
            fontSize: '20px',
            fontWeight: '700',
            zIndex: 50,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '14px', color: '#9DB8D9', marginBottom: '4px' }}>
              Circles
            </div>
            <div style={{ fontSize: '32px', lineHeight: '1' }}>
              {circlesShown} / {maxCircles}
            </div>
          </div>
        </div>
      )}

      {/* CAPTURE RESULTS SCREEN */}
      {view === "capture" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>Record Results</h2>
              <p className="muted">How many flags did you catch?</p>
            </header>

            <section className="section">
              <div className="nums-vertical">
                {Array.from({ length: 11 }, (_, i) => i).map((num) => (
                  <button
                    key={num}
                    type="button"
                    className={`num-vert ${catches === num ? "active" : ""}`}
                    onClick={() => setCatches(num)}
                  >
                    {num}
                  </button>
                ))}
              </div>
            </section>

            <div className="actions">
              <button
                className="btn small danger"
                onClick={() => setView("difficulty")}
              >
                ← Back
              </button>
              <button
                className="btn small"
                disabled={catches == null}
                onClick={handleSaveSession}
              >
                Submit Results →
              </button>
            </div>
          </div>
        </Screen>
      )}

      {/* LEADERBOARD SCREEN */}
      {view === "leaderboard" && (
        <Screen view={view}>
          <div className="panel">
            <header className="panel-header">
              <h2>🏆 Leaderboard</h2>
              <p className="muted">Top 10 performances (ranked by balanced score)</p>
            </header>

            {board.length === 0 ? (
              <div className="empty">No sessions recorded yet. Complete a test to appear here!</div>
            ) : (
              <section className="section">
                <div className="table-wrapper">
                  <table className="table">
                    <thead>
                      <tr>
                        <th className="rank-col">#</th>
                        <th>Player</th>
                        <th>Difficulty</th>
                        <th className="center">Catches</th>
                        <th className="center">Score</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {board.slice(0, 10).map((row, index) => (
                        <tr key={index} className={index < 3 ? `rank-${index + 1}` : ""}>
                          <td className="rank-col">
                            {index === 0 && "🥇"}
                            {index === 1 && "🥈"}
                            {index === 2 && "🥉"}
                            {index > 2 && index + 1}
                          </td>
                          <td className="player-name">{row.name}</td>
                          <td>
                            <span className={`difficulty-badge difficulty-${row.difficulty.toLowerCase().replace(" ", "-")}`}>
                              {row.difficulty}
                            </span>
                          </td>
                          <td className="center">{row.catches}</td>
                          <td className="center score-col">{row.score}</td>
                          <td className="date-col">
                            {row.played_at 
                              ? new Date(row.played_at).toLocaleDateString("en-US", {
                                  month: "short",
                                  day: "numeric",
                                  hour: "numeric",
                                  minute: "2-digit",
                                })
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            <div className="actions">
              <button
                className="btn small"
                onClick={() => {
                  resetGame();
                  setView("select");
                }}
              >
                Test Again
              </button>
              <button
                className="btn small ghost"
                onClick={() => setView("home")}
              >
                Return Home
              </button>
            </div>
          </div>
        </Screen>
      )}

      {/* ADMIN SCREEN */}
      {view === "admin" && (
        <Screen view={view}>
          <div className="panel panel-admin">
            <header className="panel-header">
              <h2>⚙️ Admin Panel</h2>
              <p className="muted">Manage players and settings</p>
            </header>

            {/* Game Mode Toggle */}
            <section className="section" style={{ 
              background: 'rgba(23, 201, 100, 0.15)', 
              border: '1px solid rgba(23, 201, 100, 0.2)',
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '24px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <h3 className="section-title" style={{ margin: 0, marginBottom: '4px' }}>
                    🎮 Reaction Game Mode
                  </h3>
                  <p className="muted" style={{ margin: 0, fontSize: '14px' }}>
                    {useReactionGame 
                      ? "Players will click circles that appear on screen after countdown"
                      : "Players will directly enter their score after countdown (with hardware control)"}
                  </p>
                </div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={useReactionGame}
                    onChange={(e) => handleToggleGameMode(e.target.checked)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div style={{ 
                fontSize: '13px', 
                color: useReactionGame ? '#17c964' : '#ff9500',
                fontWeight: '600',
                marginTop: '8px'
              }}>
                {useReactionGame ? "✓ Reaction Game ON" : "○ Reaction Game OFF (Hardware Mode)"}
              </div>
            </section>

            {/* Hardware Control Section */}
            {hardwareAvailable && (
              <section className="section" style={{ 
                background: 'rgba(255, 149, 0, 0.08)', 
                border: '1px solid rgba(255, 149, 0, 0.2)',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '24px'
              }}>
                <h3 className="section-title" style={{ margin: 0, marginBottom: '12px' }}>
                  🔧 Hardware Controls
                </h3>
                <p className="muted" style={{ margin: 0, fontSize: '14px', marginBottom: '16px' }}>
                  Control the electromagnets directly for testing
                </p>
                <div className="row" style={{ gap: '12px' }}>
                  <button
                    className="btn small"
                    onClick={async () => {
                      try {
                        await turnMagnetsOn();
                        showMessage("✓ All magnets ON");
                      } catch (error) {
                        showMessage("Error: " + error.message);
                      }
                    }}
                    style={{ background: '#17c964', borderColor: '#17c964', color: '#fff' }}
                  >
                    ⚡ All Magnets ON
                  </button>
                  <button
                    className="btn small danger"
                    onClick={async () => {
                      try {
                        await turnMagnetsOff();
                        showMessage("✓ All magnets OFF");
                      } catch (error) {
                        showMessage("Error: " + error.message);
                      }
                    }}
                  >
                    🔴 All Magnets OFF
                  </button>
                  <button
                    className="btn small ghost"
                    onClick={async () => {
                      try {
                        await startDropSequence("Medium");
                        showMessage("✓ Test sequence started (Medium)");
                      } catch (error) {
                        showMessage("Error: " + error.message);
                      }
                    }}
                  >
                    🧪 Test Drop Sequence
                  </button>
                </div>
              </section>
            )}

            {/* Create Player Section */}
            <section className="section">
              <h3 className="section-title">➕ Add New Player</h3>
              <div className="form-grid">
                <input
                  className="input"
                  placeholder="Full Name *"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreatePlayer()}
                />
                <select
                  className="input"
                  value={newSide}
                  onChange={(e) => setNewSide(e.target.value)}
                >
                  <option value="">Select Side *</option>
                  <option value="Offense">Offense</option>
                  <option value="Defense">Defense</option>
                  <option value="Special Teams">Special Teams</option>
                </select>
                <select
                  className="input"
                  value={newPosition}
                  onChange={(e) => setNewPosition(e.target.value)}
                >
                  <option value="">Select Position *</option>
                  <option value="Line">Line</option>
                  <option value="Center">Center</option>
                  <option value="Guard">Guard</option>
                  <option value="Tackle">Tackle</option>
                  <option value="Quarterback">Quarterback</option>
                  <option value="Back">Back</option>
                  <option value="Quarterback">Quarterback</option>
                  <option value="Wide Receiver">Wide Receiver</option>
                  <option value="End">End</option>
                </select>
                <button
                  className="btn small"
                  onClick={handleCreatePlayer}
                  disabled={!newName.trim() || !newPosition.trim() || !newSide.trim()}
                >
                  Add Player
                </button>
              </div>
            </section>

            {/* Player List Section */}
            <section className="section">
              <h3 className="section-title">
                👥 All Players ({players.length})
              </h3>
              {players.length === 0 ? (
                <div className="empty">No players yet. Add one above to get started.</div>
              ) : (
                <>
                  <ul className="list admin-list" role="listbox">
                    {players
                      .slice()
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map((player) => {
                        const meta = renderMeta(player);
                        const isSelected = selectedId === player.id;
                        
                        return (
                          <li
                            key={player.id}
                            className={`list-item ${isSelected ? "selected" : ""}`}
                            onClick={() => setSelectedId(player.id)}
                            role="option"
                            aria-selected={isSelected}
                          >
                            <div className="list-main">
                              <div className="name">{player.name}</div>
                              {meta && <div className="meta">{meta}</div>}
                            </div>
                          </li>
                        );
                      })}
                  </ul>
                  <div className="row" style={{ marginTop: 12 }}>
                    <button
                      className="btn small danger"
                      onClick={handleDeletePlayer}
                      disabled={!selectedId}
                    >
                      Delete Selected
                    </button>
                    <button
                      className="btn small ghost"
                      onClick={refreshPlayers}
                    >
                      ↻ Refresh
                    </button>
                  </div>
                </>
              )}
            </section>

            {/* Import/Export Section */}
            <section className="section">
              <h3 className="section-title">📊 Data Management</h3>
              <div className="row">
                <label className="file-btn">
                  <span>📥 Import CSV</span>
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleImportCSV(file);
                    }}
                  />
                </label>
                <button className="btn small" onClick={handleExportCSV}>
                  📤 Export CSV
                </button>
              </div>
            </section>

            <div className="actions">
              <button
                className="btn small ghost"
                onClick={() => {
                  setSelectedId(null);
                  setView("home");
                }}
              >
                ← Back to Home
              </button>
            </div>
          </div>
        </Screen>
      )}
    </div>
  );
}
