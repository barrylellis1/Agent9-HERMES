"""
Base Pydantic models for Agent9 agent protocol compliance.
All agent request/response models should inherit from these base models.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class A9AgentBaseModel(BaseModel):
    """
    Base model for all Agent9 agent models.
    Enforces Pydantic v2 compliance and consistent serialization.
    """
    model_config = ConfigDict(
        extra="allow",          # Allow extra fields for forward compatibility
        populate_by_name=True,  # Allow population by field name and alias
        validate_assignment=True # Validate attribute assignments
    )
    
    def serialize(self) -> Dict[str, Any]:
        """
        Standard serialization method for all Agent9 models.
        Uses Pydantic v2 model_dump() instead of deprecated dict().
        """
        return self.model_dump()
    
    def to_json(self) -> str:
        """
        Standard JSON serialization for all Agent9 models.
        Uses Pydantic v2 model_dump_json() instead of deprecated json().
        """
        return self.model_dump_json()


class A9AgentBaseRequest(A9AgentBaseModel):
    """
    Base request model for all Agent9 agent requests.
    Enforces protocol compliance for requests.
    """
    request_id: str = Field(..., description="Unique identifier for this request")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), 
                          description="ISO format timestamp when request was created")
    principal_id: str = Field(..., description="ID of the principal making the request")
    
    # Optional context fields with default None
    principal_context: Optional[Any] = Field(default=None, description="Context about the principal")
    situation_context: Optional[Any] = Field(default=None, description="Context about the current situation")
    business_context: Optional[Any] = Field(default=None, description="Business context for the request")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data")


class A9AgentBaseResponse(A9AgentBaseModel):
    """
    Base response model for all Agent9 agent responses.
    Enforces protocol compliance for responses.
    """
    status: str = Field(..., description="Status of the response: success, error, or pending")
    request_id: str = Field(..., description="ID of the originating request")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), 
                          description="ISO format timestamp when response was created")
    error_message: Optional[str] = Field(default=None, description="Error message if status is error")
    
    # Helper methods for standard response creation
    @classmethod
    def success(cls, request_id: str, **kwargs) -> 'A9AgentBaseResponse':
        """Create a standard success response"""
        return cls(
            status="success",
            request_id=request_id,
            **kwargs
        )
    
    @classmethod
    def error(cls, request_id: str, error_message: str, **kwargs) -> 'A9AgentBaseResponse':
        """Create a standard error response"""
        return cls(
            status="error",
            request_id=request_id,
            error_message=error_message,
            **kwargs
        )
    
    @classmethod
    def pending(cls, request_id: str, **kwargs) -> 'A9AgentBaseResponse':
        """Create a standard pending response"""
        return cls(
            status="pending",
            request_id=request_id,
            **kwargs
        )
