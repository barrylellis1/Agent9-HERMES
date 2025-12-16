"""
Consulting Persona Provider

Provides access to consulting firm personas from the registry YAML.
Used in Hybrid Council mode for CaaS market enablement.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class PersonaMethodology(BaseModel):
    """Methodology details for a consulting persona."""
    frameworks: List[str] = Field(default_factory=list)
    approach: str = ""
    analysis_style: str = ""


class PersonaPerspective(BaseModel):
    """Perspective characteristics of a consulting persona."""
    strengths: List[str] = Field(default_factory=list)
    biases: List[str] = Field(default_factory=list)
    typical_recommendations: List[str] = Field(default_factory=list)


class PersonaOutputStyle(BaseModel):
    """Output style preferences for a consulting persona."""
    tone: str = ""
    structure: str = ""
    detail_level: str = ""


class ConsultingPersona(BaseModel):
    """A consulting firm persona for the Hybrid Council."""
    id: str
    name: str
    short_name: str = ""
    specialty: str = ""
    methodology: PersonaMethodology = Field(default_factory=PersonaMethodology)
    perspective: PersonaPerspective = Field(default_factory=PersonaPerspective)
    output_style: PersonaOutputStyle = Field(default_factory=PersonaOutputStyle)
    tags: List[str] = Field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Generate prompt context for this persona."""
        lines = [
            f"## Consulting Advisor: {self.name}",
            f"**Specialty:** {self.specialty}",
            "",
            "### Methodology",
            f"- **Approach:** {self.methodology.approach}",
            f"- **Analysis Style:** {self.methodology.analysis_style}",
            f"- **Key Frameworks:** {', '.join(self.methodology.frameworks)}",
            "",
            "### Perspective",
            "**Strengths:**",
        ]
        for s in self.perspective.strengths:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("**Known Biases (to be aware of):**")
        for b in self.perspective.biases:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("### Output Style")
        lines.append(f"- **Tone:** {self.output_style.tone}")
        lines.append(f"- **Structure:** {self.output_style.structure}")
        lines.append(f"- **Detail Level:** {self.output_style.detail_level}")
        return "\n".join(lines)


class CouncilPreset(BaseModel):
    """A preset council configuration."""
    id: str
    name: str
    description: str = ""
    personas: List[str] = Field(default_factory=list)
    use_case: str = ""


class PrincipalAffinity(BaseModel):
    """Principal role to persona affinity mapping."""
    preferred: List[str] = Field(default_factory=list)
    rationale: str = ""
    default_council: str = ""


class DebateConfig(BaseModel):
    """Configuration for Hybrid Council debate mode."""
    anonymize_in_review: bool = True
    review_criteria: List[str] = Field(default_factory=list)
    synthesis_approach: str = "tension_surfacing"
    max_personas_per_council: int = 5
    min_personas_per_council: int = 2


class ConsultingPersonaProvider:
    """
    Provider for consulting personas from the registry.
    
    Usage:
        provider = ConsultingPersonaProvider()
        persona = provider.get_persona("mckinsey")
        council = provider.get_preset("mbb_council")
        personas_for_cfo = provider.get_personas_for_principal("CFO")
    """

    _instance: Optional[ConsultingPersonaProvider] = None
    _registry_data: Optional[Dict[str, Any]] = None

    def __new__(cls) -> ConsultingPersonaProvider:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if ConsultingPersonaProvider._registry_data is None:
            self._load_registry()

    def _load_registry(self) -> None:
        """Load the consulting personas registry YAML."""
        registry_path = Path(__file__).parent / "consulting_personas_registry.yaml"
        if not registry_path.exists():
            raise FileNotFoundError(f"Consulting personas registry not found: {registry_path}")
        
        with open(registry_path, "r", encoding="utf-8") as f:
            ConsultingPersonaProvider._registry_data = yaml.safe_load(f)

    def reload(self) -> None:
        """Force reload of the registry (useful for testing)."""
        ConsultingPersonaProvider._registry_data = None
        self._load_registry()

    @property
    def _data(self) -> Dict[str, Any]:
        if ConsultingPersonaProvider._registry_data is None:
            self._load_registry()
        return ConsultingPersonaProvider._registry_data or {}

    def get_persona(self, persona_id: str) -> Optional[ConsultingPersona]:
        """Get a consulting persona by ID."""
        personas = self._data.get("consulting_personas", [])
        for p in personas:
            if p.get("id") == persona_id:
                return ConsultingPersona(
                    id=p.get("id", ""),
                    name=p.get("name", ""),
                    short_name=p.get("short_name", ""),
                    specialty=p.get("specialty", ""),
                    methodology=PersonaMethodology(**p.get("methodology", {})),
                    perspective=PersonaPerspective(**p.get("perspective", {})),
                    output_style=PersonaOutputStyle(**p.get("output_style", {})),
                    tags=p.get("tags", []),
                )
        return None

    def get_preset(self, preset_id: str) -> Optional[CouncilPreset]:
        """Get a council preset by ID."""
        presets = self._data.get("council_presets", [])
        for p in presets:
            if p.get("id") == preset_id:
                return CouncilPreset(**p)
        return None

    def get_personas_for_principal(self, role: str) -> List[ConsultingPersona]:
        """Get recommended personas for a principal role."""
        affinity = self._data.get("principal_affinity", {}).get(role, {})
        preferred_ids = affinity.get("preferred", [])
        personas = []
        for pid in preferred_ids:
            persona = self.get_persona(pid)
            if persona:
                personas.append(persona)
        return personas

    def get_default_council_for_principal(self, role: str) -> Optional[CouncilPreset]:
        """Get the default council preset for a principal role."""
        affinity = self._data.get("principal_affinity", {}).get(role, {})
        default_council_id = affinity.get("default_council")
        if default_council_id:
            return self.get_preset(default_council_id)
        return None

    def get_principal_affinity(self, role: str) -> Optional[PrincipalAffinity]:
        """Get the full affinity configuration for a principal role."""
        affinity_data = self._data.get("principal_affinity", {}).get(role)
        if affinity_data:
            return PrincipalAffinity(**affinity_data)
        return None

    def get_debate_config(self) -> DebateConfig:
        """Get the debate configuration."""
        config_data = self._data.get("debate_config", {})
        return DebateConfig(**config_data)

    def list_all_personas(self) -> List[ConsultingPersona]:
        """List all available consulting personas."""
        personas = []
        for p in self._data.get("consulting_personas", []):
            personas.append(ConsultingPersona(
                id=p.get("id", ""),
                name=p.get("name", ""),
                short_name=p.get("short_name", ""),
                specialty=p.get("specialty", ""),
                methodology=PersonaMethodology(**p.get("methodology", {})),
                perspective=PersonaPerspective(**p.get("perspective", {})),
                output_style=PersonaOutputStyle(**p.get("output_style", {})),
                tags=p.get("tags", []),
            ))
        return personas

    def list_all_presets(self) -> List[CouncilPreset]:
        """List all available council presets."""
        return [CouncilPreset(**p) for p in self._data.get("council_presets", [])]

    def list_principal_roles(self) -> List[str]:
        """List all principal roles with affinity mappings."""
        return list(self._data.get("principal_affinity", {}).keys())

    def get_personas_by_tag(self, tag: str) -> List[ConsultingPersona]:
        """Get all personas with a specific tag."""
        personas = []
        for p in self._data.get("consulting_personas", []):
            if tag in p.get("tags", []):
                personas.append(self.get_persona(p.get("id", "")))
        return [p for p in personas if p is not None]

    def build_council(self, persona_ids: List[str]) -> List[ConsultingPersona]:
        """Build a custom council from a list of persona IDs."""
        config = self.get_debate_config()
        if len(persona_ids) < config.min_personas_per_council:
            raise ValueError(
                f"Council requires at least {config.min_personas_per_council} personas"
            )
        if len(persona_ids) > config.max_personas_per_council:
            raise ValueError(
                f"Council cannot exceed {config.max_personas_per_council} personas"
            )
        
        personas = []
        for pid in persona_ids:
            persona = self.get_persona(pid)
            if persona:
                personas.append(persona)
            else:
                raise ValueError(f"Unknown persona ID: {pid}")
        return personas


# Module-level convenience functions
_provider: Optional[ConsultingPersonaProvider] = None


def _get_provider() -> ConsultingPersonaProvider:
    global _provider
    if _provider is None:
        _provider = ConsultingPersonaProvider()
    return _provider


def get_consulting_persona(persona_id: str) -> Optional[ConsultingPersona]:
    """Get a consulting persona by ID."""
    return _get_provider().get_persona(persona_id)


def get_council_preset(preset_id: str) -> Optional[CouncilPreset]:
    """Get a council preset by ID."""
    return _get_provider().get_preset(preset_id)


def get_personas_for_principal(role: str) -> List[ConsultingPersona]:
    """Get recommended personas for a principal role."""
    return _get_provider().get_personas_for_principal(role)


def list_all_personas() -> List[ConsultingPersona]:
    """List all available consulting personas."""
    return _get_provider().list_all_personas()


def list_all_presets() -> List[CouncilPreset]:
    """List all available council presets."""
    return _get_provider().list_all_presets()
