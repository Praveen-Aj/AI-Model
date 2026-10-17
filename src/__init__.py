"""
Local AI Model Manager - Core Modules
"""

from .ollama_client import OllamaClient, Model, RunningModel, ModelInfo
from .database import DatabaseManager
from .resource_monitor import ResourceMonitor, SystemResources, GPUInfo
from .model_queue import ModelQueue, OperationType, OperationStatus, QueueOperation
from .auto_unload_service import AutoUnloadService, AutoUnloadRule
from .profile_manager import ProfileManager, ProfileAction

__version__ = "0.1.0"
__all__ = [
    'OllamaClient', 'Model', 'RunningModel', 'ModelInfo',
    'DatabaseManager', 
    'ResourceMonitor', 'SystemResources', 'GPUInfo',
    'ModelQueue', 'OperationType', 'OperationStatus', 'QueueOperation',
    'AutoUnloadService', 'AutoUnloadRule',
    'ProfileManager', 'ProfileAction'
]
