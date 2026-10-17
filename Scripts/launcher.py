#!/usr/bin/env python3
"""
Launcher for Local AI Model Manager - No Terminal Window
"""

import sys
import os
from pathlib import Path
import subprocess

def launch_app():
    """Launch the desktop application without terminal window"""
    script_dir = Path(__file__).parent
    python_exe = sys.executable
    main_py = script_dir.parent / "main.py"
    
    # Windows-specific launch without terminal
    if os.name == 'nt':
        # Use pythonw.exe instead of python.exe to avoid terminal window
        pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
        
        # Check if pythonw.exe exists
        if Path(pythonw_exe).exists():
            # Launch with pythonw.exe (no terminal)
            subprocess.Popen([pythonw_exe, str(main_py)], cwd=str(script_dir), 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Fallback: use regular python with hidden console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen([python_exe, str(main_py)], cwd=str(script_dir), 
                           startupinfo=startupinfo)
    else:
        # Linux/Mac
        subprocess.Popen([python_exe, str(main_py)], cwd=str(script_dir))

if __name__ == "__main__":
    launch_app()
