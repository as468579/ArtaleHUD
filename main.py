import sys
import threading
import time
import winsound
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QGroupBox, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QRectF, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase
from pynput import keyboard

# =========================
# Global Color Definitions
# =========================

# Panel
PANEL_BG_COLOR = QColor(60, 60, 60, 160)         # Panel background color
PANEL_BORDER_COLOR = QColor(255, 255, 255, 120)  # Panel border color

# Rings
RING_BG_COLOR = QColor(255, 255, 255, 60)  # Background ring color
PROGRESS_ARC_COLOR = QColor(0, 200, 127)   # Progress arc color
PAUSE_ARC_COLOR = QColor(255, 165, 0)      # Pause arc color

# Text
TIMER_TEXT_COLOR = QColor(255, 255, 255)   # Center text color

# Stroke Sizes
RING_PEN_WIDTH = 10
BORDER_PEN_WIDTH = 1
NAME_FONT_SIZE = 13
SEC_FONT_SIZE = 15
BUTTON_FONT_SIZE = 14

class Timer:
    """Single timer that supports start, stop, pause, resume, toggle"""
    def __init__(self, key, name, max_sec):
        self.key = key                # Hotkey assigned to this timer (e.g., 'f1')
        self.name = name              # Display name
        self.max_sec = max_sec        # Maximum duration in seconds
        self.current_sec = 0          # Current remaining seconds

        self.is_running = False       # True if timer is counting down
        self.is_paused = False        # True if timer is paused
        self._thread = None           # Internal thread for countdown
        self._delta = 0.1

    def start(self):
        """Start the timer. If the thread doesn't exist, create it."""
        self.current_sec = self.max_sec
        self.is_running = True
        self.is_paused = False
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def pause(self):
        """Pause the timer."""
        if self.is_running and not self.is_paused:
            self.is_paused = True

    def resume(self):
        """Resume the timer if it was paused."""
        if self.is_running and self.is_paused:
            self.is_paused = False

    def stop(self):
        """Stop the timer and reset to max_sec."""
        self.is_running = False
        self.is_paused = False
        self.current_sec = self._delta

    def toggle(self):
        """Toggle between pause and resume (or start if not running)."""
        if self.is_running:
            if self.is_paused:
                self.resume()
            else:
                self.pause()
        else:
            self.start()

    # -------- Internal Thread Logic --------
    def _run(self):
        """Internal countdown logic running in a separate thread."""
        while self.is_running and self.current_sec > 0:
            if not self.is_paused:
                time.sleep(self._delta)          # High precision countdown
                self.current_sec -= self._delta
                if self.current_sec < 0:
                    winsound.Beep(800, 300)   # Beep when timer reaches 0
                    self.current_sec = self.max_sec  # Auto-reset to max_sec
            else:
                time.sleep(self._delta)          # Sleep while paused to reduce CPU usage
        self.is_running = False
        self.is_paused = False

class UnifiedOverlay(QWidget):
    """A single transparent window that contains multiple circular timers."""
    def __init__(self):
        super().__init__()
        self.timers_list = [] # List of Timer objects
        self.dragging = False
        self.old_pos = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Internal timer to refresh the UI smoothly (60 FPS)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update)
        self.refresh_timer.start(16) 

        self.font_family = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont("fonts/Noto_Sans_TC/static/NotoSansTC-ExtraBold.ttf"))[0]
        
        # Move window to (100, 100) and set its size to 450 (width) x 180 (height)
        self.setGeometry(100, 100, 450, 180)

        self.circle_width = 100
        self.spacing = 40

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw a subtle background for the entire panel
        # painter.setBrush(PANEL_BG_COLOR)
        # painter.setPen(QPen(PANEL_BORDER_COLOR, BORDER_PEN_WIDTH))

        painter.setBrush(PANEL_BG_COLOR)

        pen = QPen(PANEL_BORDER_COLOR, BORDER_PEN_WIDTH)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # radius = min(self.width(), self.height()) * 0.1
        radius = 25
        margin = max(1, int(radius / 2))
        painter.drawRoundedRect(self.rect().adjusted(margin,margin,-margin,-margin), radius, radius)

        num_timers = len(self.timers_list)
        total_width = num_timers * self.circle_width + (num_timers - 1) * self.spacing
        start_x = (self.width() - total_width) // 2

        for i, timer in enumerate(self.timers_list):
            # Calculate position for each circle
            x_offset = start_x + (i * (self.circle_width + self.spacing))
            rect = QRectF(x_offset, (self.height()-self.circle_width) // 2 , self.circle_width, self.circle_width)

            # 1. Background Ring
            painter.setPen(QPen(RING_BG_COLOR, RING_PEN_WIDTH))
            painter.drawEllipse(rect)

            # 2. Progress Arc
            if timer.is_running and timer.max_sec > 0:
                progress = (timer.current_sec / timer.max_sec) * 360
                pen = QPen(PAUSE_ARC_COLOR if timer.is_paused else PROGRESS_ARC_COLOR, RING_PEN_WIDTH)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawArc(rect, 90 * 16, int(-progress * 16))

            # 3. Center Text
            number_rect = rect.adjusted(0, -15, 0, -15)
            painter.setPen(TIMER_TEXT_COLOR)
            painter.setFont(QFont("Arial", SEC_FONT_SIZE, QFont.Weight.Bold))
            if not timer.is_running:
                text = "OFF"
            elif timer.is_paused:
                text = "PAUSE"
            else:
                text = f"{int(timer.current_sec)}s"

            painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, text)

            # 4. Label
            name_rect = rect.adjusted(0, 25, 0, 0)
            painter.setFont(QFont(self.font_family, NAME_FONT_SIZE, QFont.Weight.Bold))
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, timer.name)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            curr_pos = event.position()

            # Check if the click is on any timer circle
            num_timers = len(self.timers_list)
            total_width = num_timers * self.circle_width + (num_timers - 1) * self.spacing
            start_x = (self.width() - total_width) // 2

            for i, timer in enumerate(self.timers_list):
                x_offset = start_x + (i * (self.circle_width + self.spacing))
                rect = QRectF(x_offset, (self.height() - self.circle_width) // 2, self.circle_width, self.circle_width)
                if rect.contains(curr_pos):
                    timer.toggle()  # Toggle the timer (pause/resume) when clicked
                    return          # Stop checking after the first timer that was clicked

            self.dragging = True
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragging:
            # Move the overlay by the calculated offset
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.dragging = False

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
        for key in ['F1', 'F2', 'F3', 'F4']:
            group = QGroupBox(f"Hotkey {key}")
            g_layout = QFormLayout()
            name_in = QLineEdit(); name_in.setText(f"{key}")
            sec_in = QLineEdit(); sec_in.setText("60")
            g_layout.addRow("Name:", name_in)
            g_layout.addRow("Inerval (sec):", sec_in)
            self.inputs[key.lower()] = {"name": name_in, "sec": sec_in}
            group.setLayout(g_layout)
            layout.addWidget(group)

        self.apply_btn = QPushButton("Reset && Stop Timers")
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.clicked.connect(self.setup_overlay)

        self.apply_btn.setStyleSheet("""
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
        """)
        
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
                sec = int(fields["sec"].text())
                self.overlay.timers_list.append(Timer(key, fields["name"].text(), sec))
            except: continue
        
        # Adjust overlay width based on number of timers
        num_timers = len(self.overlay.timers_list)
        new_width = 2 * self.overlay.spacing + (num_timers * self.overlay.circle_width + (num_timers-1) * self.overlay.spacing)
        self.overlay.setFixedWidth(max(new_width, 150))
        self.overlay.show()
        
        if self.hotkey_listener: self.hotkey_listener.stop()
        self.start_listener()

    def stop_all(self):
        for timer in self.overlay.timers_list:
            timer.stop()

    def start_listener(self):
        def on_press(key):
            try: k = key.fkey.name if hasattr(key, 'fkey') else key.name
            except: return
            for timer in self.overlay.timers_list:
                if timer.key == k.lower():
                    timer.start()

        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = UnifiedOverlay()
    panel = ControlPanel(overlay)
    panel.show()
    sys.exit(app.exec())