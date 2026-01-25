"""
API routes for managing connection profiles.

Connection profiles store reusable connection configurations for data sources
like BigQuery, allowing users to save credentials and connection details
for reuse across different datasets and data products.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yaml
import os
from datetime import datetime

router = APIRouter(prefix="/api/v1/connection-profiles", tags=["connection-profiles"])

PROFILES_PATH = "src/registry/connection_profiles.yaml"


class ConnectionProfile(BaseModel):
    """Connection profile model."""
    id: str
    name: str
    source_system: str
    config: Dict[str, Any]
    created_at: str
    updated_at: str


class CreateConnectionProfileRequest(BaseModel):
    """Request to create a new connection profile."""
    name: str
    source_system: str
    config: Dict[str, Any]


class UpdateConnectionProfileRequest(BaseModel):
    """Request to update an existing connection profile."""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


def _load_profiles() -> List[Dict[str, Any]]:
    """Load connection profiles from YAML file."""
    if not os.path.exists(PROFILES_PATH):
        return []
    
    with open(PROFILES_PATH, 'r') as f:
        data = yaml.safe_load(f) or {}
    
    return data.get('profiles', [])


def _save_profiles(profiles: List[Dict[str, Any]]) -> None:
    """Save connection profiles to YAML file."""
    os.makedirs(os.path.dirname(PROFILES_PATH), exist_ok=True)
    
    with open(PROFILES_PATH, 'w') as f:
        yaml.dump({'profiles': profiles}, f, default_flow_style=False)


@router.get("/", response_model=List[ConnectionProfile])
async def list_connection_profiles(source_system: Optional[str] = None):
    """List all connection profiles, optionally filtered by source system."""
    profiles = _load_profiles()
    
    if source_system:
        profiles = [p for p in profiles if p.get('source_system') == source_system]
    
    return profiles


@router.get("/{profile_id}", response_model=ConnectionProfile)
async def get_connection_profile(profile_id: str):
    """Get a specific connection profile by ID."""
    profiles = _load_profiles()
    
    for profile in profiles:
        if profile.get('id') == profile_id:
            return profile
    
    raise HTTPException(status_code=404, detail=f"Connection profile '{profile_id}' not found")


@router.post("/", response_model=ConnectionProfile)
async def create_connection_profile(request: CreateConnectionProfileRequest):
    """Create a new connection profile."""
    profiles = _load_profiles()
    
    # Generate ID from name
    profile_id = request.name.lower().replace(' ', '_').replace('-', '_')
    
    # Check if profile with this ID already exists
    if any(p.get('id') == profile_id for p in profiles):
        raise HTTPException(status_code=400, detail=f"Connection profile with ID '{profile_id}' already exists")
    
    # Create new profile
    now = datetime.utcnow().isoformat()
    new_profile = {
        'id': profile_id,
        'name': request.name,
        'source_system': request.source_system,
        'config': request.config,
        'created_at': now,
        'updated_at': now,
    }
    
    profiles.append(new_profile)
    _save_profiles(profiles)
    
    return new_profile


@router.put("/{profile_id}", response_model=ConnectionProfile)
async def update_connection_profile(profile_id: str, request: UpdateConnectionProfileRequest):
    """Update an existing connection profile."""
    profiles = _load_profiles()
    
    for i, profile in enumerate(profiles):
        if profile.get('id') == profile_id:
            # Update fields
            if request.name is not None:
                profile['name'] = request.name
            if request.config is not None:
                profile['config'] = request.config
            
            profile['updated_at'] = datetime.utcnow().isoformat()
            
            profiles[i] = profile
            _save_profiles(profiles)
            
            return profile
    
    raise HTTPException(status_code=404, detail=f"Connection profile '{profile_id}' not found")


@router.delete("/{profile_id}")
async def delete_connection_profile(profile_id: str):
    """Delete a connection profile."""
    profiles = _load_profiles()
    
    for i, profile in enumerate(profiles):
        if profile.get('id') == profile_id:
            profiles.pop(i)
            _save_profiles(profiles)
            return {"message": f"Connection profile '{profile_id}' deleted successfully"}
    
    raise HTTPException(status_code=404, detail=f"Connection profile '{profile_id}' not found")
