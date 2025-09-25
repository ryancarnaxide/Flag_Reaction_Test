import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QGridLayout
)
from PyQt6.QtCore import Qt
import database_setup as db
from datetime import datetime

# ==============================
# Initialize Database
# ==============================
db.setup_database()

# ==============================
# Global State
# ==============================
current_player = None
selected_difficulty = None

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

        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        # Screens
        self.start_screen = self.make_start_screen()
        self.player_screen = self.make_player_screen()
        self.round_screen = self.make_round_screen()
        self.leaderboard_screen = self.make_leaderboard_screen()

        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(self.player_screen)
        self.stack.addWidget(self.round_screen)
        self.stack.addWidget(self.leaderboard_screen)

        self.load_players()
        self.update_leaderboard()
        self.switch_to(self.start_screen)

    # --------------------------
    # Screen Builders
    # --------------------------
    def make_start_screen(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(40, 20, 40, 20)
        vbox.setSpacing(15)

        header = QLabel("Select Player")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; font-size: 22px;")
        vbox.addWidget(header)

        self.player_list = QListWidget()
        self.player_list.setFixedHeight(250)
        vbox.addWidget(self.player_list)

        btn_select = QPushButton("Select Player")
        btn_select.clicked.connect(self.select_player_from_list)
        vbox.addWidget(btn_select)

        btn_create = QPushButton("Create New Account")
        btn_create.clicked.connect(self.create_account)
        vbox.addWidget(btn_create)

        btn_select = QPushButton("Remove Account")
        btn_select.clicked.connect(self.delete_player_from_list)
        vbox.addWidget(btn_select)

        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(self.export_csv)
        vbox.addWidget(btn_export)

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
        vbox.setSpacing(15)

        header = QLabel("Leaderboard (Top 10)")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; font-size: 22px;")
        vbox.addWidget(header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Player", "Difficulty", "Flags"])
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setFixedHeight(300)
        vbox.addWidget(self.table)

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
        return w

    # --------------------------
    # Helper Methods
    # --------------------------
    def switch_to(self, widget):
        self.stack.setCurrentWidget(widget)

    def load_players(self):
        self.player_list.clear()
        players = db.get_all_players()
        for pid, name in players:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.player_list.addItem(item)

    def create_account(self):
        name, ok = QInputDialog.getText(self, "New Account", "Enter your name:")
        if ok and name:
            pid = db.create_player(name)
            if pid is None:
                QMessageBox.warning(self, "Error", "Name already exists.")
                return
            self.load_players()
            self.select_player(pid)

    def select_player_from_list(self):
        item = self.player_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        self.select_player(pid)

    def select_player(self, pid):
        global current_player, selected_difficulty
        player = db.get_player_by_id(pid)
        if player:
            current_player = player
            selected_difficulty = None
            self.player_label.setText(f"Player: {current_player['name']}")
            self.difficulty_label.setText("Selected Mode: None")
            self.switch_to(self.player_screen)

    def choose_difficulty(self, diff):
        global selected_difficulty
        selected_difficulty = diff
        self.difficulty_label.setText(f"Selected Mode: {diff}")

    def start_round(self):
        if not selected_difficulty:
            QMessageBox.warning(self, "No Mode", "Select a difficulty first.")
            return
        self.switch_to(self.round_screen)

    def record_round(self, catches):
        global current_player, selected_difficulty
        if current_player and selected_difficulty is not None:
            db.record_session(current_player['id'], selected_difficulty, catches)
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
    def delete_player_from_list(self):
        # get currently selected player then call delete_player(player_id) to remove their information from database, and reload list
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

    def play_again(self):
        global selected_difficulty
        selected_difficulty = None
        self.difficulty_label.setText("Selected Mode: None")
        self.switch_to(self.player_screen)

    def export_csv(self):
        filename = db.export_to_csv()
        QMessageBox.information(self, "CSV Exported", f"CSV data properly exported as {filename}.\nInsert USB to download latest CSV.")


# ==============================
# Run App
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlagApp()
    window.show()
    sys.exit(app.exec())