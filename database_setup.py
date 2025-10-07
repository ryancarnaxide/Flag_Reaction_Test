import sqlite3
import os
import csv
from datetime import datetime

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
        SELECT p.name, p.position, p.side, s.difficulty, s.catches, s.score, s.played_at
        FROM sessions s
        JOIN players p ON p.player_id = s.player_id
        ORDER BY s.played_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Player", "Position", "Side", "Difficulty", "Flags", "Score", "Date"])
        writer.writerows(rows)

    return filename

# ---------------------------
# CSV Import
# ---------------------------
def import_from_csv(filepath):
    """Import sessions from a CSV file into the database.
       Expected columns: Player, Position, Side, Difficulty, Flags, Score, Date
       Backward compatible with old CSVs without Position/Side.
    """
    conn = get_connection()
    cursor = conn.cursor()

    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            player_name = row.get("Player")
            position = row.get("Position") if "Position" in row else None
            side = row.get("Side") if "Side" in row else None

            # Ensure player exists or create them (with position/side if available)
            cursor.execute("SELECT player_id FROM players WHERE name=?", (player_name,))
            player = cursor.fetchone()
            if player:
                player_id = player[0]
            else:
                cursor.execute(
                    "INSERT INTO players (name, position, side) VALUES (?,?,?)",
                    (player_name, position, side)
                )
                conn.commit()
                cursor.execute("SELECT player_id FROM players WHERE name=?", (player_name,))
                player_id = cursor.fetchone()[0]

            # Insert session
            cursor.execute("""
                INSERT INTO sessions (player_id, difficulty, catches, score, played_at)
                VALUES (?,?,?,?,?)
            """, (
                player_id,
                row["Difficulty"],
                int(row["Flags"]),
                int(row["Score"]),
                row["Date"]
            ))

    conn.commit()
    conn.close()
    return True