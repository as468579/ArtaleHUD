import argparse
import os
import sys

import PyInstaller.__main__

# Define the app name
APP_NAME = "ArtaleHUD"


def run_build(target_os):
    """
    Configure and run PyInstaller based on the target OS.
    """

    # Base parameters common to both platforms
    params = [
        "main.py",
        "--noconsole",
        "--onefile",
        "--clean",
    ]

    # MacOS specific configuration
    if target_os == "mac":
        print(f"--- Building for macOS ---")

        output_name = f"{APP_NAME}-mac"

        # macOS uses colon ':' as separator
        params.extend(
            [
                f"--name={APP_NAME}-Mac",
                "--windowed",  # Added --windowed to create a .app bundle
                "--add-data=config.json:.",
                "--add-data=presets.json:.",
                "--add-data=beep.wav:.",
                "--add-data=LICENSE.txt:.",
                "--add-data=fonts:fonts",
            ]
        )
    elif target_os == "win":
        print(f"--- Building for Windows ---")

        output_name = f"{APP_NAME}-win"

        # Windows uses semicolon ';' as separator
        params.extend(
            [
                f"--name={APP_NAME}-Win",
                "--add-data=config.json;.",
                "--add-data=presets.json;.",
                "--add-data=beep.wav;.",
                "--add-data=LICENSE.txt;.",
                "--add-data=fonts;fonts",
            ]
        )
    else:
        print(f"ERROR: Unsupported target_os '{target_os}'.")
        print("Please use '--target_os win' or '--target_os mac'.")
        sys.exit(1)  # Exit with error code

    # Execute PyInstaller with the defined parameters
    PyInstaller.__main__.run(params)

    return output_name


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Build Artale Unified Control application."
    )
    parser.add_argument(
        "--target_os",
        choices=["win", "mac"],
        help="Specify the target operating system (windows or mac)",
        required=True,
    )
    args = parser.parse_args()

    print(f"Starting build process for {APP_NAME}...")
    output_name = run_build(args.target_os)

    print("-" * 30)
    print(f"Build finished! Check the 'dist' folder for {output_name}")
