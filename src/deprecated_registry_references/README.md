# Deprecated Registry References

This directory contains legacy registry reference implementations that have been deprecated in favor of the new registry-driven architecture located in `src/registry/`.

## Why were these deprecated?

1. The old registry references used a mix of technologies (Python enums, CSV files, YAML) without a consistent pattern
2. They lacked proper validation between related components (principals, business processes, KPIs)
3. The new registry architecture provides:
   - Consistent data models with Pydantic validation
   - Proper relationship validation across the registry chain
   - Better integration with Agent9's MVP workflows
   - Cleaner separation of concerns

## Migration Guide

If you were using any of these deprecated registry references:

1. Use the new registry factory from `src/registry/factory.py` instead
2. Reference the new models from `src/registry/models/`
3. Use the new providers from `src/registry/providers/`

## Deprecated Items

The following items are deprecated:

- `agent_registry/`
- `business_process_registry/`
- `data_product_registry/`
- `kpi_registry/`
- `principal_registry/`

**DO NOT use these items in new code.**
