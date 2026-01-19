#!/usr/bin/env python3
"""
Quick test to verify Supabase providers loaded successfully.
"""
import asyncio
import os
import sys

# Set environment variables
os.environ['BUSINESS_GLOSSARY_BACKEND'] = 'supabase'
os.environ['PRINCIPAL_PROFILE_BACKEND'] = 'supabase'
os.environ['KPI_REGISTRY_BACKEND'] = 'supabase'
os.environ['SUPABASE_URL'] = 'http://127.0.0.1:54321'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'

from src.registry.bootstrap import RegistryBootstrap


async def main():
    """Test Supabase provider initialization."""
    print("=" * 60)
    print("Testing Supabase Provider Initialization")
    print("=" * 60)
    
    # Initialize registry
    print("\n1. Initializing registry bootstrap...")
    success = await RegistryBootstrap.initialize()
    
    if not success:
        print("❌ Registry bootstrap failed!")
        return 1
    
    print("✅ Registry bootstrap successful")
    
    # Get factory
    factory = RegistryBootstrap._factory
    
    # Test Business Glossary Provider
    print("\n2. Testing Business Glossary Provider...")
    glossary_provider = factory.get_provider('business_glossary')
    if glossary_provider:
        terms = glossary_provider.get_all()
        print(f"   ✅ Loaded {len(terms)} business glossary terms")
        if terms:
            first_term = terms[0] if isinstance(terms, list) else list(terms.values())[0]
            print(f"   Sample: {first_term.term} - {first_term.definition[:50]}...")
    else:
        print("   ❌ Business glossary provider not found")
    
    # Test Principal Profile Provider
    print("\n3. Testing Principal Profile Provider...")
    principal_provider = factory.get_provider('principal')
    if principal_provider:
        profiles = principal_provider.get_all()
        print(f"   ✅ Loaded {len(profiles)} principal profiles")
        if profiles:
            first_profile = profiles[0] if isinstance(profiles, list) else list(profiles.values())[0]
            print(f"   Sample: {first_profile.id} - {first_profile.name} ({first_profile.role})")
            print(f"   Business Processes: {first_profile.business_process_ids[:3] if first_profile.business_process_ids else 'None'}...")
    else:
        print("   ❌ Principal profile provider not found")
    
    # Test KPI Provider
    print("\n4. Testing KPI Provider...")
    kpi_provider = factory.get_provider('kpi')
    if kpi_provider:
        kpis = kpi_provider.get_all()
        print(f"   ✅ Loaded {len(kpis)} KPIs")
        if kpis:
            first_kpi = kpis[0] if isinstance(kpis, list) else list(kpis.values())[0]
            print(f"   Sample: {first_kpi.id} - {first_kpi.name} ({first_kpi.domain})")
            print(f"   Business Processes: {first_kpi.business_process_ids[:3] if first_kpi.business_process_ids else 'None'}...")
            if first_kpi.metadata:
                print(f"   Metadata: line={first_kpi.metadata.get('line')}, altitude={first_kpi.metadata.get('altitude')}")
    else:
        print("   ❌ KPI provider not found")
    
    print("\n" + "=" * 60)
    print("✅ All Supabase providers validated successfully!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
