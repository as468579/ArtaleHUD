import os
import sys


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
