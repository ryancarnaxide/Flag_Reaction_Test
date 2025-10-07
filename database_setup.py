import sqlite3
import os
import csv
from datetime import datetime
from pathlib import Path

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

# ---------------------------
# CSV Export
# ---------------------------

def export_to_csv(folder=None):

    """Export all sessions to a uniquely named CSV file."""
    folder = folder or os.getcwd()
    today_str = datetime.now().strftime("%m-%d-%Y")
    base_filename = os.path.join(folder, today_str)

    # Count existing files
    count = 1
    for f in os.listdir(folder):
        if f.startswith(today_str) and f.endswith(".csv"):
            try:
                num = int(f.replace(today_str+"-","").replace(".csv",""))
                count = max(count, num+1)
            except:
                continue

    filename = f"{base_filename}-{count}.csv"

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

    with open(filename, mode='w', newline='') as f:

        writer = csv.writer(f)
        writer.writerow(["Player", "Difficulty", "Position", "Side", "Flags", "Score", "Date"])
        writer.writerows(rows)

    return filename

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
