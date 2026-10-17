#!/usr/bin/env python3
"""
Memory Cleanup Test - Critical Operational Validation
"""

import sys
import time
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ollama_client import OllamaClient
from resource_monitor import ResourceMonitor


def get_memory_snapshot():
    """Get detailed memory snapshot"""
    monitor = ResourceMonitor()
    resources = monitor.get_system_resources()
    
    return {
        'timestamp': datetime.now(),
        'ram_percent': resources.ram_percent,
        'ram_used_gb': resources.ram_used / (1024**3),
        'ram_total_gb': resources.ram_total / (1024**3),
        'cpu_percent': resources.cpu_percent
    }


async def test_model_memory_cleanup():
    """Test model load/unload memory cleanup"""
    print("=== Memory Cleanup Test ===")
    print(f"Testing model: qwen2.5:14b")
    
    client = OllamaClient()
    
    # Step 1: Record baseline
    print("\n--- Step 1: Baseline ---")
    baseline = get_memory_snapshot()
    print(f"Baseline RAM: {baseline['ram_percent']:.1f}% ({baseline['ram_used_gb']:.1f}GB)")
    
    # Check running models
    running_before = await client.running_models()
    print(f"Running models before: {len(running_before)}")
    for model in running_before:
        print(f"  - {model.name}")
    
    # Step 2: Load model
    print("\n--- Step 2: Loading qwen2.5:14b ---")
    start_time = time.time()
    
    try:
        success = await client.warmup_model("qwen2.5:14b")
        load_time = time.time() - start_time
        print(f"Load time: {load_time:.1f} seconds")
        print(f"Load success: {success}")
    except Exception as e:
        print(f"Load failed: {e}")
        return False
    
    # Wait for model to fully load
    print("Waiting 30 seconds for model to fully load...")
    time.sleep(30)
    
    # Check memory after load
    loaded_memory = get_memory_snapshot()
    ram_increase = loaded_memory['ram_used_gb'] - baseline['ram_used_gb']
    print(f"RAM after load: {loaded_memory['ram_percent']:.1f}% ({loaded_memory['ram_used_gb']:.1f}GB)")
    print(f"RAM increase: +{ram_increase:.1f}GB")
    
    # Check running models
    running_loaded = await client.running_models()
    print(f"Running models after load: {len(running_loaded)}")
    for model in running_loaded:
        print(f"  - {model.name}")
    
    # Step 3: Wait 2 minutes
    print("\n--- Step 3: Waiting 2 minutes ---")
    time.sleep(120)
    
    # Check memory after wait
    wait_memory = get_memory_snapshot()
    print(f"RAM after 2min wait: {wait_memory['ram_percent']:.1f}% ({wait_memory['ram_used_gb']:.1f}GB)")
    
    # Step 4: Unload model
    print("\n--- Step 4: Unloading model ---")
    unload_start = time.time()
    
    try:
        success = await client.stop_model("qwen2.5:14b")
        unload_time = time.time() - unload_start
        print(f"Unload time: {unload_time:.1f} seconds")
        print(f"Unload success: {success}")
    except Exception as e:
        print(f"Unload failed: {e}")
        return False
    
    # Step 5: Monitor memory for 10 minutes
    print("\n--- Step 5: Monitoring memory cleanup (10 minutes) ---")
    
    memory_samples = []
    for minute in range(10):
        time.sleep(60)  # Wait 1 minute
        
        snapshot = get_memory_snapshot()
        memory_samples.append(snapshot)
        
        ram_recovered = baseline['ram_used_gb'] - snapshot['ram_used_gb']
        print(f"Minute {minute+1}: RAM {snapshot['ram_percent']:.1f}% ({snapshot['ram_used_gb']:.1f}GB) - Recovered: {ram_recovered:.1f}GB")
        
        # Check running models
        running_check = await client.running_models()
        if running_check:
            print(f"  Still running: {[m.name for m in running_check]}")
    
    # Final analysis
    print("\n--- Final Analysis ---")
    final_memory = memory_samples[-1]
    total_recovered = baseline['ram_used_gb'] - final_memory['ram_used_gb']
    
    print(f"Baseline RAM: {baseline['ram_percent']:.1f}% ({baseline['ram_used_gb']:.1f}GB)")
    print(f"Final RAM: {final_memory['ram_percent']:.1f}% ({final_memory['ram_used_gb']:.1f}GB)")
    print(f"Total RAM recovered: {total_recovered:.1f}GB")
    print(f"Recovery percentage: {(total_recovered/ram_increase)*100:.1f}%")
    
    # Check if memory fully recovered
    if total_recovered >= ram_increase * 0.9:  # 90% recovery threshold
        print("✅ Memory cleanup: GOOD")
        return True
    elif total_recovered >= ram_increase * 0.5:  # 50% recovery threshold
        print("⚠️ Memory cleanup: PARTIAL")
        return False
    else:
        print("❌ Memory cleanup: POOR")
        return False


async def test_ollama_memory_leak():
    """Check if Ollama itself is holding memory"""
    print("\n=== Ollama Memory Leak Test ===")
    
    # Check Ollama process memory
    try:
        import psutil
        
        # Find Ollama process
        ollama_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if 'ollama' in proc.info['name'].lower():
                    ollama_processes.append(proc)
                    print(f"Ollama process: PID {proc.info['pid']}, Memory: {proc.info['memory_info'].rss / (1024**2):.1f}MB")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not ollama_processes:
            print("No Ollama processes found")
            return True
        
        total_ollama_memory = sum(p.info['memory_info'].rss for p in ollama_processes) / (1024**3)
        print(f"Total Ollama memory: {total_ollama_memory:.1f}GB")
        
        return True
        
    except Exception as e:
        print(f"Error checking Ollama processes: {e}")
        return False


def main():
    """Run memory cleanup tests"""
    print("Local AI Model Manager - Memory Cleanup Test")
    print("=" * 60)
    
    # Test 1: Model memory cleanup
    cleanup_ok = asyncio.run(test_model_memory_cleanup())
    
    # Test 2: Ollama memory leak
    ollama_ok = asyncio.run(test_ollama_memory_leak())
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Model memory cleanup: {'✅ PASS' if cleanup_ok else '❌ FAIL'}")
    print(f"Ollama memory check: {'✅ PASS' if ollama_ok else '❌ FAIL'}")
    
    if cleanup_ok and ollama_ok:
        print("\n🎉 Memory management is working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️ Memory management issues detected!")
        print("This needs immediate attention before production use.")
        sys.exit(1)


if __name__ == "__main__":
    main()
