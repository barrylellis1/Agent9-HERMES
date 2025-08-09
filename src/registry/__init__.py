"""
Agent9 Registry System

A unified registry access system for Agent9, providing a consistent interface
for accessing business processes, KPIs, roles, and other configuration data
regardless of storage format (YAML, JSON, CSV, Python objects, etc.).
"""

from src.registry.providers.registry_provider import RegistryProvider
from src.registry.factory import RegistryFactory

__all__ = ["RegistryProvider", "RegistryFactory"]
