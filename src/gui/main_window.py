"""
Main Window for Local AI Model Manager Desktop Application
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTabWidget,
    QMenuBar,
    QStatusBar,
    QToolBar,
    QSizePolicy,
    QPushButton,
    QApplication,
    QMessageBox,
    QLabel,
)
from PySide6.QtCore import QTimer, Qt, Signal, QObject
from PySide6.QtGui import QAction, QIcon

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ollama_client import OllamaClient
from src.database import DatabaseManager
from src.resource_monitor import ResourceMonitor
from src.model_queue import ModelQueue
from src.auto_unload_service import AutoUnloadService
from src.profile_manager import ProfileManager

from .model_widget import ModelWidget
from .resource_widget import ResourceWidget
from .profile_widget import ProfileWidget
from .tray_icon import TrayIcon
from .activity_log_widget import ActivityLogWidget, activity_logger


class ModelManagerMainWindow(QMainWindow):
    """Main application window for Local AI Model Manager"""

    # Signals
    model_status_changed = Signal(str, str)  # model_name, status
    resource_alert = Signal(str, str)  # alert_type, message

    def __init__(self):
        super().__init__()

        # Initialize core engine
        self.init_core_engine()

        # Setup UI
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()

        # Setup timers for real-time updates
        self.setup_timers()

        # Setup system tray
        self.setup_tray()

        # Start background services
        self.start_services()

    def init_core_engine(self):
        """Initialize core engine components"""
        self.ollama_client = OllamaClient()
        self.database = DatabaseManager()
        self.resource_monitor = ResourceMonitor()
        self.model_queue = ModelQueue()
        self.auto_unload_service = AutoUnloadService()
        self.profile_manager = ProfileManager()
        self.ollama_service_available = False

    def setup_ui(self):
        """Setup the UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Model Management
        self.model_widget = ModelWidget(self.ollama_client, self.model_queue)
        splitter.addWidget(self.model_widget)

        # Right panel - Profiles and Activity Log (tabbed) - Resources removed
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Create tab widget for right panel with very colorful styling
        right_tabs = QTabWidget()
        right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #4080c0;
                background-color: #5090d0;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60a0e0, stop:1 #4080c0);
                color: #ffffff;
                padding: 10px 20px;
                border: 2px solid #3080b0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff9900, stop:1 #ff6600);
                color: #ffffff;
                border: 2px solid #cc4400;
                border-bottom: 2px solid #ffcc00;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #80b0f0, stop:1 #60a0e0);
            }
        """)

        # Resource monitoring tab - REMOVED to save space
        # self.resource_widget = ResourceWidget(self.resource_monitor)
        # right_tabs.addTab(self.resource_widget, "Resources")

        # Profile management tab
        self.profile_widget = ProfileWidget(self.profile_manager, self.database)
        right_tabs.addTab(self.profile_widget, "Profiles")

        # Activity log tab
        self.activity_log = ActivityLogWidget()
        right_tabs.addTab(self.activity_log, "Activity Log")

        right_layout.addWidget(right_tabs)

        splitter.addWidget(right_widget)

        # Set splitter proportions (give more space to model management)
        splitter.setSizes([700, 500])

        # Connect signals
        self.model_widget.model_status_changed.connect(self.on_model_status_changed)
        # self.resource_widget.resource_alert.connect(self.on_resource_alert)  # Removed with resources

        # Register activity log with global logger
        activity_logger.add_widget(self.activity_log)

        # Log startup
        activity_logger.log_info("Local AI Model Manager started")

    def setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        show_models_action = QAction("Show Models", self)
        show_models_action.setCheckable(True)
        show_models_action.setChecked(True)
        show_models_action.triggered.connect(
            lambda: self.model_widget.setVisible(show_models_action.isChecked())
        )
        view_menu.addAction(show_models_action)

        # show_resources_action = QAction("Show Resources", self)  # Removed with resources
        # show_resources_action.setCheckable(True)
        # show_resources_action.setChecked(True)
        # show_resources_action.triggered.connect(lambda: self.resource_widget.setVisible(show_resources_action.isChecked()))
        # view_menu.addAction(show_resources_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        reconnect_action = QAction("Reconnect Ollama", self)
        reconnect_action.triggered.connect(self.try_reconnect_service)
        tools_menu.addAction(reconnect_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)

        exit_button = QPushButton("Exit")
        exit_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #444444, stop:1 #222222);
                color: white;
                border: 2px solid #000000;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #666666, stop:1 #333333);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #222222, stop:1 #000000);
            }
        """)
        exit_button.clicked.connect(self.close)
        toolbar.addWidget(exit_button)

        reconnect_action = QAction("Reconnect", self)
        reconnect_action.triggered.connect(self.try_reconnect_service)
        toolbar.addAction(reconnect_action)

    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status labels
        self.ollama_status_label = QLabel("Ollama: Checking...")
        self.status_bar.addPermanentWidget(self.ollama_status_label)

        self.models_status_label = QLabel("Models: 0")
        self.status_bar.addPermanentWidget(self.models_status_label)

        # Add simplified RAM/VRAM display
        self.ram_status_label = QLabel("RAM: Updating...")
        self.ram_status_label.setStyleSheet("""
            QLabel {
                color: #ffcc00;
                font-weight: bold;
                background-color: #306090;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        self.status_bar.addPermanentWidget(self.ram_status_label)

        self.vram_status_label = QLabel("VRAM: 0%")
        self.vram_status_label.setStyleSheet("""
            QLabel {
                color: #ff00ff;
                font-weight: bold;
                background-color: #306090;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        self.status_bar.addPermanentWidget(self.vram_status_label)

        # Initialize status display immediately
        self.update_status_bar_memory()
        self.update_status()

    def setup_timers(self):
        """Setup timers for real-time updates"""
        # Add timer for RAM/VRAM status bar updates and Ollama connection status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar_memory)
        self.status_timer.start(5000)  # Update every 5 seconds

        self.ollama_timer = QTimer()
        self.ollama_timer.timeout.connect(self.update_status)
        self.ollama_timer.start(5000)

    def setup_tray(self):
        """Setup system tray"""
        self.tray_icon = TrayIcon(self)
        self.tray_icon.show()

    def start_services(self):
        """Start background services"""
        loop = asyncio.new_event_loop()
        try:
            self.ollama_service_available = loop.run_until_complete(
                self.ollama_client.is_service_running()
            )
            if not self.ollama_service_available:
                # Attempt to auto-start Ollama service in the background
                self.status_bar.showMessage("Ollama offline. Starting background service...", 5000)
                try:
                    import subprocess
                    import os
                    if os.name == "nt":
                        subprocess.Popen(
                            ["ollama", "serve"],
                            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    else:
                        subprocess.Popen(
                            ["ollama", "serve"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    
                    # Poll for a few seconds to let service start up
                    for _ in range(5):
                        import time
                        time.sleep(1)
                        if loop.run_until_complete(self.ollama_client.is_service_running()):
                            self.ollama_service_available = True
                            break
                except Exception as ex:
                    print(f"Failed to auto-start Ollama service: {ex}")

            if self.ollama_service_available:
                loop.run_until_complete(self.model_queue.start())
                self.model_widget.set_service_available(True)
                self.status_bar.showMessage(
                    "Connected to Ollama service", 3000
                )
            else:
                self.model_widget.set_service_available(False)
                self.status_bar.showMessage(
                    "Ollama service offline. Start it manually and click Reconnect.",
                    5000,
                )

        except Exception as e:
            self.ollama_service_available = False
            self.model_widget.set_service_available(False)
            self.status_bar.showMessage(
                f"Ollama service offline. Click Reconnect when ready.",
                5000,
            )
        finally:
            if not loop.is_closed():
                loop.close()

    def refresh_all(self):
        """Refresh all data"""
        if not getattr(self, "ollama_service_available", False):
            QMessageBox.warning(
                self,
                "Ollama Service Required",
                "Ollama is offline. Start it using ollama-manager.ps1 before refreshing.",
            )
            return

        try:
            # Refresh models
            self.model_widget.refresh_models()

            # Refresh profiles
            self.profile_widget.refresh_profiles()

            self.status_bar.showMessage("Data refreshed", 2000)

        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to refresh data: {str(e)}")

    def update_status_bar_memory(self):
        """Update RAM/VRAM in status bar"""
        try:
            resources = self.resource_monitor.get_system_resources()

            # Update RAM
            ram_percent = resources.ram_percent
            ram_used_gb = resources.ram_used / (1024**3)
            ram_total_gb = resources.ram_total / (1024**3)
            self.ram_status_label.setText(
                f"RAM: {ram_percent:.0f}% ({ram_used_gb:.1f}/{ram_total_gb:.1f}GB)"
            )

            # Update VRAM
            gpu_info = resources.gpu_info
            if resources.gpu_info and len(resources.gpu_info) > 0:
                gpu = resources.gpu_info[0]
                gpu_used = gpu.get("memory_used", 0) / (1024**3)
                gpu_total = gpu.get("memory_total", 0) / (1024**3)
                gpu_percent = (gpu_used / gpu_total * 100) if gpu_total > 0 else 0
                self.vram_status_label.setText(
                    f"VRAM: {gpu_percent:.0f}% ({gpu_used:.1f}/{gpu_total:.1f}GB)"
                )
            else:
                self.vram_status_label.setText("VRAM: N/A")

            self.vram_status_label.setVisible(True)

        except Exception as e:
            print(f"Error updating status bar memory: {e}")

    def update_status(self):
        """Update status bar"""
        loop = asyncio.new_event_loop()
        try:
            if self.ollama_service_available:
                try:
                    models = loop.run_until_complete(self.ollama_client.list_models())
                    self.ollama_status_label.setText("Ollama: Connected")
                    self.models_status_label.setText(f"Models: {len(models)}")
                except Exception:
                    self.ollama_service_available = False
                    self.ollama_status_label.setText("Ollama: Disconnected")
                    self.models_status_label.setText("Models: 0")
                    self.model_widget.set_service_available(False)
                    self.status_bar.showMessage(
                        "Ollama service disconnected. Start it via ollama-manager.ps1.",
                        5000,
                    )
            else:
                service_running = loop.run_until_complete(
                    self.ollama_client.is_service_running()
                )
                if service_running:
                    self.ollama_service_available = True
                    loop.run_until_complete(self.model_queue.start())
                    self.model_widget.set_service_available(True)
                    self.status_bar.showMessage(
                        "Ollama service is back online.", 5000
                    )
                    models = loop.run_until_complete(self.ollama_client.list_models())
                    self.ollama_status_label.setText("Ollama: Connected")
                    self.models_status_label.setText(f"Models: {len(models)}")
                else:
                    self.ollama_status_label.setText("Ollama: Disconnected")
                    self.models_status_label.setText("Models: 0")
        finally:
            if not loop.is_closed():
                loop.close()

    def start_all_models(self):
        """Start all models in current profile"""
        if not getattr(self, "ollama_service_available", False):
            QMessageBox.warning(
                self,
                "Ollama Service Required",
                "Ollama is offline. Start it using ollama-manager.ps1 before starting models.",
            )
            return

        loop = asyncio.new_event_loop()
        try:
            current_profile = self.profile_widget.get_current_profile()
            if not current_profile:
                QMessageBox.information(self, "Info", "No profile selected")
                return

            for model_name in current_profile["models"]:
                loop.run_until_complete(self.model_queue.load_model(model_name))

            self.status_bar.showMessage(
                f"Started profile: {current_profile['name']}", 3000
            )
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to start models: {str(e)}")
        finally:
            if not loop.is_closed():
                loop.close()

    def stop_all_models(self):
        """Stop all running models"""
        if not getattr(self, "ollama_service_available", False):
            QMessageBox.warning(
                self,
                "Ollama Service Required",
                "Ollama is offline. Start it using ollama-manager.ps1 before stopping models.",
            )
            return

        loop = asyncio.new_event_loop()
        try:
            running_models = loop.run_until_complete(
                self.ollama_client.running_models()
            )

            for model in running_models:
                loop.run_until_complete(self.model_queue.unload_model(model.name))

            self.status_bar.showMessage("Stopped all models", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to stop models: {str(e)}")
        finally:
            if not loop.is_closed():
                loop.close()

    def on_model_status_changed(self, model_name: str, status: str):
        """Handle model status changes"""
        self.status_bar.showMessage(f"Model {model_name}: {status}", 3000)

    def try_reconnect_service(self):
        """Try to reconnect to Ollama service immediately."""
        loop = asyncio.new_event_loop()
        try:
            service_running = loop.run_until_complete(
                self.ollama_client.is_service_running()
            )
            if service_running:
                if not self.ollama_service_available:
                    loop.run_until_complete(self.model_queue.start())
                self.ollama_service_available = True
                self.model_widget.set_service_available(True)
                self.status_bar.showMessage(
                    "Connected to Ollama service.",
                    5000,
                )
                self.update_status()
            else:
                QMessageBox.information(
                    self,
                    "Reconnect Failed",
                    "Ollama is still offline. Start it using ollama-manager.ps1 and try again.",
                )
                self.status_bar.showMessage(
                    "Ollama service still offline.",
                    5000,
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Reconnect Error",
                f"Failed to reconnect: {str(e)}",
            )
        finally:
            if not loop.is_closed():
                loop.close()

    def stop_ollama_and_exit(self):
        """Stop Ollama service and exit the application"""
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Close the application? Ollama service will continue running.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.model_queue.stop())
        except Exception as e:
            print(f"Error stopping internal queue: {e}")
        finally:
            if not loop.is_closed():
                loop.close()

        QApplication.instance().quit()

    def on_resource_alert(self, alert_type: str, message: str):
        """Handle resource alerts"""
        if alert_type == "critical":
            QMessageBox.warning(self, "Resource Alert", message)
        else:
            self.status_bar.showMessage(message, 5000)

    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(
            self,
            "Settings",
            "Settings Dialog\n\n"
            "Current Settings:\n"
            "- Resource thresholds are managed via Profiles\n"
            "- Auto-unload settings are managed via Profiles\n"
            "- Model configurations are managed via Profiles\n\n"
            "Future Settings (coming soon):\n"
            "- Application theme customization\n"
            "- Ollama connection settings\n"
            "- Logging preferences\n"
            "- Notification settings",
        )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About",
            "Local AI Model Manager\n"
            "Version 0.2.0\n\n"
            "A desktop application for managing local Ollama models\n"
            "with automated resource optimization.",
        )

    def closeEvent(self, event):
        """Handle application close"""
        # Always cleanup and close (no tray hide for now)
        self.cleanup()
        event.accept()

    def cleanup(self):
        """Clean up resources before closing"""
        try:
            # Stop timers
            if hasattr(self, "update_timer"):
                self.update_timer.stop()
                self.update_timer.deleteLater()

            # Cleanup resource widget - REMOVED
            # if hasattr(self, 'resource_widget') and self.resource_widget:
            #     if hasattr(self.resource_widget, 'update_timer'):
            #         self.resource_widget.update_timer.stop()
            #         self.resource_widget.update_timer.deleteLater()

            if hasattr(self, "model_widget") and self.model_widget:
                if hasattr(self.model_widget, "update_timer"):
                    self.model_widget.update_timer.stop()
                    self.model_widget.update_timer.deleteLater()

            # Stop tray icon timer
            if hasattr(self, "tray_icon") and self.tray_icon:
                if hasattr(self.tray_icon, "update_timer"):
                    self.tray_icon.update_timer.stop()
                    self.tray_icon.update_timer.deleteLater()
                self.tray_icon.hide()

            # Stop model queue
            if hasattr(self, "model_queue") and self.model_queue:
                import asyncio

                try:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.model_queue.stop())
                    loop.close()
                except:
                    pass

            # Log shutdown
            if hasattr(self, "activity_log"):
                from .activity_log_widget import activity_logger

                activity_logger.log_info("Application shutting down")

        except Exception as e:
            print(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    pass  # This function is now in main.py
