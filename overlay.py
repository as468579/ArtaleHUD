import sys

from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from timer import Timer
from utils import get_resource_path

# =========================
# Colors & Styles
# =========================

# Panel
PANEL_BG_COLOR = QColor(60, 60, 60, 160)  # Panel background color
PANEL_BORDER_COLOR = QColor(255, 255, 255, 120)  # Panel border color

# Rings
RING_BG_COLOR = QColor(255, 255, 255, 60)  # Background ring color
PROGRESS_START_ARC_COLOR = QColor(0, 200, 127)  # Progress arc color
PROGRESS_COMPLETE_ARC_COLOR = QColor(255, 60, 60)  # Red color for near end
PAUSE_ARC_COLOR = QColor(255, 165, 0)  # Pause arc color

# Text
TIMER_TEXT_COLOR = QColor(255, 255, 255)  # Center text color

# Stroke Sizes
RING_PEN_WIDTH = 10
BORDER_PEN_WIDTH = 1
NAME_FONT_SIZE = 13
SEC_FONT_SIZE = 15


class UnifiedOverlay(QWidget):
    """A single transparent window that contains multiple circular timers."""

    def __init__(self):
        super().__init__()
        self.timers_list = []  # List of Timer objects
        self.dragging = False
        self.old_pos = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Ensure the window remains visible on macOS when the app loses focus
        if sys.platform == "darwin":
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

        # Internal timer to refresh the UI smoothly (60 FPS)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update)
        self.refresh_timer.start(16)

        self.font_family = QFontDatabase.applicationFontFamilies(
            QFontDatabase.addApplicationFont(
                get_resource_path(
                    "fonts/Noto_Sans_TC/static/NotoSansTC-ExtraBold.ttf"
                )
            )
        )[0]

        # Move window to (100, 100) and set its size to 450 (width) x 180 (height)
        self.setGeometry(100, 100, 450, 180)

        self.circle_width = 100
        self.spacing = 40

    def get_dynamic_color(self, ratio):
        """Calculates color based on ratio: Green(1.0) -> Orange(0.5) -> Red(0.0)"""
        if ratio > 0.5:
            # Interpolate between Orange (at 0.5) and Green (at 1.0)
            t = (ratio - 0.5) * 2  # Normalize to 0.0 - 1.0
            r = int(
                PAUSE_ARC_COLOR.red() * (1 - t)
                + PROGRESS_START_ARC_COLOR.red() * t
            )
            g = int(
                PAUSE_ARC_COLOR.green() * (1 - t)
                + PROGRESS_START_ARC_COLOR.green() * t
            )
            b = int(
                PAUSE_ARC_COLOR.blue() * (1 - t)
                + PROGRESS_START_ARC_COLOR.blue() * t
            )
        else:
            # Interpolate between Red (at 0.0) and Orange (at 0.5)
            t = ratio * 2  # Normalize to 0.0 - 1.0
            r = int(
                PROGRESS_COMPLETE_ARC_COLOR.red() * (1 - t)
                + PAUSE_ARC_COLOR.red() * t
            )
            g = int(
                PROGRESS_COMPLETE_ARC_COLOR.green() * (1 - t)
                + PAUSE_ARC_COLOR.green() * t
            )
            b = int(
                PROGRESS_COMPLETE_ARC_COLOR.blue() * (1 - t)
                + PAUSE_ARC_COLOR.blue() * t
            )
        return QColor(r, g, b)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(PANEL_BG_COLOR)
        pen = QPen(PANEL_BORDER_COLOR, BORDER_PEN_WIDTH)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # radius = min(self.width(), self.height()) * 0.1
        radius = 25
        margin = max(1, int(radius / 2))
        painter.drawRoundedRect(
            self.rect().adjusted(margin, margin, -margin, -margin),
            radius,
            radius,
        )

        num_timers = len(self.timers_list)
        total_width = (
            num_timers * self.circle_width + (num_timers - 1) * self.spacing
        )
        start_x = (self.width() - total_width) // 2

        for i, timer in enumerate(self.timers_list):
            # Calculate position for each circle
            x_offset = start_x + (i * (self.circle_width + self.spacing))
            rect = QRectF(
                x_offset,
                (self.height() - self.circle_width) // 2,
                self.circle_width,
                self.circle_width,
            )

            # 1. Background Ring
            painter.setPen(QPen(RING_BG_COLOR, RING_PEN_WIDTH))
            painter.drawEllipse(rect)

            # 2. Progress Arc
            if timer.is_running and timer.max_sec > 0:
                ratio = timer.current_sec / timer.max_sec
                progress = (timer.current_sec / timer.max_sec) * 360

                # Use pause color if paused, otherwise use dynamic gradient
                if timer.is_paused:
                    arc_color = PAUSE_ARC_COLOR
                else:
                    arc_color = self.get_dynamic_color(ratio)

                pen = QPen(arc_color, RING_PEN_WIDTH)
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
            painter.setFont(
                QFont(self.font_family, NAME_FONT_SIZE, QFont.Weight.Bold)
            )
            painter.drawText(
                name_rect, Qt.AlignmentFlag.AlignCenter, timer.name
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            curr_pos = event.position()

            # Check if the click is on any timer circle
            num_timers = len(self.timers_list)
            total_width = (
                num_timers * self.circle_width + (num_timers - 1) * self.spacing
            )
            start_x = (self.width() - total_width) // 2

            for i, timer in enumerate(self.timers_list):
                x_offset = start_x + (i * (self.circle_width + self.spacing))
                rect = QRectF(
                    x_offset,
                    (self.height() - self.circle_width) // 2,
                    self.circle_width,
                    self.circle_width,
                )
                if rect.contains(curr_pos):
                    timer.toggle()  # Toggle the timer (pause/resume) when clicked
                    return  # Stop checking after the first timer that was clicked

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
