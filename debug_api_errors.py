#!/usr/bin/env python3
"""
Debug script to identify specific API errors with DeepSeek and Qwen.
"""

import os
import time
import requests
from real_api_models import RealAPIModel

def test_specific_model(model_key: str, test_prompt: str = "Hello, this is a test."):
    """Test a specific model with detailed error reporting."""
    print(f"\n🔍 DEBUGGING {model_key.upper()}")
    print("=" * 50)
    
    try:
        # Initialize model
        model = RealAPIModel(model_key)
        print(f"✅ Model initialized: {model.config.model_name}")
        
        # Test API call
        print(f"📡 Making API call...")
        start_time = time.perf_counter()
        response = model.generate(test_prompt, max_tokens=50)
        end_time = time.perf_counter()
        
        if response.error_message:
            print(f"❌ API Error: {response.error_message}")
            return False
        
        print(f"✅ API call successful!")
        print(f"   Response: {response.text[:100]}...")
        print(f"   Tokens: {response.token_count}")
        print(f"   Latency: {(end_time - start_time) * 1000:.1f}ms")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        
        # Try to get more details for specific error types
        if "requests" in str(e):
            print(f"   Network/HTTP error details: {e}")
        elif "JSON" in str(e):
            print(f"   JSON parsing error: {e}")
        elif "timeout" in str(e).lower():
            print(f"   Timeout error: {e}")
        
        return False

def test_openrouter_directly():
    """Test OpenRouter API directly to identify issues."""
    print(f"\n🔍 DIRECT OPENROUTER API TEST")
    print("=" * 50)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ No OPENROUTER_API_KEY found")
        return
    
    base_url = "https://openrouter.ai/api/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/pcc-niuc",
        "X-Title": "PCC-NIUC Research"
    }
    
    # Test Qwen
    print(f"\n📡 Testing Qwen3 8B...")
    qwen_payload = {
        "model": "qwen/qwen3-8b:free",
        "messages": [{"role": "user", "content": "Hello, this is a test."}],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=qwen_payload, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test DeepSeek
    print(f"\n📡 Testing DeepSeek V3.1...")
    deepseek_payload = {
        "model": "deepseek/deepseek-chat-v3.1:free",
        "messages": [{"role": "user", "content": "Hello, this is a test."}],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=deepseek_payload, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    print("🐛 API ERROR DEBUGGING")
    print("=" * 50)
    
    # Test models individually
    test_specific_model("qwen/qwen3-8b:free")
    test_specific_model("deepseek/deepseek-chat-v3.1:free")
    
    # Test OpenRouter directly
    test_openrouter_directly()

