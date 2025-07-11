"""
Agent Configuration System
Manages LLM provider assignments for different agent types
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json


class AgentType(str, Enum):
    """Different types of agents in the system"""
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    WRITER = "writer"
    REVIEWER = "reviewer"


class LLMProvider(str, Enum):
    """Available LLM providers"""
    OPENAI = "openai"
    CLAUDE = "claude"
    GOOGLE = "google"
    MOCK = "mock"


@dataclass
class AgentConfig:
    """Configuration for agent LLM assignments"""
    orchestrator_llm: str = "google"
    orchestrator_model: str = "gemini-2.5-pro"
    
    planner_llm: str = "google"
    planner_model: str = "gemini-2.5-pro"
    
    writer_llm: str = "google"
    writer_model: str = "gemini-2.5-pro"
    
    reviewer_llm: str = "google"
    reviewer_model: str = "gemini-2.5-pro"
    
    # Global settings
    fallback_llm: str = "mock"
    fallback_model: str = "mock"
    
    # Performance settings
    max_retries: int = 3
    timeout_seconds: int = 30
    
    def get_llm_for_agent(self, agent_type: AgentType) -> tuple[str, str]:
        """Get LLM provider and model for a specific agent type"""
        mapping = {
            AgentType.ORCHESTRATOR: (self.orchestrator_llm, self.orchestrator_model),
            AgentType.PLANNER: (self.planner_llm, self.planner_model),
            AgentType.WRITER: (self.writer_llm, self.writer_model),
            AgentType.REVIEWER: (self.reviewer_llm, self.reviewer_model),
        }
        
        return mapping.get(agent_type, (self.fallback_llm, self.fallback_model))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "orchestrator_llm": self.orchestrator_llm,
            "orchestrator_model": self.orchestrator_model,
            "planner_llm": self.planner_llm,
            "planner_model": self.planner_model,
            "writer_llm": self.writer_llm,
            "writer_model": self.writer_model,
            "reviewer_llm": self.reviewer_llm,
            "reviewer_model": self.reviewer_model,
            "fallback_llm": self.fallback_llm,
            "fallback_model": self.fallback_model,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentConfig':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class AgentConfigManager:
    """Manages agent configurations"""
    
    def __init__(self):
        self.default_config = AgentConfig()
        self._document_configs: Dict[int, AgentConfig] = {}
    
    def get_config(self, document_id: Optional[int] = None) -> AgentConfig:
        """Get configuration for a specific document or default"""
        if document_id and document_id in self._document_configs:
            return self._document_configs[document_id]
        return self.default_config
    
    def set_config(self, config: AgentConfig, document_id: Optional[int] = None):
        """Set configuration for a specific document or default"""
        if document_id:
            self._document_configs[document_id] = config
        else:
            self.default_config = config
    
    def update_config(self, updates: Dict[str, Any], document_id: Optional[int] = None):
        """Update specific fields in configuration"""
        current_config = self.get_config(document_id)
        config_dict = current_config.to_dict()
        config_dict.update(updates)
        
        new_config = AgentConfig.from_dict(config_dict)
        self.set_config(new_config, document_id)
    
    def get_optimal_config_for_task(self, task_type: str) -> AgentConfig:
        """Get optimal configuration based on task type"""
        # For now, return default config
        # This can be expanded to have task-specific optimizations
        return self.default_config
    
    def validate_config(self, config: AgentConfig) -> tuple[bool, Optional[str]]:
        """Validate configuration settings"""
        valid_providers = [provider.value for provider in LLMProvider]
        
        # Check all LLM providers are valid
        for agent_type in AgentType:
            provider, model = config.get_llm_for_agent(agent_type)
            if provider not in valid_providers:
                return False, f"Invalid provider '{provider}' for {agent_type.value}"
        
        # Check performance settings
        if config.max_retries < 1:
            return False, "max_retries must be at least 1"
        
        if config.timeout_seconds < 5:
            return False, "timeout_seconds must be at least 5"
        
        return True, None


# Global instance
agent_config_manager = AgentConfigManager()