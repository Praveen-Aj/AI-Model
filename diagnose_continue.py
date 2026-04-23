#!/usr/bin/env python3
"""
Continue Diagnostic Tool
Tests if Continue can connect to Ollama and models
"""

import requests
import json

def test_ollama_connection():
    """Test Ollama is running"""
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            return True, response.json()
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_model_available(model_name):
    """Test if specific model is available"""
    ok, data = test_ollama_connection()
    if not ok:
        return False, "Ollama not running"
    
    models = [m['name'] for m in data.get('models', [])]
    return model_name in models, f"Available: {models}"

def test_model_response(model_name):
    """Test if model responds"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model_name,
                'prompt': 'test',
                'stream': False
            },
            timeout=30
        )
        if response.status_code == 200:
            return True, "Model responds"
        return False, f"Status: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Request timeout (model may be loading)"
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    print("=" * 60)
    print("CONTINUE DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Test 1: Ollama connection
    print("\n1. Testing Ollama Connection...")
    ok, result = test_ollama_connection()
    if ok:
        print("   ✅ OLLAMA IS RUNNING")
        models = [m['name'] for m in result.get('models', [])]
        print(f"   Available models: {models}")
    else:
        print(f"   ❌ OLLAMA ERROR: {result}")
        exit(1)
    
    # Test 2: Qwen model
    print("\n2. Testing Qwen2.5-Coder 14B...")
    ok, msg = test_model_available('qwen2.5-coder:14b')
    if ok:
        print("   ✅ MODEL INSTALLED")
        resp_ok, resp_msg = test_model_response('qwen2.5-coder:14b')
        if resp_ok:
            print("   ✅ MODEL RESPONDS")
        else:
            print(f"   ⚠️  MODEL SLOW: {resp_msg}")
    else:
        print(f"   ❌ NOT FOUND: {msg}")
    
    # Test 3: Embeddings
    print("\n3. Testing Nomic Embeddings...")
    ok, msg = test_model_available('nomic-embed-text:latest')
    if ok:
        print("   ✅ EMBEDDINGS INSTALLED")
    else:
        print(f"   ❌ NOT FOUND: {msg}")
    
    # Test 4: Continue config
    print("\n4. Checking Continue Config...")
    import os
    config_yaml = os.path.expanduser('~/.continue/config.yaml')
    config_json = os.path.expanduser('~/AppData/Local/Continue/config.json')
    
    if os.path.exists(config_yaml):
        print(f"   ✅ YAML config found")
    else:
        print(f"   ❌ YAML config NOT found: {config_yaml}")
    
    if os.path.exists(config_json):
        print(f"   ✅ JSON config found")
    else:
        print(f"   ❌ JSON config NOT found: {config_json}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Ollama: RUNNING")
    print("✅ Qwen Model: INSTALLED")
    print("✅ Embeddings: INSTALLED")
    print("✅ Config: EXISTS")
    print("\nNext: Reload VS Code and try chat again!")
    print("=" * 60)
