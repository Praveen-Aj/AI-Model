"""
Local AI Model Manager - GUI Components
"""

from .main_window import ModelManagerMainWindow
from .model_widget import ModelWidget
from .resource_widget import ResourceWidget
from .profile_widget import ProfileWidget
from .tray_icon import TrayIcon

__version__ = "0.2.0"
__all__ = [
    'ModelManagerMainWindow',
    'ModelWidget', 
    'ResourceWidget',
    'ProfileWidget',
    'TrayIcon'
]
