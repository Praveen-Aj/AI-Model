# Local AI Model Manager

A modular orchestration engine for managing local Ollama models with automated resource optimization.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app_modular.py
```

## Architecture

### Core Engine (`src/`)
- **ollama_client.py** - Async Ollama REST API wrapper
- **database.py** - SQLite persistence and configuration
- **resource_monitor.py** - System resource monitoring (RAM/VRAM/CPU)
- **model_queue.py** - Async operation queue with progress tracking
- **auto_unload_service.py** - Automation rules engine
- **profile_manager.py** - Model profile orchestration

### Presentation Layer (`app_modular.py`)
- Streamlit-based UI (temporary, will be replaced with PySide6)
- Real-time resource monitoring
- Model lifecycle controls
- Profile management interface

### Data Layer (`data/`)
- SQLite database for models, profiles, settings, usage history
- Automatic schema initialization

## Features

### 🎯 Core Functionality
- **Model Management**: List, load, unload, delete models
- **Resource Monitoring**: Real-time RAM, VRAM, CPU tracking
- **Profile System**: Pre-configured model sets for different workflows
- **Automation**: Auto-unload idle models based on memory thresholds
- **Queue System**: Serialized operations to prevent resource spikes

### 📊 Profiles
- **Coding**: `qwen2.5-coder:7b` - Lightweight development
- **Agent**: `qwen2.5:14b` - Reasoning and complex tasks
- **Lightweight**: `qwen2.5-coder:7b` - Minimal resource usage
- **Full**: Both models for maximum capability

### 🔧 Automation Rules
- **High RAM Usage**: Unload oldest idle model when RAM > 85%
- **Idle Timeout**: Remove models idle for > 15 minutes
- **Critical Memory**: Emergency unload when RAM > 95%

## Operational Status

### ✅ Working
- Model listing and warmup (5-7 second load times)
- Resource monitoring (±2% accuracy)
- Model switching between 14B ↔ 7B models
- Database persistence and queue system

### ⚠️ Needs Fixes
- Unicode logging on Windows (encoding issues)
- Streamlit async event loop conflicts
- API response validation improvements
- Model state synchronization

## Development

### Module Structure
```
src/
├── __init__.py          # Package exports
├── ollama_client.py      # API wrapper
├── database.py           # Data layer
├── resource_monitor.py    # System monitoring
├── model_queue.py       # Operation queue
├── auto_unload_service.py # Automation engine
└── profile_manager.py    # Business logic

tests/                     # Test suite
config/                     # Configuration
logs/                      # Application logs
docs/                       # Documentation
Scripts/                    # Utility scripts
```

### Testing
```bash
# Test individual components
python -m src.ollama_client
python -m src.database
python -m src.resource_monitor

# Integration tests
python tests/test_operations.py
```

## Roadmap

### Phase 1: Stabilization (Current)
- Fix Unicode logging issues
- Resolve Streamlit async conflicts
- Add comprehensive error handling
- Complete test suite

### Phase 2: UI Migration
- Replace Streamlit with PySide6 desktop app
- Add Windows tray integration
- Implement proper async handling

### Phase 3: Integration
- VSCode extension integration
- Advanced automation rules
- Performance optimization

## Configuration

### Settings
- Auto-unload timeout: 15 minutes
- RAM threshold: 80%
- Startup profile: "coding"
- Check interval: 60 seconds

### Database Schema
- Models table: Installed models with usage tracking
- Profiles table: Model sets with configuration
- Settings table: Application preferences
- Usage history: Operational analytics

## Troubleshooting

### Common Issues
1. **Unicode errors**: Fixed with UTF-8 logging
2. **Async conflicts**: Use app_modular.py
3. **Port conflicts**: Use different port (8502)
4. **Ollama not running**: Start with `ollama serve`

### Logs
- Application logs: `logs/`
- Database: `data/models.db`
- Configuration: `config/`

This project provides a solid foundation for local AI model orchestration with room for evolution toward desktop integration and advanced automation.
