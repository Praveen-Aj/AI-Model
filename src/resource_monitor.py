"""
Resource Monitor for System Resources
Tracks RAM, VRAM, CPU, and GPU usage
"""

import psutil
import subprocess
import json
import re
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SystemResources:
    ram_total: int
    ram_used: int
    ram_percent: float
    cpu_percent: float
    gpu_info: List[Dict]

@dataclass
class GPUInfo:
    name: str
    memory_total: int
    memory_used: int
    memory_percent: float
    utilization: float
    temperature: float

class ResourceMonitor:
    def __init__(self):
        self.gpu_available = self._check_gpu_available()
    
    def _check_gpu_available(self) -> bool:
        """Check if NVIDIA GPU is available"""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_system_resources(self) -> SystemResources:
        """Get current system resource usage"""
        # RAM usage
        memory = psutil.virtual_memory()
        
        # CPU usage (non-blocking)
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # GPU info
        gpu_info = self.get_gpu_info()
        
        return SystemResources(
            ram_total=memory.total,
            ram_used=memory.used,
            ram_percent=memory.percent,
            cpu_percent=cpu_percent,
            gpu_info=gpu_info
        )
    
    def get_gpu_info(self) -> List[Dict]:
        """Get GPU information using nvidia-smi"""
        if not self.gpu_available:
            return []
        
        try:
            # Use nvidia-smi with JSON output for parsing
            cmd = [
                'nvidia-smi',
                '--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu',
                '--format=csv,noheader,nounits'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            gpu_info = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 5:
                        memory_total = int(parts[1]) * 1024 * 1024  # Convert MB to bytes
                        memory_used = int(parts[2]) * 1024 * 1024   # Convert MB to bytes
                        memory_percent = (memory_used / memory_total) * 100 if memory_total > 0 else 0
                        
                        gpu_info.append({
                            'name': parts[0],
                            'memory_total': memory_total,
                            'memory_used': memory_used,
                            'memory_percent': memory_percent,
                            'utilization': float(parts[3]),
                            'temperature': float(parts[4])
                        })
            
            return gpu_info
            
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, IndexError) as e:
            print(f"Error getting GPU info: {str(e)}")
            return []
    
    def get_ram_usage(self) -> Dict[str, float]:
        """Get detailed RAM usage"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'used': memory.used,
            'available': memory.available,
            'percent': memory.percent
        }
    
    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    def check_memory_thresholds(self, ram_threshold: float = 80.0, vram_threshold: float = 85.0) -> Dict[str, bool]:
        """Check if memory usage exceeds thresholds"""
        resources = self.get_system_resources()
        
        alerts = {
            'ram_high': resources.ram_percent > ram_threshold,
            'vram_high': False,
            'critical': False
        }
        
        # Check VRAM for each GPU
        for gpu in resources.gpu_info:
            if gpu['memory_percent'] > vram_threshold:
                alerts['vram_high'] = True
                break
        
        # Critical if both RAM and VRAM are high
        alerts['critical'] = alerts['ram_high'] and alerts['vram_high']
        
        return alerts
    
    def get_process_memory_usage(self, process_name: str) -> List[Dict]:
        """Get memory usage for specific processes"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_rss': proc.info['memory_info'].rss,
                        'memory_vms': proc.info['memory_info'].vms,
                        'memory_percent': proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def get_ollama_processes(self) -> List[Dict]:
        """Get Ollama-related processes"""
        return self.get_process_memory_usage('ollama')
    
    def estimate_model_memory(self, model_size_gb: float) -> Dict[str, int]:
        """Estimate memory usage for a model"""
        # Rough estimation: model + 20% overhead
        estimated_bytes = int(model_size_gb * 1024**3 * 1.2)
        
        return {
            'estimated_bytes': estimated_bytes,
            'estimated_gb': model_size_gb * 1.2,
            'available_ram': psutil.virtual_memory().available,
            'can_fit': estimated_bytes < psutil.virtual_memory().available
        }
    
    def get_resource_history(self, minutes: int = 60) -> List[Dict]:
        """Get resource usage history (simplified version)"""
        # In a real implementation, this would store historical data
        # For now, return current snapshot
        current = self.get_system_resources()
        
        return [{
            'timestamp': datetime.now().isoformat(),
            'ram_percent': current.ram_percent,
            'cpu_percent': current.cpu_percent,
            'gpu_count': len(current.gpu_info),
            'vram_percent': current.gpu_info[0]['memory_percent'] if current.gpu_info else 0
        }]

# Test function
def test_resource_monitor():
    """Test resource monitoring"""
    monitor = ResourceMonitor()
    
    print("Testing resource monitor...")
    
    # System resources
    resources = monitor.get_system_resources()
    print(f"RAM: {resources.ram_percent:.1f}% ({resources.ram_used / (1024**3):.1f}GB / {resources.ram_total / (1024**3):.1f}GB)")
    print(f"CPU: {resources.cpu_percent:.1f}%")
    
    # GPU info
    if resources.gpu_info:
        for i, gpu in enumerate(resources.gpu_info):
            print(f"GPU {i}: {gpu['name']}")
            print(f"  VRAM: {gpu['memory_percent']:.1f}% ({gpu['memory_used'] / (1024**3):.1f}GB / {gpu['memory_total'] / (1024**3):.1f}GB)")
            print(f"  Utilization: {gpu['utilization']:.1f}%")
            print(f"  Temperature: {gpu['temperature']:.0f}°C")
    else:
        print("No GPU detected")
    
    # Memory thresholds
    alerts = monitor.check_memory_thresholds()
    print(f"Memory alerts: {alerts}")
    
    # Ollama processes
    ollama_procs = monitor.get_ollama_processes()
    print(f"Ollama processes: {len(ollama_procs)}")
    for proc in ollama_procs:
        print(f"  PID {proc['pid']}: {proc['memory_percent']:.1f}% RAM")
    
    print("Resource monitor test complete!")

if __name__ == "__main__":
    test_resource_monitor()
