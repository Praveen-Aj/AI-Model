"""
Model Queue for Async Operations
Manages serialized model loading/unloading operations
"""

import asyncio
import logging
import queue
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ollama_client import OllamaClient, Model, RunningModel
from resource_monitor import ResourceMonitor
from database import DatabaseManager


class OperationType(Enum):
    LOAD = "load"
    UNLOAD = "unload"
    DELETE = "delete"
    PULL = "pull"


class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueOperation:
    id: str
    type: OperationType
    model_name: str
    status: OperationStatus = OperationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_callback: Optional[Callable[[str, float], None]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "model_name": self.model_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
        }


class ModelQueue:
    def __init__(self, max_concurrent_operations: int = 1):
        self.max_concurrent_operations = max_concurrent_operations
        self.queue = queue.Queue()
        self.active_operations: Dict[str, QueueOperation] = {}
        self.completed_operations: List[QueueOperation] = []
        self.max_completed_history = 100

        self.ollama_client = OllamaClient()
        self.resource_monitor = ResourceMonitor()
        self.db = DatabaseManager()

        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _activity_logger(self):
        import sys

        mod_name = "src.gui.activity_log_widget"

        # If the GUI logger module is already imported (likely created on main thread),
        # return the real activity_logger. Avoid importing the module from a worker
        # thread because that would instantiate Qt QObjects in a non-Qt thread.
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            try:
                return getattr(mod, "activity_logger")
            except Exception:
                pass

        # Fallback stub logger for non-GUI contexts (worker threads before GUI init)
        class _StubLogger:
            def log_debug(self, message, model_name=None, operation=None, duration=None):
                logging.getLogger(__name__).debug(
                    f"[DEBUG] {message} {f'({model_name})' if model_name else ''} {f'[{operation}]' if operation else ''}"
                )

            def log_info(self, message, model_name=None, operation=None, duration=None):
                logging.getLogger(__name__).info(
                    f"[INFO] {message} {f'({model_name})' if model_name else ''} {f'[{operation}]' if operation else ''}"
                )

            def log_warning(self, message, model_name=None, operation=None, duration=None):
                logging.getLogger(__name__).warning(
                    f"[WARN] {message} {f'({model_name})' if model_name else ''} {f'[{operation}]' if operation else ''}"
                )

            def log_error(self, message, model_name=None, operation=None, duration=None):
                logging.getLogger(__name__).error(
                    f"[ERROR] {message} {f'({model_name})' if model_name else ''} {f'[{operation}]' if operation else ''}"
                )

            def log_success(self, message, model_name=None, operation=None, duration=None):
                logging.getLogger(__name__).info(
                    f"[SUCCESS] {message} {f'({model_name})' if model_name else ''} {f'[{operation}]' if operation else ''}"
                )

        return _StubLogger()

    async def start(self):
        """Start the queue worker"""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self.logger.info("Model queue started")

    async def stop(self):
        """Stop the queue worker"""
        self._running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        self.logger.info("Model queue stopped")

    def _worker_loop(self):
        """Main worker loop running in a background thread"""
        while self._running:
            try:
                operation = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                asyncio.run(self._execute_operation(operation))
            except Exception as e:
                self.logger.error(f"Worker error: {str(e)}")
                time.sleep(1.0)

    async def _execute_operation(self, operation: QueueOperation):
        """Execute a single operation"""
        self.active_operations[operation.id] = operation
        operation.status = OperationStatus.RUNNING
        operation.started_at = datetime.now()

        self._activity_logger().log_debug(
            f"Queue operation started: {operation.type.value} {operation.model_name}",
            operation.model_name,
            "queue",
        )

        try:
            if operation.progress_callback:
                operation.progress_callback(
                    f"Starting {operation.type.value} for {operation.model_name}", 0.0
                )

            if operation.type == OperationType.LOAD:
                await self._load_model(operation)
            elif operation.type == OperationType.UNLOAD:
                await self._unload_model(operation)
            elif operation.type == OperationType.DELETE:
                await self._delete_model(operation)
            elif operation.type == OperationType.PULL:
                await self._pull_model(operation)

            operation.status = OperationStatus.COMPLETED
            operation.completed_at = datetime.now()

            if operation.progress_callback:
                operation.progress_callback(
                    f"Completed {operation.type.value} for {operation.model_name}", 1.0
                )

            self._activity_logger().log_success(
                f"Queue operation completed: {operation.type.value}",
                operation.model_name,
                "queue",
                (operation.completed_at - operation.started_at).total_seconds(),
            )

            # Update database
            if operation.type == OperationType.LOAD:
                load_time = (
                    operation.completed_at - operation.started_at
                ).total_seconds()
                resources = self.resource_monitor.get_system_resources()
                self.db.update_model_usage(
                    operation.model_name, load_time, resources.ram_used
                )

        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()

            self.logger.error(f"Operation {operation.id} failed: {str(e)}")
            self._activity_logger().log_error(
                f"Queue operation failed: {operation.type.value} {str(e)}",
                operation.model_name,
                "queue",
            )

            if operation.progress_callback:
                operation.progress_callback(
                    f"Failed {operation.type.value} for {operation.model_name}: {str(e)}",
                    1.0,
                )

        finally:
            # Move to completed history
            self.active_operations.pop(operation.id, None)
            self.completed_operations.append(operation)

            # Limit history size
            if len(self.completed_operations) > self.max_completed_history:
                self.completed_operations.pop(0)

    async def _load_model(self, operation: QueueOperation):
        """Load/warmup a model"""
        target_model_name = operation.model_name
        model_info = await self.ollama_client.get_model_info(target_model_name)
        if not model_info:
            self._activity_logger().log_warning(
                "Model metadata lookup failed, falling back to available tags",
                operation.model_name,
                "load",
            )
            available_models = await self.ollama_client.list_models()
            matched_model = next(
                (
                    model
                    for model in available_models
                    if model.name.lower() == target_model_name.lower()
                ),
                None,
            )
            if not matched_model:
                raise Exception(f"Model {operation.model_name} not found")
            target_model_name = matched_model.name
            self._activity_logger().log_info(
                f"Resolved model name from tags: {target_model_name}",
                operation.model_name,
                "load",
            )

        # Check if model is already running
        running_models = await self.ollama_client.running_models()
        if any(
            (rm.model and rm.model.lower() == target_model_name.lower())
            or (rm.name and rm.name.lower() == target_model_name.lower())
            for rm in running_models
        ):
            self._activity_logger().log_info(
                "Model already running, skipping load",
                target_model_name,
                "load",
            )
            return  # Already loaded

        # Check memory availability
        resources = self.resource_monitor.get_system_resources()
        if resources.ram_percent > 85:
            raise Exception(f"Insufficient RAM: {resources.ram_percent:.1f}% used")

        # Unload some models if needed
        await self._auto_unload_if_needed()

        if operation.progress_callback:
            operation.progress_callback(f"Starting {target_model_name}", 0.5)

        # Start the model and keep it alive
        success = await self.ollama_client.start_model(target_model_name)
        if not success:
            raise Exception(f"Failed to start model {target_model_name}")

        self._activity_logger().log_debug(
            f"Start request sent for {target_model_name}",
            target_model_name,
            "load",
        )

        # Verify the model actually appears as running
        timeout_seconds = 30
        while timeout_seconds > 0:
            running_models = await self.ollama_client.running_models()
            if any(
                operation.model_name == rm.model
                or operation.model_name in rm.model
                or rm.model in operation.model_name
                for rm in running_models
            ):
                self._activity_logger().log_success(
                    "Model started successfully",
                    operation.model_name,
                    "load",
                )
                return
            await asyncio.sleep(1)
            timeout_seconds -= 1

        raise Exception(
            f"Model {operation.model_name} did not become running after start"
        )

    async def _unload_model(self, operation: QueueOperation):
        """Unload a model"""
        success = await self.ollama_client.stop_model(operation.model_name)
        if not success:
            raise Exception(f"Failed to unload model {operation.model_name}")

    async def _delete_model(self, operation: QueueOperation):
        """Delete a model"""
        # First unload if running
        running_models = await self.ollama_client.running_models()
        if any(m.model == operation.model_name for m in running_models):
            await self.ollama_client.stop_model(operation.model_name)

        # Then delete
        success = await self.ollama_client.delete_model(operation.model_name)
        if not success:
            raise Exception(f"Failed to delete model {operation.model_name}")

    async def _pull_model(self, operation: QueueOperation):
        """Pull a new model"""
        success = await self.ollama_client.pull_model(operation.model_name)
        if not success:
            raise Exception(f"Failed to pull model {operation.model_name}")

    async def _auto_unload_if_needed(self):
        """Automatically unload models if memory is low"""
        resources = self.resource_monitor.get_system_resources()

        if resources.ram_percent < 75:
            return  # Plenty of memory

        # Get running models
        running_models = await self.ollama_client.running_models()

        if not running_models:
            return

        # Sort by usage (least used first)
        models_to_unload = []
        for running_model in running_models:
            model_data = self.db.get_model(running_model.model)
            if model_data:
                models_to_unload.append(
                    {
                        "name": running_model.model,
                        "last_used": model_data.get("last_used"),
                        "usage_count": model_data.get("usage_count", 0),
                    }
                )

        # Sort by last used time and usage count
        models_to_unload.sort(
            key=lambda x: (x["last_used"] or datetime.min, x["usage_count"])
        )

        # Unload the least used model
        if models_to_unload:
            model_to_unload = models_to_unload[0]["name"]
            await self.ollama_client.stop_model(model_to_unload)
            self.logger.info(
                f"Auto-unloaded model {model_to_unload} due to memory pressure"
            )

    async def load_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> str:
        """Queue a model load operation"""
        operation_id = f"load_{model_name}_{datetime.now().timestamp()}"
        operation = QueueOperation(
            id=operation_id,
            type=OperationType.LOAD,
            model_name=model_name,
            progress_callback=progress_callback,
        )

        self.queue.put(operation)
        return operation_id

    async def unload_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> str:
        """Queue a model unload operation"""
        operation_id = f"unload_{model_name}_{datetime.now().timestamp()}"
        operation = QueueOperation(
            id=operation_id,
            type=OperationType.UNLOAD,
            model_name=model_name,
            progress_callback=progress_callback,
        )

        self.queue.put(operation)
        return operation_id

    async def delete_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> str:
        """Queue a model delete operation"""
        operation_id = f"delete_{model_name}_{datetime.now().timestamp()}"
        operation = QueueOperation(
            id=operation_id,
            type=OperationType.DELETE,
            model_name=model_name,
            progress_callback=progress_callback,
        )

        self.queue.put(operation)
        return operation_id

    async def pull_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> str:
        """Queue a model pull operation"""
        operation_id = f"pull_{model_name}_{datetime.now().timestamp()}"
        operation = QueueOperation(
            id=operation_id,
            type=OperationType.PULL,
            model_name=model_name,
            progress_callback=progress_callback,
        )

        self.queue.put(operation)
        return operation_id

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_size": self.queue.qsize(),
            "active_operations": [
                op.to_dict() for op in self.active_operations.values()
            ],
            "recent_operations": [
                op.to_dict() for op in self.completed_operations[-10:]
            ],
            "total_completed": len(self.completed_operations),
        }

    def get_operation(self, operation_id: str) -> Optional[QueueOperation]:
        """Get operation by ID"""
        # Check active operations
        if operation_id in self.active_operations:
            return self.active_operations[operation_id]

        # Check completed operations
        for op in self.completed_operations:
            if op.id == operation_id:
                return op

        return None


# Test function
async def test_model_queue():
    """Test the model queue"""
    queue = ModelQueue()
    await queue.start()

    print("Testing model queue...")

    def progress_callback(message: str, progress: float):
        print(f"Progress: {message} ({progress:.1%})")

    # Test loading a model (if available)
    try:
        models = await queue.ollama_client.list_models()
        if models:
            model_name = models[0].name
            print(f"Testing load of {model_name}")
            op_id = await queue.load_model(model_name, progress_callback)

            # Wait for completion
            for _ in range(60):  # Wait up to 60 seconds
                operation = queue.get_operation(op_id)
                if operation and operation.status in [
                    OperationStatus.COMPLETED,
                    OperationStatus.FAILED,
                ]:
                    print(f"Operation {operation.status.value}")
                    break
                await asyncio.sleep(1)
        else:
            print("No models found to test with")

    except Exception as e:
        print(f"Test error: {str(e)}")

    finally:
        await queue.stop()
        print("Model queue test complete!")


if __name__ == "__main__":
    asyncio.run(test_model_queue())
