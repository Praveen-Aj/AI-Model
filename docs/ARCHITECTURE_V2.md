# Local AI Model Manager - Modular Architecture V2

## Directory Structure

```
ai-model-manager/
├── src/                          # Core engine modules
│   ├── __init__.py             # Package initialization
│   ├── ollama_client.py         # Ollama REST API wrapper
│   ├── database.py              # SQLite persistence layer
│   ├── resource_monitor.py       # System resource monitoring
│   ├── model_queue.py           # Async operation queue
│   ├── auto_unload_service.py   # Automation rules engine
│   └── profile_manager.py       # Profile orchestration
├── tests/                         # Test suite
│   └── __init__.py
├── config/                        # Configuration files
│   └── __init__.py
├── docs/                          # Documentation
│   └── __init__.py
├── logs/                          # Application logs
├── data/                          # Runtime data (SQLite DB)
├── app_modular.py               # Streamlit UI (temporary)
├── app.py                        # Legacy Streamlit UI
└── requirements.txt               # Dependencies
```

## Module Dependencies

```
src/
├── ollama_client.py          # Pure HTTP API calls
├── database.py               # SQLite + data models
├── resource_monitor.py        # psutil + nvidia-smi
├── model_queue.py           # asyncio.Queue + operations
├── auto_unload_service.py   # Background rules engine
└── profile_manager.py       # Business logic orchestration

app_modular.py
├── imports all from src/
├── Streamlit presentation layer
└── Will be replaced by PySide6
```

## Import Strategy

### Core Modules (src/)
```python
# src/__init__.py exports clean interface
from src import OllamaClient, DatabaseManager, ResourceMonitor
```

### UI Layer (app_modular.py)
```python
# Add src to path for clean imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
from src import OllamaClient, DatabaseManager, ResourceMonitor
```

## Separation of Concerns

### Engine Layer (src/)
- **Business Logic**: Model orchestration, profiles, automation
- **Data Layer**: Database persistence, configuration
- **External APIs**: Ollama REST client
- **System Integration**: Resource monitoring, process management

### Presentation Layer (app_modular.py)
- **UI Components**: Streamlit widgets, charts, forms
- **User Interactions**: Button clicks, form submissions
- **State Management**: Streamlit session state

### Test Layer (tests/)
- **Unit Tests**: Individual module testing
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Load/stress testing

## Benefits of Modular Architecture

### 1. Clear Separation
- Engine logic independent of UI framework
- Easy to replace Streamlit with PySide6
- Testable components in isolation

### 2. Maintainable Codebase
- Single responsibility per module
- Defined interfaces between layers
- Easy debugging and profiling

### 3. Scalable Structure
- Add new features without touching core
- Swap UI frameworks without engine changes
- Extend test coverage systematically

### 4. Development Workflow
- Parallel development: engine vs UI vs tests
- Independent module deployment
- Clear ownership boundaries

## Migration Path

### Phase 1: Current State
- Engine in src/ (stable)
- UI in app_modular.py (Streamlit)
- Tests in tests/ (building)

### Phase 2: UI Migration
- Keep src/ unchanged
- Replace app_modular.py with PySide6 desktop app
- Add Windows tray integration
- Maintain same engine interface

### Phase 3: Enhancement
- Add VSCode integration hooks
- Implement advanced automation rules
- Extend monitoring capabilities

## Configuration Management

### Runtime Configuration
```python
# config/settings.json
{
    "ollama": {
        "base_url": "http://localhost:11434",
        "timeout": 300
    },
    "auto_unload": {
        "enabled": true,
        "check_interval": 60,
        "rules": [...]
    },
    "ui": {
        "theme": "dark",
        "auto_refresh": true
    }
}
```

### Database Schema
```sql
-- models table
CREATE TABLE models (
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
);

-- profiles table
CREATE TABLE profiles (
    name TEXT PRIMARY KEY,
    models TEXT,
    max_context INTEGER,
    auto_unload_minutes INTEGER,
    ram_threshold INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Next Steps

### Immediate (Phase 1)
1. Fix Unicode logging in all modules
2. Resolve Streamlit async conflicts
3. Add API response validation
4. Create comprehensive test suite

### Short-term (Phase 2)
1. Implement PySide6 desktop UI
2. Add Windows tray integration
3. Create installer package

### Medium-term (Phase 3)
1. VSCode extension integration
2. Advanced automation rules
3. Performance optimization

This modular architecture provides a solid foundation for evolution while maintaining the working orchestration engine.
