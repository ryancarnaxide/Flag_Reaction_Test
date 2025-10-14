import sqlite3
import os
import csv
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog

DB_FILE = "flag_reaction_test.db"

# ---------------------------
# Connection & Setup
# ---------------------------
def get_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def setup_database():
    """Create tables if they don't exist (with Position and Side)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        position TEXT,
        side TEXT CHECK(side IN ('Offense','Defense','Special Teams')),
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        difficulty TEXT CHECK(difficulty IN ('Easy','Medium','Hard','Very Hard')),
        catches INTEGER NOT NULL,
        score INTEGER NOT NULL,
        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );
    """)
    conn.commit()
    conn.close()

# ---------------------------
# Player Functions (no changes, but players now have position + side fields)
# ---------------------------
def create_player(name, position=None, side=None):
    """Add a new player. Returns player_id or None if name exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO players (name, position, side) VALUES (?,?,?)", (name, position, side))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return None
    cursor.execute("SELECT player_id FROM players WHERE name = ?", (name,))
    pid = cursor.fetchone()[0]
    conn.close()
    return pid

def get_all_players():
    """Return a list of tuples (player_id, name, position, side)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT player_id, name, position, side FROM players ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_player_by_id(player_id):
    """Return a dict with player info, or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT player_id, name, position, side FROM players WHERE player_id=?", (player_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "position": row[2], "side": row[3]}
    return None

def delete_player(player_id):
    """Delete a player and their sessions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE player_id=?", (player_id,))
    cursor.execute("DELETE FROM players WHERE player_id=?", (player_id,))
    conn.commit()
    conn.close()

# ---------------------------
# Session Functions (no change)
# ---------------------------

def record_session(player_id, difficulty, catches):
    """Insert a new session for a player."""
    multiplier = {"Easy":1, "Medium":2, "Hard":3, "Very Hard":5}[difficulty]
    score = catches * multiplier
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (player_id, difficulty, catches, score) VALUES (?,?,?,?)",
        (player_id, difficulty, catches, score)
    )
    conn.commit()
    conn.close()

def get_leaderboard(top_n=10):
    """Return a list of top sessions (name, difficulty, catches, score)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.name, s.difficulty, s.catches, s.score
        FROM sessions s
        JOIN players p ON p.player_id = s.player_id
        ORDER BY s.score DESC
        LIMIT ?
    """, (top_n,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_player_sessions(player_id):
    """Return all sessions for a given player."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT difficulty, catches, score, played_at
        FROM sessions
        WHERE player_id=?
        ORDER BY played_at ASC
    """, (player_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def find_onedrive_path():
    """
    Cross-platform detection of the user's OneDrive folder.
    Returns Path object or None if not found.
    """
    import platform
    from pathlib import Path

    home = Path.home()
    system = platform.system()
    candidates = []

    # --- Windows typical paths ---
    candidates += [
        home / "OneDrive",
        home / "OneDrive - Personal",
    ]

    # --- macOS typical CloudStorage path ---
    if system == "Darwin":
        cloud_root = home / "Library" / "CloudStorage"
        if cloud_root.exists():
            for folder in cloud_root.iterdir():
                if folder.name.startswith("OneDrive"):
                    candidates.append(folder)

    # --- Linux / WSL fallback ---
    candidates.append(Path("/mnt/OneDrive"))

    for path in candidates:
        if path.exists() and path.is_dir():
            return path
    return None


def export_to_csv():
    """
    Export all session data to a CSV file in two locations:
      1. ./CSV directory (created if it doesn't exist)
      2. OneDrive folder (if found on Windows or macOS)
    Returns:
        (local_path, onedrive_path)  # onedrive_path may be None
    """
    from pathlib import Path
    from datetime import datetime
    import csv
    import shutil

    today_str = datetime.now().strftime("%m-%d-%Y")

    # ---- Local CSV folder ----
    local_dir = Path.cwd() / "CSV"
    local_dir.mkdir(exist_ok=True)

    def unique_name(folder):
        count = 1
        while True:
            filename = folder / f"{today_str}-{count}.csv"
            if not filename.exists():
                return filename
            count += 1

    # ---- Get data from DB ----
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.name, s.difficulty, p.position, p.side, s.catches, s.score, s.played_at
        FROM sessions s
        JOIN players p ON p.player_id = s.player_id
        ORDER BY s.played_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    # ---- Write local CSV ----
    local_file = unique_name(local_dir)
    with open(local_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Player", "Difficulty", "Position", "Side", "Flags", "Score", "Date"])
        writer.writerows(rows)

    # ---- Try to also copy to OneDrive ----
    onedrive_dir = find_onedrive_path()
    onedrive_file = None
    if onedrive_dir:
        try:
            target_dir = onedrive_dir / "Flag_Reaction_Test" / "CSV"
            target_dir.mkdir(parents=True, exist_ok=True)
            onedrive_file = unique_name(target_dir)
            shutil.copy(local_file, onedrive_file)
        except Exception as e:
            print(f"Error exporting to OneDrive: {e}")
            onedrive_file = None

    return local_file, onedrive_file

# ---------------------------
# CSV Import
# ---------------------------

def import_from_csv(path: str):
    """
    Imports players from a CSV with 'name', 'position', and 'side' columns.
    All column names are case-insensitive.
    Returns: {"imported": N, "skipped": M, "errors": [(line_no, message), ...]}.
    """
    import csv

    imported, skipped = 0, 0
    errors = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")

        # Map lowercase field names to original names
        hmap = {h.lower().strip(): h for h in reader.fieldnames}
        if "name" not in hmap:
            raise ValueError("CSV must have a 'name' column.")

        conn = get_connection()
        cur = conn.cursor()

        line_no = 1
        for row in reader:
            line_no += 1
            try:
                name = (row.get(hmap["name"]) or "").strip()
                position = (row.get(hmap.get("position", ""), "") or "").strip()
                side = (row.get(hmap.get("side", ""), "") or "").strip().title()

                if not name:
                    skipped += 1
                    errors.append((line_no, "Missing 'name'"))
                    continue

                # Optional validation for side
                if side and side not in ["Offense", "Defense", "Special Teams"]:
                    skipped += 1
                    errors.append((line_no, f"Invalid side: '{side}'"))
                    continue

                # Insert player
                cur.execute("""
                    INSERT OR IGNORE INTO players (name, position, side)
                    VALUES (?, ?, ?)
                """, (name, position or None, side or None))

                imported += 1

            except Exception as row_err:
                skipped += 1
                errors.append((line_no, str(row_err)))

    conn.commit()
    conn.close()
    return True
