"""
Activity Log Widget for Operational Visibility
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QFileDialog,
    QApplication,
)
from PySide6.QtCore import QTimer, Qt, Signal, Slot, QObject
from PySide6.QtGui import QColor, QFont

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class LogLevel(Enum):
    """Log levels with colors"""

    INFO = ("INFO", QColor(0, 150, 0))  # Green
    WARNING = ("WARN", QColor(255, 165, 0))  # Orange
    ERROR = ("ERROR", QColor(200, 0, 0))  # Red
    SUCCESS = ("SUCCESS", QColor(0, 100, 200))  # Blue
    DEBUG = ("DEBUG", QColor(100, 100, 100))  # Gray


class ActivityEntry:
    """Single activity log entry"""

    def __init__(
        self,
        level: LogLevel,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
        duration: Optional[float] = None,
    ):
        self.timestamp = datetime.now()
        self.level = level
        self.message = message
        self.model_name = model_name
        self.operation = operation
        self.duration = duration

    def format_message(self) -> str:
        """Format log entry for display"""
        time_str = self.timestamp.strftime("%H:%M:%S")

        base_msg = f"[{time_str}] {self.level.value[0]} {self.message}"

        if self.model_name:
            base_msg += f" ({self.model_name})"

        if self.operation:
            base_msg += f" [{self.operation}]"

        if self.duration is not None:
            base_msg += f" ({self.duration:.1f}s)"

        return base_msg


class ActivityLogWidget(QWidget):
    """Activity log panel with timestamped operations"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: List[ActivityEntry] = []
        self.max_entries = 1000

        self.setup_ui()
        self.add_entry(LogLevel.INFO, "Activity log initialized")

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)

        # Header with controls
        header_layout = QHBoxLayout()

        # Title
        title_label = QLabel("Activity Log")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Filter controls
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(
            ["All", "INFO", "WARNING", "ERROR", "SUCCESS", "DEBUG"]
        )
        self.filter_combo.currentTextChanged.connect(self.filter_entries)
        header_layout.addWidget(self.filter_combo)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_log)
        header_layout.addWidget(self.clear_btn)

        # Copy button
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_log)
        header_layout.addWidget(self.copy_btn)

        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_log)
        header_layout.addWidget(self.export_btn)

        # Auto-scroll checkbox
        self.autoscroll_check = QCheckBox("Auto-scroll")
        self.autoscroll_check.setChecked(True)
        header_layout.addWidget(self.autoscroll_check)

        layout.addLayout(header_layout)

        # Log list
        self.log_list = QListWidget()
        self.log_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
            QListWidget::item {
                padding: 2px 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #0066cc;
            }
        """)
        layout.addWidget(self.log_list)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search log entries...")
        self.search_edit.textChanged.connect(self.filter_entries)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_edit)

        layout.addLayout(search_layout)

    def add_entry(
        self,
        level: LogLevel,
        message: str,
        model_name: str = None,
        operation: str = None,
        duration: float = None,
    ):
        """Add new log entry"""
        entry = ActivityEntry(level, message, model_name, operation, duration)
        self.entries.append(entry)

        # Limit entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

        # Update display
        self.update_display()

    def update_display(self):
        """Update the log display"""
        self.log_list.clear()

        filter_level = self.filter_combo.currentText()
        search_text = self.search_edit.text().lower()

        for entry in reversed(self.entries):  # Show newest first
            # Apply filters
            if filter_level != "All" and entry.level.name != filter_level:
                continue

            if search_text and search_text not in entry.message.lower():
                if not entry.model_name or search_text not in entry.model_name.lower():
                    if (
                        not entry.operation
                        or search_text not in entry.operation.lower()
                    ):
                        continue

            # Create list item
            item = QListWidgetItem(entry.format_message())

            # Set color based on level
            color = entry.level.value[1]
            item.setForeground(color)

            # Add to list
            self.log_list.addItem(item)

        # Auto-scroll to bottom if enabled
        if self.autoscroll_check.isChecked():
            self.log_list.scrollToBottom()

    def filter_entries(self):
        """Filter log entries"""
        self.update_display()

    def clear_log(self):
        """Clear all log entries"""
        self.entries.clear()
        self.log_list.clear()
        self.add_entry(LogLevel.INFO, "Activity log cleared")

    def copy_log(self):
        """Copy visible log entries to clipboard"""
        log_text = []
        for index in range(self.log_list.count()):
            item = self.log_list.item(index)
            if item:
                log_text.append(item.text())

        QApplication.clipboard().setText("\n".join(log_text))
        self.add_entry(LogLevel.INFO, "Copied visible log entries to clipboard")

    def export_log(self):
        """Export visible log entries to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Activity Log",
            "activity_log.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as output_file:
                    for index in range(self.log_list.count()):
                        item = self.log_list.item(index)
                        if item:
                            output_file.write(item.text() + "\n")
                self.add_entry(LogLevel.INFO, f"Exported log to {file_path}")
            except Exception as exc:
                self.add_entry(LogLevel.ERROR, f"Failed to export log: {exc}")

    def log_model_operation(
        self,
        operation: str,
        model_name: str,
        success: bool,
        duration: float = None,
        error_msg: str = None,
    ):
        """Log model operation with standardized format"""
        if success:
            level = LogLevel.SUCCESS
            message = f"Model {operation} completed successfully"
        else:
            level = LogLevel.ERROR
            message = f"Model {operation} failed"
            if error_msg:
                message += f": {error_msg}"

        self.add_entry(level, message, model_name, operation, duration)

    def log_resource_alert(self, alert_type: str, message: str):
        """Log resource alert"""
        level_name = (
            "ERROR"
            if alert_type == "critical"
            else "WARNING" if alert_type == "warning" else "INFO"
        )
        self.log_entry.emit(
            level_name, f"Resource {alert_type}: {message}", None, None, None
        )

    def log_debug(
        self,
        message: str,
        model_name: str = None,
        operation: str = None,
        duration: float = None,
    ):
        """Log debug message"""
        self.add_entry(LogLevel.DEBUG, message, model_name, operation, duration)

    def log_queue_operation(
        self, operation: str, model_name: str, queue_size: int = None
    ):
        """Log queue operation"""
        message = f"Queue {operation}: {model_name}"
        if queue_size is not None:
            message += f" (queue size: {queue_size})"

        self.add_entry(LogLevel.DEBUG, message, model_name, operation)

    def log_profile_operation(self, operation: str, profile_name: str, success: bool):
        """Log profile operation"""
        if success:
            level = LogLevel.SUCCESS
            message = f"Profile {operation} completed"
        else:
            level = LogLevel.ERROR
            message = f"Profile {operation} failed"

        self.add_entry(level, message, None, f"Profile {operation}")

    def get_recent_entries(self, count: int = 10) -> List[ActivityEntry]:
        """Get recent log entries"""
        return self.entries[-count:]


class ActivityLogger(QObject):
    """Global activity logger for the application"""

    log_entry = Signal(str, str, object, object, object)

    def __init__(self):
        super().__init__()
        self.widgets: List[ActivityLogWidget] = []
        self.log_entry.connect(self._dispatch_log_entry)

    def add_widget(self, widget: ActivityLogWidget):
        """Add a widget to receive log updates"""
        self.widgets.append(widget)

    @Slot(str, str, object, object, object)
    def _dispatch_log_entry(
        self,
        level: str,
        message: str,
        model_name: Optional[str],
        operation: Optional[str],
        duration: Optional[float],
    ):
        for widget in self.widgets:
            if level in LogLevel.__members__:
                log_level = LogLevel[level]
            else:
                log_level = LogLevel.DEBUG
            widget.add_entry(log_level, message, model_name, operation, duration)

    def log_info(
        self,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        """Log info message"""
        self.log_entry.emit("INFO", message, model_name, operation, None)

    def log_warning(
        self,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        """Log warning message"""
        self.log_entry.emit("WARNING", message, model_name, operation, None)

    def log_error(
        self,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        """Log error message"""
        self.log_entry.emit("ERROR", message, model_name, operation, None)

    def log_success(
        self,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
        duration: Optional[float] = None,
    ):
        """Log success message"""
        self.log_entry.emit("SUCCESS", message, model_name, operation, duration)

    def log_debug(
        self,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
        duration: Optional[float] = None,
    ):
        """Log debug message"""
        self.log_entry.emit("DEBUG", message, model_name, operation, duration)

    def log_model_operation(
        self,
        operation: str,
        model_name: str,
        success: bool,
        duration: float = None,
        error_msg: str = None,
    ):
        """Log model operation"""
        self.log_entry.emit(
            "SUCCESS" if success else "ERROR",
            f"Model {operation} {'completed successfully' if success else 'failed'}"
            + (f": {error_msg}" if error_msg else ""),
            model_name,
            operation,
            duration,
        )

    def log_resource_alert(self, alert_type: str, message: str):
        """Log resource alert"""
        for widget in self.widgets:
            widget.log_resource_alert(alert_type, message)


# Global logger instance
activity_logger = ActivityLogger()
