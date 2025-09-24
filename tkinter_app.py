import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import database_setup as db

# ==============================
# App State
# ==============================
current_player = None
selected_difficulty = None
countdown_value = 5
difficulty_buttons = {}   # diff -> ttk.Button
difficulty_wraps = {}     # diff -> wrapper Frame for hover outline

# ==============================
# Helpers
# ==============================
def switch_frame(frame):
    for f in (start_frame, player_frame, countdown_frame,
              proceed_frame, round_frame, leaderboard_frame):
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
        # reset visuals
        for d in difficulty_buttons:
            difficulty_buttons[d].configure(style="Flat.TButton")
            difficulty_wraps[d].configure(highlightthickness=0)
        switch_frame(player_frame)

# ---------- Difficulty visuals ----------
def choose_difficulty(diff):
    global selected_difficulty
    selected_difficulty = diff
    difficulty_label.config(text=f"Selected Mode: {diff}")
    for d in difficulty_buttons:
        difficulty_buttons[d].configure(style="Flat.TButton")
        difficulty_wraps[d].configure(highlightthickness=0)
    # selected: navy + WHITE text
    difficulty_buttons[diff].configure(style="Selected.TButton")

def on_hover(event):
    txt = event.widget.cget("text")
    if txt != selected_difficulty:
        difficulty_wraps[txt].configure(
            highlightbackground="#001E44", highlightcolor="#001E44", highlightthickness=2
        )

def on_leave(event):
    txt = event.widget.cget("text")
    if txt != selected_difficulty:
        difficulty_wraps[txt].configure(highlightthickness=0)

# ---------- Countdown Flow ----------
def start_round():
    if not selected_difficulty:
        messagebox.showwarning("No Mode", "Select a difficulty first.")
        return
    start_countdown()

def start_countdown():
    global countdown_value
    countdown_value = 5
    countdown_label.config(text=f"Starting in... {countdown_value}", fg="black", bg="white")
    switch_frame(countdown_frame)
    root.after(1000, update_countdown)

def update_countdown():
    global countdown_value
    countdown_value -= 1
    if countdown_value > 0:
        countdown_label.config(text=f"Starting in... {countdown_value}")
        root.after(1000, update_countdown)
    else:
        show_go_screen()

def show_go_screen():
    countdown_frame.config(bg="green")
    countdown_label.config(text="GO!", bg="green", fg="white", font=("Arial", 28, "bold"))
    root.after(1000, lambda: (
        countdown_frame.config(bg="white"),
        countdown_label.config(bg="white", fg="black", font=("Arial", 22, "bold")),
        switch_frame(proceed_frame)
    ))

def proceed_to_round():
    switch_frame(round_frame)

# ---------- DB / Leaderboard ----------
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
    for d in difficulty_buttons:
        difficulty_buttons[d].configure(style="Flat.TButton")
        difficulty_wraps[d].configure(highlightthickness=0)
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
root.configure(bg="white")

# ttk styles with borders
style = ttk.Style()
style.theme_use("clam")

# Normal buttons: white with visible border
style.configure(
    "Flat.TButton",
    background="white",
    foreground="black",
    borderwidth=2,
    relief="ridge",
    padding=6
)
style.map(
    "Flat.TButton",
    background=[("active", "#e6e6e6")],
    relief=[("pressed", "sunken"), ("active", "ridge")]
)

# Selected difficulty: navy + white text, visible border
style.configure(
    "Selected.TButton",
    background="#001E44",
    foreground="white",
    borderwidth=2,
    relief="ridge",
    padding=6
)
style.map(
    "Selected.TButton",
    background=[("active", "#001E44")],
    foreground=[("active", "white")],
    relief=[("pressed", "sunken"), ("active", "ridge")]
)

# ----- Start Screen -----
start_frame = tk.Frame(root, bg="white")
tk.Label(start_frame, text="Select Player", font=("Arial", 14, "bold"), bg="white").pack(pady=10)

player_list = tk.Listbox(start_frame, width=30, height=10, bg="white")
player_list.pack(pady=5)

ttk.Button(start_frame, text="Select Player", style="Flat.TButton",
           takefocus=False, command=select_player_from_list).pack(pady=5)
ttk.Button(start_frame, text="Create New Account", style="Flat.TButton",
           takefocus=False, command=create_account).pack(pady=5)
ttk.Button(start_frame, text="CSV Export", style="Flat.TButton",
           takefocus=False, command=export_csv).pack(pady=10)

# ----- Player Screen -----
player_frame = tk.Frame(root, bg="white")
player_label = tk.Label(player_frame, text="Player: ???", font=("Arial", 14, "bold"), bg="white")
player_label.pack(pady=10)

tk.Label(player_frame, text="Select Difficulty:", font=("Arial", 12), bg="white").pack(pady=5)

for diff in ["Easy", "Medium", "Hard", "Very Hard"]:
    wrap = tk.Frame(player_frame, bg="white", highlightthickness=0)
    wrap.pack(pady=6)
    btn = ttk.Button(wrap, text=diff, style="Flat.TButton",
                     takefocus=False, command=lambda d=diff: choose_difficulty(d))
    btn.pack()
    btn.bind("<Enter>", on_hover)
    btn.bind("<Leave>", on_leave)
    difficulty_buttons[diff] = btn
    difficulty_wraps[diff] = wrap

difficulty_label = tk.Label(player_frame, text="Selected Mode: None", font=("Arial", 12), bg="white")
difficulty_label.pack(pady=10)

nav_frame = tk.Frame(player_frame, bg="white")
nav_frame.pack(pady=10)
ttk.Button(nav_frame, text="← Back", style="Flat.TButton",
           takefocus=False, command=lambda: switch_frame(start_frame)).pack(side="left", padx=5)
ttk.Button(nav_frame, text="Start Round", style="Flat.TButton",
           takefocus=False, command=start_round).pack(side="left", padx=5)

# ----- Countdown Screen -----
countdown_frame = tk.Frame(root, bg="white")
countdown_label = tk.Label(countdown_frame, text="Starting in... 5",
                           font=("Arial", 22, "bold"), bg="white")
countdown_label.pack(expand=True, pady=40)

# ----- Proceed Screen -----
proceed_frame = tk.Frame(root, bg="white")
tk.Label(proceed_frame, text="Click to proceed", font=("Arial", 16, "bold"), bg="white").pack(pady=30)
ttk.Button(proceed_frame, text="Proceed", style="Flat.TButton",
           takefocus=False, command=proceed_to_round).pack(pady=10)

# ----- Round Screen (compact grid fits in 500x450) -----
round_frame = tk.Frame(root, bg="white")
tk.Label(round_frame, text="How many flags did you catch?",
         font=("Arial", 14, "bold"), bg="white").pack(pady=(10, 6))

buttons_frame = tk.Frame(round_frame, bg="white")
buttons_frame.pack(pady=6)

MAX_COLS = 4
for col in range(MAX_COLS):
    buttons_frame.grid_columnconfigure(col, weight=1)

for i in range(11):
    r, c = divmod(i, MAX_COLS)
    ttk.Button(buttons_frame, text=str(i), style="Flat.TButton",
               takefocus=False, command=lambda c=i: record_round(c)
               ).grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

# ----- Leaderboard Screen -----
leaderboard_frame = tk.Frame(root, bg="white")
tk.Label(leaderboard_frame, text="Leaderboard (Top 10)", font=("Arial", 14, "bold"), bg="white").pack(pady=10)

leaderboard_table = ttk.Treeview(leaderboard_frame, columns=("Player","Difficulty","Flags"), show="headings")
leaderboard_table.heading("Player", text="Player")
leaderboard_table.heading("Difficulty", text="Difficulty")
leaderboard_table.heading("Flags", text="Flags")
leaderboard_table.column("Player", width=150, anchor="w")
leaderboard_table.column("Difficulty", width=100, anchor="center")
leaderboard_table.column("Flags", width=80, anchor="center")
leaderboard_table.pack(fill="both", expand=True, padx=10, pady=10)

buttons_frame2 = tk.Frame(leaderboard_frame, bg="white")
buttons_frame2.pack(pady=5)
ttk.Button(buttons_frame2, text="Back to Players", style="Flat.TButton",
           takefocus=False, command=lambda: switch_frame(start_frame)).pack(side="left", padx=5)
ttk.Button(buttons_frame2, text="Play Again", style="Flat.TButton",
           takefocus=False, command=play_again).pack(side="left", padx=5)

# ==============================
# Initialize App
# ==============================
db.setup_database()
load_players()
update_leaderboard()
switch_frame(start_frame)

root.mainloop()
