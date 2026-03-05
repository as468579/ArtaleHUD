import sys

from PyQt6.QtWidgets import QApplication

from control_panel import ControlPanel
from overlay import UnifiedOverlay

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = UnifiedOverlay()
    panel = ControlPanel(overlay)
    panel.show()
    sys.exit(app.exec())
