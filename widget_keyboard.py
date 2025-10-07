from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

class VirtualKeyboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        keys = [
            ['1','2','3','4','5','6','7','8','9','0'],
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['Z','X','C','V','B','N','M','Backspace'],
            ['Space']
        ]

        for row, line in enumerate(keys):
            for col, key in enumerate(line):
                btn = QPushButton(" " if key == "Space" else key)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                btn.clicked.connect(lambda _, k=key: self.send_key(k))
                if key == "Space":
                    layout.addWidget(btn, row, 0, 1, len(line))
                else:
                    layout.addWidget(btn, row, col)

    def send_key(self, key):
        widget = QApplication.focusWidget()
        if not widget:
            return

        if key == "Backspace":
            event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        elif key == "Space":
            event = QKeyEvent(QKeyEvent.Type.KeyPress, 0, Qt.KeyboardModifier.NoModifier, " ")
        else:
            event = QKeyEvent(QKeyEvent.Type.KeyPress, 0, Qt.KeyboardModifier.NoModifier, key)
        QApplication.postEvent(widget, event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.edit = QLineEdit()
        layout.addWidget(self.edit)
        self.keyboard = VirtualKeyboard()
        layout.addWidget(self.keyboard)

app = QApplication([])
window = MainWindow()
window.setWindowTitle("PyQt6 Virtual Keyboard (Python-based)")
window.show()
app.exec()