from pynput import keyboard
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from timer import Timer

# =========================
# Colors & Styles
# =========================

# Button
BUTTON_FONT_SIZE = 14


class ControlPanel(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.hotkey_listener = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Artale Unified Control")
        self.setGeometry(600, 100, 320, 500)
        layout = QVBoxLayout()

        self.inputs = {}
        for key in ["F1", "F2", "F3", "F4"]:
            group = QGroupBox(f"Hotkey {key}")
            g_layout = QFormLayout()
            name_in = QLineEdit()
            name_in.setText(f"{key}")
            sec_in = QLineEdit()
            sec_in.setText("60")
            playalarm_checkbox = QCheckBox("Play alarm on timeout")
            playalarm_checkbox.setChecked(False)
            g_layout.addRow("Name:", name_in)
            g_layout.addRow("Inerval (sec):", sec_in)
            g_layout.addRow("", playalarm_checkbox)
            self.inputs[key.lower()] = {
                "name": name_in,
                "sec": sec_in,
                "play alarm": playalarm_checkbox,
            }
            group.setLayout(g_layout)
            layout.addWidget(group)

        self.apply_btn = QPushButton("Reset && Stop Timers")
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.clicked.connect(self.setup_overlay)

        self.apply_btn.setStyleSheet(
            """
            QPushButton {
                background-color: black;   /* 黑底 */
                color: white;              /* 白字 */
                border-radius: 10px;       /* 圓角，可選 */
                border: 2px solid white;   /* 白色邊框，可選 */
            }
            QPushButton:hover {
                background-color: #444444; /* 滑鼠經過，稍亮 */
            }
            QPushButton:pressed {
                background-color: #999999; /* 點擊效果，更亮 */
            }
        """
        )

        # self.stop_btn = QPushButton("Stop All Timers")
        # self.stop_btn.setFixedHeight(40)
        # self.stop_btn.clicked.connect(self.stop_all)

        font = QFont("Arial", BUTTON_FONT_SIZE, QFont.Weight.Bold)
        self.apply_btn.setFont(font)

        layout.addWidget(self.apply_btn)
        # layout.addWidget(self.stop_btn)
        self.setLayout(layout)

    def setup_overlay(self):
        self.stop_all()
        self.overlay.timers_list = []
        for key, fields in self.inputs.items():
            try:
                name = fields["name"].text()
                sec = int(fields["sec"].text())
                play_alarm_on_timeout = fields["play alarm"].isChecked()
                self.overlay.timers_list.append(
                    Timer(key, name, sec, play_alarm_on_timeout)
                )
            except:
                continue

        # Adjust overlay width based on number of timers
        num_timers = len(self.overlay.timers_list)
        new_width = 2 * self.overlay.spacing + (
            num_timers * self.overlay.circle_width
            + (num_timers - 1) * self.overlay.spacing
        )
        self.overlay.setFixedWidth(max(new_width, 150))
        self.overlay.show()

        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.start_listener()

    def stop_all(self):
        for timer in self.overlay.timers_list:
            timer.stop()

    def start_listener(self):
        def on_press(key):
            try:
                k = key.fkey.name if hasattr(key, "fkey") else key.name
            except:
                return
            for timer in self.overlay.timers_list:
                if timer.key == k.lower():
                    timer.start()

        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()
