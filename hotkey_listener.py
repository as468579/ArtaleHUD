from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyListener(QObject):
    """
    A standalone listener that monitors global key presses and 
    notifies the application via Qt Signals.
    """
    # Define a signal that carries the key in a lower case as a string
    hotkey_pressed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.listener = None

    def start(self):
        """Starts the global keyboard listener in a daemon thread."""
        if self.listener:
            self.stop()

        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.daemon = True
        self.listener.start()

    def stop(self):
        """Stops the active keyboard listener."""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_press(self, key):
        """
        Internal callback for pynput to process key events.
        Designed to work consistently across Windows and macOS.
        """
        try:
            if hasattr(key, "name") and key.name:
                k = key.name
            else:
                k = str(key).strip("'")
            
            # Emit signal to the main thread
            self.hotkey_pressed.emit(k.lower())
        except Exception as e:
            print(f"Hotkey listener error: {e}")
    