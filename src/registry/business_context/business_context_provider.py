"""
Business Context Provider for Agent9.

Supports both YAML and Supabase backends for business context metadata.
"""
from __future__ import annotations

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    import httpx
except ImportError:
    httpx = None

from src.agents.shared.a9_debate_protocol_models import A9_PS_BusinessContext

logger = logging.getLogger(__name__)


class SupabaseBusinessContextProvider:
    """Provider for business contexts stored in Supabase."""
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_service_key: Optional[str] = None,
        table_name: str = "business_contexts",
        schema: str = "public"
    ):
        """Initialize Supabase business context provider.
        
        Args:
            supabase_url: Supabase project URL (defaults to env var SUPABASE_URL)
            supabase_service_key: Service role key (defaults to env var SUPABASE_SERVICE_ROLE_KEY)
            table_name: Table name (defaults to business_contexts)
            schema: Database schema (defaults to public)
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_service_key = supabase_service_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.table_name = table_name
        self.schema = schema
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError(
                "Supabase URL and service key required. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
            )
        
        if httpx is None:
            raise ImportError("httpx is required for Supabase provider. Install with: pip install httpx")
        
        self.endpoint = f"{self.supabase_url}/rest/v1/{self.table_name}"
        self.headers = {
            "apikey": self.supabase_service_key,
            "Authorization": f"Bearer {self.supabase_service_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Profile": self.schema,
        }
        
        logger.info(f"Initialized SupabaseBusinessContextProvider (table={table_name})")
    
    async def get_context(self, context_id: str) -> Optional[A9_PS_BusinessContext]:
        """Fetch a business context by ID.
        
        Args:
            context_id: Unique context identifier (e.g., demo_bicycle, demo_lubricants)
            
        Returns:
            A9_PS_BusinessContext instance or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{context_id}", "select": "*"}
                )
                response.raise_for_status()
                
                rows = response.json()  # pydantic-lint: allow - HTTP response object, not Pydantic model
                if not rows:
                    logger.warning(f"Business context not found: {context_id}")
                    return None
                
                row = rows[0]
                return self._row_to_model(row)
                
        except Exception as e:
            logger.error(f"Failed to fetch business context {context_id}: {e}")
            return None
    
    async def list_contexts(self, is_demo: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List all business contexts.
        
        Args:
            is_demo: Filter by demo flag (None = all contexts)
            
        Returns:
            List of context metadata dicts
        """
        try:
            params = {"select": "*"}
            if is_demo is not None:
                params["is_demo"] = f"eq.{is_demo}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.endpoint,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                return response.json()  # pydantic-lint: allow - HTTP response object, not Pydantic model
                
        except Exception as e:
            logger.error(f"Failed to list business contexts: {e}")
            return []
    
    def _row_to_model(self, row: Dict[str, Any]) -> A9_PS_BusinessContext:
        """Convert Supabase row to A9_PS_BusinessContext model.
        
        Args:
            row: Raw row from Supabase
            
        Returns:
            A9_PS_BusinessContext instance
        """
        # Extract fields that match the model
        model_data = {
            "name": row.get("name"),
            "industry": row.get("industry"),
            "sub_sector": row.get("sub_sector"),
            "description": row.get("description"),
            "revenue": row.get("revenue"),
            "employees": row.get("employees"),
            "ownership": row.get("ownership"),
            "business_model": row.get("business_model", {}),
            "strategic_priorities": row.get("strategic_priorities", []),
            "competitors": row.get("competitors", []),
            "operational_context": row.get("operational_context", {}),
            "consulting_spend": row.get("consulting_spend"),
            "consulting_firms_used": row.get("consulting_firms_used", {}),
            "pain_points": row.get("pain_points", []),
        }
        
        # Remove None values
        model_data = {k: v for k, v in model_data.items() if v is not None}
        
        return A9_PS_BusinessContext(**model_data)


def create_supabase_business_context_provider() -> SupabaseBusinessContextProvider:
    """Factory function to create Supabase business context provider.
    
    Returns:
        SupabaseBusinessContextProvider instance
        
    Raises:
        ValueError: If required environment variables not set
    """
    return SupabaseBusinessContextProvider()


async def get_business_context(context_id: str) -> Optional[A9_PS_BusinessContext]:
    """Convenience function to get a business context.
    
    Checks BUSINESS_CONTEXT_BACKEND env var to determine provider.
    Falls back to YAML if Supabase fails.
    
    Args:
        context_id: Context identifier
        
    Returns:
        A9_PS_BusinessContext or None
    """
    backend = os.getenv("BUSINESS_CONTEXT_BACKEND", "yaml").lower()
    
    if backend == "supabase":
        try:
            provider = create_supabase_business_context_provider()
            context = await provider.get_context(context_id)
            if context:
                logger.info(f"Loaded business context '{context_id}' from Supabase")
                return context
            else:
                logger.warning(f"Context '{context_id}' not found in Supabase, trying YAML fallback")
        except Exception as e:
            logger.error(f"Supabase provider failed: {e}, falling back to YAML")
    
    # Fallback to YAML
    from src.agents.shared.business_context_loader import try_load_business_context
    
    # Map context_id to YAML file path
    yaml_paths = {
        "demo_bicycle": "src/registry_references/business_context/bicycle_retail_context.yaml",
        "demo_lubricants": "src/registry_references/business_context/lubricants_context.yaml",
    }
    
    yaml_path = yaml_paths.get(context_id)
    if yaml_path:
        context = try_load_business_context(yaml_path)
        if context:
            logger.info(f"Loaded business context '{context_id}' from YAML")
            return context
    
    logger.error(f"Failed to load business context '{context_id}' from any source")
    return None
