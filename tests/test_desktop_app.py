#!/usr/bin/env python3
"""
Test desktop application without full GUI launch
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_desktop_components():
    """Test desktop components without GUI"""
    print("Testing desktop components...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        # Create minimal application for testing
        app = QApplication(sys.argv)
        app.setApplicationName("Test")
        
        print("✅ QApplication created")
        
        # Test core engine integration
        from src.ollama_client import OllamaClient
        from src.resource_monitor import ResourceMonitor
        from src.database import DatabaseManager
        
        client = OllamaClient()
        monitor = ResourceMonitor()
        db = DatabaseManager()
        
        print("✅ Core engine components initialized")
        
        # Test basic functionality
        resources = monitor.get_system_resources()
        print(f"✅ Resource monitoring: RAM {resources.ram_percent:.1f}%, CPU {resources.cpu_percent:.1f}%")
        
        # Test database
        profiles = db.get_profiles()
        print(f"✅ Database: {len(profiles)} profiles found")
        
        # Test Ollama connection
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            models = loop.run_until_complete(client.list_models())
            print(f"✅ Ollama connection: {len(models)} models found")
        except Exception as e:
            print(f"⚠️ Ollama connection failed: {e}")
        
        print("✅ Desktop components test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Desktop components test failed: {e}")
        return False

def test_gui_components():
    """Test GUI component creation"""
    print("\nTesting GUI component creation...")
    
    try:
        from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
        from PySide6.QtCore import QTimer
        
        app = QApplication(sys.argv)
        
        # Test individual widgets
        from src.gui.model_widget import ModelWidget
        from src.gui.resource_widget import ResourceWidget
        from src.gui.profile_widget import ProfileWidget
        
        # Create mock components for testing
        from src.ollama_client import OllamaClient
        from src.model_queue import ModelQueue
        from src.resource_monitor import ResourceMonitor
        from src.database import DatabaseManager
        from src.profile_manager import ProfileManager
        
        client = OllamaClient()
        queue = ModelQueue()
        monitor = ResourceMonitor()
        db = DatabaseManager()
        profile_manager = ProfileManager()
        
        # Test widget creation (without showing)
        model_widget = ModelWidget(client, queue)
        resource_widget = ResourceWidget(monitor)
        profile_widget = ProfileWidget(profile_manager, db)
        
        print("✅ GUI widgets created successfully")
        print("✅ GUI component test successful!")
        return True
        
    except Exception as e:
        print(f"❌ GUI component test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Desktop Application Test ===")
    
    components_ok = test_desktop_components()
    gui_ok = test_gui_components()
    
    if components_ok and gui_ok:
        print("\n🎉 All tests passed! Desktop application is ready.")
        print("\nTo run the full desktop application:")
        print("  python main.py")
        print("\nOr use the PowerShell script:")
        print("  .\\Scripts\\start_desktop_clean.ps1")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
