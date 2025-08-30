"""
Model wrapper for PCC-NIUC system.
Supports local quantized 7B models and API models while keeping guard logic pure.
"""

import time
import json
import os
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class ModelType(Enum):
    """Supported model types."""
    LOCAL_7B = "local_7b"
    API = "api"
    MOCK = "mock"


@dataclass
class ModelResponse:
    """Response from model with metadata."""
    text: str
    model_type: ModelType
    model_name: str
    generation_time_ms: float
    token_count: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class LatencyMeasurement:
    """Detailed latency measurement for the full pipeline."""
    model_generation_ms: float
    niuc_checking_ms: float
    runtime_gate_ms: float
    total_pipeline_ms: float
    tokens_per_second: Optional[float] = None


class BaseModel(ABC):
    """Abstract base class for all model implementations."""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 512) -> ModelResponse:
        """Generate response from prompt."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and capabilities."""
        pass


class MockModel(BaseModel):
    """Mock model for testing and development."""
    
    def __init__(self, response_template: str = "I understand you're asking about '{prompt_snippet}'. Here's my response: This is a mock response for testing purposes."):
        self.response_template = response_template
        self.model_name = "mock-gpt-4-demo"
        self.simulated_latency_ms = 100  # Simulate realistic latency
    
    def generate(self, prompt: str, max_tokens: int = 512) -> ModelResponse:
        """Generate mock response with simulated latency."""
        start_time = time.perf_counter()
        
        # Simulate processing time
        time.sleep(self.simulated_latency_ms / 1000)
        
        # Generate mock response
        prompt_snippet = prompt[:50].replace('\n', ' ')
        response_text = self.response_template.format(prompt_snippet=prompt_snippet)
        
        generation_time = (time.perf_counter() - start_time) * 1000
        
        return ModelResponse(
            text=response_text,
            model_type=ModelType.MOCK,
            model_name=self.model_name,
            generation_time_ms=generation_time,
            token_count=len(response_text.split()),  # Rough token estimate
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information."""
        return {
            "model_name": self.model_name,
            "model_type": "mock",
            "max_tokens": 4096,
            "supports_streaming": False,
            "cost_per_1k_tokens": 0.0,
            "simulated_latency_ms": self.simulated_latency_ms
        }


class LocalQuantizedModel(BaseModel):
    """Local quantized 7B model wrapper (placeholder for actual implementation)."""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        """
        Initialize local quantized model.
        
        Args:
            model_path: Path to model files (None = auto-detect)
            device: Device to run on ("auto", "cpu", "cuda")
        """
        self.model_path = model_path or "models/quantized-7b"
        self.device = device
        self.model_name = "local-quantized-7b"
        self._model = None
        self._tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the quantized model (placeholder - would use actual library)."""
        try:
            # Placeholder for actual model loading
            # In real implementation, would use transformers, llama.cpp, etc.
            print(f"📦 Loading quantized model from {self.model_path}")
            print(f"🔧 Device: {self.device}")
            
            # Simulate model loading time
            time.sleep(2.0)
            
            # Mock model loading success
            self._model = "mock_model_placeholder"
            self._tokenizer = "mock_tokenizer_placeholder"
            
            print("✅ Local model loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to load local model: {e}")
            print("💡 Falling back to mock mode")
            self._model = None
            self._tokenizer = None
    
    def generate(self, prompt: str, max_tokens: int = 512) -> ModelResponse:
        """Generate response using local quantized model."""
        start_time = time.perf_counter()
        
        if self._model is None:
            # Fallback to mock response if model failed to load
            return MockModel().generate(prompt, max_tokens)
        
        try:
            # Placeholder for actual model inference
            # In real implementation:
            # inputs = self._tokenizer(prompt, return_tensors="pt")
            # outputs = self._model.generate(inputs.input_ids, max_new_tokens=max_tokens)
            # response_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Mock response for demonstration
            response_text = f"[LOCAL-7B] Based on your input: '{prompt[:30]}...', here is my response. I'll analyze this carefully for any security concerns."
            
            # Simulate realistic 7B model latency (2-5 tokens/sec)
            estimated_tokens = max_tokens // 4  # Assume we generate 1/4 of max tokens
            latency_per_token = 0.5  # 500ms per token for 7B quantized
            time.sleep(estimated_tokens * latency_per_token)
            
            generation_time = (time.perf_counter() - start_time) * 1000
            
            return ModelResponse(
                text=response_text,
                model_type=ModelType.LOCAL_7B,
                model_name=self.model_name,
                generation_time_ms=generation_time,
                token_count=len(response_text.split()),
            )
        
        except Exception as e:
            generation_time = (time.perf_counter() - start_time) * 1000
            return ModelResponse(
                text="",
                model_type=ModelType.LOCAL_7B,
                model_name=self.model_name,
                generation_time_ms=generation_time,
                error_message=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get local model information."""
        return {
            "model_name": self.model_name,
            "model_type": "local_quantized_7b", 
            "model_path": self.model_path,
            "device": self.device,
            "loaded": self._model is not None,
            "max_tokens": 4096,
            "supports_streaming": True,
            "cost_per_1k_tokens": 0.0,  # Free local inference
            "estimated_vram_gb": 4.0
        }


class APIModel(BaseModel):
    """API model wrapper (placeholder for actual API implementation)."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4", 
                 base_url: Optional[str] = None):
        """
        Initialize API model.
        
        Args:
            api_key: API key for authentication (None = use environment)
            model_name: Name of API model to use
            base_url: Custom API endpoint (None = use default)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.base_url = base_url or "https://api.openai.com/v1"
        self._client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup API client (placeholder - would use actual API library)."""
        try:
            # Placeholder for actual API client setup
            # In real implementation:
            # from openai import OpenAI
            # self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            
            if not self.api_key:
                print("⚠️  No API key found - API model will use mock responses")
                self._client = None
            else:
                print(f"🔗 API client configured for {self.model_name}")
                self._client = "mock_api_client"
                
        except Exception as e:
            print(f"❌ Failed to setup API client: {e}")
            self._client = None
    
    def generate(self, prompt: str, max_tokens: int = 512) -> ModelResponse:
        """Generate response using API model."""
        start_time = time.perf_counter()
        
        if self._client is None:
            # Fallback to mock if no API access
            return MockModel().generate(prompt, max_tokens)
        
        try:
            # Placeholder for actual API call
            # In real implementation:
            # response = self._client.chat.completions.create(
            #     model=self.model_name,
            #     messages=[{"role": "user", "content": prompt}],
            #     max_tokens=max_tokens
            # )
            # response_text = response.choices[0].message.content
            
            # Mock API response with realistic latency
            response_text = f"[API-{self.model_name.upper()}] I've received your request: '{prompt[:30]}...'. I'll process this carefully and provide a helpful response while maintaining safety guidelines."
            
            # Simulate API latency (200-800ms typical)
            api_latency = 0.5  # 500ms simulation
            time.sleep(api_latency)
            
            generation_time = (time.perf_counter() - start_time) * 1000
            
            return ModelResponse(
                text=response_text,
                model_type=ModelType.API,
                model_name=self.model_name,
                generation_time_ms=generation_time,
                token_count=len(response_text.split()),
            )
        
        except Exception as e:
            generation_time = (time.perf_counter() - start_time) * 1000
            return ModelResponse(
                text="",
                model_type=ModelType.API, 
                model_name=self.model_name,
                generation_time_ms=generation_time,
                error_message=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get API model information."""
        return {
            "model_name": self.model_name,
            "model_type": "api",
            "base_url": self.base_url,
            "has_api_key": self.api_key is not None,
            "max_tokens": 4096,
            "supports_streaming": True,
            "cost_per_1k_tokens": 0.03,  # Estimated API cost
        }


class ModelWrapper:
    """Main model wrapper that routes to appropriate model implementation."""
    
    def __init__(self, model_type: ModelType = ModelType.MOCK, **kwargs):
        """
        Initialize model wrapper.
        
        Args:
            model_type: Type of model to use
            **kwargs: Model-specific configuration
        """
        self.model_type = model_type
        self.model = self._create_model(**kwargs)
    
    def _create_model(self, **kwargs) -> BaseModel:
        """Create appropriate model instance."""
        if self.model_type == ModelType.MOCK:
            return MockModel(**kwargs)
        elif self.model_type == ModelType.LOCAL_7B:
            return LocalQuantizedModel(**kwargs)
        elif self.model_type == ModelType.API:
            return APIModel(**kwargs)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def generate_with_guard(self, segments: List[Tuple[str, str, str]], 
                           mode: str = "block", max_tokens: int = 512) -> Dict[str, Any]:
        """
        Generate response with NIUC guard protection and latency measurement.
        
        Args:
            segments: List of (text, channel, source_id) tuples
            mode: "block" or "rewrite" mode for runtime gate
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with response, guard results, and latency measurements
        """
        # Import here to keep model wrapper independent of core PCC logic
        from pcc.runtime_gate import process_with_block_mode, process_with_rewrite_mode
        
        pipeline_start = time.perf_counter()
        
        # Step 1: Create prompt from segments
        prompt = self._build_prompt_from_segments(segments)
        
        # Step 2: Generate model response
        generation_start = time.perf_counter()
        model_response = self.model.generate(prompt, max_tokens)
        generation_time = (time.perf_counter() - generation_start) * 1000
        
        if model_response.error_message:
            return {
                "success": False,
                "error": model_response.error_message,
                "model_info": self.model.get_model_info(),
                "latency": LatencyMeasurement(
                    model_generation_ms=generation_time,
                    niuc_checking_ms=0,
                    runtime_gate_ms=0,
                    total_pipeline_ms=generation_time
                )
            }
        
        # Step 3: Run through NIUC runtime gate
        gate_start = time.perf_counter()
        
        if mode == "block":
            gate_result = process_with_block_mode(segments, model_response.text)
        elif mode == "rewrite":
            gate_result = process_with_rewrite_mode(segments, model_response.text)
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'block' or 'rewrite'")
        
        gate_time = (time.perf_counter() - gate_start) * 1000
        
        # Step 4: Compute total pipeline latency
        total_time = (time.perf_counter() - pipeline_start) * 1000
        
        # Estimate NIUC checking time (part of gate time)
        niuc_time = gate_time * 0.3  # Rough estimate: 30% of gate time is pure checking
        
        # Calculate tokens per second if possible
        tokens_per_sec = None
        if model_response.token_count and model_response.generation_time_ms > 0:
            tokens_per_sec = (model_response.token_count / model_response.generation_time_ms) * 1000
        
        latency = LatencyMeasurement(
            model_generation_ms=model_response.generation_time_ms,
            niuc_checking_ms=niuc_time,
            runtime_gate_ms=gate_time,
            total_pipeline_ms=total_time,
            tokens_per_second=tokens_per_sec
        )
        
        return {
            "success": True,
            "model_response": model_response,
            "gate_result": gate_result,
            "latency": latency,
            "mode": mode,
            "model_info": self.model.get_model_info(),
            "certificate": json.loads(gate_result.certificate_json),
            "final_text": gate_result.final_text if gate_result.allowed else None
        }
    
    def _build_prompt_from_segments(self, segments: List[Tuple[str, str, str]]) -> str:
        """Build single prompt string from segments for model input."""
        prompt_parts = []
        
        for text, channel, source_id in segments:
            # Add channel annotation for clarity
            if channel == "trusted":
                prompt_parts.append(f"[TRUSTED:{source_id}] {text}")
            else:
                prompt_parts.append(f"[UNTRUSTED:{source_id}] {text}")
        
        return "\n".join(prompt_parts)
    
    def benchmark_latency(self, test_prompt: str = "Hello, how are you?", 
                         iterations: int = 5) -> Dict[str, float]:
        """
        Benchmark model latency with simple test prompts.
        
        Args:
            test_prompt: Simple test prompt for latency measurement
            iterations: Number of iterations to average
            
        Returns:
            Dictionary with latency statistics
        """
        latencies = []
        token_rates = []
        
        print(f"🏃 Benchmarking {self.model_type.value} model latency ({iterations} iterations)...")
        
        for i in range(iterations):
            start_time = time.perf_counter()
            response = self.model.generate(test_prompt, max_tokens=50)
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            if response.token_count and latency_ms > 0:
                tokens_per_sec = (response.token_count / latency_ms) * 1000
                token_rates.append(tokens_per_sec)
            
            if i == 0:  # Show first response
                print(f"   Sample response: {response.text[:60]}...")
        
        stats = {
            "avg_latency_ms": sum(latencies) / len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
        }
        
        if token_rates:
            stats.update({
                "avg_tokens_per_sec": sum(token_rates) / len(token_rates),
                "min_tokens_per_sec": min(token_rates),
                "max_tokens_per_sec": max(token_rates),
            })
        
        return stats


# Factory functions for easy model creation

def create_mock_model(**kwargs) -> ModelWrapper:
    """Create mock model wrapper for testing."""
    return ModelWrapper(ModelType.MOCK, **kwargs)


def create_local_model(model_path: Optional[str] = None, device: str = "auto") -> ModelWrapper:
    """Create local quantized 7B model wrapper."""
    return ModelWrapper(ModelType.LOCAL_7B, model_path=model_path, device=device)


def create_api_model(api_key: Optional[str] = None, model_name: str = "gpt-4", 
                    base_url: Optional[str] = None) -> ModelWrapper:
    """Create API model wrapper."""
    return ModelWrapper(ModelType.API, api_key=api_key, model_name=model_name, base_url=base_url)


def auto_detect_model() -> ModelWrapper:
    """Auto-detect and create best available model."""
    # Check for API key
    if os.getenv("OPENAI_API_KEY"):
        print("🔑 API key found - using API model")
        return create_api_model()
    
    # Check for local model
    local_model_paths = [
        "models/quantized-7b",
        "../models/llama-7b-quantized",
        "./llama.cpp/models",
    ]
    
    for path in local_model_paths:
        if os.path.exists(path):
            print(f"📂 Local model found at {path}")
            return create_local_model(path)
    
    # Fallback to mock
    print("🎭 No models found - using mock model")
    return create_mock_model()


# Convenience function for quick testing
def test_model_with_guard(model_type: ModelType = ModelType.MOCK, 
                         test_segments: Optional[List[Tuple[str, str, str]]] = None) -> Dict[str, Any]:
    """
    Quick test of model with NIUC guard.
    
    Args:
        model_type: Type of model to test
        test_segments: Test segments (None = use default)
        
    Returns:
        Test result with latency measurements
    """
    if test_segments is None:
        test_segments = [
            ("System: You are a helpful assistant.", "trusted", "system"),
            ("User input: Please help me calculate fibonacci(10)", "trusted", "user")
        ]
    
    wrapper = ModelWrapper(model_type)
    return wrapper.generate_with_guard(test_segments, mode="block")


if __name__ == "__main__":
    # Add pcc module to path for standalone execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    # Demo script
    print("🔒 PCC-NIUC Model Wrapper Demo")
    print("=" * 40)
    
    # Test different model types
    model_types = [ModelType.MOCK, ModelType.LOCAL_7B, ModelType.API]
    
    for model_type in model_types:
        print(f"\n🧪 Testing {model_type.value} model:")
        try:
            result = test_model_with_guard(model_type)
            if result["success"]:
                latency = result["latency"]
                print(f"   ✅ Success - Total latency: {latency.total_pipeline_ms:.1f}ms")
                print(f"   🤖 Model: {latency.model_generation_ms:.1f}ms")
                print(f"   🔒 NIUC: {latency.niuc_checking_ms:.1f}ms") 
                print(f"   🚪 Gate: {latency.runtime_gate_ms:.1f}ms")
                print(f"   🎯 Decision: {'ALLOWED' if result['gate_result'].allowed else 'BLOCKED'}")
            else:
                print(f"   ❌ Failed: {result['error']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 Model wrapper demo complete!")
