"""
SQLite Database Management for Model Manager
Handles persistent storage for models, profiles, and usage data
"""

import sqlite3
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str = "data/models.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Models table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    name TEXT PRIMARY KEY,
                    size_gb REAL,
                    architecture TEXT,
                    parameters TEXT,
                    context_length INTEGER,
                    capabilities TEXT,
                    last_used TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    total_load_time REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    name TEXT PRIMARY KEY,
                    models TEXT,
                    max_context INTEGER,
                    auto_unload_minutes INTEGER,
                    ram_threshold INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Usage history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    memory_usage REAL,
                    load_time REAL,
                    FOREIGN KEY (model_name) REFERENCES models (name)
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            self._insert_default_profiles()
    
    def _insert_default_profiles(self):
        """Insert default model profiles"""
        default_profiles = [
            {
                'name': 'coding',
                'models': json.dumps(['qwen2.5-coder:7b']),
                'max_context': 4096,
                'auto_unload_minutes': 10,
                'ram_threshold': 80
            },
            {
                'name': 'agent',
                'models': json.dumps(['qwen2.5:14b']),
                'max_context': 8192,
                'auto_unload_minutes': 15,
                'ram_threshold': 85
            },
            {
                'name': 'lightweight',
                'models': json.dumps(['qwen2.5-coder:7b']),
                'max_context': 2048,
                'auto_unload_minutes': 5,
                'ram_threshold': 75
            },
            {
                'name': 'full',
                'models': json.dumps(['qwen2.5-coder:7b', 'qwen2.5:14b']),
                'max_context': 8192,
                'auto_unload_minutes': 20,
                'ram_threshold': 90
            }
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for profile in default_profiles:
                cursor.execute('''
                    INSERT OR IGNORE INTO profiles 
                    (name, models, max_context, auto_unload_minutes, ram_threshold)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    profile['name'],
                    profile['models'],
                    profile['max_context'],
                    profile['auto_unload_minutes'],
                    profile['ram_threshold']
                ))
            conn.commit()
    
    def upsert_model(self, model_data: Dict[str, Any]):
        """Insert or update model information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO models 
                (name, size_gb, architecture, parameters, context_length, capabilities)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                model_data['name'],
                model_data.get('size_gb', 0),
                model_data.get('architecture', ''),
                model_data.get('parameters', ''),
                model_data.get('context_length', 0),
                json.dumps(model_data.get('capabilities', []))
            ))
            conn.commit()
    
    def get_model(self, name: str) -> Optional[Dict[str, Any]]:
        """Get model information by name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM models WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'name': row['name'],
                    'size_gb': row['size_gb'],
                    'architecture': row['architecture'],
                    'parameters': row['parameters'],
                    'context_length': row['context_length'],
                    'capabilities': json.loads(row['capabilities']) if row['capabilities'] else [],
                    'last_used': row['last_used'],
                    'usage_count': row['usage_count'],
                    'total_load_time': row['total_load_time']
                }
        return None
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all models"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM models ORDER BY last_used DESC')
            
            models = []
            for row in cursor.fetchall():
                models.append({
                    'name': row['name'],
                    'size_gb': row['size_gb'],
                    'architecture': row['architecture'],
                    'parameters': row['parameters'],
                    'context_length': row['context_length'],
                    'capabilities': json.loads(row['capabilities']) if row['capabilities'] else [],
                    'last_used': row['last_used'],
                    'usage_count': row['usage_count'],
                    'total_load_time': row['total_load_time']
                })
            return models
    
    def update_model_usage(self, model_name: str, load_time: float = 0, memory_usage: float = 0):
        """Update model usage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update models table
            cursor.execute('''
                UPDATE models 
                SET last_used = CURRENT_TIMESTAMP,
                    usage_count = usage_count + 1,
                    total_load_time = total_load_time + ?
                WHERE name = ?
            ''', (load_time, model_name))
            
            # Add to usage history
            cursor.execute('''
                INSERT INTO usage_history 
                (model_name, action, memory_usage, load_time)
                VALUES (?, 'load', ?, ?)
            ''', (model_name, memory_usage, load_time))
            
            conn.commit()
    
    def get_profiles(self) -> List[Dict[str, Any]]:
        """Get all profiles"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM profiles ORDER BY name')
            
            profiles = []
            for row in cursor.fetchall():
                profiles.append({
                    'name': row['name'],
                    'models': json.loads(row['models']) if row['models'] else [],
                    'max_context': row['max_context'],
                    'auto_unload_minutes': row['auto_unload_minutes'],
                    'ram_threshold': row['ram_threshold']
                })
            return profiles
    
    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific profile"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM profiles WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'name': row['name'],
                    'models': json.loads(row['models']) if row['models'] else [],
                    'max_context': row['max_context'],
                    'auto_unload_minutes': row['auto_unload_minutes'],
                    'ram_threshold': row['ram_threshold']
                }
        return None
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))
            conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    
    def get_usage_history(self, model_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get usage history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if model_name:
                cursor.execute('''
                    SELECT * FROM usage_history 
                    WHERE model_name = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (model_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM usage_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row['id'],
                    'model_name': row['model_name'],
                    'action': row['action'],
                    'timestamp': row['timestamp'],
                    'memory_usage': row['memory_usage'],
                    'load_time': row['load_time']
                })
            return history

# Test function
def test_database():
    """Test database functionality"""
    db = DatabaseManager()
    
    print("Testing database...")
    
    # Test profiles
    profiles = db.get_profiles()
    print(f"Found {len(profiles)} profiles:")
    for profile in profiles:
        print(f"  - {profile['name']}: {profile['models']}")
    
    # Test settings
    db.set_setting('startup_profile', 'coding')
    startup = db.get_setting('startup_profile')
    print(f"Startup profile: {startup}")
    
    print("Database test complete!")

if __name__ == "__main__":
    test_database()
