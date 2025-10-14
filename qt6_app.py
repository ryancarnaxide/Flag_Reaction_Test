import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QGridLayout, QLineEdit, QFileDialog, QDialog, QComboBox
)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QTouchEvent
import database_setup as db

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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
        self.setGeometry(150, 150, 700, 550)
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

        
        # global values as object oriented attributes
        self.current_player = None
        self.selected_difficulty = None
        self.admin_password = 'dan5171'

        self.load_players()
        self.update_leaderboard()
        self.switch_to(self.start_screen)
        self.switch_to_player_mode()

    # --------------------------
    # Screen Builders
    # --------------------------
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
        self.btn_view.show()
        self.btn_export.show()
        self.btn_import.show()
        self.btn_logout.show()

        # Toggle or change header
        self.header_label.setText("Admin Panel")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 22px; color: orange;")

    def switch_to_player_mode(self):
        self.btn_login_admin.show()
        self.btn_select.show()
        self.btn_create.hide()
        self.btn_delete.hide()
        self.btn_view.hide()
        self.btn_export.hide()
        self.btn_import.hide()
        self.btn_logout.hide()

        # Toggle or change header
        self.header_label.setText("Select Player")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 22px; color: white;")

    def update_countdown(self):
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.countdown_label.setText(f"Starting in {self.countdown_value}")
        else:
            self.timer.stop()
            self.switch_to(self.go_screen)
            QTimer.singleShot(1000, lambda: self.switch_to(self.round_screen))

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