"""
Consulting Personas Registry Module

Provides external consulting firm personas for CaaS market enablement.
Used in Hybrid Council mode with Principal Context voicing.
"""

from .consulting_persona_provider import (
    ConsultingPersonaProvider,
    ConsultingPersona,
    CouncilPreset,
    get_consulting_persona,
    get_council_preset,
    get_personas_for_principal,
    list_all_personas,
    list_all_presets,
)

__all__ = [
    "ConsultingPersonaProvider",
    "ConsultingPersona",
    "CouncilPreset",
    "get_consulting_persona",
    "get_council_preset",
    "get_personas_for_principal",
    "list_all_personas",
    "list_all_presets",
]
