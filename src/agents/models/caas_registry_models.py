"""
Pydantic models for the Consulting-as-a-Service (CaaS) Agent Registry.
Defines the structure for 'Agent Cards' that represent hireable digital workers.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field
from src.agents.shared.a9_agent_base_model import A9AgentBaseModel

class AgentHireType(str, Enum):
    FRACTIONAL = "fractional"  # Pay per task/token
    DEDICATED = "dedicated"    # Retainer / monthly
    PROJECT = "project"        # Fixed bid

class AgentCapability(A9AgentBaseModel):
    name: str
    proficiency: float = 1.0  # 0.0 to 1.0
    description: Optional[str] = None
    tools: List[str] = Field(default_factory=list)

class AgentReview(A9AgentBaseModel):
    reviewer_role: str
    rating: float  # 1-5
    comment: str
    timestamp: str

class AgentPricing(A9AgentBaseModel):
    model: AgentHireType
    rate: float
    currency: str = "USD"
    unit: str = "hour"  # or "token_1k", "task"

class AgentCard(A9AgentBaseModel):
    """
    Represents a hireable agent in the CaaS marketplace.
    """
    id: str
    name: str
    role: str  # e.g. "Forensic Accountant", "Supply Chain Optimizer"
    description: str
    avatar_icon: str  # Icon name reference
    
    # Commercials
    pricing: List[AgentPricing] = Field(default_factory=list)
    availability: str = "immediate"
    
    # Skills & Specs
    capabilities: List[AgentCapability] = Field(default_factory=list)
    specializations: List[str] = Field(default_factory=list) # e.g. "Retail", "Manufacturing"
    supported_languages: List[str] = ["en"]
    
    # Social Proof
    rating_avg: float = 5.0
    reviews_count: int = 0
    success_rate: float = 1.0
    reviews: List[AgentReview] = Field(default_factory=list)
    
    # System Metadata
    factory_ref: str  # Class name to instantiate
    version: str = "1.0.0"
    compliance_level: str = "standard"  # standard, hipaa, soc2
