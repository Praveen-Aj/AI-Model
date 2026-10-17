# Local AI Model Manager

A web-based tool for managing local Ollama models with automated resource optimization and profile-based orchestration.

## Features

### Core Functionality
- **Model Visibility**: List installed and running models with detailed information
- **Lifecycle Management**: Start, stop, and delete models with async queue operations
- **Resource Monitoring**: Real-time RAM, VRAM, and CPU usage tracking
- **Profile System**: Pre-configured model sets for different use cases

### Automation
- **Auto-Unload**: Automatically removes idle models based on configurable rules
- **Memory Thresholds**: Intelligent unloading when memory usage exceeds limits
- **Queue Management**: Serialized model operations to prevent resource spikes

### Profiles
- **Coding**: `qwen2.5-coder:7b` - Lightweight for development
- **Agent**: `qwen2.5:14b` - For reasoning and complex tasks  
- **Lightweight**: `qwen2.5-coder:7b` - Minimal resource usage
- **Full**: Both models for maximum capability

## Installation

### Prerequisites
- Python 3.8+
- Ollama installed and running (`http://localhost:11434`)
- NVIDIA GPU (optional, for VRAM monitoring)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve
```

## Usage

### Start the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Basic Workflow

1. **View Models**: See all installed models and their current status
2. **Monitor Resources**: Check RAM/VRAM usage in the sidebar
3. **Load Models**: Click "Start" to warmup models for use
4. **Switch Profiles**: Use profile selector for quick model sets
5. **Configure Settings**: Set auto-unload thresholds and timeouts

### Model Operations

#### Starting a Model
- Select a model from the dropdown
- Click "▶️ Start" to queue the load operation
- Model will be warmed up and ready for use

#### Stopping a Model  
- Select a running model
- Click "⏹️ Stop" to unload and free memory

#### Deleting a Model
- Select a model from the dropdown
- Click "🗑️ Delete" to permanently remove from disk
- **Warning**: This cannot be undone

### Profile Management

#### Available Profiles
- **Coding**: Optimized for code completion and development
- **Agent**: Best for reasoning and complex tasks
- **Lightweight**: Minimal memory footprint
- **Full**: Maximum capability with both models

#### Profile Switching
1. Select profile from sidebar dropdown
2. Click "Load Profile" 
3. System will unload unnecessary models and load required ones

### Resource Monitoring

#### Metrics Displayed
- **RAM Usage**: System memory percentage with color indicators
- **VRAM Usage**: GPU memory usage (if NVIDIA GPU detected)
- **CPU Usage**: Current processor utilization

#### Alert Thresholds
- 🟢 Normal: < 75% RAM, < 80% VRAM
- 🟡 Warning: 75-85% RAM, 80-90% VRAM  
- 🔴 Critical: > 85% RAM, > 90% VRAM

### Automation Settings

#### Auto-Unload Rules
1. **High RAM Usage**: Unload oldest idle model when RAM > 85%
2. **Idle Timeout**: Remove models idle for > 15 minutes
3. **Critical Memory**: Emergency unload when RAM > 95%

#### Configuration
- **Auto-unload after**: Minutes of inactivity before unloading
- **RAM threshold**: Percentage that triggers auto-unload

## Architecture

### Core Components

#### `ollama_client.py`
- Async REST API wrapper for Ollama
- Model listing, loading, and management
- Error handling and timeout management

#### `database.py`  
- SQLite persistence for models and profiles
- Usage history and statistics
- Configuration storage

#### `resource_monitor.py`
- System resource tracking (RAM, VRAM, CPU)
- GPU monitoring via nvidia-smi
- Threshold checking and alerts

#### `model_queue.py`
- Async operation queue for model lifecycle
- Serialized loading to prevent resource spikes
- Progress tracking and error handling

#### `auto_unload_service.py`
- Background service for automatic model management
- Rule-based decision engine
- Activity tracking and idle detection

#### `profile_manager.py`
- Profile-based model orchestration
- Intelligent profile switching
- Model set optimization

### Data Flow
```
Streamlit UI → Model Queue → Ollama Client → Ollama API
     ↓              ↓              ↓
Database ← Resource Monitor ← Auto-Unload Service
```

## Configuration

### Database
- SQLite database stored in `data/models.db`
- Automatic initialization on first run
- Includes models, profiles, usage history, and settings

### Settings
Settings are stored in the database and configurable via the UI:
- `auto_unload_minutes`: Default 15
- `ram_threshold`: Default 80
- `startup_profile`: Default "coding"

### Profiles
Profiles define model sets and behavior:
```json
{
  "name": "coding",
  "models": ["qwen2.5-coder:7b"],
  "max_context": 4096,
  "auto_unload_minutes": 10,
  "ram_threshold": 80
}
```

## Troubleshooting

### Common Issues

#### Ollama Not Connected
- Ensure Ollama is running: `ollama serve`
- Check if accessible: `curl http://localhost:11434`
- Restart the application

#### Models Not Loading
- Check available disk space
- Verify model is installed: `ollama list`
- Check system memory availability

#### GPU Monitoring Not Working
- Install NVIDIA drivers
- Ensure nvidia-smi is in PATH
- Check GPU is recognized by Ollama

#### High Memory Usage
- Enable auto-unload in settings
- Use lightweight profiles
- Manually unload unused models

### Logs
- Application logs: Streamlit console output
- Database: `data/models.db`
- Auto-unload service: Console logging

## Development

### Running Tests
```bash
# Test individual components
python ollama_client.py
python database.py
python resource_monitor.py
python model_queue.py
python auto_unload_service.py
python profile_manager.py
```

### Adding New Profiles
1. Use the UI to create custom profiles
2. Or modify `database.py` default profiles
3. Restart the application

### Extending Automation
Add new rules to `auto_unload_service.py`:
```python
self.rules.append(AutoUnloadRule(
    name="custom_rule",
    condition="your_condition",
    action="your_action",
    priority=3
))
```

## Performance

### Expected Resource Usage
- **Base Application**: ~50-100MB RAM
- **Model Loading**: Depends on model size
- **Monitoring**: Minimal CPU overhead

### Optimization Tips
- Use appropriate profiles for your workload
- Enable auto-unload for automatic cleanup
- Monitor memory usage during development
- Prefer 7B models for coding tasks

## License

This project is provided as-is for local AI model management.

## Support

For issues and feature requests, check the troubleshooting section or modify the source code as needed.
