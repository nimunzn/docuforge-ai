"""
Agent States and State Management
Defines the states and transitions for the multi-agent system
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


class AgentState(str, Enum):
    """Possible states for agents"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    WRITING = "writing"
    REVIEWING = "reviewing"
    UPDATING_PREVIEW = "updating_preview"
    WAITING_FEEDBACK = "waiting_feedback"
    ERROR = "error"


class AgentAction(str, Enum):
    """Actions that agents can perform"""
    ANALYZE_REQUEST = "analyze_request"
    CREATE_PLAN = "create_plan"
    UPDATE_PLAN = "update_plan"
    WRITE_CONTENT = "write_content"
    REVIEW_CONTENT = "review_content"
    UPDATE_PREVIEW = "update_preview"
    REQUEST_FEEDBACK = "request_feedback"
    HANDLE_ERROR = "handle_error"


@dataclass
class AgentMessage:
    """Message from an agent to the user or other agents"""
    agent_type: str
    message_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "message_type": self.message_type,
            "content": self.content,
            "message_metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DocumentPlan:
    """Plan for document creation/modification"""
    document_type: str
    title: str
    sections: List[Dict[str, Any]]
    estimated_time: int  # in seconds
    current_step: int = 0
    total_steps: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_type": self.document_type,
            "title": self.title,
            "sections": self.sections,
            "estimated_time": self.estimated_time,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentPlan':
        data = data.copy()
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class AgentContext:
    """Context for agent operations"""
    document_id: int
    conversation_id: Optional[int] = None
    user_message: Optional[str] = None
    plan: Optional[DocumentPlan] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentStateManager:
    """Manages agent states and transitions"""
    
    def __init__(self):
        self.current_state: AgentState = AgentState.IDLE
        self.previous_states: List[AgentState] = []
        self.state_history: List[Dict[str, Any]] = []
        self.current_agent: Optional[str] = None
        self.message_queue: List[AgentMessage] = []
    
    def transition_to(self, new_state: AgentState, agent_type: str, message: str = None):
        """Transition to a new state"""
        if self.current_state != new_state:
            self.previous_states.append(self.current_state)
            self.current_state = new_state
            self.current_agent = agent_type
            
            # Record state transition
            self.state_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "from_state": self.previous_states[-1] if self.previous_states else None,
                "to_state": new_state.value,
                "agent": agent_type,
                "message": message
            })
    
    def add_message(self, message: AgentMessage):
        """Add a message to the queue"""
        self.message_queue.append(message)
    
    def get_messages(self, clear: bool = True) -> List[AgentMessage]:
        """Get all messages, optionally clearing the queue"""
        messages = self.message_queue.copy()
        if clear:
            self.message_queue.clear()
        return messages
    
    def is_busy(self) -> bool:
        """Check if agents are currently busy"""
        return self.current_state not in [AgentState.IDLE, AgentState.WAITING_FEEDBACK]
    
    def can_transition_to(self, new_state: AgentState) -> bool:
        """Check if transition to new state is allowed"""
        # Define allowed transitions
        allowed_transitions = {
            AgentState.IDLE: [AgentState.ANALYZING],
            AgentState.ANALYZING: [AgentState.PLANNING, AgentState.WRITING, AgentState.ERROR],
            AgentState.PLANNING: [AgentState.WRITING, AgentState.ERROR],
            AgentState.WRITING: [AgentState.REVIEWING, AgentState.UPDATING_PREVIEW, AgentState.ERROR],
            AgentState.REVIEWING: [AgentState.WRITING, AgentState.UPDATING_PREVIEW, AgentState.WAITING_FEEDBACK, AgentState.ERROR],
            AgentState.UPDATING_PREVIEW: [AgentState.IDLE, AgentState.WAITING_FEEDBACK],
            AgentState.WAITING_FEEDBACK: [AgentState.ANALYZING, AgentState.IDLE],
            AgentState.ERROR: [AgentState.IDLE, AgentState.ANALYZING]
        }
        
        return new_state in allowed_transitions.get(self.current_state, [])
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information"""
        return {
            "current_state": self.current_state.value,
            "current_agent": self.current_agent,
            "is_busy": self.is_busy(),
            "message_count": len(self.message_queue),
            "last_transition": self.state_history[-1] if self.state_history else None
        }


class PreviewUpdateDecision:
    """Decides when to update the document preview"""
    
    def __init__(self):
        self.last_update_time: Optional[datetime] = None
        self.min_update_interval = 30  # seconds
        self.force_update_triggers = [
            AgentState.IDLE,
            AgentState.WAITING_FEEDBACK
        ]
    
    def should_update_preview(self, 
                            current_state: AgentState,
                            last_action: AgentAction,
                            time_since_last_update: int,
                            content_changes: int,
                            user_requested: bool = False) -> bool:
        """Determine if preview should be updated"""
        
        # Always update if user explicitly requested
        if user_requested:
            return True
        
        # Update when agent reaches certain states
        if current_state in self.force_update_triggers:
            return True
        
        # Update if significant content changes and enough time has passed
        if (content_changes > 100 and 
            time_since_last_update >= self.min_update_interval):
            return True
        
        # Update after completing major sections
        if (last_action == AgentAction.WRITE_CONTENT and 
            time_since_last_update >= self.min_update_interval):
            return True
        
        # Update after review suggests changes
        if last_action == AgentAction.REVIEW_CONTENT:
            return True
        
        return False
    
    def record_update(self):
        """Record that preview was updated"""
        self.last_update_time = datetime.utcnow()


# Global instances
agent_state_manager = AgentStateManager()
preview_decision_engine = PreviewUpdateDecision()