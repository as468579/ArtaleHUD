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

# def show_license():
#     """
#     Reads the LICENSE.txt file and displays it in a modal dialog.
#     Ensures users are aware of the Non-Commercial Clause before use.
#     """
#     # Get the correct path for the license file, compatible with PyInstaller
#     license_path = get_resource_path("LICENSE.txt")

#     license_content = "License file not found."
#     if os.path.exists(license_path):
#         try:
#             with open(license_path, "r", encoding="utf-8") as f:
#                 license_content = f.read()
#         except Exception as e:
#             license_content = f"Error reading license: {e}"

#     # Create and configure the message box
#     msg = QMessageBox()
#     msg.setWindowTitle("License Agreement")
#     msg.setText("Software Terms and Conditions")

#     # Using informative text for the long license content
#     msg.setInformativeText(license_content)
#     msg.setStandardButtons(QMessageBox.StandardButton.Ok)
#     msg.setIcon(QMessageBox.Icon.Information)
#     # msg.setStyleSheet("QLabel{min-width: 300px;}")
#     msg.exec()


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

    # Show the license dialog before launching the main UI [cite: 4]
    # show_license()

    dialog = LicenseDialog()
    if dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    overlay = UnifiedOverlay()
    panel = ControlPanel(overlay)
    panel.show()

    sys.exit(app.exec())
