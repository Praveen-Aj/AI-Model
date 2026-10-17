"""
Resource Monitoring Widget for Local AI Model Manager
"""

from typing import Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QProgressBar, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.resource_monitor import ResourceMonitor, SystemResources


class ResourceWidget(QWidget):
    """Widget for monitoring system resources"""
    
    resource_alert = Signal(str, str)  # alert_type, message
    
    def __init__(self, resource_monitor: ResourceMonitor):
        super().__init__()
        self.resource_monitor = resource_monitor
        
        self.setup_ui()
        self.setup_timers()
        
        # Initial update
        self.update_resources()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Title with colorful styling - more compact
        title_label = QLabel("System Resources")
        title_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold;
            color: #ffffff;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff6600, stop:1 #ff9900);
            padding: 6px;
            border-radius: 6px;
            border: 2px solid #cc4400;
        """)
        layout.addWidget(title_label)
        
        # Main resource display - more compact layout
        main_layout = QGridLayout()
        main_layout.setSpacing(8)
        
        # RAM Usage with colorful styling - more compact
        ram_group = QGroupBox("RAM")
        ram_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #ff9900;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #5090d0;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
        """)
        ram_layout = QVBoxLayout(ram_group)
        ram_layout.setSpacing(4)
        
        self.ram_progress = QProgressBar()
        self.ram_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ff9900;
                border-radius: 6px;
                text-align: center;
                background-color: #306090;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffcc00, stop:1 #ff9900);
                border-radius: 4px;
            }
        """)
        self.ram_progress.setRange(0, 100)
        ram_layout.addWidget(self.ram_progress)
        
        # Combine RAM label and details into one compact label
        self.ram_label = QLabel("RAM: 0% (0/0GB)")
        self.ram_label.setAlignment(Qt.AlignCenter)
        self.ram_label.setStyleSheet("""
            color: #ffcc00;
            font-size: 10px;
            font-weight: bold;
            background-color: #306090;
            border-radius: 4px;
            padding: 3px;
        """)
        ram_layout.addWidget(self.ram_label)
        
        main_layout.addWidget(ram_group, 0, 0)
        
        # CPU Usage with colorful styling - more compact
        cpu_group = QGroupBox("CPU")
        cpu_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #00ff66;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #5090d0;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
        """)
        cpu_layout = QVBoxLayout(cpu_group)
        cpu_layout.setSpacing(4)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #00ff66;
                border-radius: 6px;
                text-align: center;
                background-color: #306090;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:1 #00ff66);
                border-radius: 4px;
            }
        """)
        self.cpu_progress.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_progress)
        
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setAlignment(Qt.AlignCenter)
        self.cpu_label.setStyleSheet("""
            color: #ffffff;
            font-size: 10px;
            font-weight: bold;
            background-color: #306090;
            border-radius: 4px;
            padding: 3px;
        """)
        cpu_layout.addWidget(self.cpu_label)
        
        main_layout.addWidget(cpu_group, 0, 1)
        
        # GPU Usage with colorful styling - more compact
        self.gpu_group = QGroupBox("GPU")
        self.gpu_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #ff00ff;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #5090d0;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
        """)
        gpu_layout = QVBoxLayout(self.gpu_group)
        gpu_layout.setSpacing(4)
        
        self.gpu_progress = QProgressBar()
        self.gpu_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ff00ff;
                border-radius: 6px;
                text-align: center;
                background-color: #306090;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff66ff, stop:1 #ff00ff);
                border-radius: 4px;
            }
        """)
        self.gpu_progress.setRange(0, 100)
        gpu_layout.addWidget(self.gpu_progress)
        
        self.gpu_label = QLabel("GPU: 0%")
        self.gpu_label.setAlignment(Qt.AlignCenter)
        self.gpu_label.setStyleSheet("""
            color: #ffffff;
            font-size: 10px;
            font-weight: bold;
            background-color: #306090;
            border-radius: 4px;
            padding: 3px;
        """)
        gpu_layout.addWidget(self.gpu_label)
        
        main_layout.addWidget(self.gpu_group, 1, 0, 1, 2)
        
        # Remove alert area to save space
        layout.addLayout(main_layout)
    
    def setup_timers(self):
        """Setup timers for updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_resources)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def update_resources(self):
        """Update resource display"""
        try:
            resources = self.resource_monitor.get_system_resources()
            
            # Update RAM with compact format
            ram_percent = resources.ram_percent
            self.ram_progress.setValue(int(ram_percent))
            
            ram_used_gb = resources.ram_used / (1024**3)
            ram_total_gb = resources.ram_total / (1024**3)
            self.ram_label.setText(f"RAM: {ram_percent:.0f}% ({ram_used_gb:.1f}/{ram_total_gb:.1f}GB)")
            
            # Update RAM color based on usage
            if ram_percent > 90:
                self.ram_progress.setStyleSheet("""
                    QProgressBar::chunk {
                        background-color: #F44336;
                        border-radius: 3px;
                    }
                """)
            elif ram_percent > 80:
                self.ram_progress.setStyleSheet("""
                    QProgressBar::chunk {
                        background-color: #FF9800;
                        border-radius: 3px;
                    }
                """)
            else:
                self.ram_progress.setStyleSheet("""
                    QProgressBar::chunk {
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #ffcc00, stop:1 #ff9900);
                        border-radius: 4px;
                    }
                """)
            
            # Update CPU
            self.cpu_progress.setValue(int(resources.cpu_percent))
            self.cpu_label.setText(f"CPU: {resources.cpu_percent:.0f}%")
            
            # Update GPU
            gpu_info = resources.gpu_info
            if gpu_info and 'memory' in gpu_info:
                gpu_used = gpu_info['memory'].get('used', 0) / (1024**3)
                gpu_total = gpu_info['memory'].get('total', 0) / (1024**3)
                gpu_percent = (gpu_used / gpu_total * 100) if gpu_total > 0 else 0
                
                self.gpu_progress.setValue(int(gpu_percent))
                self.gpu_label.setText(f"GPU: {gpu_percent:.0f}%")
                
                self.gpu_group.show()
            else:
                self.gpu_group.hide()
                
        except Exception as e:
            print(f"Error updating resources: {e}")


class ResourceGauge(QWidget):
    """Custom gauge widget for resource visualization"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = 0
        self.max_value = 100
        self.color = QColor(76, 175, 80)  # Green
        
        self.setMinimumSize(120, 120)
    
    def setValue(self, value: int):
        """Set gauge value"""
        self.value = max(0, min(value, self.max_value))
        self.update()
    
    def setColor(self, color: QColor):
        """Set gauge color"""
        self.color = color
        self.update()
    
    def paintEvent(self, event):
        """Paint the gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions
        size = min(self.width(), self.height())
        rect = self.rect()
        
        # Draw background circle
        painter.setPen(QPen(QColor(200, 200, 200), 8))
        painter.setBrush(QBrush(Qt.transparent))
        painter.drawEllipse(rect.center(), size//2 - 10, size//2 - 10)
        
        # Draw value arc
        start_angle = 90 * 16  # Start from top
        span_angle = -int((self.value / self.max_value) * 270 * 16)  # 270 degrees total
        
        painter.setPen(QPen(self.color, 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawArc(rect.adjusted(10, 10, -10, -10), start_angle, span_angle)
        
        # Draw text
        painter.setPen(QPen(Qt.black))
        font = QFont()
        font.setBold(True)
        font.setPointSize(20)
        painter.setFont(font)
        
        text = f"{self.value}%"
        painter.drawText(rect, Qt.AlignCenter, text)
        
        # Draw title
        font.setPointSize(10)
        painter.setFont(font)
        title_rect = rect.adjusted(0, size//2 + 10, 0, 0)
        painter.drawText(title_rect, Qt.AlignCenter, self.title)
