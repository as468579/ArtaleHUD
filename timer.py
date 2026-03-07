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

        self._next_time = 0  # The exact 'time.perf_counter()' when timer hits 0
        self._remaining_at_pause = 0  # Seconds left when the timer was paused

        self.alarm = QSoundEffect()
        self.alarm.setSource(QUrl.fromLocalFile(get_resource_path("beep.wav")))
        self.alarm.setVolume(0.8)
        self.alarm_signal.connect(self.alarm.play)

    def reset(self, key, name, max_sec, play_alarm_on_timeout, is_repeating):
        """Reset timer configurations."""
        self.stop()

        self.key = key  # Hotkey assigned to this timer (e.g., 'f1')
        self.name = name  # Display name
        self.max_sec = max_sec  # Maximum duration in seconds
        self.current_sec = 0  # Current remaining seconds
        self.play_alarm_on_timeout = play_alarm_on_timeout
        self.is_repeating = is_repeating

    def start(self):
        """Start the timer. If the thread doesn't exist, create it."""
        self._next_time = time.perf_counter() + self.max_sec
        self._remaining_at_pause = 0
        self.current_sec = self.max_sec
        self.is_running = True
        self.is_paused = False

        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def pause(self):
        """Pause the timer."""
        if self.is_running and not self.is_paused:
            self._remaining_at_pause = self._next_time - time.perf_counter()
            self.is_paused = True

    def resume(self):
        """Resume the timer if it was paused."""
        if self.is_running and self.is_paused:
            self._next_time = time.perf_counter() + self._remaining_at_pause
            self._remaining_at_pause = 0
            self.is_paused = False

    def stop(self):
        """Stop the timer and reset to max_sec."""
        self._next_time = 0
        self._remaining_at_pause = 0
        self.is_running = False
        self.is_paused = False
        self.current_sec = 0

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
        while self.is_running:
            if not self.is_paused:
                self.current_sec = self._next_time - time.perf_counter()

                # Check if timer has expired
                if self.current_sec <= 0:
                    if self.play_alarm_on_timeout:
                        self.alarm_signal.emit()

                    if self.is_repeating:
                        # IMPORTANT: Increment the next timestamp by max_sec.
                        # Do NOT use 'time.perf_counter() + max_sec' here,
                        # because adding to the old target fixes any loop processing delays.
                        self._next_time += self.max_sec
                        self._remaining_at_pause = 0

                    else:
                        self.current_sec = 0
                        self.is_running = False
                        break

            time.sleep(self._delta)

        self.is_running = False
        self.is_paused = False
