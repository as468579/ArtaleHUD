import os

import PyInstaller.__main__

# Define the app name
APP_NAME = "ArtaleHUD"

# Configuration for PyInstaller
# --noconsole: Hide the terminal window
# --onefile: Bundle everything into a single executable
# --add-data: Include external assets (format: "source;destination")
params = [
    "main.py",
    "--name=%s" % APP_NAME,
    "--noconsole",
    "--onefile",
    "--add-data=config.json;.",
    "--add-data=presets.json;.",
    "--add-data=beep.wav;.",
    "--add-data=LICENSE.txt;.",
    "--add-data=fonts;fonts",
    "--clean",
]

if __name__ == "__main__":
    print(f"Starting build process for {APP_NAME}...")

    # Execute PyInstaller with the defined parameters
    PyInstaller.__main__.run(params)

    print("-" * 30)
    print(f"Build finished! Check the 'dist' folder for {APP_NAME}.exe")
