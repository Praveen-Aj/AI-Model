#!/usr/bin/env python3
"""
Test core model operations without Streamlit complications
"""

import asyncio
import logging
from ollama_client import OllamaClient
from resource_monitor import ResourceMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/test_operations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_core_operations():
    """Test the most critical operations"""
    
    client = OllamaClient()
    monitor = ResourceMonitor()
    
    logger.info("=== CORE OPERATIONS TEST ===")
    
    # Test 1: List models
    logger.info("Test 1: Listing models...")
    models = await client.list_models()
    logger.info(f"✅ Found {len(models)} models")
    
    if not models:
        logger.error("❌ No models found - cannot continue tests")
        return
    
    # Test 2: Check running models
    logger.info("Test 2: Checking running models...")
    running = await client.running_models()
    logger.info(f"✅ Currently running: {len(running)} models")
    
    # Test 3: System resources
    logger.info("Test 3: Getting system resources...")
    resources = monitor.get_system_resources()
    logger.info(f"✅ RAM: {resources.ram_percent:.1f}% ({resources.ram_used / (1024**3):.1f}GB used)")
    logger.info(f"✅ CPU: {resources.cpu_percent:.1f}%")
    
    if resources.gpu_info:
        gpu = resources.gpu_info[0]
        logger.info(f"✅ GPU: {gpu['name']}")
        logger.info(f"✅ VRAM: {gpu['memory_percent']:.1f}% ({gpu['memory_used'] / (1024**3):.1f}GB used)")
    
    # Test 4: Model warmup (stress test)
    test_model = models[0].name
    logger.info(f"Test 4: Warming up model {test_model}...")
    
    start_time = asyncio.get_event_loop().time()
    success = await client.warmup_model(test_model)
    end_time = asyncio.get_event_loop().time()
    
    load_time = end_time - start_time
    logger.info(f"✅ Warmup {'SUCCESS' if success else 'FAILED'} in {load_time:.1f} seconds")
    
    # Test 5: Verify model is running
    logger.info("Test 5: Verifying model is running...")
    running_after = await client.running_models()
    is_running = any(rm.model == test_model for rm in running_after)
    logger.info(f"✅ Model {test_model} {'IS RUNNING' if is_running else 'IS NOT RUNNING'}")
    
    # Test 6: Model unload
    logger.info(f"Test 6: Unloading model {test_model}...")
    start_time = asyncio.get_event_loop().time()
    unload_success = await client.stop_model(test_model)
    end_time = asyncio.get_event_loop().time()
    
    unload_time = end_time - start_time
    logger.info(f"✅ Unload {'SUCCESS' if unload_success else 'FAILED'} in {unload_time:.1f} seconds")
    
    # Test 7: Verify model is stopped
    logger.info("Test 7: Verifying model is stopped...")
    running_final = await client.running_models()
    is_still_running = any(rm.model == test_model for rm in running_final)
    logger.info(f"✅ Model {test_model} {'IS STILL RUNNING' if is_still_running else 'IS STOPPED'}")
    
    # Test 8: Memory thresholds
    logger.info("Test 8: Checking memory thresholds...")
    alerts = monitor.check_memory_thresholds()
    logger.info(f"✅ Memory alerts: {alerts}")
    
    # Test 9: Model switching simulation
    if len(models) >= 2:
        model1 = models[0].name
        model2 = models[1].name
        
        logger.info(f"Test 9: Model switching {model1} → {model2}...")
        
        # Load model2
        logger.info(f"Loading {model2}...")
        await client.warmup_model(model2)
        
        # Check state
        running_switch = await client.running_models()
        running_names = [rm.model for rm in running_switch]
        logger.info(f"✅ Running models: {running_names}")
        
        # Unload model2
        logger.info(f"Unloading {model2}...")
        await client.stop_model(model2)
    
    logger.info("=== CORE OPERATIONS TEST COMPLETE ===")
    
    # Summary
    final_resources = monitor.get_system_resources()
    final_running = await client.running_models()
    
    logger.info("=== SUMMARY ===")
    logger.info(f"Final RAM: {final_resources.ram_percent:.1f}%")
    logger.info(f"Final running models: {len(final_running)}")
    logger.info(f"Models tested: {[m.name for m in models[:2]]}")

if __name__ == "__main__":
    asyncio.run(test_core_operations())
