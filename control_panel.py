import json
import os
import sys

from pynput import keyboard
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent
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
from utils import get_resource_path

# =========================
# Colors & Styles
# =========================

# Button
BUTTON_FONT_SIZE = 14


class HotkeySetterButton(QPushButton):
    changed = pyqtSignal(str)

    QT_TO_PYNPUT = {
        Qt.Key.Key_Control: "ctrl" if sys.platform != "darwin" else "cmd",
        Qt.Key.Key_Shift: "shift",
        Qt.Key.Key_Alt: "alt",
        Qt.Key.Key_Meta: "cmd" if sys.platform != "darwin" else "ctrl",
        Qt.Key.Key_Space: "space",
        Qt.Key.Key_Enter: "enter",
        Qt.Key.Key_Return: "enter",
        Qt.Key.Key_Tab: "tab",
        Qt.Key.Key_Escape: "esc",
        Qt.Key.Key_Backspace: "backspace",
        Qt.Key.Key_Delete: "delete",
        Qt.Key.Key_Insert: "insert",
        Qt.Key.Key_Home: "home",
        Qt.Key.Key_End: "end",
        Qt.Key.Key_PageUp: "page_up",
        Qt.Key.Key_PageDown: "page_down",
        Qt.Key.Key_Up: "up",
        Qt.Key.Key_Down: "down",
        Qt.Key.Key_Left: "left",
        Qt.Key.Key_Right: "right",
        Qt.Key.Key_CapsLock: "caps_lock",
        Qt.Key.Key_NumLock: "num_lock",
        Qt.Key.Key_ScrollLock: "scroll_lock",
        Qt.Key.Key_Print: "print_screen",
        Qt.Key.Key_Pause: "pause",
        Qt.Key.Key_Backslash: "\\",
    }

    def __init__(self, default_key="None"):
        super().__init__(default_key.upper())
        self.setCheckable(True)
        self.key = default_key.lower()
        self.set_idle_style()
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        if self.isChecked():
            self.setText("Press any key...")
            self.setStyleSheet(
                "background-color: #800000; color: white; border: 2px solid #FF4444;"
            )
            self.grabKeyboard()
        else:
            self.set_idle_style()

    def set_idle_style(self):
        self.releaseKeyboard()
        self.setChecked(False)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #333333; color: #00FF00; border: 1px solid #555555;
                font-family: 'Segoe UI', Arial; font-weight: bold;
            }
            QPushButton:hover { background-color: #444444; }
        """
        )

    def keyPressEvent(self, event: QKeyEvent):
        if self.isChecked():
            try:
                qt_key = event.key()

                # Handle Function Keys (F1-F12)
                if Qt.Key.Key_F1 <= qt_key <= Qt.Key.Key_F12:
                    key_text = f"f{qt_key - Qt.Key.Key_F1 + 1}"

                # Handle Special Keys (Ctrl, Alt, Shift, etc.)
                elif qt_key in self.QT_TO_PYNPUT:
                    key_text = self.QT_TO_PYNPUT[qt_key]

                # Handle Standard Characters
                else:
                    key_text = event.text()

                if key_text:
                    key_text = key_text.lower()
                    self.key = key_text
                    self.setText(key_text.upper())
                    self.changed.emit(key_text)
                    self.set_idle_style()
                else:
                    self.set_idle_style()

            except Exception as e:
                # Catch any unexpected errors during key processing to prevent UI crashes
                self.set_idle_style()


class ControlPanel(QWidget):
    def __init__(self, overlay, hotkey_listener):
        super().__init__()
        self.overlay = overlay
        self.hotkey_listener = hotkey_listener
        self.hotkey_listener.hotkey_pressed.connect(self.handle_hotkey_signal)

        # Load both preset database and initial configuration
        self.presets = self.load_json(get_resource_path("presets.json"), {})
        self.defaults = self.load_json(
            get_resource_path("panel_defaults.json"), []
        )

        self.init_ui()

    def handle_hotkey_signal(self, key):
        """
        Processes the key press event. This slot runs on the Main Thread,
        ensuring thread-safe updates to UI and QTimers.
        """
        for index, field in enumerate(self.inputs):
            if field["hotkey_btn"].key == key:
                timer = self.overlay.timers_list[index]
                timer.stop()
                try:
                    # Fetch latest parameters from UI fields
                    name = field["combo"].currentText()
                    sec = int(field["sec"].text())
                    play_alarm = field["play alarm"].isChecked()
                    repeat = field["repeat"].isChecked()

                    # Reset and restart the specific timer
                    timer.reset(timer.key, name, sec, play_alarm, repeat)
                    timer.start()
                except (ValueError, KeyError):
                    # Handle invalid inputs gracefully
                    continue

    def load_json(self, filename, default_val):
        """Helper to load JSON data with a fallback."""
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        return default_val

    def init_ui(self):
        self.setWindowTitle("Artale Unified Control")
        self.setGeometry(600, 100, 320, 500)
        layout = QVBoxLayout()

        self.inputs = []
        hotkeys = self.defaults.get("hotkeys", ["F1", "F2", "F3", "F4"])
        for index, key in enumerate(hotkeys):
            key = key.lower()
            group = QGroupBox(f"Timer {index+1}")
            g_layout = QFormLayout()

            hotkey_btn = HotkeySetterButton(key)

            # Load initial values from panel_default.json if available
            try:
                field = self.defaults.get("fields", [])[index]
            except IndexError:
                field = {}

            name_combo = QComboBox()
            # Allows users to type custom names not present in the dropdown list
            name_combo.setEditable(True)
            name_combo.addItems(list(self.presets.keys()))
            name_combo.setCurrentText(field.get("name", key))

            sec_in = QLineEdit()
            sec_in.setText(str(field.get("sec", "60")))

            playalarm_checkbox = QCheckBox("Play alarm on timeout")
            playalarm_checkbox.setChecked(field.get("play alarm", False))

            repeat_checkbox = QCheckBox("Repeat this timer")
            repeat_checkbox.setChecked(field.get("repeat", False))

            # Connect signal to update other fields when a preset is selected
            name_combo.currentTextChanged.connect(
                lambda text, idx=index: self.on_preset_changed(idx, text)
            )

            g_layout.addRow("Hotkey:", hotkey_btn)
            g_layout.addRow("Name:", name_combo)
            g_layout.addRow("Inerval (sec):", sec_in)
            g_layout.addRow("", playalarm_checkbox)
            g_layout.addRow("", repeat_checkbox)

            self.inputs.append(
                {
                    "hotkey_btn": hotkey_btn,
                    "combo": name_combo,
                    "sec": sec_in,
                    "play alarm": playalarm_checkbox,
                    "repeat": repeat_checkbox,
                }
            )

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

    def on_preset_changed(self, index, text):
        """
        Automatically fill in Interval, Alarm, and Repeat fields
        when a matching preset name is selected or typed.
        """
        if text in self.presets:
            data = self.presets[text]
            fields = self.inputs[index]
            fields["sec"].setText(str(data.get("sec", "60")))
            fields["play alarm"].setChecked(data.get("play alarm", False))
            fields["repeat"].setChecked(data.get("repeat", False))

    def setup_overlay(self):
        """
        Apply current UI settings to the overlay and restart hotkey listener.
        """
        self.stop_all()
        self.overlay.timers_list = []
        for fields in self.inputs:
            key = fields["hotkey_btn"].key
            name = fields["combo"].currentText()
            if not name.strip():
                name = "Unknown"

            try:
                sec = int(fields["sec"].text())
            except (ValueError, TypeError):
                sec = 60

            play_alarm_on_timeout = fields["play alarm"].isChecked()
            is_repeating = fields["repeat"].isChecked()

            self.overlay.timers_list.append(
                Timer(key, name, sec, play_alarm_on_timeout, is_repeating)
            )

        # Adjust overlay width based on number of timers
        num_timers = len(self.overlay.timers_list)
        new_width = 2 * self.overlay.spacing + (
            num_timers * self.overlay.circle_width
            + (num_timers - 1) * self.overlay.spacing
        )
        self.overlay.setFixedWidth(max(new_width, 150))

    def stop_all(self):
        for timer in self.overlay.timers_list:
            timer.stop()
