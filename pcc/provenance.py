"""
Provenance tracking for PCC-NIUC system.
Maintains computation lineage and data flow tracking.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import hashlib


class ProvenanceEventType(Enum):
    """Types of provenance events."""
    DATA_INPUT = "data_input"
    DATA_OUTPUT = "data_output"
    COMPUTATION = "computation"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    CERTIFICATION = "certification"


@dataclass
class ProvenanceEvent:
    """Single provenance event in computation lineage."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: ProvenanceEventType = ProvenanceEventType.COMPUTATION
    timestamp: float = field(default_factory=time.time)
    actor: str = "system"
    operation: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    data_hash: str = ""
    
    def __post_init__(self):
        """Compute data hash after initialization."""
        if not self.data_hash:
            self.data_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash of event data."""
        data = f"{self.event_type.value}{self.actor}{self.operation}" + \
               "".join(sorted(self.inputs)) + "".join(sorted(self.outputs))
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class ProvenanceTracker:
    """Tracks computation provenance and data lineage."""
    
    def __init__(self, computation_id: Optional[str] = None):
        self.computation_id = computation_id or str(uuid.uuid4())
        self.events: List[ProvenanceEvent] = []
        self.data_lineage: Dict[str, List[str]] = {}  # data_id -> list of event_ids
        self.event_dependencies: Dict[str, Set[str]] = {}  # event_id -> set of dependent event_ids
    
    def record_event(self, 
                    event_type: ProvenanceEventType,
                    operation: str,
                    inputs: Optional[List[str]] = None,
                    outputs: Optional[List[str]] = None,
                    actor: str = "system",
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Record a provenance event.
        
        Args:
            event_type: Type of event
            operation: Description of operation performed
            inputs: List of input data identifiers
            outputs: List of output data identifiers
            actor: Entity performing the operation
            metadata: Additional metadata
            
        Returns:
            Event ID
        """
        event = ProvenanceEvent(
            event_type=event_type,
            operation=operation,
            inputs=inputs or [],
            outputs=outputs or [],
            actor=actor,
            metadata=metadata or {}
        )
        
        self.events.append(event)
        
        # Update data lineage
        for input_id in event.inputs:
            if input_id not in self.data_lineage:
                self.data_lineage[input_id] = []
            self.data_lineage[input_id].append(event.event_id)
        
        for output_id in event.outputs:
            if output_id not in self.data_lineage:
                self.data_lineage[output_id] = []
            self.data_lineage[output_id].append(event.event_id)
        
        # Update event dependencies
        self._update_dependencies(event.event_id, event.inputs)
        
        return event.event_id
    
    def record_data_input(self, data_id: str, source: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record data input event."""
        return self.record_event(
            ProvenanceEventType.DATA_INPUT,
            f"Input from {source}",
            outputs=[data_id],
            metadata=metadata
        )
    
    def record_data_output(self, data_id: str, destination: str,
                          inputs: Optional[List[str]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record data output event."""
        return self.record_event(
            ProvenanceEventType.DATA_OUTPUT,
            f"Output to {destination}",
            inputs=inputs or [],
            outputs=[data_id],
            metadata=metadata
        )
    
    def record_computation(self, operation: str, 
                          inputs: List[str], 
                          outputs: List[str],
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record computation event."""
        return self.record_event(
            ProvenanceEventType.COMPUTATION,
            operation,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata
        )
    
    def get_data_lineage(self, data_id: str) -> List[ProvenanceEvent]:
        """Get lineage for specific data item."""
        if data_id not in self.data_lineage:
            return []
        
        event_ids = self.data_lineage[data_id]
        return [event for event in self.events if event.event_id in event_ids]
    
    def get_computation_graph(self) -> Dict[str, Any]:
        """Get computation graph representation."""
        nodes = []
        edges = []
        
        for event in self.events:
            nodes.append({
                'id': event.event_id,
                'type': event.event_type.value,
                'operation': event.operation,
                'actor': event.actor,
                'timestamp': event.timestamp,
                'metadata': event.metadata
            })
            
            # Add edges for dependencies
            for input_id in event.inputs:
                for prev_event in self.events:
                    if input_id in prev_event.outputs:
                        edges.append({
                            'from': prev_event.event_id,
                            'to': event.event_id,
                            'data': input_id
                        })
        
        return {
            'computation_id': self.computation_id,
            'nodes': nodes,
            'edges': edges
        }
    
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify provenance integrity."""
        violations = []
        
        # Check for orphaned data
        all_inputs = set()
        all_outputs = set()
        for event in self.events:
            all_inputs.update(event.inputs)
            all_outputs.update(event.outputs)
        
        orphaned_inputs = all_inputs - all_outputs
        if orphaned_inputs:
            violations.append(f"Orphaned inputs: {orphaned_inputs}")
        
        # Check event hash integrity
        for event in self.events:
            expected_hash = event._compute_hash()
            if event.data_hash != expected_hash:
                violations.append(f"Hash mismatch for event {event.event_id}")
        
        # Check temporal consistency
        for i in range(1, len(self.events)):
            if self.events[i].timestamp < self.events[i-1].timestamp:
                violations.append(f"Temporal inconsistency at event {self.events[i].event_id}")
        
        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'total_events': len(self.events),
            'unique_data_items': len(self.data_lineage)
        }
    
    def export_lineage(self) -> Dict[str, Any]:
        """Export complete provenance lineage."""
        return {
            'computation_id': self.computation_id,
            'events': [
                {
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'timestamp': event.timestamp,
                    'actor': event.actor,
                    'operation': event.operation,
                    'inputs': event.inputs,
                    'outputs': event.outputs,
                    'metadata': event.metadata,
                    'data_hash': event.data_hash
                }
                for event in self.events
            ],
            'lineage': self.data_lineage,
            'dependencies': {k: list(v) for k, v in self.event_dependencies.items()}
        }
    
    def _update_dependencies(self, event_id: str, inputs: List[str]):
        """Update event dependency graph."""
        if event_id not in self.event_dependencies:
            self.event_dependencies[event_id] = set()
        
        for input_id in inputs:
            # Find events that produced this input
            for event in self.events:
                if input_id in event.outputs and event.event_id != event_id:
                    self.event_dependencies[event_id].add(event.event_id)


def create_provenance_tracker(computation_id: Optional[str] = None) -> ProvenanceTracker:
    """Create a new provenance tracker."""
    return ProvenanceTracker(computation_id)
