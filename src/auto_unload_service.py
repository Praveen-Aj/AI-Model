"""
Auto-Unload Service for Model Manager
Automatically unloads idle models based on configurable rules
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from ollama_client import OllamaClient, RunningModel
from resource_monitor import ResourceMonitor
from database import DatabaseManager

@dataclass
class AutoUnloadRule:
    name: str
    condition: str
    action: str
    enabled: bool = True
    priority: int = 0

class AutoUnloadService:
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval  # seconds
        self.running = False
        self.task = None
        
        self.ollama_client = OllamaClient()
        self.resource_monitor = ResourceMonitor()
        self.db = DatabaseManager()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Default rules
        self.rules = [
            AutoUnloadRule(
                name="high_ram_usage",
                condition="ram_percent > 85",
                action="unload_oldest_idle",
                priority=1
            ),
            AutoUnloadRule(
                name="idle_timeout",
                condition="idle_minutes > 15",
                action="unload_idle_models",
                priority=2
            ),
            AutoUnloadRule(
                name="critical_memory",
                condition="ram_percent > 95",
                action="emergency_unload",
                priority=0  # Highest priority
            )
        ]
        
        # Track model activity
        self.model_activity: Dict[str, datetime] = {}
        self.last_check = datetime.now()
    
    async def start(self):
        """Start the auto-unload service"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        self.logger.info("Auto-unload service started")
    
    async def stop(self):
        """Stop the auto-unload service"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info("Auto-unload service stopped")
    
    async def _run_loop(self):
        """Main service loop"""
        while self.running:
            try:
                await self._check_and_unload()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-unload service error: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_and_unload(self):
        """Check conditions and perform unloads"""
        self.last_check = datetime.now()
        
        # Get current state
        running_models = await self.ollama_client.running_models()
        resources = self.resource_monitor.get_system_resources()
        
        if not running_models:
            return  # No models to unload
        
        # Update model activity tracking
        await self._update_model_activity(running_models)
        
        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted([r for r in self.rules if r.enabled], key=lambda x: x.priority)
        
        for rule in sorted_rules:
            if await self._evaluate_condition(rule.condition, resources, running_models):
                self.logger.info(f"Triggering rule: {rule.name}")
                await self._execute_action(rule.action, running_models, resources)
                
                # Check if models were unloaded and break if so
                new_running = await self.ollama_client.running_models()
                if len(new_running) < len(running_models):
                    break
    
    async def _update_model_activity(self, running_models: List[RunningModel]):
        """Update model activity tracking"""
        current_time = datetime.now()
        
        for model in running_models:
            if model.model not in self.model_activity:
                # New model detected
                self.model_activity[model.model] = current_time
                self.logger.info(f"Tracking activity for new model: {model.model}")
    
    async def _evaluate_condition(self, condition: str, resources, running_models: List[RunningModel]) -> bool:
        """Evaluate a rule condition"""
        try:
            # Create a safe evaluation context
            context = {
                'ram_percent': resources.ram_percent,
                'cpu_percent': resources.cpu_percent,
                'running_models_count': len(running_models),
                'current_time': datetime.now()
            }
            
            # Add GPU info if available
            if resources.gpu_info:
                context['vram_percent'] = resources.gpu_info[0]['memory_percent']
            
            # Add idle time for each model
            for model in running_models:
                if model.model in self.model_activity:
                    last_activity = self.model_activity[model.model]
                    idle_minutes = (datetime.now() - last_activity).total_seconds() / 60
                    context[f'{model.model}_idle_minutes'] = idle_minutes
            
            # Check for any idle model
            idle_times = []
            for model in running_models:
                if model.model in self.model_activity:
                    last_activity = self.model_activity[model.model]
                    idle_minutes = (datetime.now() - last_activity).total_seconds() / 60
                    idle_times.append(idle_minutes)
            
            context['idle_minutes'] = max(idle_times) if idle_times else 0
            context['min_idle_minutes'] = min(idle_times) if idle_times else 0
            
            # Evaluate condition safely
            return eval(condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {str(e)}")
            return False
    
    async def _execute_action(self, action: str, running_models: List[RunningModel], resources):
        """Execute an unload action"""
        try:
            if action == "unload_oldest_idle":
                await self._unload_oldest_idle_model(running_models)
            elif action == "unload_idle_models":
                await self._unload_idle_models(running_models)
            elif action == "emergency_unload":
                await self._emergency_unload(running_models)
            else:
                self.logger.warning(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Error executing action '{action}': {str(e)}")
    
    async def _unload_oldest_idle_model(self, running_models: List[RunningModel]):
        """Unload the oldest idle model"""
        models_with_idle = []
        
        for model in running_models:
            if model.model in self.model_activity:
                last_activity = self.model_activity[model.model]
                idle_minutes = (datetime.now() - last_activity).total_seconds() / 60
                models_with_idle.append((model.model, idle_minutes, last_activity))
        
        if models_with_idle:
            # Sort by last activity time
            models_with_idle.sort(key=lambda x: x[2])
            oldest_model = models_with_idle[0][0]
            
            success = await self.ollama_client.stop_model(oldest_model)
            if success:
                self.model_activity.pop(oldest_model, None)
                self.logger.info(f"Auto-unloaded oldest idle model: {oldest_model}")
            else:
                self.logger.error(f"Failed to auto-unload model: {oldest_model}")
    
    async def _unload_idle_models(self, running_models: List[RunningModel]):
        """Unload all models that have been idle too long"""
        auto_unload_minutes = int(self.db.get_setting('auto_unload_minutes', '15'))
        
        for model in running_models:
            if model.model in self.model_activity:
                last_activity = self.model_activity[model.model]
                idle_minutes = (datetime.now() - last_activity).total_seconds() / 60
                
                if idle_minutes > auto_unload_minutes:
                    success = await self.ollama_client.stop_model(model.model)
                    if success:
                        self.model_activity.pop(model.model, None)
                        self.logger.info(f"Auto-unloaded idle model: {model.model} (idle for {idle_minutes:.1f} minutes)")
                    else:
                        self.logger.error(f"Failed to auto-unload model: {model.model}")
    
    async def _emergency_unload(self, running_models: List[RunningModel]):
        """Emergency unload - unload all models except keep one if possible"""
        if not running_models:
            return
        
        # Keep the most recently used model, unload others
        models_with_activity = []
        
        for model in running_models:
            if model.model in self.model_activity:
                last_activity = self.model_activity[model.model]
                models_with_activity.append((model.model, last_activity))
        
        if models_with_activity:
            # Sort by last activity (most recent first)
            models_with_activity.sort(key=lambda x: x[1], reverse=True)
            
            # Keep the most recent, unload others
            models_to_unload = [m[0] for m in models_with_activity[1:]]
            
            for model_name in models_to_unload:
                success = await self.ollama_client.stop_model(model_name)
                if success:
                    self.model_activity.pop(model_name, None)
                    self.logger.info(f"Emergency unloaded model: {model_name}")
                else:
                    self.logger.error(f"Failed to emergency unload model: {model_name}")
        else:
            # No activity data, unload all but one
            models_to_unload = [m.model for m in running_models[:-1]]
            
            for model_name in models_to_unload:
                success = await self.ollama_client.stop_model(model_name)
                if success:
                    self.model_activity.pop(model_name, None)
                    self.logger.info(f"Emergency unloaded model: {model_name}")
    
    def record_model_activity(self, model_name: str):
        """Record activity for a model"""
        self.model_activity[model_name] = datetime.now()
        self.logger.debug(f"Recorded activity for model: {model_name}")
    
    def get_model_idle_time(self, model_name: str) -> Optional[float]:
        """Get idle time in minutes for a model"""
        if model_name not in self.model_activity:
            return None
        
        last_activity = self.model_activity[model_name]
        idle_minutes = (datetime.now() - last_activity).total_seconds() / 60
        return idle_minutes
    
    def get_service_status(self) -> Dict:
        """Get service status"""
        return {
            'running': self.running,
            'last_check': self.last_check.isoformat(),
            'check_interval': self.check_interval,
            'tracked_models': list(self.model_activity.keys()),
            'rules_count': len([r for r in self.rules if r.enabled]),
            'idle_models': [name for name, last_activity in self.model_activity.items() 
                          if (datetime.now() - last_activity).total_seconds() / 60 > 15]
        }

# Test function
async def test_auto_unload_service():
    """Test the auto-unload service"""
    service = AutoUnloadService(check_interval=5)  # 5 second interval for testing
    
    print("Testing auto-unload service...")
    
    # Start the service
    await service.start()
    
    # Simulate some activity
    models = await service.ollama_client.list_models()
    if models:
        model_name = models[0].name
        service.record_model_activity(model_name)
        print(f"Recorded activity for {model_name}")
        
        # Show status
        status = service.get_service_status()
        print(f"Service status: {status}")
    
    # Let it run for a bit
    await asyncio.sleep(10)
    
    # Stop the service
    await service.stop()
    print("Auto-unload service test complete!")

if __name__ == "__main__":
    asyncio.run(test_auto_unload_service())
