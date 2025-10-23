# api.py — Flag Reaction Test API
import io
import csv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import database_setup as db
from database_setup import get_connection


# ---------------------------
# App Initialization
# ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.setup_database()
    yield


app = FastAPI(title="Flag Reaction Test API", lifespan=lifespan)

# Allow frontend access (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


# ---------------------------
# Players
# ---------------------------
@app.get("/players")
def list_players():
    rows = db.get_all_players()
    return [{"id": r[0], "name": r[1], "position": r[2], "side": r[3]} for r in rows]


@app.post("/players")
def create_player(payload: dict):
    name = (payload.get("name") or "").strip()
    position = payload.get("position")
    side = payload.get("side")
    if not name:
        raise HTTPException(400, "name is required")
    pid = db.create_player(name, position, side)
    if pid is None:
        raise HTTPException(409, "player name already exists")
    return {"id": pid}


@app.delete("/players/{player_id}")
def delete_player(player_id: int):
    db.delete_player(player_id)
    return {"ok": True}


# ---------------------------
# Sessions / Leaderboard
# ---------------------------
@app.post("/sessions")
def add_session(payload: dict):
    """Accepts: { player_id, difficulty, catches }"""
    pid = payload.get("player_id")
    difficulty = payload.get("difficulty")
    catches = payload.get("catches")
    if pid is None or difficulty is None or catches is None:
        raise HTTPException(400, "player_id, difficulty, catches are required")

    try:
        db.record_session(int(pid), str(difficulty), int(catches))
    except Exception as e:
        raise HTTPException(400, f"could not save session: {e}")

    return {"ok": True}


@app.get("/leaderboard")
def get_leaderboard(top_n: int = 10):
    """
    Leaderboard ranked by difficulty multiplier × catches.
    Multipliers: Easy=1, Medium=2, Hard=3, Very Hard=5.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.name, 
            s.difficulty, 
            s.catches, 
            CASE 
                WHEN s.difficulty='Easy' THEN 1
                WHEN s.difficulty='Medium' THEN 2
                WHEN s.difficulty='Hard' THEN 3
                WHEN s.difficulty='Very Hard' THEN 5
                ELSE 1
            END AS multiplier,
            (s.catches * 
                CASE 
                    WHEN s.difficulty='Easy' THEN 1
                    WHEN s.difficulty='Medium' THEN 2
                    WHEN s.difficulty='Hard' THEN 3
                    WHEN s.difficulty='Very Hard' THEN 5
                    ELSE 1
                END
            ) AS balanced_score,
            s.played_at
        FROM sessions s
        JOIN players p ON p.player_id = s.player_id
        ORDER BY balanced_score DESC, s.played_at ASC
        LIMIT ?
    """, (top_n,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "name": n,
            "difficulty": d,
            "catches": c,
            "multiplier": m,
            "score": s,
            "played_at": t,
        }
        for (n, d, c, m, s, t) in rows
    ]


# ---------------------------
# CSV Export / Import
# ---------------------------
@app.get("/export-simple")
def export_simple_csv():
    """
    Export all players with total score, position, and side.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.name, 
            p.position,
            p.side,
            COALESCE(SUM(s.score), 0) AS total_score
        FROM players p
        LEFT JOIN sessions s ON s.player_id = p.player_id
        GROUP BY p.player_id, p.name, p.position, p.side
        ORDER BY total_score DESC, p.name ASC
    """)

    rows = cur.fetchall()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name", "position", "side", "total_score"])
    writer.writerows(rows)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=players_scores.csv"}
    )


@app.post("/import-simple")
async def import_simple(file: UploadFile = File(...)):
    """
    Import CSV with at least a 'name' column.
    Accepts optional 'position' and 'side'.
    """
    try:
        text = (await file.read()).decode("utf-8-sig")
    except Exception:
        raise HTTPException(400, "Could not read uploaded file")

    f = io.StringIO(text)
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        raise HTTPException(400, "CSV has no header row")

    headers = {h.lower().strip(): h for h in reader.fieldnames}
    if "name" not in headers:
        raise HTTPException(400, "CSV must include a 'name' column")

    imported = skipped = 0
    errors = []
    line_no = 1

    for row in reader:
        line_no += 1
        name = (row.get(headers["name"]) or "").strip()
        position = (row.get(headers.get("position", "")) or "").strip()
        side = (row.get(headers.get("side", "")) or "").strip()

        if not name:
            skipped += 1
            errors.append((line_no, "Missing name"))
            continue

        pid = db.create_player(name, position, side)
        if pid is None:
            skipped += 1
        else:
            imported += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}
