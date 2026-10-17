"""
Profile Manager for Model Manager
Handles model profiles and switching
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ollama_client import OllamaClient
from model_queue import ModelQueue
from database import DatabaseManager
from auto_unload_service import AutoUnloadService

@dataclass
class ProfileAction:
    action_type: str  # 'load', 'unload', 'stop_all'
    model_name: Optional[str] = None
    priority: int = 0

class ProfileManager:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.db = DatabaseManager()
        self.queue = ModelQueue()
        self.auto_unload = AutoUnloadService()
        
        self.current_profile = None
        self.profile_switching = False
    
    async def initialize(self):
        """Initialize the profile manager"""
        await self.queue.start()
        await self.auto_unload.start()
        
        # Load startup profile
        startup_profile = self.db.get_setting('startup_profile', 'coding')
        await self.switch_to_profile(startup_profile, force=True)
    
    async def get_available_profiles(self) -> List[Dict]:
        """Get all available profiles"""
        return self.db.get_profiles()
    
    async def get_current_profile(self) -> Optional[Dict]:
        """Get current active profile"""
        if not self.current_profile:
            # Try to detect current state
            running_models = await self.ollama_client.running_models()
            if running_models:
                running_model_names = [m.model for m in running_models]
                profiles = await self.get_available_profiles()
                
                for profile in profiles:
                    if set(profile['models']) == set(running_model_names):
                        self.current_profile = profile
                        break
            else:
                # Default to lightweight profile
                self.current_profile = next((p for p in await self.get_available_profiles() 
                                           if p['name'] == 'lightweight'), None)
        
        return self.current_profile
    
    async def switch_to_profile(self, profile_name: str, force: bool = False) -> bool:
        """Switch to a specific profile"""
        if self.profile_switching and not force:
            return False
        
        try:
            self.profile_switching = True
            
            # Get target profile
            profile = self.db.get_profile(profile_name)
            if not profile:
                return False
            
            # Get current state
            running_models = await self.ollama_client.running_models()
            running_model_names = [m.model for m in running_models]
            
            # Calculate required actions
            actions = self._calculate_profile_actions(
                current_models=running_model_names,
                target_models=profile['models']
            )
            
            # Execute actions in priority order
            for action in sorted(actions, key=lambda x: x.priority):
                if action.action_type == 'unload':
                    await self.queue.unload_model(action.model_name)
                elif action.action_type == 'load':
                    await self.queue.load_model(action.model_name)
                elif action.action_type == 'stop_all':
                    # Unload all running models
                    for model_name in running_model_names:
                        await self.queue.unload_model(model_name)
            
            # Wait for operations to complete
            await self._wait_for_profile_completion(profile['models'])
            
            # Update current profile
            self.current_profile = profile
            self.db.set_setting('current_profile', profile_name)
            
            return True
            
        except Exception as e:
            print(f"Error switching to profile {profile_name}: {str(e)}")
            return False
        finally:
            self.profile_switching = False
    
    def _calculate_profile_actions(self, current_models: List[str], target_models: List[str]) -> List[ProfileAction]:
        """Calculate actions needed to switch profiles"""
        actions = []
        
        # Models to unload (in current but not in target)
        models_to_unload = set(current_models) - set(target_models)
        for model_name in models_to_unload:
            actions.append(ProfileAction(
                action_type='unload',
                model_name=model_name,
                priority=0  # Unload first to free memory
            ))
        
        # Models to load (in target but not in current)
        models_to_load = set(target_models) - set(current_models)
        for model_name in models_to_load:
            actions.append(ProfileAction(
                action_type='load',
                model_name=model_name,
                priority=1  # Load after unloading
            ))
        
        return actions
    
    async def _wait_for_profile_completion(self, target_models: List[str], timeout: int = 300):
        """Wait for profile switch to complete"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check queue status
            queue_status = self.queue.get_queue_status()
            
            if queue_status['queue_size'] == 0 and len(queue_status['active_operations']) == 0:
                # Check if target models are running
                running_models = await self.ollama_client.running_models()
                running_model_names = [m.model for m in running_models]
                
                if set(target_models) == set(running_model_names):
                    return True
            
            await asyncio.sleep(2)
        
        return False
    
    async def create_profile(self, name: str, models: List[str], max_context: int = 8192,
                           auto_unload_minutes: int = 15, ram_threshold: int = 80) -> bool:
        """Create a new profile"""
        try:
            # Validate models exist
            available_models = await self.ollama_client.list_models()
            available_model_names = [m.name for m in available_models]
            
            for model in models:
                if model not in available_model_names:
                    return False  # Model doesn't exist
            
            # Create profile in database
            import json
            profile_data = {
                'name': name,
                'models': json.dumps(models),
                'max_context': max_context,
                'auto_unload_minutes': auto_unload_minutes,
                'ram_threshold': ram_threshold
            }
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO profiles 
                    (name, models, max_context, auto_unload_minutes, ram_threshold)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, profile_data['models'], max_context, auto_unload_minutes, ram_threshold))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error creating profile {name}: {str(e)}")
            return False
    
    async def update_profile(self, name: str, **kwargs) -> bool:
        """Update an existing profile"""
        try:
            profile = self.db.get_profile(name)
            if not profile:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if key in profile:
                    profile[key] = value
            
            # Save to database
            import json
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE profiles SET
                    models = ?,
                    max_context = ?,
                    auto_unload_minutes = ?,
                    ram_threshold = ?
                    WHERE name = ?
                ''', (
                    json.dumps(profile['models']),
                    profile['max_context'],
                    profile['auto_unload_minutes'],
                    profile['ram_threshold'],
                    name
                ))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating profile {name}: {str(e)}")
            return False
    
    async def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        try:
            # Don't allow deleting default profiles
            if name in ['coding', 'agent', 'lightweight', 'full']:
                return False
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM profiles WHERE name = ?', (name,))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting profile {name}: {str(e)}")
            return False
    
    async def get_profile_recommendation(self, task_type: str) -> Optional[str]:
        """Get recommended profile for a task type"""
        recommendations = {
            'coding': 'coding',
            'autocomplete': 'lightweight',
            'agent': 'agent',
            'reasoning': 'agent',
            'chat': 'agent',
            'development': 'full',
            'testing': 'coding'
        }
        
        return recommendations.get(task_type.lower())
    
    async def get_profile_status(self) -> Dict:
        """Get current profile status"""
        current_profile = await self.get_current_profile()
        running_models = await self.ollama_client.running_models()
        
        status = {
            'current_profile': current_profile['name'] if current_profile else None,
            'running_models': [m.model for m in running_models],
            'profile_models': current_profile['models'] if current_profile else [],
            'is_profile_active': False,
            'switching': self.profile_switching
        }
        
        if current_profile:
            status['is_profile_active'] = set(status['running_models']) == set(status['profile_models'])
        
        return status
    
    def record_model_activity(self, model_name: str):
        """Record activity for auto-unload service"""
        self.auto_unload.record_model_activity(model_name)
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.queue.stop()
        await self.auto_unload.stop()

# Test function
async def test_profile_manager():
    """Test profile manager"""
    manager = ProfileManager()
    
    print("Testing profile manager...")
    
    try:
        await manager.initialize()
        
        # Get available profiles
        profiles = await manager.get_available_profiles()
        print(f"Available profiles: {[p['name'] for p in profiles]}")
        
        # Get current status
        status = await manager.get_profile_status()
        print(f"Current status: {status}")
        
        # Test profile recommendation
        rec = await manager.get_profile_recommendation('coding')
        print(f"Recommendation for coding: {rec}")
        
        print("Profile manager test complete!")
        
    finally:
        await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_profile_manager())
