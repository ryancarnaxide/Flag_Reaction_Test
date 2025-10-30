import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QGridLayout, QLineEdit, QFileDialog, QDialog, QComboBox
)
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QTouchEvent
import database_setup as db

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# GPIO Control for Magnets (with error handling for non-Raspberry Pi systems)
try:
    from gpiozero import LED
    GPIO_AVAILABLE = True
    # Initialize all 10 Magnets according to maglist
    M1 = LED(5)   # GPIO5
    M2 = LED(6)   # GPIO6
    M3 = LED(16)  # GPIO16
    M4 = LED(17)  # GPIO17
    M5 = LED(20)  # GPIO20
    M6 = LED(21)  # GPIO21
    M7 = LED(22)  # GPIO22
    M8 = LED(23)  # GPIO23
    M9 = LED(24)  # GPIO24
    M10 = LED(25) # GPIO25
    
    # List of all magnets for easy iteration
    ALL_MAGS = [M1, M2, M3, M4, M5, M6, M7, M8, M9, M10]
    print("✓ GPIO initialized: All 10 magnets ready")
except (ImportError, RuntimeError) as e:
    GPIO_AVAILABLE = False
    print(f"GPIO not available: {e}")
    M1 = M2 = M3 = M4 = M5 = M6 = M7 = M8 = M9 = M10 = None
    ALL_MAGS = []

#from datetime import datetime

# ==============================
# Initialize Database
# ==============================
db.setup_database()

# ==============================
# Dark Mode Stylesheet
# ==============================
dark_style = """
QWidget { background-color: #1e1e2f; color: #ffffff; font-family: Arial; font-size: 18px; }
QPushButton { background-color: #1e407c; color: #ffffff; border-radius: 12px; padding: 12px 20px; font-size: 18px; }
QPushButton:hover { background-color: #96BEE6; color: #001E44 }
QPushButton:pressed { background-color: #2a2a44; }
QTableWidget { background-color: #2b2b3d; gridline-color: #444466; }
QHeaderView::section { background-color: #3b3b5c; padding: 4px; font-weight: bold; }
QListWidget { background-color: #001E44; border-radius: 12px; padding: 6px; font-size: 16px;}
/* Larger Scrollbar */
QScrollBar:vertical {
    background: #2b2b3d;
    width: 12px;
    margin: 20px 0 20px 0;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #565680;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
"""

# ==============================
# Main Application
# ==============================
class FlagApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flag Reaction Test (Dark Mode)")
        self.setGeometry(150, 150, 700, 700)
        self.setFixedSize(self.size())
        self.setObjectName("MainAppWindow")
        self.setStyleSheet(dark_style)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        # Screens
        self.start_screen = self.make_start_screen()
        self.player_screen = self.make_player_screen()
        self.round_screen = self.make_round_screen()
        self.leaderboard_screen = self.make_leaderboard_screen()
        self.countdown_screen = self.make_countdown_screen()
        self.go_screen = self.make_go_screen()

        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(self.player_screen)
        self.stack.addWidget(self.round_screen)
        self.stack.addWidget(self.leaderboard_screen)
        self.stack.addWidget(self.countdown_screen)
        self.stack.addWidget(self.go_screen)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)

        self.stats_screen = self.make_stats_screen()
        self.stack.addWidget(self.stats_screen)
        
        self.dropping_screen = self.make_dropping_screen()
        self.stack.addWidget(self.dropping_screen)

        
        # global values as object oriented attributes
        self.current_player = None
        self.selected_difficulty = None
        self.admin_password = 'dan5171'
        self.dev_mode = False  # Developer mode flag
        self.led_timer = QTimer()  # Timer for LED control
        self.led_timer.timeout.connect(self.turn_off_leds)
        
        # Keep all magnets ON by default
        if GPIO_AVAILABLE:
            for mag in ALL_MAGS:
                mag.on()
            print("✓ All magnets turned ON (default state)")

        self.load_players()
        self.update_leaderboard()
        self.switch_to(self.start_screen)
        self.switch_to_player_mode()

    # --------------------------
    # Screen Builders
    # --------------------------
    '''
    def make_start_screen(self):
        w = QWidget()
    
        # Main layout on `w`
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(40, 20, 40, 20)
        vbox.setSpacing(15)

        self.player_list = QListWidget()
        self.player_list.setFixedHeight(250)
        vbox.addWidget(self.player_list)

        # Player-only button
        self.btn_login_admin = QPushButton("Admin Login")
        self.btn_login_admin.clicked.connect(self.login_admin)
        vbox.addWidget(self.btn_login_admin)

        self.header_label = QLabel("Select Player")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet("font-weight: bold; font-size: 22px;")
        vbox.addWidget(self.header_label)

        # --- action buttons ---
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.clicked.connect(self.logout_admin)
        vbox.addWidget(self.btn_logout)

        self.btn_select = QPushButton("Select Player")
        self.btn_select.clicked.connect(self.select_player_from_list)
        vbox.addWidget(self.btn_select)

        self.btn_create = QPushButton("Create New Account")
        self.btn_create.clicked.connect(self.create_account)
        vbox.addWidget(self.btn_create)

        self.btn_delete = QPushButton("Remove Account")
        self.btn_delete.clicked.connect(self.delete_player_from_list)
        vbox.addWidget(self.btn_delete)

        self.btn_view = QPushButton("View Leaderboard")
        self.btn_view.clicked.connect(lambda: self.switch_to(self.leaderboard_screen))
        vbox.addWidget(self.btn_view)

        self.btn_export = QPushButton("Export CSV")
        self.btn_export.clicked.connect(self.export_csv)
        vbox.addWidget(self.btn_export)

        # Minimal Import CSV (admin-only visibility toggled)
        self.btn_import = QPushButton("Import CSV")
        self.btn_import.clicked.connect(self.import_csv)
        vbox.addWidget(self.btn_import)

        return w
    '''
    def make_start_screen(self):
        w = QWidget()
    
        # Main vertical layout
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(40, 20, 40, 20)
        vbox.setSpacing(15)

        # ---------------------------
        # Header (still useful for admin/player modes)
        # ---------------------------
        self.header_label = QLabel("Select Player")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet("font-weight: bold; font-size: 22px; color: white;")
        vbox.addWidget(self.header_label)

        # ---------------------------
        # Player List (now larger)
        # ---------------------------
        self.player_list = QListWidget()
        self.player_list.setStyleSheet("""
        QListWidget {
            font-size: 20px;
            font-weight: bold;
        }
        QListWidget::item {
            padding: 5px 5px;
            height: 40px;
        }
        """)

        #self.player_list.setFixedHeight(250)  # ⬅️ Increased height for more visibility
        vbox.addWidget(self.player_list)

        # ---------------------------
        # Select Player Button (moved directly below list)
        # ---------------------------
        self.btn_select = QPushButton("Select Player")
        self.btn_select.setMinimumHeight(50)
        self.btn_select.clicked.connect(self.select_player_from_list)
        vbox.addWidget(self.btn_select)

        # ---------------------------
        # Spacer pushes admin button to bottom
        # ---------------------------
        vbox.addStretch()

        # ---------------------------
        # Admin Login at bottom of screen
        # ---------------------------
        self.btn_login_admin = QPushButton("Admin Login")
        self.btn_login_admin.setMinimumHeight(40)
        self.btn_login_admin.clicked.connect(self.login_admin)
        vbox.addWidget(self.btn_login_admin)

        # ---------------------------
        # Hidden admin-only buttons (remain for admin mode)
        # ---------------------------
        self.btn_create = QPushButton("Add New Player")
        self.btn_create.clicked.connect(self.create_account)
        vbox.addWidget(self.btn_create)

        self.btn_delete = QPushButton("Remove Selected Player")
        self.btn_delete.clicked.connect(self.delete_player_from_list)
        vbox.addWidget(self.btn_delete)

        #self.btn_view = QPushButton("View Leaderboard")
        #self.btn_view.clicked.connect(lambda: self.switch_to(self.leaderboard_screen))
        #vbox.addWidget(self.btn_view)

        self.btn_export = QPushButton("Export CSV")
        self.btn_export.clicked.connect(self.export_csv)
        vbox.addWidget(self.btn_export)

        self.btn_import = QPushButton("Import CSV")
        self.btn_import.clicked.connect(self.import_csv)
        vbox.addWidget(self.btn_import)

        self.btn_logout = QPushButton("Logout")
        self.btn_logout.clicked.connect(self.logout_admin)
        vbox.addWidget(self.btn_logout)

        # Developer Mode Button (hidden by default)
        self.btn_dev_mode = QPushButton("🔧 Dev Mode")
        self.btn_dev_mode.clicked.connect(self.toggle_dev_mode)
        vbox.addWidget(self.btn_dev_mode)

        # Quick Test Button (only visible in dev mode)
        self.btn_quick_test = QPushButton("⚡ Quick Test (Skip to GO)")
        self.btn_quick_test.clicked.connect(self.quick_test_sequence)
        self.btn_quick_test.setStyleSheet("background-color: #ff6b35; color: white;")
        vbox.addWidget(self.btn_quick_test)

        # Guest Mode Button (always visible at bottom)
        vbox.addStretch()
        self.btn_guest_mode = QPushButton("👤 Guest Mode (Quick Test)")
        self.btn_guest_mode.clicked.connect(self.guest_mode_sequence)
        self.btn_guest_mode.setStyleSheet("background-color: #4a90e2; color: white;")
        self.btn_guest_mode.setMinimumHeight(50)
        vbox.addWidget(self.btn_guest_mode)

        return w


    def make_player_screen(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(40, 20, 40, 20)
        vbox.setSpacing(15)

        self.player_label = QLabel("Player: ???")
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_label.setStyleSheet("font-weight: bold; font-size: 20px;")
        vbox.addWidget(self.player_label)

        vbox.addWidget(QLabel("Select Difficulty:", alignment=Qt.AlignmentFlag.AlignCenter))

        for diff in ["Easy", "Medium", "Hard", "Very Hard"]:
            btn = QPushButton(diff)
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda _, d=diff: self.choose_difficulty(d))
            vbox.addWidget(btn)

        self.difficulty_label = QLabel("Selected Mode: None")
        self.difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.difficulty_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top:10px;")
        vbox.addWidget(self.difficulty_label)

        nav = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setMinimumHeight(40)
        back_btn.clicked.connect(lambda: self.switch_to(self.start_screen))
        nav.addWidget(back_btn)

        start_btn = QPushButton("Start Round")
        start_btn.setMinimumHeight(40)
        start_btn.clicked.connect(self.start_round)
        nav.addWidget(start_btn)

        vbox.addLayout(nav)
        return w

    def make_round_screen(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(40, 20, 40, 20)
        vbox.setSpacing(15)

        label = QLabel("How many flags did you catch?")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-weight: bold; font-size: 20px;")
        vbox.addWidget(label)

        grid = QGridLayout()
        grid.setSpacing(10)
        for i in range(11):
            btn = QPushButton(str(i))
            btn.setMinimumSize(70, 60)
            btn.clicked.connect(lambda _, c=i: self.record_round(c))
            grid.addWidget(btn, i // 6, i % 6)
        vbox.addLayout(grid)

        return w

    def make_leaderboard_screen(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(40, 20, 40, 20)
        vbox.setSpacing(5)

        # -------- Navigation Buttons

        # adding buttons to top to reduce error where tapping 7 flags also taps back button
        nav = QHBoxLayout()
        back_btn = QPushButton("Back to Players")
        back_btn.setMinimumHeight(40)
        back_btn.clicked.connect(lambda: self.switch_to(self.start_screen))
        nav.addWidget(back_btn)

        again_btn = QPushButton("Play Again")
        again_btn.setMinimumHeight(40)
        again_btn.clicked.connect(self.play_again)
        nav.addWidget(again_btn)

        vbox.addLayout(nav)

        # -------- screen header below buttons
        header = QLabel("Leaderboard (Top 10)")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; font-size: 22px;")
        vbox.addWidget(header)
        
        # -------- leaderboard on bottom
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Player", "Difficulty", "Flags"])
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setFixedHeight(400)
        vbox.addSpacing(5)
        vbox.addWidget(self.table)

        self.btn_my_stats = QPushButton("My Stats")
        self.btn_my_stats.setMinimumHeight(40)
        self.btn_my_stats.clicked.connect(self.show_player_stats)
        vbox.addWidget(self.btn_my_stats)


        return w

    def make_countdown_screen(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.countdown_label = QLabel("Starting in 5")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("font-weight: bold; font-size: 48px;")
        vbox.addWidget(self.countdown_label)

        return w

    def make_go_screen(self):
        w = QWidget()
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w.setLayout(vbox)

        w.setStyleSheet("background-color: green;")

        self.go_label = QLabel("GO")
        self.go_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.go_label.setStyleSheet("font-weight: bold; font-size: 48px; color: white;")
        vbox.addWidget(self.go_label)

        return w
    
    def make_dropping_screen(self):
        """Screen that shows when flags are dropping - changes from white to Nittany Blue"""
        w = QWidget()
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w.setLayout(vbox)

        # Start with white background (default state)
        w.setStyleSheet("background-color: white;")

        self.dropping_label = QLabel("DROPPING")
        self.dropping_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dropping_label.setStyleSheet("font-weight: bold; font-size: 48px; color: #001E44;")
        vbox.addWidget(self.dropping_label)

        return w
    
    def make_stats_screen(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(40, 20, 40, 20)
        vbox.setSpacing(15)

        # Header
        self.stats_header = QLabel("Player Stats")
        self.stats_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_header.setStyleSheet("font-weight: bold; font-size: 22px;")
        vbox.addWidget(self.stats_header)

        # Matplotlib canvas
        self.stats_canvas = FigureCanvas(Figure(figsize=(8, 5)))
        vbox.addWidget(self.stats_canvas)

        # Back button
        back_btn = QPushButton("Back to Leaderboard")
        back_btn.setMinimumHeight(40)
        back_btn.clicked.connect(lambda: self.switch_to(self.leaderboard_screen))
        vbox.addWidget(back_btn)

        return w


    # --------------------------
    # Helper Methods
    # --------------------------
    def switch_to(self, widget):
        self.stack.setCurrentWidget(widget)

    def load_players(self):
        self.player_list.clear()
        players = db.get_all_players()  # returns (player_id, name, position, side)
        for pid, name, position, side in players:
            display = f"{name} ({position or 'N/A'}, {side or 'N/A'})"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.player_list.addItem(item)

    def create_account(self):
        dialog = PlayerInfoDialog()
        if dialog.exec():
            data = dialog.get_data()
            name = data["name"]
            pos = data["position"]
            side = data["side"]

            pid = db.create_player(name, pos, side)
            if pid is None:
                QMessageBox.warning(self, "Error", "Name already exists.")
                return
            self.load_players()
        else:
            print("User cancelled.")

    def select_player_from_list(self):
        item = self.player_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        self.select_player(pid)

    def select_player(self, pid):
        player = db.get_player_by_id(pid)
        if player:
            self.current_player = player
            self.selected_difficulty = None
            self.player_label.setText(f"Player: {self.current_player['name']}")
            self.difficulty_label.setText("Selected Mode: None")
            self.switch_to(self.player_screen)

    def choose_difficulty(self, diff):
        self.selected_difficulty = diff
        self.difficulty_label.setText(f"Selected Mode: {diff}")

    def start_round(self):
        if not self.selected_difficulty:
            QMessageBox.warning(self, "No Mode", "Select a difficulty first.")
            return
        self.countdown_value = 5  # Reset countdown
        self.countdown_label.setText(f"Starting in {self.countdown_value}")
        self.switch_to(self.countdown_screen)
        self.timer.start(1000)

    def record_round(self, catches):
        if self.current_player and self.selected_difficulty is not None:
            db.record_session(self.current_player['id'], self.selected_difficulty, catches)
            self.update_leaderboard()
            self.switch_to(self.leaderboard_screen)

    def update_leaderboard(self):
        self.table.setRowCount(0)
        rows = db.get_leaderboard(top_n=10)
        for row_num, (name, diff, catches, score) in enumerate(rows):
            self.table.insertRow(row_num)
            self.table.setItem(row_num, 0, QTableWidgetItem(name))
            self.table.setItem(row_num, 1, QTableWidgetItem(diff))
            self.table.setItem(row_num, 2, QTableWidgetItem(str(catches)))

    def show_player_stats(self):
        if not self.current_player:
            QMessageBox.warning(self, "No Player", "Select a player first.")
            return

        sessions = db.get_player_sessions(self.current_player['id'])
        if not sessions:
            QMessageBox.information(self, "No Data", "No sessions found for this player.")
            return

        # Parse data
        from datetime import datetime
        dates = [datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S") for row in sessions]
        scores = [row[2] for row in sessions]

        # Clear previous figure
        self.stats_canvas.figure.clear()

        # Plot on the embedded canvas
        ax = self.stats_canvas.figure.add_subplot(111)
        ax.plot(dates, scores, marker='o', linestyle='-', color='blue')
        ax.set_title(f"{self.current_player['name']}'s Scores Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Score")
        ax.grid(True)
        self.stats_canvas.figure.autofmt_xdate()
        self.stats_canvas.draw()

        # Switch to stats screen
        self.switch_to(self.stats_screen)


    def delete_player_from_list(self):
        item = self.player_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        player = db.get_player_by_id(pid)
        if player:
            result = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete player '{player['name']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                db.delete_player(pid)
                self.load_players()
        self.switch_to(self.start_screen)

    # slight issue, after first time clicking play_again, automatically tosses to player_screen. No way to play indefinitely
    def play_again(self):
        global selected_difficulty
        selected_difficulty = None
        self.difficulty_label.setText("Selected Mode: None")
        self.switch_to(self.player_screen)
    
    def export_csv(self):
        local_path, onedrive_path = db.export_to_csv()

        if local_path and onedrive_path:
            message = (
                f"✅ CSV successfully exported to both locations:\n\n"
                f"📂 Local: {local_path}\n"
                f"☁️ OneDrive: {onedrive_path}"
            )
        elif local_path:
            message = f"✅ CSV successfully exported locally to:\n\n📂 {local_path}\n\n⚠️ OneDrive not found or unavailable."
        elif onedrive_path:
            message = f"✅ CSV successfully exported to OneDrive:\n\n☁️ {onedrive_path}"
        else:
            message = "❌ CSV export failed — no files were created."

        QMessageBox.information(self, "CSV Export", message)

    # --------------------------
    # Import CSV (names only)
    # --------------------------
    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        try:
            result = db.import_from_csv(path)  # expects 'name' column; ignores others
            imported = result.get("imported", 0)
            skipped = result.get("skipped", 0)
            errors = result.get("errors", [])
            msg = [f"Successfully imported data from {path}.\nImported: {imported}", f"Skipped: {skipped}"]
            if errors:
                preview = "\n".join([f"- Line {ln}: {err}" for ln, err in errors[:8]])
                if len(errors) > 8:
                    preview += f"\n...and {len(errors)-8} more."
                msg.append("\nIssues:\n" + preview)
            QMessageBox.information(self, "CSV Import", "\n".join(msg))
            self.load_players()
        except Exception as ex:
            QMessageBox.critical(self, "Import Failed", f"Error importing CSV:\n{ex}")

    def login_admin(self):
        password, ok = QInputDialog.getText(self, "Admin Access", "Enter the Admin Access Code:", QLineEdit.EchoMode.Password)
        if ok and password == self.admin_password:
            self.switch_to(self.start_screen)
            self.switch_to_admin_mode()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect password!")

    def logout_admin(self):
        result = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to log out of admin access?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if result == QMessageBox.StandardButton.Yes:
            self.switch_to(self.start_screen)
            self.switch_to_player_mode()

    def switch_to_admin_mode(self):
        self.btn_login_admin.hide()
        self.btn_select.hide()
        self.btn_create.show()
        self.btn_delete.show()
        #self.btn_view.show()
        self.btn_export.show()
        self.btn_import.show()
        self.btn_logout.show()
        self.btn_dev_mode.show()
        self.btn_guest_mode.hide()  # Hide guest mode in admin
        if self.dev_mode:
            self.btn_quick_test.show()

        # Toggle or change header
        self.header_label.setText("Admin Panel")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 22px; color: orange;")

        self.player_list.setFixedHeight(250)

    def switch_to_player_mode(self):
        self.btn_login_admin.show()
        self.btn_select.show()
        self.btn_create.hide()
        self.btn_delete.hide()
        #self.btn_view.hide()
        self.btn_export.hide()
        self.btn_import.hide()
        self.btn_logout.hide()
        self.btn_dev_mode.hide()
        self.btn_quick_test.hide()
        self.btn_guest_mode.show()  # Guest mode always visible

        # Toggle or change header
        self.header_label.setText("Select Player")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 22px; color: white;")

        self.player_list.setFixedHeight(350)

    def update_countdown(self):
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.countdown_label.setText(f"Starting in {self.countdown_value}")
        else:
            self.timer.stop()
            self.execute_go_sequence()
    
    def execute_go_sequence(self):
        """Execute the GO sequence with LED control and visual feedback"""
        # Show GO screen
        self.switch_to(self.go_screen)
        
        # Both LEDs stay ON during GO screen (default state)
        # After 1 second, show dropping screen and start LED sequence
        QTimer.singleShot(1000, self.start_dropping_sequence)
    
    def start_dropping_sequence(self):
        """Start the dropping sequence - show initial white screen"""
        # Initial state: White background, Nittany Blue text
        self.dropping_screen.setStyleSheet("background-color: white;")
        self.dropping_label.setStyleSheet("font-weight: bold; font-size: 48px; color: #001E44;")
        self.switch_to(self.dropping_screen)
        
        # Drop all 10 magnets sequentially with 1 second intervals
        # Each magnet drop alternates the screen colors
        for i in range(10):
            delay = (i + 1) * 1000  # 1s, 2s, 3s, 4s, 5s, 6s, 7s, 8s, 9s, 10s
            QTimer.singleShot(delay, lambda idx=i: self.drop_magnet(idx))
        
        # After all magnets dropped (11 seconds), finish sequence
        QTimer.singleShot(11000, self.finish_dropping_sequence)
    
    def drop_magnet(self, index):
        """Turn off magnet at given index and swap colors"""
        magnet_names = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10']
        gpio_pins = [5, 6, 16, 17, 20, 21, 22, 23, 24, 25]
        
        if GPIO_AVAILABLE and index < len(ALL_MAGS):
            ALL_MAGS[index].off()
            print(f"{magnet_names[index]} (GPIO{gpio_pins[index]}) turned OFF")
        
        # Alternate colors: even index = Nittany Blue bg, odd index = White bg
        if index % 2 == 0:
            # Even: Nittany Blue background, White text
            self.dropping_screen.setStyleSheet("background-color: #001E44;")
            self.dropping_label.setStyleSheet("font-weight: bold; font-size: 48px; color: white;")
        else:
            # Odd: White background, Nittany Blue text
            self.dropping_screen.setStyleSheet("background-color: white;")
            self.dropping_label.setStyleSheet("font-weight: bold; font-size: 48px; color: #001E44;")
    
    def finish_dropping_sequence(self):
        """Finish the dropping sequence and return to round screen"""
        # Turn all magnets back on (default state)
        if GPIO_AVAILABLE:
            for i, mag in enumerate(ALL_MAGS):
                mag.on()
            print("✓ All 10 magnets turned back ON")
        
        # Reset dropping screen to white for next time
        self.dropping_screen.setStyleSheet("background-color: white;")
        self.dropping_label.setStyleSheet("font-weight: bold; font-size: 48px; color: #001E44;")
        
        # Go to round screen
        self.switch_to(self.round_screen)
    
    def turn_off_leds(self):
        """Turn off all magnets (called by timer)"""
        if GPIO_AVAILABLE:
            for mag in ALL_MAGS:
                mag.off()
            print("All magnets turned OFF")
    
    def toggle_dev_mode(self):
        """Toggle developer mode on/off"""
        self.dev_mode = not self.dev_mode
        if self.dev_mode:
            self.btn_dev_mode.setText("🔧 Dev Mode: ON")
            self.btn_dev_mode.setStyleSheet("background-color: #00ff00; color: black;")
            self.btn_quick_test.show()
            QMessageBox.information(self, "Developer Mode", "Developer mode enabled!\n\n✓ Quick test button available\n✓ Can override player selection")
        else:
            self.btn_dev_mode.setText("🔧 Dev Mode")
            self.btn_dev_mode.setStyleSheet("")
            self.btn_quick_test.hide()
    
    def quick_test_sequence(self):
        """Quick test - skip directly to GO sequence with test player"""
        # Create or use test player
        if not self.current_player:
            # Try to find existing test player
            players = db.get_all_players()
            test_player = None
            for pid, name, pos, side in players:
                if name == "TEST_PLAYER":
                    test_player = db.get_player_by_id(pid)
                    break
            
            if not test_player:
                # Create test player
                pid = db.create_player("TEST_PLAYER", "DEV", "Offense")
                test_player = db.get_player_by_id(pid)
            
            self.current_player = test_player
        
        # Set default difficulty
        if not self.selected_difficulty:
            self.selected_difficulty = "Medium"
        
        # Skip directly to GO sequence
        self.execute_go_sequence()
    
    def guest_mode_sequence(self):
        """Guest mode - allows anyone to quickly test the system without selecting a player"""
        # Create or use guest player
        players = db.get_all_players()
        guest_player = None
        for pid, name, pos, side in players:
            if name == "GUEST":
                guest_player = db.get_player_by_id(pid)
                break
        
        if not guest_player:
            # Create guest player
            pid = db.create_player("GUEST", "Guest", "Offense")
            guest_player = db.get_player_by_id(pid)
        
        self.current_player = guest_player
        self.selected_difficulty = "Medium"  # Default difficulty for guest
        
        # Show confirmation and go directly to GO sequence
        QMessageBox.information(self, "Guest Mode", "Starting quick test as GUEST\nDifficulty: Medium")
        self.execute_go_sequence()

    def event(self, e):
        if e.type() in (QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate, QEvent.Type.TouchEnd):
            self.handle_touch(e)
            e.accept()
            return True
        return super().event(e)

    def handle_touch(self, event):
        if isinstance(event, QTouchEvent):
            for point in event.points():
                pos = point.position()
                if self.stack.currentWidget() == self.round_screen:
                    for btn in self.round_screen.findChildren(QPushButton):
                        local_pos = btn.mapFrom(self.round_screen, pos.toPoint())
                        if btn.rect().contains(local_pos):
                            # Block re-firing the clicked signal by disabling first
                            btn.setEnabled(False)
                            self.record_round(int(btn.text()))
                            btn.setEnabled(True)
                            break


# qdialog normal can't do more than 1 entry box, making a custom version that takes in name, pos as text and side as dropbox/combobox
class PlayerInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Player Info")

        # Widgets
        self.name_input = QLineEdit()
        self.position_input = QLineEdit()
        self.side_dropdown = QComboBox()
        # O/D/S is what I got from Nayl, can easily switch to just O/D
        self.side_dropdown.addItems(["Offense", "Defense", "Special Teams"])

        # Layout
        layout = QVBoxLayout()

        # Name
        layout.addLayout(self._labeled_input("Name:", self.name_input))
        # Position
        layout.addLayout(self._labeled_input("Position:", self.position_input))
        # Side
        layout.addLayout(self._labeled_input("Side:", self.side_dropdown))

        # Buttons
        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        self.setLayout(layout)

    def _labeled_input(self, label_text, widget):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def get_data(self):
        # returning a dictionary we can parse out above
        return {
            "name": self.name_input.text().strip(),
            "position": self.position_input.text().strip(),
            "side": self.side_dropdown.currentText()
        }

# ==============================
# Run App
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlagApp()
    window.show()
    sys.exit(app.exec())