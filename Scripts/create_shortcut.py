#!/usr/bin/env python3
"""
Create Desktop Shortcut for Local AI Model Manager
"""

import sys
import os
from pathlib import Path


def create_shortcut():
    """Create desktop shortcut"""
    try:
        import win32com.client
        from win32com.shell import shell, shellcon

        # Get paths
        script_dir = Path(__file__).parent.resolve()
        launcher_bat = (script_dir.parent / "Launch_AI_Model_Manager.bat").resolve()
        icon_file = (script_dir.parent / "ai_model_stylish.ico").resolve()

        # Desktop path
        desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)

        # Create shortcut
        shortcut_path = os.path.join(desktop, "Local AI Model Manager.lnk")

        shell_client = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell_client.CreateShortCut(shortcut_path)

        shortcut.Targetpath = str(launcher_bat)
        shortcut.WorkingDirectory = str(script_dir.parent)

        # Set window style to normal (not minimized)
        shortcut.WindowStyle = 1  # Normal window

        if icon_file.exists():
            shortcut.IconLocation = f"{icon_file},0"

        shortcut.Description = "Local AI Model Manager - Desktop Application"
        shortcut.save()

        print("Shortcut details:")
        print(f"Target: {shortcut.Targetpath}")
        print(f"Working Directory: {shortcut.WorkingDirectory}")
        print(f"Icon: {shortcut.IconLocation}")
        print(f"Success: Desktop shortcut created: {shortcut_path}")
        return True

    except ImportError:
        print("Error: pywin32 not installed. Run: pip install pywin32")
        return False
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False


if __name__ == "__main__":
    print("Creating Desktop Shortcut for Local AI Model Manager")
    print("=" * 60)
    create_shortcut()
