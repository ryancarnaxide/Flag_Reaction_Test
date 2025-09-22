import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import database_setup as db

# ==============================
# App State
# ==============================
current_player = None
selected_difficulty = None

# ==============================
# Helper Functions
# ==============================
def switch_frame(frame):
    for f in (start_frame, player_frame, round_frame, leaderboard_frame):
        f.pack_forget()
    frame.pack(fill="both", expand=True)

def load_players():
    player_list.delete(0, tk.END)
    for pid, name in db.get_all_players():
        player_list.insert(tk.END, f"{pid}: {name}")

def create_account():
    name = simpledialog.askstring("New Account", "Enter your name:")
    if name:
        pid = db.create_player(name)
        if not pid:
            messagebox.showerror("Error", "Name already exists.")
            return
        load_players()
        select_player(pid)

def select_player_from_list():
    selection = player_list.curselection()
    if not selection:
        return
    pid = int(player_list.get(selection[0]).split(":")[0])
    select_player(pid)

def select_player(pid):
    global current_player, selected_difficulty
    player = db.get_player_by_id(pid)
    if player:
        current_player = player
        selected_difficulty = None
        player_label.config(text=f"Player: {current_player['name']}")
        difficulty_label.config(text="Selected Mode: None")
        switch_frame(player_frame)

def choose_difficulty(diff):
    global selected_difficulty
    selected_difficulty = diff
    difficulty_label.config(text=f"Selected Mode: {diff}")

def start_round():
    if not selected_difficulty:
        messagebox.showwarning("No Mode", "Select a difficulty first.")
        return
    switch_frame(round_frame)

def record_round(catches):
    global current_player, selected_difficulty
    if current_player and selected_difficulty is not None:
        db.record_session(current_player['id'], selected_difficulty, catches)
        update_leaderboard()
        switch_frame(leaderboard_frame)

def update_leaderboard():
    for row in leaderboard_table.get_children():
        leaderboard_table.delete(row)
    for name, diff, catches, score in db.get_leaderboard():
        leaderboard_table.insert("", "end", values=(name, diff, catches))

def play_again():
    global selected_difficulty
    selected_difficulty = None
    difficulty_label.config(text="Selected Mode: None")
    switch_frame(player_frame)

def export_csv():
    filename = db.export_to_csv()
    messagebox.showinfo("CSV Exported", f"CSV data properly exported as {filename}.\nInsert USB to download latest CSV.")

# ==============================
# UI Setup
# ==============================
root = tk.Tk()
root.title("Flag Reaction Test Prototype")
root.geometry("500x450")

# ----- Start Screen -----
start_frame = tk.Frame(root)
tk.Label(start_frame, text="Select Player", font=("Arial", 14, "bold")).pack(pady=10)

player_list = tk.Listbox(start_frame, width=30, height=10)
player_list.pack(pady=5)

tk.Button(start_frame, text="Select Player", command=select_player_from_list).pack(pady=5)
tk.Button(start_frame, text="Create New Account", command=create_account).pack(pady=5)
tk.Button(start_frame, text="CSV Export", command=export_csv).pack(pady=10)

# ----- Player Screen -----
player_frame = tk.Frame(root)
player_label = tk.Label(player_frame, text="Player: ???", font=("Arial", 14, "bold"))
player_label.pack(pady=10)

tk.Label(player_frame, text="Select Difficulty:", font=("Arial", 12)).pack(pady=5)

for diff in ["Easy", "Medium", "Hard", "Very Hard"]:
    tk.Button(player_frame, text=diff, width=15, command=lambda d=diff: choose_difficulty(d)).pack(pady=2)

difficulty_label = tk.Label(player_frame, text="Selected Mode: None", font=("Arial", 12))
difficulty_label.pack(pady=10)

nav_frame = tk.Frame(player_frame)
nav_frame.pack(pady=10)
tk.Button(nav_frame, text="← Back", command=lambda: switch_frame(start_frame)).pack(side="left", padx=5)
tk.Button(nav_frame, text="Start Round", command=start_round).pack(side="left", padx=5)

# ----- Round Screen -----
round_frame = tk.Frame(root)
tk.Label(round_frame, text="How many flags did you catch?", font=("Arial", 14, "bold")).pack(pady=10)

buttons_frame = tk.Frame(round_frame)
buttons_frame.pack(pady=10)
for i in range(11):
    tk.Button(buttons_frame, text=str(i), width=4, command=lambda c=i: record_round(c)).grid(row=i//6, column=i%6, padx=5, pady=5)

# ----- Leaderboard Screen -----
leaderboard_frame = tk.Frame(root)
tk.Label(leaderboard_frame, text="Leaderboard (Top 10)", font=("Arial", 14, "bold")).pack(pady=10)

leaderboard_table = ttk.Treeview(leaderboard_frame, columns=("Player","Difficulty","Flags"), show="headings")
leaderboard_table.heading("Player", text="Player")
leaderboard_table.heading("Difficulty", text="Difficulty")
leaderboard_table.heading("Flags", text="Flags")
leaderboard_table.column("Player", width=150, anchor="w")
leaderboard_table.column("Difficulty", width=100, anchor="center")
leaderboard_table.column("Flags", width=80, anchor="center")
leaderboard_table.pack(fill="both", expand=True, padx=10, pady=10)

buttons_frame2 = tk.Frame(leaderboard_frame)
buttons_frame2.pack(pady=5)
tk.Button(buttons_frame2, text="Back to Players", command=lambda: switch_frame(start_frame)).pack(side="left", padx=5)
tk.Button(buttons_frame2, text="Play Again", command=play_again).pack(side="left", padx=5)

# ==============================
# Initialize App
# ==============================
db.setup_database()
load_players()
update_leaderboard()
switch_frame(start_frame)

root.mainloop()
