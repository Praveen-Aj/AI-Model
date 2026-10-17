"""
Model Management Widget for Local AI Model Manager - Fixed Version
"""

import asyncio
import time
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLabel,
    QGroupBox,
    QProgressBar,
    QMessageBox,
    QMenu,
    QHeaderView,
    QSplitter,
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QColor

# Add src to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ollama_client import OllamaClient, Model, RunningModel
from src.model_queue import ModelQueue
from .activity_log_widget import activity_logger


class ModelWidget(QWidget):
    """Widget for managing models"""

    model_status_changed = Signal(str, str)  # model_name, status
    queue_progress_signal = Signal(str, str, float)

    def __init__(self, ollama_client: OllamaClient, model_queue: ModelQueue):
        super().__init__()
        self.ollama_client = ollama_client
        self.model_queue = model_queue

        self.models = []
        self.running_models = []
        self._last_status_by_model: Dict[str, str] = {}
        self.service_available = False

        self.setup_ui()
        self.setup_timers()
        self.queue_progress_signal.connect(self._queue_progress_callback)

    def set_service_available(self, available: bool):
        """Enable or disable periodic model polling based on Ollama availability"""
        self.service_available = available
        if available:
            if not self.update_timer.isActive():
                self.update_timer.start(3000)
            self.update_models(log=True)
        else:
            if self.update_timer.isActive():
                self.update_timer.stop()

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)

        # Title with colorful styling
        title_label = QLabel("Model Management")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold;
            color: #ffffff;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00ccff, stop:1 #0099cc);
            padding: 10px;
            border-radius: 8px;
            border: 2px solid #006699;
        """)
        layout.addWidget(title_label)

        # Controls with colorful buttons
        controls_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60d660, stop:1 #42a840);
                color: white;
                border: 2px solid #2f8f2f;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7ce26f, stop:1 #54b45a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #38903f, stop:1 #2f7a34);
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_models)
        controls_layout.addWidget(self.refresh_btn)

        self.start_all_btn = QPushButton("Start All")
        self.start_all_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff66, stop:1 #00cc44);
                color: white;
                border: 2px solid #009933;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00dd55);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00aa44, stop:1 #008833);
            }
        """)
        self.start_all_btn.clicked.connect(self.start_all_models)
        controls_layout.addWidget(self.start_all_btn)

        self.stop_all_btn = QPushButton("Stop All")
        self.stop_all_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6666, stop:1 #cc4444);
                color: white;
                border: 2px solid #993333;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8888, stop:1 #dd5555);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #aa4444, stop:1 #883333);
            }
        """)
        self.stop_all_btn.clicked.connect(self.stop_all_models)
        controls_layout.addWidget(self.stop_all_btn)

        layout.addLayout(controls_layout)

        # Queue status strip
        queue_status_layout = QHBoxLayout()
        self.queue_status_label = QLabel("Queue status: Idle")
        self.queue_status_label.setStyleSheet(
            "color: #00ff88; font-weight: bold; padding: 4px;"
        )
        self.queue_progress_bar = QProgressBar()
        self.queue_progress_bar.setRange(0, 100)
        self.queue_progress_bar.setValue(0)
        self.queue_progress_bar.setTextVisible(True)
        self.queue_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4caf50;
                border-radius: 6px;
                background-color: #2e7d32;
                color: white;
                padding: 4px;
            }
            QProgressBar::chunk {
                background-color: #66bb6a;
                border-radius: 6px;
            }
        """)
        queue_status_layout.addWidget(self.queue_status_label)
        queue_status_layout.addWidget(self.queue_progress_bar)
        layout.addLayout(queue_status_layout)

        # Model tree with colorful styling
        self.model_tree = QTreeWidget()
        self.model_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #4080c0;
                color: #ffffff;
                border: 2px solid #306090;
                border-radius: 6px;
                font-size: 11pt;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #5090d0;
            }
            QTreeWidget::item:selected {
                background-color: #ff9900;
                color: #000000;
            }
            QTreeWidget::header {
                background-color: #306090;
                color: #ffffff;
                border: 1px solid #205080;
                padding: 8px;
                font-weight: bold;
            }
        """)
        self.model_tree.setHeaderLabels(["Model", "Status", "Size", "Modified"])
        self.model_tree.setRootIsDecorated(False)
        self.model_tree.setAlternatingRowColors(True)
        self.model_tree.setSelectionBehavior(QTreeWidget.SelectRows)
        self.model_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.model_tree.setFocusPolicy(Qt.StrongFocus)
        self.model_tree.itemClicked.connect(self.on_model_selected)
        self.model_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.model_tree.customContextMenuRequested.connect(self.show_context_menu)

        # Set column widths
        header = self.model_tree.header()
        header.setStretchLastSection(False)
        header.resizeSection(0, 200)  # Model name
        header.resizeSection(1, 100)  # Status
        header.resizeSection(2, 100)  # Size
        header.resizeSection(3, 150)  # Modified

        layout.addWidget(self.model_tree)

        # Model details
        details_group = QGroupBox("Model Details")
        details_layout = QVBoxLayout(details_group)

        self.model_name_label = QLabel("Select a model to view details")
        self.model_size_label = QLabel("")
        self.model_arch_label = QLabel("")
        self.model_params_label = QLabel("")
        self.model_context_label = QLabel("")
        self.model_capabilities_label = QLabel("")

        details_layout.addWidget(self.model_name_label)
        details_layout.addWidget(self.model_size_label)
        details_layout.addWidget(self.model_arch_label)
        details_layout.addWidget(self.model_params_label)
        details_layout.addWidget(self.model_context_label)
        details_layout.addWidget(self.model_capabilities_label)

        layout.addWidget(details_group)

        # Individual model controls
        individual_layout = QHBoxLayout()

        self.start_selected_btn = QPushButton("Start Selected")
        self.start_selected_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff66, stop:1 #00cc44);
                color: white;
                border: 2px solid #009933;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00dd55);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00aa44, stop:1 #008833);
            }
        """)
        self.start_selected_btn.clicked.connect(self.start_selected_model)
        individual_layout.addWidget(self.start_selected_btn)

        self.stop_selected_btn = QPushButton("Stop Selected")
        self.stop_selected_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6666, stop:1 #cc4444);
                color: white;
                border: 2px solid #993333;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8888, stop:1 #dd5555);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #aa4444, stop:1 #883333);
            }
        """)
        self.stop_selected_btn.clicked.connect(self.stop_selected_model)
        individual_layout.addWidget(self.stop_selected_btn)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        self.select_all_btn.clicked.connect(self.select_all_models)
        individual_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        individual_layout.addWidget(self.clear_selection_btn)

        layout.addLayout(individual_layout)

    def setup_timers(self):
        """Setup update timers"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._timer_refresh_models)

    def _timer_refresh_models(self):
        """Refresh models from timer without extra log noise"""
        self.update_models(log=False)

    def update_models(self, log: bool = False):
        """Update model list"""
        checked_models = self.get_checked_models()
        loop = asyncio.new_event_loop()
        try:
            if log:
                activity_logger.log_info("Refreshing model list", None, "refresh")

            # Get available models
            self.models = loop.run_until_complete(self.ollama_client.list_models())

            # Get running models
            self.running_models = loop.run_until_complete(
                self.ollama_client.running_models()
            )

            if log:
                activity_logger.log_debug(
                    f"Available models: {[m.name for m in self.models]}",
                    None,
                    "refresh",
                )
                activity_logger.log_debug(
                    f"Running models: {[rm.model or rm.name for rm in self.running_models]}",
                    None,
                    "ps",
                )

            # Update tree
            self.update_model_tree(checked_models)

        except Exception as e:
            activity_logger.log_error(
                f"Error updating model list: {str(e)}", None, "refresh"
            )
        finally:
            if not loop.is_closed():
                loop.close()

    def update_model_tree(self, checked_models=None):
        """Update the model tree widget"""
        if checked_models is None:
            checked_models = []
        self.model_tree.clear()

        running_model_names = set()
        for rm in self.running_models:
            if rm.model:
                running_model_names.add(rm.model.lower())
            if rm.name:
                running_model_names.add(rm.name.lower())

        for model in self.models:
            normalized_model_name = model.name.lower()
            is_running = any(
                normalized_model_name == running_name
                or normalized_model_name in running_name
                or running_name in normalized_model_name
                for running_name in running_model_names
            )

            previous_status = self._last_status_by_model.get(model.name)
            current_status = "Running" if is_running else "Stopped"
            if previous_status != current_status:
                self._last_status_by_model[model.name] = current_status
                activity_logger.log_debug(
                    f"Model {model.name} status changed to {current_status}",
                    model.name,
                    "status",
                )

            item = QTreeWidgetItem()
            item.setText(0, model.name)
            item.setText(1, "Running" if is_running else "Stopped")
            item.setText(2, self.format_size(model.size) if model.size else "Unknown")
            item.setCheckState(
                0, Qt.Checked if model.name in checked_models else Qt.Unchecked
            )
            item.setText(
                3,
                (
                    model.modified_at.strftime("%Y-%m-%d %H:%M")
                    if model.modified_at
                    else "Unknown"
                ),
            )

            # Store model data
            item.setData(0, Qt.UserRole, model)

            # Set color based on status
            if is_running:
                item.setForeground(1, QColor(0, 255, 0))  # Bright green
            else:
                item.setForeground(1, QColor(255, 100, 100))  # Light red

            self.model_tree.addTopLevelItem(item)

    def format_size(self, size_bytes: int) -> str:
        """Format size in bytes to GB with one decimal place"""
        if not size_bytes:
            return "Unknown"
        return f"{size_bytes / (1024**3):.1f}GB"

    def on_model_selected(self, item: QTreeWidgetItem, column: int):
        """Handle model selection"""
        model = item.data(0, Qt.UserRole)
        if model:
            self.show_model_details(model)

    def show_model_details(self, model: Model):
        """Show model details"""
        self.model_name_label.setText(f"Name: {model.name}")
        self.model_size_label.setText(
            f"Size: {self.format_size(model.size)}" if model.size else "Size: Unknown"
        )

        # Get details from the details dictionary
        details = model.details if hasattr(model, "details") and model.details else {}

        architecture = details.get("architecture", "Unknown")
        parameters = details.get("parameter_count", "Unknown")
        context = details.get("context_length", "Unknown")
        capabilities = details.get("capabilities", [])

        self.model_arch_label.setText(f"Architecture: {architecture}")
        self.model_params_label.setText(f"Parameters: {parameters}")
        self.model_context_label.setText(f"Context: {context}")

        if capabilities and isinstance(capabilities, list):
            capabilities_str = ", ".join(capabilities)
            self.model_capabilities_label.setText(f"Capabilities: {capabilities_str}")
        else:
            self.model_capabilities_label.setText("Capabilities: Unknown")

    def clear_model_details(self):
        """Clear model details"""
        self.model_name_label.setText("Select a model to view details")
        self.model_size_label.setText("")
        self.model_arch_label.setText("")
        self.model_params_label.setText("")
        self.model_context_label.setText("")
        self.model_capabilities_label.setText("")

    def show_context_menu(self, position):
        """Show context menu for model"""
        item = self.model_tree.itemAt(position)
        if not item:
            return

        model = item.data(0, Qt.UserRole)
        if not model:
            return

        menu = QMenu(self)

        # Start/Stop action
        normalized_model_name = model.name.lower()
        is_running = any(
            normalized_model_name == (rm.model or rm.name or "").lower()
            or normalized_model_name in (rm.model or rm.name or "").lower()
            or (rm.model or rm.name or "").lower() in normalized_model_name
            for rm in self.running_models
        )
        if is_running:
            stop_action = menu.addAction("Stop Model")
            stop_action.triggered.connect(lambda: self.stop_model(model.name))
        else:
            start_action = menu.addAction("Start Model")
            start_action.triggered.connect(lambda: self.start_model(model.name))
            warmup_action = menu.addAction("Warmup Model")
            warmup_action.triggered.connect(lambda: self.warmup_model(model.name))

        menu.addSeparator()

        # Model info
        info_action = menu.addAction("Model Info")
        info_action.triggered.connect(lambda: self.show_model_info(model))

        menu.exec_(self.model_tree.mapToGlobal(position))

    def show_model_info(self, model: Model):
        """Show detailed model information"""
        loop = asyncio.new_event_loop()
        try:
            info = loop.run_until_complete(
                self.ollama_client.get_model_info(model.name)
            )

            # Create info dialog
            msg = QMessageBox(self)
            msg.setWindowTitle(f"Model Info: {model.name}")
            msg.setText(f"Architecture: {info.get('architecture', 'Unknown')}")
            msg.setInformativeText(
                f"Parameters: {info.get('parameter_count', 'Unknown')}"
            )
            msg.exec_()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to get model info: {str(e)}")
        finally:
            if not loop.is_closed():
                loop.close()

    def _queue_progress_callback(self, model_name: str, message: str, progress: float):
        """Handle progress updates from queue operations"""
        self.model_status_changed.emit(model_name, message)
        activity_logger.log_debug(
            f"Queue progress for {model_name}: {message} ({progress:.0%})",
            model_name,
            "queue",
        )
        self._update_queue_status(message, progress)

        if (
            progress >= 1.0
            or "completed" in message.lower()
            or "failed" in message.lower()
        ):
            QTimer.singleShot(500, self.update_models)

    def _update_queue_status(self, message: str, progress: float):
        """Update the queue status strip"""
        percent = min(max(int(progress * 100), 0), 100)
        self.queue_status_label.setText(f"Queue status: {message} ({percent}%)")
        self.queue_progress_bar.setValue(percent)
        if "failed" in message.lower():
            self.queue_status_label.setStyleSheet(
                "color: #ff6666; font-weight: bold; padding: 4px;"
            )
        elif percent >= 100:
            self.queue_status_label.setStyleSheet(
                "color: #88ff88; font-weight: bold; padding: 4px;"
            )
        else:
            self.queue_status_label.setStyleSheet(
                "color: #00ff88; font-weight: bold; padding: 4px;"
            )

    def start_model(self, model_name: str):
        """Start a model"""
        start_time = time.time()
        activity_logger.log_info("Queueing model start", model_name, "load")

        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self.model_queue.load_model(
                    model_name,
                    progress_callback=lambda msg, prog: self.queue_progress_signal.emit(
                        model_name, msg, prog
                    ),
                )
            )

            self.update_models()
            duration = time.time() - start_time
            activity_logger.log_success(
                "Model queued successfully", model_name, "load", duration
            )
            self.model_status_changed.emit(model_name, "Queued")
        except Exception as e:
            duration = time.time() - start_time
            activity_logger.log_error(
                f"Failed to queue model: {str(e)}", model_name, "load", duration
            )
            QMessageBox.warning(self, "Error", f"Failed to start model: {str(e)}")
        finally:
            if not loop.is_closed():
                loop.close()

    def stop_model(self, model_name: str):
        """Stop a model"""
        start_time = time.time()
        activity_logger.log_info("Queueing model stop", model_name, "unload")

        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self.model_queue.unload_model(
                    model_name,
                    progress_callback=lambda msg, prog: self.queue_progress_signal.emit(
                        model_name, msg, prog
                    ),
                )
            )

            self.update_models()
            duration = time.time() - start_time
            activity_logger.log_success(
                "Model queued for unload", model_name, "unload", duration
            )
            self.model_status_changed.emit(model_name, "Queued")
        except Exception as e:
            duration = time.time() - start_time
            activity_logger.log_error(
                f"Failed to queue model stop: {str(e)}", model_name, "unload", duration
            )
            QMessageBox.warning(self, "Error", f"Failed to stop model: {str(e)}")
        finally:
            if not loop.is_closed():
                loop.close()

    def warmup_model(self, model_name: str):
        """Warmup a model"""
        start_time = time.time()
        activity_logger.log_info("Warming up model", model_name, "warmup")

        try:
            loop = asyncio.new_event_loop()
            success = loop.run_until_complete(
                self.ollama_client.warmup_model(model_name)
            )

            duration = time.time() - start_time

            if success:
                activity_logger.log_success(
                    "Model warmed up successfully", model_name, "warmup", duration
                )
                self.model_status_changed.emit(model_name, "Warmed up")
            else:
                activity_logger.log_error(
                    "Model warmup failed", model_name, "warmup", duration
                )
                self.model_status_changed.emit(model_name, "Warmup failed")

        except Exception as e:
            duration = time.time() - start_time
            activity_logger.log_error(
                f"Failed to warmup model: {str(e)}", model_name, "warmup", duration
            )
            QMessageBox.warning(self, "Error", f"Failed to warmup model: {str(e)}")

    def refresh_models(self):
        """Refresh models from Ollama"""
        if not self.service_available:
            activity_logger.log_warning(
                "Cannot refresh models: Ollama service is offline.",
                None,
                "refresh",
            )
            return
        self.update_models(log=True)

    def start_selected_model(self):
        """Start selected model"""
        current_item = self.model_tree.currentItem()
        checked_models = self.get_checked_models()
        if checked_models:
            for model_name in checked_models:
                self.start_model(model_name)
            return

        if current_item:
            model = current_item.data(0, Qt.UserRole)
            if model:
                self.start_model(model.name)

    def stop_selected_model(self):
        """Stop selected model"""
        current_item = self.model_tree.currentItem()
        checked_models = self.get_checked_models()
        if checked_models:
            for model_name in checked_models:
                self.stop_model(model_name)
            return

        if current_item:
            model = current_item.data(0, Qt.UserRole)
            if model:
                self.stop_model(model.name)

    def warmup_selected_model(self):
        """Warmup selected model"""
        current_item = self.model_tree.currentItem()
        if current_item:
            model = current_item.data(0, Qt.UserRole)
            if model:
                self.warmup_model(model.name)

    def start_all_models(self):
        """Start all models"""
        for model in self.models:
            self.start_model(model.name)

    def stop_all_models(self):
        """Stop all models"""
        for model in self.models:
            self.stop_model(model.name)

    def select_all_models(self):
        """Select all models with checkboxes"""
        root_count = self.model_tree.topLevelItemCount()
        for i in range(root_count):
            item = self.model_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)

    def clear_selection(self):
        """Clear all checkbox selections"""
        root_count = self.model_tree.topLevelItemCount()
        for i in range(root_count):
            item = self.model_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)

    def get_checked_models(self):
        """Return checked model names"""
        checked = []
        root_count = self.model_tree.topLevelItemCount()
        for i in range(root_count):
            item = self.model_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                model = item.data(0, Qt.UserRole)
                if model:
                    checked.append(model.name)
        return checked
