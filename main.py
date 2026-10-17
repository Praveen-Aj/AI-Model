#!/usr/bin/env python3
"""
Local AI Model Manager - Desktop Application Entry Point
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon

from src.gui.main_window import ModelManagerMainWindow


def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import PySide6
    except ImportError:
        missing_deps.append("PySide6")
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    try:
        import aiohttp
    except ImportError:
        missing_deps.append("aiohttp")
    
    if missing_deps:
        QMessageBox.critical(None, "Missing Dependencies", 
            f"Please install the following dependencies:\n\n" + 
            "\n".join(f"- {dep}" for dep in missing_deps) +
            "\n\nRun: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main application entry point"""
    # Set high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.Round
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Local AI Model Manager")
    app.setApplicationVersion("0.2.0")
    app.setOrganizationName("AI Model Manager")
    
    # Set application icon
    icon_path = Path(__file__).parent / "ai_model.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Set application style
    app.setStyle("Fusion")
    
    # Set very colorful vibrant palette
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    
    # Very vibrant colorful theme with multiple colors
    palette.setColor(QPalette.Window, QColor(70, 130, 180))      # Blue background
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(60, 120, 170))         # Lighter blue
    palette.setColor(QPalette.AlternateBase, QColor(80, 140, 190)) # Alternate blue
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 200))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(100, 180, 230))       # Bright blue buttons
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 100, 100))
    palette.setColor(QPalette.Link, QColor(255, 200, 100))         # Orange links
    palette.setColor(QPalette.Highlight, QColor(255, 150, 50))    # Orange highlight
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    
    app.setPalette(palette)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    try:
        # Create and show main window
        window = ModelManagerMainWindow()
        window.show()
        
        # Show startup message
        window.status_bar.showMessage("Local AI Model Manager started", 3000)
        
        # Run application
        exit_code = app.exec()
        
        # Cleanup before exit
        window.cleanup()
        
        # Force quit the application
        app.quit()
        
        return exit_code
        
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", 
            f"Failed to start Local AI Model Manager:\n\n{str(e)}")
        return 1
    finally:
        # Ensure cleanup happens
        try:
            if 'window' in locals():
                window.cleanup()
            app.quit()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
