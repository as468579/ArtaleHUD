import os
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from control_panel import ControlPanel
from overlay import UnifiedOverlay
from utils import get_resource_path
from hotkey_listener import HotkeyListener

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("License Agreement")
        self.resize(800, 640)
        layout = QVBoxLayout(self)

        # License text viewer
        self.text = QTextBrowser()
        self.text.setReadOnly(True)

        font = QFont("Consolas")
        font.setPointSize(11)
        self.text.setFont(font)

        self.text.setStyleSheet(
            """
            QTextBrowser {
                padding: 16px;
                border: 1px solid #cccccc;
            }
        """
        )

        # Load license file
        try:
            with open(
                get_resource_path("LICENSE.txt"), "r", encoding="utf-8"
            ) as f:
                self.text.setPlainText(f.read())
        except FileNotFoundError:
            self.text.setPlainText("License file not found.")

        layout.addWidget(self.text)

        # Buttons
        button_layout = QHBoxLayout()

        self.accept_btn = QPushButton("Accept")
        self.decline_btn = QPushButton("Decline")

        # Accept button disabled until conditions are met
        self.accept_btn.setEnabled(False)

        self.accept_btn.clicked.connect(self.accept)
        self.decline_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.accept_btn)
        button_layout.addWidget(self.decline_btn)

        layout.addLayout(button_layout)

        # Detect scroll position
        scrollbar = self.text.verticalScrollBar()
        scrollbar.valueChanged.connect(self._check_scroll)

        # Enable Accept if the content fits without scrolling
        if scrollbar.maximum() <= 0:
            self.accept_btn.setEnabled(True)

    def _check_scroll(self):
        """Enable Accept button when scrolled to bottom."""
        scrollbar = self.text.verticalScrollBar()

        if scrollbar.value() == scrollbar.maximum():
            self.accept_btn.setEnabled(True)

    def closeEvent(self, event):
        """Treat window close as rejection."""
        self.reject()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Show the license dialog before launching the main UI
    dialog = LicenseDialog()
    hotkey_listener = HotkeyListener()

    # On macOS, start listening before dialog.exec() because pynput's listener
    # thread may conflict with Qt's event loop during initialization.
    if sys.platform == "darwin":
        hotkey_listener.start()

    if dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    # On Windows, start listening after the dialog is completed
    if sys.platform == "win32":
        hotkey_listener = HotkeyListener()
        hotkey_listener.start()        

    overlay = UnifiedOverlay()
    panel = ControlPanel(overlay, hotkey_listener)

    overlay.show()
    panel.show()

    sys.exit(app.exec())
