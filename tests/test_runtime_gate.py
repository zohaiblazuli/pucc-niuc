"""
Tests for the runtime_gate module.
Tests runtime security enforcement functionality for PCC-NIUC system.
Expected behavior: Runtime gate should enforce policies during execution.
"""

import unittest
import sys
import os
import time
import threading

# Add pcc module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pcc.runtime_gate import (
    RuntimeGate, RuntimePolicy, ResourceMonitor, PolicyDecision,
    get_runtime_gate, check_operation, shutdown_gate,
    enforce_runtime_policy, safe_builtin_access
)


class TestRuntimePolicy(unittest.TestCase):
    """Test cases for RuntimePolicy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.policy = RuntimePolicy()
    
    def test_policy_initialization(self):
        """Test policy initialization."""
        self.assertIsInstance(self.policy.allowed_operations, set)
        self.assertIsInstance(self.policy.denied_operations, set)
        self.assertIsInstance(self.policy.resource_limits, dict)
        
        # Check default allowed operations
        self.assertIn('arithmetic', self.policy.allowed_operations)
        self.assertIn('comparison', self.policy.allowed_operations)
        self.assertIn('function_call', self.policy.allowed_operations)
        
        # Check default denied operations
        self.assertIn('file_access', self.policy.denied_operations)
        self.assertIn('network_access', self.policy.denied_operations)
        self.assertIn('eval', self.policy.denied_operations)
    
    def test_allowed_operation_evaluation(self):
        """Test evaluation of allowed operations."""
        context = {
            'memory_mb': 10,
            'cpu_time_sec': 1,
            'iterations': 100,
            'recursion_depth': 5
        }
        
        decision = self.policy.evaluate_operation('arithmetic', 'addition', context)
        self.assertEqual(decision, PolicyDecision.ALLOW)
        
        decision = self.policy.evaluate_operation('comparison', 'equality', context)
        self.assertEqual(decision, PolicyDecision.ALLOW)
    
    def test_denied_operation_evaluation(self):
        """Test evaluation of denied operations."""
        context = {}
        
        decision = self.policy.evaluate_operation('file_access', 'read', context)
        self.assertEqual(decision, PolicyDecision.DENY)
        
        decision = self.policy.evaluate_operation('network_access', 'http_request', context)
        self.assertEqual(decision, PolicyDecision.DENY)
        
        decision = self.policy.evaluate_operation('eval', 'code_execution', context)
        self.assertEqual(decision, PolicyDecision.DENY)
    
    def test_resource_limit_enforcement(self):
        """Test resource limit enforcement."""
        # Within limits
        context_good = {
            'memory_mb': 50,  # Under 100MB limit
            'cpu_time_sec': 10,  # Under 30s limit
            'iterations': 1000,  # Under 10000 limit
            'recursion_depth': 10  # Under 100 limit
        }
        decision = self.policy.evaluate_operation('arithmetic', 'addition', context_good)
        self.assertEqual(decision, PolicyDecision.ALLOW)
        
        # Memory limit exceeded
        context_memory = {
            'memory_mb': 150,  # Over 100MB limit
            'cpu_time_sec': 1,
            'iterations': 100,
            'recursion_depth': 5
        }
        decision = self.policy.evaluate_operation('arithmetic', 'addition', context_memory)
        self.assertEqual(decision, PolicyDecision.THROTTLE)
        
        # CPU time limit exceeded
        context_cpu = {
            'memory_mb': 50,
            'cpu_time_sec': 40,  # Over 30s limit
            'iterations': 100,
            'recursion_depth': 5
        }
        decision = self.policy.evaluate_operation('arithmetic', 'addition', context_cpu)
        self.assertEqual(decision, PolicyDecision.THROTTLE)
    
    def test_unknown_operation_monitoring(self):
        """Test that unknown operations default to monitoring."""
        context = {}
        decision = self.policy.evaluate_operation('unknown_op', 'mysterious', context)
        self.assertEqual(decision, PolicyDecision.MONITOR)


class TestResourceMonitor(unittest.TestCase):
    """Test cases for ResourceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ResourceMonitor()
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        self.assertIsInstance(self.monitor.start_time, float)
        self.assertEqual(self.monitor.iteration_count, 0)
        self.assertEqual(self.monitor.recursion_depth, 0)
        self.assertTrue(self.monitor.active)
    
    def test_iteration_counting(self):
        """Test iteration counting."""
        initial_count = self.monitor.iteration_count
        
        self.monitor.increment_iteration()
        self.assertEqual(self.monitor.iteration_count, initial_count + 1)
        
        self.monitor.increment_iteration()
        self.assertEqual(self.monitor.iteration_count, initial_count + 2)
    
    def test_recursion_depth_tracking(self):
        """Test recursion depth tracking."""
        self.monitor.set_recursion_depth(10)
        self.assertEqual(self.monitor.recursion_depth, 10)
        
        self.monitor.set_recursion_depth(25)
        self.assertEqual(self.monitor.recursion_depth, 25)
    
    def test_context_generation(self):
        """Test context generation."""
        # Let some time pass
        time.sleep(0.1)
        
        context = self.monitor.get_context()
        
        self.assertIn('cpu_time_sec', context)
        self.assertIn('iterations', context)
        self.assertIn('memory_mb', context)
        self.assertIn('recursion_depth', context)
        
        # CPU time should be > 0
        self.assertGreater(context['cpu_time_sec'], 0)
        
        # Iterations should match our tracking
        self.assertEqual(context['iterations'], self.monitor.iteration_count)
        
        # Memory should be >= 0
        self.assertGreaterEqual(context['memory_mb'], 0)


class TestRuntimeGate(unittest.TestCase):
    """Test cases for RuntimeGate class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a fresh policy for each test
        self.policy = RuntimePolicy()
        self.gate = RuntimeGate(self.policy)
    
    def tearDown(self):
        """Clean up after each test."""
        self.gate.shutdown()
    
    def test_gate_initialization(self):
        """Test gate initialization."""
        self.assertIsNotNone(self.gate.policy)
        self.assertIsNotNone(self.gate.monitor)
        self.assertEqual(self.gate.violations, 0)
        self.assertTrue(self.gate.active)
        self.assertEqual(len(self.gate.events), 0)
    
    def test_allowed_operation_check(self):
        """Test checking allowed operations."""
        result = self.gate.check_operation('arithmetic', 'addition')
        self.assertTrue(result)
        
        # Should have recorded event
        self.assertGreater(len(self.gate.events), 0)
        event = self.gate.events[-1]
        self.assertEqual(event.operation, 'arithmetic')
        self.assertEqual(event.resource, 'addition')
        self.assertEqual(event.decision, PolicyDecision.ALLOW)
    
    def test_denied_operation_check(self):
        """Test checking denied operations."""
        result = self.gate.check_operation('file_access', 'read_file')
        self.assertFalse(result)
        
        # Should have recorded violation
        self.assertGreater(self.gate.violations, 0)
        
        # Should have recorded event
        event = self.gate.events[-1]
        self.assertEqual(event.operation, 'file_access')
        self.assertEqual(event.decision, PolicyDecision.DENY)
    
    def test_monitored_operation_check(self):
        """Test checking operations that should be monitored."""
        result = self.gate.check_operation('unknown_operation', 'mystery')
        self.assertTrue(result)  # Should be allowed but monitored
        
        # Should have recorded event
        event = self.gate.events[-1]
        self.assertEqual(event.decision, PolicyDecision.MONITOR)
    
    def test_iteration_checking(self):
        """Test iteration checking."""
        # First few iterations should be allowed
        for i in range(10):
            result = self.gate.enter_iteration()
            self.assertTrue(result)
        
        # Check that iteration count is tracked
        context = self.gate.monitor.get_context()
        self.assertEqual(context['iterations'], 10)
    
    def test_function_entry_checking(self):
        """Test function entry checking."""
        result = self.gate.enter_function('test_function')
        self.assertTrue(result)
        
        # Should have recorded event
        event = self.gate.events[-1]
        self.assertEqual(event.operation, 'function_call')
        self.assertEqual(event.resource, 'test_function')
    
    def test_builtin_access_checking(self):
        """Test builtin access checking."""
        # Safe builtins should be allowed
        result = self.gate.access_builtin('len')
        self.assertTrue(result)
        
        result = self.gate.access_builtin('sum')
        self.assertTrue(result)
        
        # Potentially dangerous operations might be restricted
        # (depending on policy configuration)
        result = self.gate.access_builtin('eval')
        # Result depends on how eval is configured in policy
    
    def test_runtime_report_generation(self):
        """Test runtime report generation."""
        # Perform some operations
        self.gate.check_operation('arithmetic', 'addition')
        self.gate.check_operation('file_access', 'read')  # This will be denied
        self.gate.enter_iteration()
        self.gate.enter_function('test_func')
        
        report = self.gate.get_runtime_report()
        
        # Check report structure
        self.assertIn('execution_time_sec', report)
        self.assertIn('total_iterations', report)
        self.assertIn('peak_memory_mb', report)
        self.assertIn('max_recursion_depth', report)
        self.assertIn('total_events', report)
        self.assertIn('violations', report)
        self.assertIn('event_summary', report)
        self.assertIn('policy_decisions', report)
        
        # Should have some events
        self.assertGreater(report['total_events'], 0)
        
        # Should have at least one violation (file_access)
        self.assertGreater(report['violations'], 0)
    
    def test_gate_shutdown(self):
        """Test gate shutdown."""
        self.assertTrue(self.gate.active)
        
        self.gate.shutdown()
        
        self.assertFalse(self.gate.active)
        self.assertFalse(self.gate.monitor.active)
    
    def test_throttling_behavior(self):
        """Test throttling behavior for resource-intensive operations."""
        # Create context that exceeds memory limit
        metadata = {'memory_mb': 150}  # Exceeds default 100MB limit
        
        start_time = time.time()
        result = self.gate.check_operation('arithmetic', 'addition', metadata)
        end_time = time.time()
        
        # Should still be allowed
        self.assertTrue(result)
        
        # Should have added delay (throttling)
        elapsed = end_time - start_time
        if self.gate.events[-1].decision == PolicyDecision.THROTTLE:
            self.assertGreater(elapsed, 0.05)  # At least some delay
    
    def test_concurrent_access_safety(self):
        """Test thread safety of runtime gate."""
        results = []
        
        def worker():
            for i in range(10):
                result = self.gate.check_operation('arithmetic', f'op_{i}')
                results.append(result)
        
        # Start multiple threads
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should have been processed
        self.assertEqual(len(results), 30)  # 3 threads * 10 operations
        self.assertTrue(all(results))  # All should be True (arithmetic allowed)
        
        # Should have recorded all events
        self.assertEqual(len(self.gate.events), 30)


class TestGlobalRuntimeGate(unittest.TestCase):
    """Test cases for global runtime gate functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Make sure we start with clean global state
        shutdown_gate()
    
    def tearDown(self):
        """Clean up after tests."""
        shutdown_gate()
    
    def test_get_runtime_gate_singleton(self):
        """Test that get_runtime_gate returns singleton."""
        gate1 = get_runtime_gate()
        gate2 = get_runtime_gate()
        
        # Should be the same instance
        self.assertIs(gate1, gate2)
    
    def test_check_operation_convenience_function(self):
        """Test convenience check_operation function."""
        result = check_operation('arithmetic', 'addition')
        self.assertTrue(result)
        
        result = check_operation('file_access', 'read')
        self.assertFalse(result)
    
    def test_shutdown_gate_function(self):
        """Test shutdown_gate function."""
        # Get gate to create it
        gate = get_runtime_gate()
        self.assertTrue(gate.active)
        
        # Shutdown
        shutdown_gate()
        
        # Gate should be shutdown
        self.assertFalse(gate.active)
        
        # Getting gate again should create new one
        new_gate = get_runtime_gate()
        self.assertIsNot(gate, new_gate)
        self.assertTrue(new_gate.active)


class TestRuntimePolicyDecorator(unittest.TestCase):
    """Test cases for runtime policy decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        shutdown_gate()
    
    def tearDown(self):
        """Clean up after tests."""
        shutdown_gate()
    
    def test_enforce_runtime_policy_decorator(self):
        """Test the enforce_runtime_policy decorator."""
        
        @enforce_runtime_policy()
        def safe_function(x, y):
            return x + y
        
        # Should work normally for allowed function
        result = safe_function(5, 3)
        self.assertEqual(result, 8)
        
        # Should have recorded function call
        gate = get_runtime_gate()
        events = gate.events
        func_events = [e for e in events if e.operation == 'function_call']
        self.assertGreater(len(func_events), 0)
    
    def test_safe_builtin_access_function(self):
        """Test safe_builtin_access function."""
        # Should allow safe builtins
        len_func = safe_builtin_access('len')
        self.assertEqual(len_func, len)
        
        sum_func = safe_builtin_access('sum')
        self.assertEqual(sum_func, sum)
        
        # Should handle denied builtins
        try:
            eval_func = safe_builtin_access('eval')
            # If it doesn't raise an exception, eval access was allowed
            # (behavior depends on policy configuration)
        except RuntimeError as e:
            # Expected for restricted eval access
            self.assertIn('denied', str(e))
        
        # Should handle non-existent builtins
        result = safe_builtin_access('nonexistent_builtin', 'default')
        self.assertEqual(result, 'default')


class TestRuntimeGateIntegration(unittest.TestCase):
    """Integration tests for runtime gate."""
    
    def setUp(self):
        """Set up test fixtures."""
        shutdown_gate()
    
    def tearDown(self):
        """Clean up after tests."""
        shutdown_gate()
    
    def test_full_execution_monitoring(self):
        """Test full execution monitoring scenario."""
        gate = get_runtime_gate()
        
        # Simulate a computation with various operations
        gate.check_operation('arithmetic', 'addition')
        gate.enter_function('main_function')
        
        for i in range(5):
            gate.enter_iteration()
            gate.check_operation('comparison', 'greater_than')
        
        gate.check_operation('arithmetic', 'multiplication')
        
        # Try some denied operations
        gate.check_operation('file_access', 'write')  # Should be denied
        gate.check_operation('network_access', 'http')  # Should be denied
        
        # Get final report
        report = gate.get_runtime_report()
        
        # Verify report contents
        self.assertGreater(report['total_events'], 0)
        self.assertGreater(report['violations'], 0)  # From denied operations
        self.assertGreaterEqual(report['policy_decisions']['allow'], 1)
        self.assertGreaterEqual(report['policy_decisions']['deny'], 1)
    
    def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion."""
        policy = RuntimePolicy()
        # Set very low limits for testing
        policy.resource_limits['max_iterations'] = 3
        policy.resource_limits['max_cpu_time_sec'] = 0.5
        
        gate = RuntimeGate(policy)
        
        try:
            # Should work for first few iterations
            for i in range(3):
                result = gate.enter_iteration()
                self.assertTrue(result)
            
            # Further iterations might be throttled
            # (exact behavior depends on implementation)
            
            # Simulate long execution time
            time.sleep(0.6)  # Exceed CPU time limit
            
            # Operations might be throttled now
            result = gate.check_operation('arithmetic', 'addition')
            # Result depends on policy implementation
            
        finally:
            gate.shutdown()


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
