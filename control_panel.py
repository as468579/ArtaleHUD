import json
import os

from pynput import keyboard
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
        self.presets = self.load_presets()
        self.init_ui()

    def load_presets(self):
        """
        Load preset timer configurations from a JSON file.
        Returns a dictionary of presets.
        """
        file_path = "presets.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load presets: {e}")

        # Default fallback data if file is missing or corrupted
        return {
            "重複計時器": {"sec": "60", "play alarm": False, "repeat": True}
        }

    def init_ui(self):
        self.setWindowTitle("Artale Unified Control")
        self.setGeometry(600, 100, 320, 500)
        layout = QVBoxLayout()

        self.inputs = {}
        for key in ["F1", "F2", "F3", "F4"]:
            group = QGroupBox(f"Hotkey {key}")
            g_layout = QFormLayout()

            name_combo = QComboBox()
            # Allows users to type custom names not present in the dropdown list
            name_combo.setEditable(True)
            name_combo.addItems(list(self.presets.keys()))

            sec_in = QLineEdit()
            playalarm_checkbox = QCheckBox("Play alarm on timeout")
            repeat_checkbox = QCheckBox("Repeat this timer")

            # Connect signal to update other fields when a preset is selected
            # Use a lambda to pass the specific hotkey key to the handler
            name_combo.currentTextChanged.connect(
                lambda text, ky=key.lower(): self.on_preset_changed(ky, text)
            )

            g_layout.addRow("Name:", name_combo)
            g_layout.addRow("Inerval (sec):", sec_in)
            g_layout.addRow("", playalarm_checkbox)
            g_layout.addRow("", repeat_checkbox)

            self.inputs[key.lower()] = {
                "combo": name_combo,
                "sec": sec_in,
                "play alarm": playalarm_checkbox,
                "repeat": repeat_checkbox,
            }

            # Trigger initial fill-in based on the first item in the combo box
            self.on_preset_changed(key.lower(), name_combo.currentText())

            group.setLayout(g_layout)
            layout.addWidget(group)

        self.apply_btn = QPushButton("Configure && Reset All Timers")
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.clicked.connect(self.setup_overlay)

        self.apply_btn.setStyleSheet(
            """
            QPushButton {
                background-color: black; 
                color: white;
                border-radius: 10px;
                border: 2px solid white;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #999999;
            }
        """
        )

        self.apply_btn.setFont(
            QFont("Arial", BUTTON_FONT_SIZE, QFont.Weight.Bold)
        )

        layout.addWidget(self.apply_btn)
        self.setLayout(layout)

        # Initialize overlay settings on startup
        self.setup_overlay()

    def on_preset_changed(self, key, text):
        """
        Automatically fill in Interval, Alarm, and Repeat fields
        when a matching preset name is selected or typed.
        """
        if text in self.presets:
            data = self.presets[text]
            fields = self.inputs[key]
            fields["sec"].setText(str(data.get("sec", "60")))
            fields["play alarm"].setChecked(data.get("play alarm", False))
            fields["repeat"].setChecked(data.get("repeat", True))

    def setup_overlay(self):
        """
        Apply current UI settings to the overlay and restart hotkey listener.
        """
        self.stop_all()
        self.overlay.timers_list = []
        for key, fields in self.inputs.items():
            try:
                name = fields["combo"].currentText()
                sec = int(fields["sec"].text())
                play_alarm_on_timeout = fields["play alarm"].isChecked()
                is_repeating = fields["repeat"].isChecked()

                # Only add timers that have a name
                if name.strip():
                    self.overlay.timers_list.append(
                        Timer(
                            key, name, sec, play_alarm_on_timeout, is_repeating
                        )
                    )
            except:
                # Skip if interval is not a valid integer
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
                    timer.stop()
                    fields = self.inputs[timer.key]
                    timer.reset(
                        timer.key,
                        fields["combo"].currentText(),
                        int(fields["sec"].text()),
                        fields["play alarm"].isChecked(),
                        fields["repeat"].isChecked(),
                    )
                    timer.start()

        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()
