# create & activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate

# install dependencies
python -m pip install --upgrade pip
pip install fastapi "uvicorn[standard]" python-multipart

# run FastAPI (backend)
uvicorn api:app --reload 

# install frontend dependencies
npm install

# run frontend dev server in separate terminal
cd react-ui
npm run dev

[ React UI (Vite) ]  <--fetch-->  [ FastAPI (Python) ]  <--->  [ SQLite DB ]
         |                               |                          |
       src/                             api.py                flag_reaction_test.db


Frontend (React / Vite) — src/
src/App.jsx
The main UI “state machine” that moves between views: home → select → difficulty → countdown → flash → ready → capture → leaderboard → admin.
Triggers API calls (via src/api.js) when you load players, create players, save a session, fetch leaderboard, import/export.
Edit this when you change screens, buttons, what happens when a user clicks a thing, or how data is displayed.

src/api.js
A tiny client that wraps fetch to the backend.
Exports functions: listPlayers, createPlayer, deletePlayer, addSession, getLeaderboard, exportCSVSimple, importCSVSimple.
Edit this when you add/rename backend endpoints or change the request/response shapes.
If your backend base URL changes, set VITE_API_BASE in a .env.

src/App.css
Visual theme & layout: colors, panels, lists, buttons, table styles, animations.
Edit this when changing styles/spacing/responsiveness/branding.
public/psu-logo.png
Logo shown in top-left.

api.py
HTTP API for the frontend.
Defines routes:
GET /players — list players
POST /players — create player (name, position, side)
DELETE /players/{id} — delete player + sessions
POST /sessions — record a session (player_id, difficulty, catches)
GET /leaderboard?top_n=10 — top sessions (balanced score)
GET /export-simple — CSV export (name, position, side, total_score)
POST /import-simple — CSV import (name [+ optional position, side])
Business logic: leaderboard combines catches × multiplier (Easy=1, Medium=2, Hard=3, Very Hard=5). You can change multipliers or ranking SQL here without touching the DB schema.
Edit this when you add/modify API endpoints, change leaderboard logic, or adjust CSV import/export rules/CORS.