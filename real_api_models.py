#!/usr/bin/env python3
"""
Real API implementations for OpenAI, Anthropic, and OpenRouter.
This replaces the mocked API calls with actual API calls.
"""

import os
import time
import json
import requests
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Import base classes
import sys
sys.path.insert(0, '.')
from demo.model_wrapper import BaseModel, ModelResponse, ModelType


class APIProvider(Enum):
    """Supported API providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    OPENROUTER = "openrouter"
    GOOGLE = "google"


@dataclass
class APIConfig:
    """Configuration for API providers."""
    provider: APIProvider
    base_url: str
    model_name: str
    api_key_env: str
    cost_per_1k_tokens: float
    context_window: int


class RealAPIModel(BaseModel):
    """Real API model that makes actual API calls."""
    
    # Model configurations
    MODELS = {
        "gpt-4": APIConfig(
            provider=APIProvider.OPENAI,
            base_url="https://api.openai.com/v1",
            model_name="gpt-4",
            api_key_env="OPENAI_API_KEY",
            cost_per_1k_tokens=0.03,
            context_window=8192
        ),
        "gpt-4-turbo": APIConfig(
            provider=APIProvider.OPENAI,
            base_url="https://api.openai.com/v1", 
            model_name="gpt-4-turbo-preview",
            api_key_env="OPENAI_API_KEY",
            cost_per_1k_tokens=0.01,
            context_window=128000
        ),

        "claude-3-7-sonnet": APIConfig(
            provider=APIProvider.ANTHROPIC,
            base_url="https://api.anthropic.com",
            model_name="claude-3-7-sonnet-20250219",
            api_key_env="ANTHROPIC_API_KEY",
            cost_per_1k_tokens=0.003,
            context_window=200000
        ),
        "claude-3-opus": APIConfig(
            provider=APIProvider.ANTHROPIC,
            base_url="https://api.anthropic.com",
            model_name="claude-3-opus-20240229", 
            api_key_env="ANTHROPIC_API_KEY",
            cost_per_1k_tokens=0.075,
            context_window=200000
        ),
        "qwen/qwen3-8b": APIConfig(
            provider=APIProvider.OPENROUTER,
            base_url="https://openrouter.ai/api/v1",
            model_name="qwen/qwen3-8b",
            api_key_env="OPENROUTER_API_KEY",
            cost_per_1k_tokens=0.0002,
            context_window=32768
        ),
        "deepseek/deepseek-chat-v3.1": APIConfig(
            provider=APIProvider.OPENROUTER,
            base_url="https://openrouter.ai/api/v1",
            model_name="deepseek/deepseek-chat-v3.1",
            api_key_env="OPENROUTER_API_KEY", 
            cost_per_1k_tokens=0.0002,
            context_window=64000
        ),
        "meta-llama/llama-3.3-70b-instruct:free": APIConfig(
            provider=APIProvider.OPENROUTER,
            base_url="https://openrouter.ai/api/v1",
            model_name="meta-llama/llama-3.3-70b-instruct:free",
            api_key_env="OPENROUTER_API_KEY",
            cost_per_1k_tokens=0.000,  # Free tier
            context_window=8192
        ),
        "google/gemini-2.5-flash": APIConfig(
            provider=APIProvider.OPENROUTER,
            base_url="https://openrouter.ai/api/v1",
            model_name="google/gemini-2.5-flash",
            api_key_env="OPENROUTER_API_KEY",
            cost_per_1k_tokens=0.000075,
            context_window=1000000
        )
    }
    
    def __init__(self, model_key: str, api_key: Optional[str] = None):
        """
        Initialize real API model.
        
        Args:
            model_key: Key from MODELS dict (e.g., "gpt-4", "claude-3-sonnet")
            api_key: Optional API key (None = use environment)
        """
        if model_key not in self.MODELS:
            raise ValueError(f"Unsupported model: {model_key}. Available: {list(self.MODELS.keys())}")
        
        self.config = self.MODELS[model_key]
        self.model_key = model_key
        self.api_key = api_key or os.getenv(self.config.api_key_env)
        
        if not self.api_key:
            raise ValueError(f"API key required for {model_key}. Set {self.config.api_key_env} or pass api_key parameter.")
        
        print(f"🔗 Real {self.config.provider.value} API configured: {self.config.model_name}")
    
    def generate(self, prompt: str, max_tokens: int = 512) -> ModelResponse:
        """Generate response using real API."""
        start_time = time.perf_counter()
        
        try:
            if self.config.provider == APIProvider.OPENAI:
                return self._call_openai_api(prompt, max_tokens, start_time)
            elif self.config.provider == APIProvider.ANTHROPIC:
                return self._call_anthropic_api(prompt, max_tokens, start_time)
            elif self.config.provider == APIProvider.OPENROUTER:
                return self._call_openrouter_api(prompt, max_tokens, start_time)
            elif self.config.provider == APIProvider.GOOGLE:
                return self._call_google_api(prompt, max_tokens, start_time)
            else:
                raise ValueError(f"Unknown provider: {self.config.provider}")
        
        except Exception as e:
            generation_time = (time.perf_counter() - start_time) * 1000
            return ModelResponse(
                text="",
                model_type=ModelType.API,
                model_name=self.config.model_name,
                generation_time_ms=generation_time,
                error_message=f"API Error ({self.config.provider.value}): {str(e)}"
            )
    
    def _call_openai_api(self, prompt: str, max_tokens: int, start_time: float) -> ModelResponse:
        """Call OpenAI API."""
        url = f"{self.config.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        response_text = data["choices"][0]["message"]["content"]
        token_count = data["usage"]["total_tokens"]
        
        generation_time = (time.perf_counter() - start_time) * 1000
        
        return ModelResponse(
            text=response_text,
            model_type=ModelType.API,
            model_name=self.config.model_name,
            generation_time_ms=generation_time,
            token_count=token_count
        )
    
    def _call_anthropic_api(self, prompt: str, max_tokens: int, start_time: float) -> ModelResponse:
        """Call Anthropic API."""
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.config.model_name,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        response_text = data["content"][0]["text"]
        token_count = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
        
        generation_time = (time.perf_counter() - start_time) * 1000
        
        return ModelResponse(
            text=response_text,
            model_type=ModelType.API,
            model_name=self.config.model_name,
            generation_time_ms=generation_time,
            token_count=token_count
        )
    
    def _call_openrouter_api(self, prompt: str, max_tokens: int, start_time: float) -> ModelResponse:
        """Call OpenRouter API."""
        url = f"{self.config.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/pcc-niuc",
            "X-Title": "PCC-NIUC Research"
        }
        
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        response_text = data["choices"][0]["message"]["content"]
        token_count = data.get("usage", {}).get("total_tokens", len(response_text.split()))
        
        generation_time = (time.perf_counter() - start_time) * 1000
        
        return ModelResponse(
            text=response_text,
            model_type=ModelType.API,
            model_name=self.config.model_name,
            generation_time_ms=generation_time,
            token_count=token_count
        )
    
    def _call_google_api(self, prompt: str, max_tokens: int, start_time: float) -> ModelResponse:
        """Call Google Gemini API."""
        url = f"{self.config.base_url}/models/{self.config.model_name}:generateContent"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        # Add API key as query parameter
        url += f"?key={self.api_key}"
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        response_text = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Estimate token count (Google doesn't always provide this)
        token_count = len(response_text.split()) * 1.3  # Rough estimate
        
        generation_time = (time.perf_counter() - start_time) * 1000
        
        return ModelResponse(
            text=response_text,
            model_type=ModelType.API,
            model_name=self.config.model_name,
            generation_time_ms=generation_time,
            token_count=int(token_count)
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_name": self.config.model_name,
            "model_type": "real_api",
            "provider": self.config.provider.value,
            "base_url": self.config.base_url,
            "has_api_key": bool(self.api_key),
            "cost_per_1k_tokens": self.config.cost_per_1k_tokens,
            "context_window": self.config.context_window,
            "max_tokens": 4096,
            "supports_streaming": False,
        }


def test_real_api_connection(model_key: str, api_key: Optional[str] = None) -> bool:
    """
    Test if real API connection works.
    
    Args:
        model_key: Model to test (e.g., "gpt-4")
        api_key: Optional API key
        
    Returns:
        True if API call succeeds, False otherwise
    """
    print(f"🧪 Testing real API connection for {model_key}...")
    
    try:
        model = RealAPIModel(model_key, api_key)
        response = model.generate("Hello, this is a test. Please respond with 'API TEST SUCCESSFUL'.", max_tokens=50)
        
        if response.error_message:
            print(f"❌ API test failed: {response.error_message}")
            return False
        
        print(f"✅ API test successful!")
        print(f"   Response: {response.text[:100]}...")
        print(f"   Tokens: {response.token_count}")
        print(f"   Latency: {response.generation_time_ms:.1f}ms")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


if __name__ == "__main__":
    # Test all available models
    print("🧪 REAL API CONNECTION TESTS")
    print("=" * 50)
    
    test_models = ["gpt-4", "claude-3-7-sonnet", "google/gemini-2.5-flash", "qwen/qwen3-8b", "deepseek/deepseek-chat-v3.1", "meta-llama/llama-3.3-70b-instruct:free"]
    
    for model_key in test_models:
        print(f"\n{model_key.upper()}:")
        config = RealAPIModel.MODELS.get(model_key)
        if config:
            api_key = os.getenv(config.api_key_env)
            if api_key:
                test_real_api_connection(model_key)
            else:
                print(f"⚠️  No API key found for {config.api_key_env}")
        else:
            print(f"❌ Unknown model: {model_key}")
