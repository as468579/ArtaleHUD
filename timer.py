import threading
import time
import winsound

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QSoundEffect

from utils import get_resource_path


class Timer(QObject):
    """Single timer that supports start, stop, pause, resume, toggle"""

    alarm_signal = pyqtSignal()

    def __init__(
        self,
        key,
        name,
        max_sec,
        play_alarm_on_timeout=False,
        is_repeating=False,
    ):
        super().__init__()

        self.key = key  # Hotkey assigned to this timer (e.g., 'f1')
        self.name = name  # Display name
        self.max_sec = max_sec  # Maximum duration in seconds
        self.current_sec = 0  # Current remaining seconds
        self.play_alarm_on_timeout = play_alarm_on_timeout
        self.is_repeating = is_repeating

        self.is_running = False  # True if timer is counting down
        self.is_paused = False  # True if timer is paused
        self._thread = None  # Internal thread for countdown
        self._delta = 0.1

        self._start_time = 0
        self._elapsed_before_pause = 0

        self.alarm = QSoundEffect()
        self.alarm.setSource(QUrl.fromLocalFile(get_resource_path("beep.wav")))
        self.alarm.setVolume(0.8)
        self.alarm_signal.connect(self.alarm.play)

    def reset(self, key, name, max_sec, play_alarm_on_timeout, is_repeating):
        self.key = key  # Hotkey assigned to this timer (e.g., 'f1')
        self.name = name  # Display name
        self.max_sec = max_sec  # Maximum duration in seconds
        self.current_sec = 0  # Current remaining seconds
        self.play_alarm_on_timeout = play_alarm_on_timeout
        self.is_repeating = is_repeating

    def start(self):
        """Start the timer. If the thread doesn't exist, create it."""
        self._elapsed_before_pause = 0
        self._start_time = time.perf_counter()

        self.current_sec = self.max_sec
        self.is_running = True
        self.is_paused = False
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def pause(self):
        """Pause the timer."""
        if self.is_running and not self.is_paused:
            self._elapsed_before_pause += time.perf_counter() - self._start_time
            self._start_time = time.perf_counter()
            self.is_paused = True

    def resume(self):
        """Resume the timer if it was paused."""
        if self.is_running and self.is_paused:
            self._start_time = time.perf_counter()
            self.is_paused = False

    def stop(self):
        """Stop the timer and reset to max_sec."""
        self._elapsed_before_pause = 0
        self._start_time = 0
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
                time.sleep(self._delta)  # High precision countdown
                elapsed = self._elapsed_before_pause + (
                    time.perf_counter() - self._start_time
                )
                self.current_sec = self.max_sec - elapsed

                if self.is_running and self.current_sec < 0:

                    if self.is_repeating:
                        # Auto reset
                        self._start_time = time.perf_counter()
                        self._elapsed_before_pause = 0
                        self.current_sec = self.max_sec

                    # All operation needs to be placed after reset to prevent driff accumulation
                    if self.play_alarm_on_timeout:
                        self.alarm_signal.emit()  # Beep when timer reaches 0

                    if not self.is_repeating:
                        break

            else:
                time.sleep(
                    self._delta
                )  # Sleep while paused to reduce CPU usage

        self.is_running = False
        self.is_paused = False
