#!/usr/bin/env python3
"""
Test Activity Log Integration
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_activity_log():
    """Test activity log functionality"""
    print("=== Activity Log Test ===")
    
    try:
        # Test imports
        from PySide6.QtWidgets import QApplication
        from src.gui.activity_log_widget import ActivityLogWidget, activity_logger, LogLevel
        print("✅ Activity log imports: OK")
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create log widget
        log_widget = ActivityLogWidget()
        print("✅ Activity log widget created")
        
        # Register with global logger
        activity_logger.add_widget(log_widget)
        print("✅ Registered with global logger")
        
        # Test logging
        activity_logger.log_info("Test info message", "test_model", "test_operation")
        activity_logger.log_warning("Test warning message", "test_model", "test_operation")
        activity_logger.log_error("Test error message", "test_model", "test_operation")
        activity_logger.log_success("Test success message", "test_model", "test_operation", 5.2)
        
        # Test model operation logging
        activity_logger.log_model_operation("load", "qwen2.5:14b", True, 12.5)
        activity_logger.log_model_operation("unload", "qwen2.5:14b", False, 3.1, "Connection timeout")
        
        # Test resource alert logging
        activity_logger.log_resource_alert("warning", "High RAM usage detected")
        activity_logger.log_resource_alert("critical", "Memory usage critical")
        
        print("✅ All log entries added")
        print(f"✅ Total entries: {len(log_widget.entries)}")
        
        # Test filtering
        print("\n--- Testing Filters ---")
        log_widget.filter_combo.setCurrentText("ERROR")
        log_widget.update_display()
        print("✅ Error filter applied")
        
        log_widget.filter_combo.setCurrentText("All")
        log_widget.update_display()
        print("✅ All entries filter applied")
        
        # Test search
        log_widget.search_edit.setText("qwen2.5")
        log_widget.update_display()
        print("✅ Search filter applied")
        
        # Test clear
        log_widget.clear_log()
        print("✅ Log cleared")
        
        print("\n🎉 Activity log test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Activity log test failed: {e}")
        return False

def test_desktop_integration():
    """Test desktop application integration"""
    print("\n=== Desktop Integration Test ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import ModelManagerMainWindow
        print("✅ Desktop imports: OK")
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create main window (without showing)
        window = ModelManagerMainWindow()
        print("✅ Main window created with activity log")
        
        # Test activity log is present
        if hasattr(window, 'activity_log'):
            print("✅ Activity log integrated into main window")
        else:
            print("❌ Activity log not integrated")
            return False
        
        # Test logging through main window
        window.activity_log.add_entry(
            window.activity_log.LogLevel.INFO,
            "Desktop integration test",
            "test_model",
            "integration"
        )
        print("✅ Activity logging through main window works")
        
        print("\n🎉 Desktop integration test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Desktop integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("Activity Log Integration Test")
    print("=" * 50)
    
    log_ok = test_activity_log()
    desktop_ok = test_desktop_integration()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Activity log: {'✅ PASS' if log_ok else '❌ FAIL'}")
    print(f"Desktop integration: {'✅ PASS' if desktop_ok else '❌ FAIL'}")
    
    if log_ok and desktop_ok:
        print("\n🎉 Activity log integration is working!")
        print("✅ Timestamped operations logging is ready")
        print("✅ Operational visibility is improved")
        sys.exit(0)
    else:
        print("\n❌ Activity log integration failed!")
        sys.exit(1)
