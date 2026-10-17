#!/usr/bin/env python3
"""
Test PySide6 imports for desktop application
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all required imports"""
    print("Testing PySide6 imports...")
    
    try:
        from PySide6.QtWidgets import (
            QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
            QSplitter, QTabWidget, QMenuBar, QStatusBar, 
            QToolBar, QApplication, QMessageBox
        )
        print("✅ QtWidgets imports: OK")
    except Exception as e:
        print(f"❌ QtWidgets imports failed: {e}")
        return False
    
    try:
        from PySide6.QtCore import QTimer, Qt, Signal, QObject
        print("✅ QtCore imports: OK")
    except Exception as e:
        print(f"❌ QtCore imports failed: {e}")
        return False
    
    try:
        from PySide6.QtGui import QAction, QIcon
        print("✅ QtGui imports: OK")
    except Exception as e:
        print(f"❌ QtGui imports failed: {e}")
        return False
    
    print("\nTesting GUI component imports...")
    
    try:
        from src.gui.model_widget import ModelWidget
        print("✅ ModelWidget import: OK")
    except Exception as e:
        print(f"❌ ModelWidget import failed: {e}")
        return False
    
    try:
        from src.gui.resource_widget import ResourceWidget
        print("✅ ResourceWidget import: OK")
    except Exception as e:
        print(f"❌ ResourceWidget import failed: {e}")
        return False
    
    try:
        from src.gui.profile_widget import ProfileWidget
        print("✅ ProfileWidget import: OK")
    except Exception as e:
        print(f"❌ ProfileWidget import failed: {e}")
        return False
    
    try:
        from src.gui.tray_icon import TrayIcon
        print("✅ TrayIcon import: OK")
    except Exception as e:
        print(f"❌ TrayIcon import failed: {e}")
        return False
    
    try:
        from src.gui.main_window import ModelManagerMainWindow
        print("✅ ModelManagerMainWindow import: OK")
    except Exception as e:
        print(f"❌ ModelManagerMainWindow import failed: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True

def test_basic_functionality():
    """Test basic functionality without GUI"""
    print("\nTesting core engine functionality...")
    
    try:
        from src.ollama_client import OllamaClient
        print("✅ OllamaClient import: OK")
    except Exception as e:
        print(f"❌ OllamaClient import failed: {e}")
        return False
    
    try:
        from src.resource_monitor import ResourceMonitor
        print("✅ ResourceMonitor import: OK")
    except Exception as e:
        print(f"❌ ResourceMonitor import failed: {e}")
        return False
    
    try:
        from src.database import DatabaseManager
        print("✅ DatabaseManager import: OK")
    except Exception as e:
        print(f"❌ DatabaseManager import failed: {e}")
        return False
    
    print("\n✅ Core engine imports successful!")
    return True

if __name__ == "__main__":
    print("=== Desktop Application Import Test ===")
    
    imports_ok = test_imports()
    core_ok = test_basic_functionality()
    
    if imports_ok and core_ok:
        print("\n🎉 All tests passed! Desktop application ready to run.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please fix import issues.")
        sys.exit(1)
