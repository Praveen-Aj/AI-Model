#!/usr/bin/env python3
"""
Test script to verify shortcut execution
"""

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

def main():
    app = QApplication([])
    
    # Create a simple message box to test if shortcut works
    msg = QMessageBox()
    msg.setWindowTitle("Shortcut Test")
    msg.setText("Shortcut is working! This is a test.")
    msg.setIcon(QMessageBox.Information)
    
    # Auto-close after 2 seconds
    QTimer.singleShot(2000, msg.close)
    
    msg.exec()

if __name__ == "__main__":
    main()
