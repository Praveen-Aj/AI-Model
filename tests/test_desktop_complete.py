#!/usr/bin/env python3
"""
Complete Desktop Application Test
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_desktop_app():
    """Test desktop application components"""
    print("=== Desktop Application Test ===")
    
    # Test imports
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import QTimer, Qt
        print("✅ PySide6 imports: OK")
    except Exception as e:
        print(f"❌ PySide6 imports failed: {e}")
        return False
    
    # Test GUI components
    try:
        from src.gui.main_window import ModelManagerMainWindow
        from src.gui.model_widget import ModelWidget
        from src.gui.resource_widget import ResourceWidget
        from src.gui.profile_widget import ProfileWidget
        from src.gui.tray_icon import TrayIcon
        print("✅ GUI components: OK")
    except Exception as e:
        print(f"❌ GUI components failed: {e}")
        return False
    
    # Test core engine
    try:
        from src.ollama_client import OllamaClient
        from src.resource_monitor import ResourceMonitor
        from src.database import DatabaseManager
        print("✅ Core engine: OK")
    except Exception as e:
        print(f"❌ Core engine failed: {e}")
        return False
    
    # Test application creation (without showing)
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Test")
        
        # Test window creation
        window = ModelManagerMainWindow()
        print("✅ Window creation: OK")
        
        # Test basic functionality
        resources = ResourceMonitor().get_system_resources()
        print(f"✅ Resource monitoring: RAM {resources.ram_percent:.1f}%, CPU {resources.cpu_percent:.1f}%")
        
        # Test database
        profiles = DatabaseManager().get_profiles()
        print(f"✅ Database: {len(profiles)} profiles found")
        
        # Test Ollama connection
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            models = loop.run_until_complete(OllamaClient().list_models())
            print(f"✅ Ollama connection: {len(models)} models found")
        except Exception as e:
            print(f"⚠️ Ollama connection failed: {e}")
        
        print("✅ Desktop application test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Application test failed: {e}")
        return False

def test_desktop_launch():
    """Test desktop application launch"""
    print("\n=== Desktop Launch Test ===")
    
    try:
        # Import main function
        import main
        
        print("✅ Main module imported successfully")
        print("✅ Desktop application ready to launch")
        print("\nTo launch the desktop application:")
        print("  python main.py")
        print("\nOr use the PowerShell script:")
        print("  .\\Scripts\\start_desktop_clean.ps1")
        
        return True
        
    except Exception as e:
        print(f"❌ Desktop launch test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Local AI Model Manager Desktop Application")
    print("=" * 60)
    
    app_ok = test_desktop_app()
    launch_ok = test_desktop_launch()
    
    if app_ok and launch_ok:
        print("\n🎉 All tests passed!")
        print("🚀 Desktop application is ready for launch!")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Test model management in desktop UI")
        print("3. Verify system tray functionality")
        print("4. Check resource monitoring")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
