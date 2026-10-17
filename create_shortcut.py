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
        launcher_bat = (script_dir / "Launch_AI_Model_Manager.bat").resolve()
        icon_file = (script_dir / "ai_model_stylish.ico").resolve()

        # Desktop paths to try
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Praveen")
        desktop_paths = [
            shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0),
            os.path.join(user_profile, "Desktop"),
            os.path.join(user_profile, "OneDrive", "Desktop"),
            os.path.join(user_profile, "OneDrive - Personal", "Desktop")
        ]

        # Deduplicate paths and verify existence
        valid_desktops = []
        for path in desktop_paths:
            if path:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path) and abs_path not in valid_desktops:
                    valid_desktops.append(abs_path)

        shell_client = win32com.client.Dispatch("WScript.Shell")
        created_any = False

        for desktop in valid_desktops:
            try:
                shortcut_path = os.path.join(desktop, "Local AI Model Manager.lnk")
                
                # Delete existing if present
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)

                shortcut = shell_client.CreateShortCut(shortcut_path)
                shortcut.Targetpath = str(launcher_bat)
                shortcut.WorkingDirectory = str(script_dir)
                shortcut.WindowStyle = 1  # Normal window

                if icon_file.exists():
                    shortcut.IconLocation = f"{icon_file},0"

                shortcut.Description = "Local AI Model Manager - Desktop Application"
                shortcut.save()
                
                print(f"Success: Desktop shortcut created at: {shortcut_path}")
                created_any = True
            except Exception as ex:
                print(f"Skipping directory {desktop}: {ex}")

        return created_any

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
