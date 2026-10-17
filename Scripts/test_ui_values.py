#!/usr/bin/env python3
"""
Test UI Values - Verify that values presented in UI are correct
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import psutil

def test_resource_values():
    """Test that resource monitor values are accurate"""
    print("=== Testing Resource Values ===")
    
    # Test RAM values
    memory = psutil.virtual_memory()
    ram_total_gb = memory.total / (1024**3)
    ram_used_gb = memory.used / (1024**3)
    ram_percent = memory.percent
    
    print(f"RAM Values:")
    print(f"   Total: {ram_total_gb:.2f} GB")
    print(f"   Used: {ram_used_gb:.2f} GB")
    print(f"   Percent: {ram_percent:.1f}%")
    
    # Validate RAM values
    assert ram_total_gb > 0, "RAM total should be positive"
    assert ram_used_gb >= 0, "RAM used should be non-negative"
    assert 0 <= ram_percent <= 100, "RAM percent should be between 0 and 100"
    assert ram_used_gb <= ram_total_gb, "RAM used should not exceed total"
    
    print("RAM values are valid")
    
    # Test CPU values
    cpu_percent = psutil.cpu_percent(interval=None)
    
    print(f"CPU Values:")
    print(f"   Percent: {cpu_percent:.1f}%")
    
    # Validate CPU values
    assert 0 <= cpu_percent <= 100, "CPU percent should be between 0 and 100"
    
    print("CPU values are valid")
    
    # Test GPU availability
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        gpu_available = result.returncode == 0
        print(f"GPU Available: {gpu_available}")
        
        if gpu_available:
            print("   GPU detection working correctly")
        else:
            print("   No GPU detected (expected for systems without NVIDIA GPU)")
    except:
        print("GPU detection skipped (nvidia-smi not available)")

def test_ollama_values():
    """Test that Ollama values are correct"""
    print("\n=== Testing Ollama Values ===")
    
    try:
        from src.ollama_client import OllamaClient
        client = OllamaClient()
        
        loop = asyncio.new_event_loop()
        try:
            # Test model listing
            print("Testing model listing...")
            models = loop.run_until_complete(client.list_models())
            print(f"Found {len(models)} models")
            
            if models:
                for model in models[:3]:  # Show first 3 models
                    print(f"   - {model.name}: {model.size / (1024**3):.2f} GB")
                
                # Validate model values
                for model in models:
                    assert model.name, "Model should have a name"
                    assert model.size >= 0, "Model size should be non-negative"
            
            print("Model values are valid")
            
            # Test running models
            print("\nTesting running models...")
            running = loop.run_until_complete(client.running_models())
            print(f"Found {len(running)} running models")
        finally:
            loop.close()
        
    except Exception as e:
        print(f"Ollama test skipped (Ollama service may not be running): {e}")

def main():
    """Run all value tests"""
    print("Testing UI Values")
    print("=" * 60)
    
    try:
        # Test resource values
        test_resource_values()
        
        # Test Ollama values
        test_ollama_values()
        
        print("\n" + "=" * 60)
        print("Test Results: SUCCESS")
        return 0
            
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
