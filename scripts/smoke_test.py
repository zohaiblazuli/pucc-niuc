#!/usr/bin/env python3
"""
Smoke tests for PCC-NIUC system.
Tests basic imports and function calls to ensure CI passes.
"""

import sys
import os
import traceback

# Add pcc module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🔍 Testing imports...")
    
    try:
        # Core PCC modules
        from pcc.normalizer import normalize_code
        from pcc.imperative_grammar import validate_grammar  
        from pcc.provenance import create_provenance_tracker
        from pcc.checker import check_code_security
        from pcc.certificate import generate_certificate, validate_certificate
        from pcc.runtime_gate import get_runtime_gate, check_operation
        from pcc.rewrite import rewrite_code
        
        # Support modules
        from bench.score import BenchmarkRunner
        from demo.demo_cli import DemoSession
        
        print("   ✅ All imports successful")
        return True
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_normalizer():
    """Test code normalizer basic functionality."""
    print("🔧 Testing normalizer...")
    
    try:
        from pcc.normalizer import normalize_code
        
        # Simple test code
        code = "def test(): return 42"
        result = normalize_code(code)
        
        # Check required fields
        assert 'normalized_code' in result
        assert 'original_hash' in result
        assert 'metadata' in result
        assert isinstance(result['metadata']['complexity_score'], int)
        
        print("   ✅ Normalizer working")
        return True
    except Exception as e:
        print(f"   ❌ Normalizer failed: {e}")
        traceback.print_exc()
        return False

def test_checker():
    """Test security checker basic functionality."""
    print("🔒 Testing checker...")
    
    try:
        from pcc.checker import check_code_security
        
        # Test safe code
        safe_code = "def add(a, b): return a + b"
        result = check_code_security(safe_code)
        
        # Check required fields and deterministic behavior
        assert 'security_level' in result
        assert 'total_violations' in result
        assert 'violations' in result
        assert result['security_level'] in ['approved', 'monitored', 'restricted', 'rejected']
        
        # Test deterministic behavior (same input = same output)
        result2 = check_code_security(safe_code)
        assert result == result2, "Checker must be deterministic"
        
        # Test dangerous code
        dangerous_code = "exec('malicious')"
        dangerous_result = check_code_security(dangerous_code)
        assert dangerous_result['security_level'] == 'rejected'
        assert dangerous_result['total_violations'] > 0
        
        print("   ✅ Checker working and deterministic")
        return True
    except Exception as e:
        print(f"   ❌ Checker failed: {e}")
        traceback.print_exc()
        return False

def test_certificate():
    """Test certificate generation and validation."""
    print("📜 Testing certificates...")
    
    try:
        from pcc.certificate import generate_certificate, validate_certificate
        
        # Generate certificate
        cert_json = generate_certificate(
            computation_code="def test(): return 42",
            input_data="test_input", 
            output_data="test_output"
        )
        
        # Validate certificate structure
        import json
        cert_data = json.loads(cert_json)
        required_fields = ['version', 'timestamp', 'certificate_id', 'computation_hash']
        for field in required_fields:
            assert field in cert_data, f"Missing required field: {field}"
        
        # Validate certificate
        validation_result = validate_certificate(cert_json)
        assert 'is_valid' in validation_result
        
        print("   ✅ Certificate generation/validation working")
        return True
    except Exception as e:
        print(f"   ❌ Certificate failed: {e}")
        traceback.print_exc()
        return False

def test_runtime_gate():
    """Test runtime gate basic functionality."""
    print("🚪 Testing runtime gate...")
    
    try:
        from pcc.runtime_gate import get_runtime_gate, check_operation, shutdown_gate
        
        # Test basic operation checking
        result = check_operation('arithmetic', 'addition')
        assert isinstance(result, bool)
        
        # Test gate retrieval
        gate = get_runtime_gate()
        assert gate is not None
        assert hasattr(gate, 'check_operation')
        
        # Cleanup
        shutdown_gate()
        
        print("   ✅ Runtime gate working")
        return True
    except Exception as e:
        print(f"   ❌ Runtime gate failed: {e}")
        traceback.print_exc()
        return False

def test_grammar():
    """Test imperative grammar validation."""
    print("📝 Testing grammar validation...")
    
    try:
        from pcc.imperative_grammar import validate_grammar
        
        # Test valid code
        code = "def safe_func(x): return x + 1"
        result = validate_grammar(code)
        
        assert 'is_valid' in result
        assert 'violations' in result
        assert 'security_level' in result
        
        print("   ✅ Grammar validation working")
        return True
    except Exception as e:
        print(f"   ❌ Grammar validation failed: {e}")
        traceback.print_exc()
        return False

def test_provenance():
    """Test provenance tracking."""
    print("📊 Testing provenance...")
    
    try:
        from pcc.provenance import create_provenance_tracker
        
        tracker = create_provenance_tracker()
        assert tracker is not None
        assert hasattr(tracker, 'record_event')
        
        # Record a simple event
        event_id = tracker.record_computation(
            "test_computation",
            ["input1"],
            ["output1"]
        )
        assert event_id is not None
        
        print("   ✅ Provenance tracking working")
        return True
    except Exception as e:
        print(f"   ❌ Provenance failed: {e}")
        traceback.print_exc()
        return False

def test_rewrite():
    """Test code rewriting."""
    print("🔄 Testing code rewriter...")
    
    try:
        from pcc.rewrite import rewrite_code
        
        code = "def simple(): return 42"
        result = rewrite_code(code)
        
        assert 'success' in result
        assert 'rewritten_code' in result
        
        print("   ✅ Code rewriter working")
        return True
    except Exception as e:
        print(f"   ❌ Code rewriter failed: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """Test basic integration between components."""
    print("🔗 Testing integration...")
    
    try:
        from pcc.normalizer import normalize_code
        from pcc.checker import check_code_security
        from pcc.certificate import generate_certificate
        
        # Test integration flow
        code = "def safe_add(a, b): return a + b"
        
        # Step 1: Normalize
        norm_result = normalize_code(code)
        
        # Step 2: Check security  
        sec_result = check_code_security(code)
        
        # Step 3: Generate certificate if approved
        if sec_result['security_level'] == 'approved':
            cert = generate_certificate(code, "input", "output")
            assert len(cert) > 0
        
        print("   ✅ Integration working")
        return True
    except Exception as e:
        print(f"   ❌ Integration failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all smoke tests."""
    print("🧪 PCC-NIUC Smoke Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_normalizer,
        test_checker,
        test_certificate,
        test_runtime_gate,
        test_grammar,
        test_provenance,
        test_rewrite,
        test_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ⚠️  {test_func.__name__} had issues")
        except Exception as e:
            print(f"   ❌ {test_func.__name__} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All smoke tests passed! System is working.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
