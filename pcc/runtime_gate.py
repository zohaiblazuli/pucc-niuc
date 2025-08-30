"""
Runtime gate for PCC-NIUC system.
Enforces runtime security policies during computation execution.
"""

from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
import time
import threading
import traceback
import sys
import os


class PolicyDecision(Enum):
    """Runtime policy decisions."""
    ALLOW = "allow"
    DENY = "deny"
    MONITOR = "monitor"
    THROTTLE = "throttle"


@dataclass
class RuntimeEvent:
    """Runtime security event."""
    timestamp: float
    event_type: str
    operation: str
    resource: str
    decision: PolicyDecision
    metadata: Dict[str, Any]


class RuntimePolicy:
    """Runtime security policy definition."""
    
    def __init__(self):
        self.allowed_operations: Set[str] = {
            'arithmetic', 'comparison', 'assignment', 'iteration', 'function_call'
        }
        self.denied_operations: Set[str] = {
            'file_access', 'network_access', 'system_call', 'eval', 'exec'
        }
        self.resource_limits = {
            'max_memory_mb': 100,
            'max_cpu_time_sec': 30,
            'max_iterations': 10000,
            'max_recursion_depth': 100
        }
        self.monitoring_rules = {
            'log_all_operations': False,
            'alert_on_violations': True,
            'track_resource_usage': True
        }
    
    def evaluate_operation(self, operation: str, resource: str, 
                          context: Dict[str, Any]) -> PolicyDecision:
        """Evaluate whether an operation should be allowed."""
        if operation in self.denied_operations:
            return PolicyDecision.DENY
        
        if operation in self.allowed_operations:
            # Check resource limits
            if self._check_resource_limits(context):
                return PolicyDecision.ALLOW
            else:
                return PolicyDecision.THROTTLE
        
        # Default to monitoring unknown operations
        return PolicyDecision.MONITOR
    
    def _check_resource_limits(self, context: Dict[str, Any]) -> bool:
        """Check if resource limits are within bounds."""
        memory_usage = context.get('memory_mb', 0)
        cpu_time = context.get('cpu_time_sec', 0)
        iterations = context.get('iterations', 0)
        recursion_depth = context.get('recursion_depth', 0)
        
        return (memory_usage <= self.resource_limits['max_memory_mb'] and
                cpu_time <= self.resource_limits['max_cpu_time_sec'] and
                iterations <= self.resource_limits['max_iterations'] and
                recursion_depth <= self.resource_limits['max_recursion_depth'])


class ResourceMonitor:
    """Monitors runtime resource usage."""
    
    def __init__(self):
        self.start_time = time.time()
        self.iteration_count = 0
        self.memory_peak = 0
        self.recursion_depth = 0
        self.active = True
        self._lock = threading.Lock()
    
    def get_context(self) -> Dict[str, Any]:
        """Get current resource usage context."""
        with self._lock:
            return {
                'cpu_time_sec': time.time() - self.start_time,
                'iterations': self.iteration_count,
                'memory_mb': self._get_memory_usage(),
                'recursion_depth': self.recursion_depth
            }
    
    def increment_iteration(self):
        """Increment iteration counter."""
        with self._lock:
            self.iteration_count += 1
    
    def set_recursion_depth(self, depth: int):
        """Update recursion depth."""
        with self._lock:
            self.recursion_depth = depth
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback if psutil not available
            return 0.0


class RuntimeGate:
    """Main runtime security gate."""
    
    def __init__(self, policy: Optional[RuntimePolicy] = None):
        self.policy = policy or RuntimePolicy()
        self.monitor = ResourceMonitor()
        self.events: List[RuntimeEvent] = []
        self.violations = 0
        self.active = True
        self._lock = threading.Lock()
    
    def check_operation(self, operation: str, resource: str = "", 
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if an operation should be allowed.
        
        Args:
            operation: Type of operation being performed
            resource: Resource being accessed
            metadata: Additional operation metadata
            
        Returns:
            True if operation is allowed, False otherwise
        """
        if not self.active:
            return True
        
        context = self.monitor.get_context()
        context.update(metadata or {})
        
        decision = self.policy.evaluate_operation(operation, resource, context)
        
        # Record event
        event = RuntimeEvent(
            timestamp=time.time(),
            event_type="operation_check",
            operation=operation,
            resource=resource,
            decision=decision,
            metadata=context
        )
        
        with self._lock:
            self.events.append(event)
        
        # Handle decision
        if decision == PolicyDecision.DENY:
            self.violations += 1
            if self.policy.monitoring_rules.get('alert_on_violations', True):
                self._alert_violation(operation, resource, context)
            return False
        
        elif decision == PolicyDecision.THROTTLE:
            # Implement throttling by adding delay
            time.sleep(0.1)
            return True
        
        elif decision == PolicyDecision.MONITOR:
            # Log operation for monitoring
            self._log_operation(operation, resource, context)
            return True
        
        else:  # ALLOW
            return True
    
    def enter_iteration(self):
        """Called when entering an iteration loop."""
        self.monitor.increment_iteration()
        return self.check_operation("iteration", "loop")
    
    def enter_function(self, func_name: str):
        """Called when entering a function."""
        depth = len(traceback.extract_stack())
        self.monitor.set_recursion_depth(depth)
        return self.check_operation("function_call", func_name)
    
    def access_builtin(self, builtin_name: str):
        """Called when accessing builtin functions."""
        return self.check_operation("builtin_access", builtin_name)
    
    def get_runtime_report(self) -> Dict[str, Any]:
        """Get runtime execution report."""
        context = self.monitor.get_context()
        
        with self._lock:
            event_summary = {}
            for event in self.events:
                key = f"{event.operation}_{event.decision.value}"
                event_summary[key] = event_summary.get(key, 0) + 1
        
        return {
            'execution_time_sec': context['cpu_time_sec'],
            'total_iterations': context['iterations'],
            'peak_memory_mb': context['memory_mb'],
            'max_recursion_depth': context['recursion_depth'],
            'total_events': len(self.events),
            'violations': self.violations,
            'event_summary': event_summary,
            'policy_decisions': {
                'allow': sum(1 for e in self.events if e.decision == PolicyDecision.ALLOW),
                'deny': sum(1 for e in self.events if e.decision == PolicyDecision.DENY),
                'monitor': sum(1 for e in self.events if e.decision == PolicyDecision.MONITOR),
                'throttle': sum(1 for e in self.events if e.decision == PolicyDecision.THROTTLE)
            }
        }
    
    def shutdown(self):
        """Shutdown the runtime gate."""
        self.active = False
        self.monitor.active = False
    
    def _alert_violation(self, operation: str, resource: str, context: Dict[str, Any]):
        """Handle security violation alert."""
        # In a real system, this would send alerts to security monitoring
        print(f"SECURITY VIOLATION: {operation} on {resource} - Context: {context}")
    
    def _log_operation(self, operation: str, resource: str, context: Dict[str, Any]):
        """Log operation for monitoring."""
        if self.policy.monitoring_rules.get('log_all_operations', False):
            print(f"MONITORED: {operation} on {resource}")


# Global runtime gate instance
_runtime_gate = None
_gate_lock = threading.Lock()


def get_runtime_gate(policy: Optional[RuntimePolicy] = None) -> RuntimeGate:
    """Get or create the global runtime gate."""
    global _runtime_gate
    with _gate_lock:
        if _runtime_gate is None:
            _runtime_gate = RuntimeGate(policy)
        return _runtime_gate


def check_operation(operation: str, resource: str = "", 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to check operation."""
    gate = get_runtime_gate()
    return gate.check_operation(operation, resource, metadata)


def shutdown_gate():
    """Shutdown the global runtime gate."""
    global _runtime_gate
    with _gate_lock:
        if _runtime_gate:
            _runtime_gate.shutdown()
            _runtime_gate = None


# Runtime enforcement decorators
def enforce_runtime_policy(operation_type: str = "function_call"):
    """Decorator to enforce runtime policy on functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            gate = get_runtime_gate()
            func_name = func.__name__
            
            if not gate.enter_function(func_name):
                raise RuntimeError(f"Function {func_name} denied by security policy")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_builtin_access(builtin_name: str, default_value=None):
    """Safely access builtin functions through runtime gate."""
    gate = get_runtime_gate()
    if gate.access_builtin(builtin_name):
        try:
            return getattr(__builtins__, builtin_name)
        except AttributeError:
            return default_value
    else:
        raise RuntimeError(f"Access to builtin '{builtin_name}' denied by security policy")
