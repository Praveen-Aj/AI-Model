"""
System Tray Integration for Local AI Model Manager
"""

import sys
from typing import Optional, Callable
from pathlib import Path

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QAction, QIcon

# Add src to path for imports
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.resource_monitor import ResourceMonitor
from src.ollama_client import OllamaClient


class TrayIcon(QSystemTrayIcon):
    """System tray icon for Local AI Model Manager"""

    # Signals
    show_main_window = Signal()
    quick_start_model = Signal(str)
    quick_stop_model = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize components
        self.resource_monitor = ResourceMonitor()
        self.parent_window = parent
        self.ollama_client = (
            parent.ollama_client
            if parent is not None and hasattr(parent, "ollama_client")
            else OllamaClient()
        )
        self.model_queue = (
            parent.model_queue
            if parent is not None and hasattr(parent, "model_queue")
            else None
        )

        # Setup tray icon
        self.setup_icon()
        self.setup_menu()
        self.setup_tooltips()

        # Setup update timer
        self.setup_timer()

    def setup_icon(self):
        """Setup tray icon"""
        # Try to use ai_model.ico
        icon_path = Path(__file__).parent.parent.parent / "ai_model.ico"
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        else:
            # Fallback to system icon
            self.setIcon(QIcon.fromTheme("computer"))

        # Show tray icon
        self.show()
        self.setToolTip("Local AI Model Manager")

    def setup_menu(self):
        """Setup context menu"""
        menu = QMenu()

        # Quick actions
        quick_menu = menu.addMenu("Quick Actions")

        # Model actions (will be populated dynamically)
        self.model_menu = quick_menu.addMenu("Models")
        self.update_model_menu()

        quick_menu.addSeparator()

        # Start/Stop all
        start_all_action = QAction("Start All", self)
        start_all_action.triggered.connect(self.start_all_models)
        quick_menu.addAction(start_all_action)

        stop_all_action = QAction("Stop All", self)
        stop_all_action.triggered.connect(self.stop_all_models)
        quick_menu.addAction(stop_all_action)

        menu.addSeparator()

        # Resource status
        self.resource_action = QAction("Resources: Checking...", self)
        self.resource_action.setEnabled(False)
        menu.addAction(self.resource_action)

        menu.addSeparator()

        # Show main window
        show_action = QAction("Show Manager", self)
        show_action.triggered.connect(self.show_main_window.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def setup_tooltips(self):
        """Setup tooltips and messages"""
        self.activated.connect(self.on_activated)

    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(10000)  # Update every 10 seconds

    def update_model_menu(self):
        """Update model menu with available models"""
        try:
            import asyncio

            loop = asyncio.new_event_loop()
            models = loop.run_until_complete(self.ollama_client.list_models())
            running_models = loop.run_until_complete(
                self.ollama_client.running_models()
            )

            # Clear existing actions
            self.model_menu.clear()

            # Add model actions
            for model in models:
                is_running = any(rm.model == model.name for rm in running_models)

                if is_running:
                    action = QAction(f"🟢 {model.name}", self)
                    action.triggered.connect(
                        lambda checked, name=model.name: self.stop_model(name)
                    )
                else:
                    action = QAction(f"🔴 {model.name}", self)
                    action.triggered.connect(
                        lambda checked, name=model.name: self.start_model(name)
                    )

                self.model_menu.addAction(action)

            if not models:
                no_models_action = QAction("No models available", self)
                no_models_action.setEnabled(False)
                self.model_menu.addAction(no_models_action)

        except Exception as e:
            error_action = QAction("Error loading models", self)
            error_action.setEnabled(False)
            self.model_menu.addAction(error_action)

    def update_status(self):
        """Update tray status"""
        try:
            # Update resource status
            resources = self.resource_monitor.get_system_resources()

            status_text = (
                f"RAM: {resources.ram_percent:.0f}% | CPU: {resources.cpu_percent:.0f}%"
            )

            if resources.gpu_info:
                gpu = resources.gpu_info[0]
                status_text += f" | VRAM: {gpu['memory_percent']:.0f}%"

            self.resource_action.setText(f"Resources: {status_text}")

            # Update tooltip
            self.setToolTip(f"Local AI Model Manager\n{status_text}")

            # Update model menu
            self.update_model_menu()

            # Check for alerts
            alerts = self.resource_monitor.check_memory_thresholds()
            if alerts["critical"]:
                self.show_notification(
                    "Critical Memory Usage",
                    "Memory usage is critical. Models may be auto-unloaded.",
                    "warning",
                )
            elif alerts["ram_high"]:
                self.setToolTip(
                    f"Local AI Model Manager - ⚠️ High RAM Usage\n{status_text}"
                )

        except Exception as e:
            self.resource_action.setText("Resources: Error")
            print(f"Error updating tray status: {e}")

    def on_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window.emit()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click - show context menu
            pass

    def start_model(self, model_name: str):
        """Start a model"""
        if self.model_queue is None:
            self.show_notification(
                "Error",
                "Tray actions require the main application queue to be running.",
                "error",
            )
            return

        try:
            import asyncio

            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.model_queue.load_model(model_name))

            self.show_notification(
                "Model Queued",
                f"Model {model_name} queued for start",
            )
            self.quick_start_model.emit(model_name)

        except Exception as e:
            self.show_notification(
                "Error", f"Failed to start model {model_name}: {str(e)}", "error"
            )

    def stop_model(self, model_name: str):
        """Stop a model"""
        if self.model_queue is None:
            self.show_notification(
                "Error",
                "Tray actions require the main application queue to be running.",
                "error",
            )
            return

        try:
            import asyncio

            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.model_queue.unload_model(model_name))

            self.show_notification(
                "Model Queued",
                f"Model {model_name} queued for stop",
            )
            self.quick_stop_model.emit(model_name)

        except Exception as e:
            self.show_notification(
                "Error", f"Failed to stop model {model_name}: {str(e)}", "error"
            )

    def start_all_models(self):
        """Start all models"""
        if self.model_queue is None:
            self.show_notification(
                "Error",
                "Tray actions require the main application queue to be running.",
                "error",
            )
            return

        try:
            import asyncio

            loop = asyncio.new_event_loop()
            models = loop.run_until_complete(self.ollama_client.list_models())

            for model in models:
                loop.run_until_complete(self.model_queue.load_model(model.name))

            self.show_notification(
                "Models Queued",
                f"Queued {len(models)} models for start",
            )

        except Exception as e:
            self.show_notification(
                "Error", f"Failed to start models: {str(e)}", "error"
            )

    def stop_all_models(self):
        """Stop all models"""
        if self.model_queue is None:
            self.show_notification(
                "Error",
                "Tray actions require the main application queue to be running.",
                "error",
            )
            return

        try:
            import asyncio

            loop = asyncio.new_event_loop()
            running_models = loop.run_until_complete(
                self.ollama_client.running_models()
            )

            for model in running_models:
                loop.run_until_complete(self.model_queue.unload_model(model.name))

            self.show_notification(
                "Models Queued",
                f"Queued {len(running_models)} models for stop",
            )

        except Exception as e:
            self.show_notification("Error", f"Failed to stop models: {str(e)}", "error")

    def show_notification(self, title: str, message: str, icon_type: str = "info"):
        """Show system notification"""
        # Map icon types to QSystemTrayIcon message icons
        icon_map = {
            "info": QSystemTrayIcon.Information,
            "warning": QSystemTrayIcon.Warning,
            "error": QSystemTrayIcon.Critical,
        }

        icon = icon_map.get(icon_type, QSystemTrayIcon.Information)

        self.showMessage(title, message, icon, 5000)  # Show for 5 seconds

    def exit_application(self):
        """Exit the application"""
        reply = QMessageBox.question(
            None,
            "Confirm Exit",
            "Are you sure you want to exit Local AI Model Manager?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        main_window = self.parent()
        if main_window and hasattr(main_window, "stop_ollama_and_exit"):
            main_window.stop_ollama_and_exit()
            return

        # Fallback: stop models and quit
        try:
            from src.model_queue import ModelQueue
            import asyncio

            queue = ModelQueue()
            loop = asyncio.new_event_loop()
            running_models = loop.run_until_complete(
                self.ollama_client.running_models()
            )

            for model in running_models:
                loop.run_until_complete(queue.unload_model(model.name))
        except Exception as e:
            print(f"Error stopping models on exit: {e}")

        from PySide6.QtWidgets import QApplication

        QApplication.instance().quit()
