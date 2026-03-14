import os
import sys

from PyQt6.QtGui import QFontDatabase


def get_system_font():
    """
    Select an appropriate font based on the OS.
    On macOS, prefer PingFang TC or Source Han Sans.
    On Windows, prefer Microsoft JhengHei or Noto Sans TC.
    Fallback to default sans-serif font if none is available.
    """
    if sys.platform == "darwin":  # macOS
        preferred_fonts = ["PingFang TC", "Source Han Sans", "Heiti TC"]
    else:  # Windows / Linux
        preferred_fonts = ["Microsoft JhengHei", "Noto Sans TC", "SimHei"]

    for f in preferred_fonts:
        if f in QFontDatabase.families():
            return f
    # Fallback font
    return "Sans Serif"


def get_resource_path(relative_path):
    """
    Get the absolute path to the resource, relative to the application location.
    Works for both development mode and PyInstaller's frozen environment.
    """
    if hasattr(sys, "_MEIPASS"):
        #  When running as a PyInstaller executable,
        # use the internal temporary folder path.
        base_path = sys._MEIPASS
    else:
        #  When running in a normal Python environment,
        # get the directory where the current script (or main script) is located.
        # This ensures the path is relative to the script file, not the CMD working directory.
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


# File names
PRESETS_FILE = get_resource_path("presets.json")
PANEL_DEFAULTS_FILE = get_resource_path("panel_defaults.json")
BEEP_FILE = get_resource_path("beep.wav")
