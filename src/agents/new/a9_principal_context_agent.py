"""
# doc-sync-skip
Principal Context Agent

This agent manages principal context and relationships in business operations.
It handles registration, retrieval, and management of principal profiles as well
as mapping principals to business processes and KPIs.
"""
# doc-sync-skip

import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional

from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.agents.models.data_product_onboarding_models import (
    PrincipalOwnershipRequest,
    PrincipalOwnershipResponse,
    OwnershipChainEntry,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registry-data extraction helpers (fix for hardcoded PrincipalContext fields).
#
# get_principal_context()/get_principal_context_by_id() previously hardcoded
# preferred_timeframes to the same two enum values for every principal, and
# read decision_style/communication_style from key paths that don't exist on
# the current PrincipalProfile registry model (persona_profile.*, flat
# communication_style) — so both silently fell through to defaults
# ("Analytical"/"Concise") for effectively every principal, regardless of
# their real profile. Seed data (scripts/clients/*.py) uses two inconsistent
# shapes for decision_style/communication_style — flat top-level keys AND
# nested persona_profile.{decision_style,communication_style} — so both are
# checked. time_frame is not seeded anywhere yet, but the registry model
# default (PrincipalProfile.time_frame) is still read rather than overridden
# by a Python literal, so real per-client values work the moment they exist.
# ---------------------------------------------------------------------------

def _extract_decision_style(profile_data: Dict[str, Any]) -> str:
    """KNOWN GAP: PrincipalProfile (src/registry/models/principal.py) has no
    decision_style field at all. PrincipalProfileProvider.get()/.get_all()
    return validated PrincipalProfile instances, and Pydantic silently drops
    unknown keys on load (no extra="allow") — so the flat/persona_profile
    checks below will NEVER fire for data reached through the provider path,
    regardless of what scripts/clients/*.py seeds. metadata (Dict[str,str])
    is the one declared field that survives model_dump(), so it's checked as
    the best-available real extension point. Until decision_style is either
    a first-class registry field or consistently seeded into metadata, this
    resolves to the "Analytical" default for effectively every principal —
    a registry-schema gap, not something a runtime fix alone can close."""
    if not isinstance(profile_data, dict):
        return "Analytical"
    flat = profile_data.get('decision_style')
    if flat:
        return flat
    persona_profile = profile_data.get('persona_profile')
    if isinstance(persona_profile, dict) and persona_profile.get('decision_style'):
        return persona_profile['decision_style']
    metadata = profile_data.get('metadata')
    if isinstance(metadata, dict) and metadata.get('decision_style'):
        return metadata['decision_style']
    return "Analytical"


def _extract_communication_style(profile_data: Dict[str, Any]) -> str:
    if not isinstance(profile_data, dict):
        return "Concise"
    flat = profile_data.get('communication_style')
    if flat:
        return flat
    persona_profile = profile_data.get('persona_profile')
    if isinstance(persona_profile, dict) and persona_profile.get('communication_style'):
        return persona_profile['communication_style']
    # Formal PrincipalProfile field: communication.detail_level (nested)
    comm = profile_data.get('communication')
    if isinstance(comm, dict) and comm.get('detail_level'):
        return comm['detail_level']
    return "Concise"


_PERIOD_TO_TIMEFRAME_ENUM = {
    "ytd": "year_to_date",
    "qtd": "quarter_to_date",
    "mtd": "month_to_date",
}


def _extract_preferred_timeframes(profile_data: Dict[str, Any]) -> list:
    """Returns a list of situation_awareness_models.TimeFrame enum members,
    derived from the registry's PrincipalProfile.time_frame.default_period."""
    from src.agents.models.situation_awareness_models import TimeFrame as _TF
    if isinstance(profile_data, dict):
        tf = profile_data.get('time_frame')
        if isinstance(tf, dict):
            period = str(tf.get('default_period', '')).lower()
            mapped_value = _PERIOD_TO_TIMEFRAME_ENUM.get(period)
            if mapped_value:
                return [_TF(mapped_value)]
    return [_TF.CURRENT_QUARTER, _TF.YEAR_TO_DATE]


class A9_Principal_Context_Agent:
    """
    Principal Context Agent responsible for managing principal profiles and context.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Principal Context Agent.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.principal_profiles = {}
        self._setup_logging()
        # Use a single canonical attribute name for registry factory
        self.registry_factory = None
        self._principal_provider = None
        
    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> 'A9_Principal_Context_Agent':
        """
        Create a new instance of the Principal Context Agent.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            Initialized Principal Context Agent instance.
        """
        agent = cls(config)
        await agent.connect()
        return agent

    def _setup_logging(self):
        """Set up logging for the agent."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    async def connect(self, orchestrator=None):
        """
        Connect to dependencies and initialize required resources.
        
        Args:
            orchestrator: Optional orchestrator agent for service discovery
        """
        try:
            # Store orchestrator reference for service discovery
            if orchestrator:
                self.orchestrator = orchestrator
                self.logger.info("Orchestrator reference stored for service discovery")
            
            # Initialize registry factory and providers
            self.registry_factory = RegistryFactory()
            self._principal_provider = None
            self._business_process_provider = None

            # Ensure the registry is actually bootstrapped before asking it for
            # anything. RegistryBootstrap.initialize() is idempotent and
            # self-healing — it re-verifies principal_profile/business_glossary/
            # data_product/kpi and only re-runs what's missing — so this is a
            # cheap no-op on the normal path (app startup already ran it) and a
            # correct, on-demand bootstrap on the abnormal one (this agent
            # connecting before that startup sequence finished).
            #
            # Previously, when get_principal_profile_provider() returned None,
            # this method manufactured its own PrincipalProfileProvider() (a
            # flat, in-memory, bare-ID-keyed class with none of
            # DatabaseRegistryProvider's client_id-aware filtering) and
            # REGISTERED it into the shared factory — which could pre-empt
            # RegistryBootstrap's own registration for the rest of the process,
            # since RegistryBootstrap only registers a provider "if existing is
            # None". That startup race was confirmed live, Aug 2026: this agent
            # ended up permanently holding the non-tenant-aware fallback while
            # other routes (which re-resolve the factory per request) correctly
            # got the real one — see identify_data_product_owner's card entry
            # for the cross-tenant leak that produced.
            try:
                from src.registry.bootstrap import RegistryBootstrap
                await RegistryBootstrap.initialize()
            except Exception as e:
                self.logger.warning(f"RegistryBootstrap.initialize() failed: {e}")

            # Try to get the principal profile provider from the (now-bootstrapped) factory
            try:
                self._principal_provider = self.registry_factory.get_principal_profile_provider()
                if not self._principal_provider:
                    # RegistryBootstrap ran and STILL found nothing — a real failure
                    # (e.g. DB unreachable), not a race. Fall back for local
                    # degraded operation only; deliberately NOT registered into
                    # the shared factory, so it can never be handed to any other
                    # consumer as if it were the real, tenant-aware provider.
                    self.logger.error(
                        "No principal_profile provider after RegistryBootstrap.initialize() — "
                        "using a local, unregistered, non-tenant-aware fallback. Ownership "
                        "resolution and role-based lookup will be degraded until this resolves."
                    )
                    self._principal_provider = PrincipalProfileProvider()
                    await self._principal_provider.load()
                else:
                    # If provider exists but not marked initialized, load now
                    init = getattr(self.registry_factory, "_provider_initialization_status", {})
                    if not init.get("principal_profile", False):
                        self.logger.info("Principal profile provider exists but not initialized; loading now")
                        await self._principal_provider.load()
                        if hasattr(self.registry_factory, "_provider_initialization_status"):
                            self.registry_factory._provider_initialization_status["principal_profile"] = True
                # Log how many profiles are available
                try:
                    loaded = self._principal_provider.get_all() or []
                    self.logger.info(f"Principal profile provider ready with {len(loaded)} profiles")
                except Exception:
                    pass
                self.logger.info("Successfully retrieved principal profile provider from registry factory")
            except Exception as e:
                self.logger.warning(f"Failed to get principal profile provider: {str(e)}")
                self.logger.info("Initializing local, unregistered fallback principal profile provider")
                self._principal_provider = PrincipalProfileProvider()
                # Load default profiles
                await self._principal_provider.load()
                
            # Get the business process provider from the registry factory
            # The factory will create a default provider if none exists
            try:
                self._business_process_provider = self.registry_factory.get_business_process_provider()
                if self._business_process_provider:
                    # Ensure the provider is loaded
                    if not self.registry_factory._provider_initialization_status.get("business_process", False):
                        self.logger.info("Loading business process provider data")
                        await self._business_process_provider.load()
                        self.registry_factory._provider_initialization_status["business_process"] = True
                    self.logger.info("Successfully retrieved business process provider from registry factory")
                else:
                    self.logger.error("Failed to get or create business process provider from registry factory")
            except Exception as e:
                self.logger.error(f"Error initializing business process provider: {str(e)}")
                # No fallback needed as the factory already handles creation
            
            # Load all principal profiles
            await self._load_principal_profiles()
            
            self.logger.info("Connected to dependencies")
        except Exception as e:
            self.logger.error(f"Error connecting to dependencies: {str(e)}")
    
    async def disconnect(self):
        """
        Disconnect from dependencies and clean up resources.
        """
        self.logger.info("Disconnected from dependencies")
    
    async def _load_principal_profiles(self):
        """
        Load principal profiles from the registry.
        """
        try:
            # Check if provider exists
            if not self._principal_provider:
                self.logger.error("Cannot load principal profiles: principal provider is None")
                # Initialize default profiles
                self.principal_profiles = self._get_default_profiles()
                return
                
            # Get all principal profiles
            profiles = self._principal_provider.get_all() or {}
            if not profiles:
                self.logger.error("No principal profiles found in Supabase registry — verify seed data")
                self.principal_profiles = self._get_default_profiles()
                return
            
            # Ensure profiles is in the correct format
            if isinstance(profiles, list):
                self.logger.info(f"Loaded {len(profiles)} principal profiles (list format) from registry")
                self.principal_profiles = profiles
                try:
                    sample = profiles[0] if profiles else None
                    self.logger.debug(f"Sample profile (list): {getattr(sample, 'id', getattr(sample, 'name', str(sample)))})")
                except Exception:
                    pass
            elif isinstance(profiles, dict):
                self.logger.info(f"Loaded {len(profiles)} principal profiles (dict format) from registry")
                self.principal_profiles = profiles
                try:
                    self.logger.debug(f"Profile keys: {list(profiles.keys())[:10]}")
                except Exception:
                    pass
            else:
                self.logger.warning(f"Unexpected principal profiles format: {type(profiles)}")
                self.principal_profiles = {}
        except Exception as e:
            self.logger.error(f"Error loading principal profiles: {str(e)}")
            # Initialize default profiles
            self.principal_profiles = self._get_default_profiles()
            
    def _get_default_profiles(self):
        """
        Get default principal profiles when registry loading fails.
        
        Returns:
            Dict of default principal profiles
        """
        self.logger.info("Using default principal profiles")
        return {
            "CFO": {
                "id": "cfo_001",
                "name": "Chief Financial Officer",
                "role": "CFO",
                "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"],
                "default_filters": {},
                "persona_profile": {
                    "decision_style": "Analytical"
                },
                "communication_style": "Concise"
            },
            "Finance Manager": {
                "id": "finance_mgr_001",
                "name": "Finance Manager",
                "role": "Finance Manager",
                "business_processes": ["Finance: Budget Planning", "Finance: Cost Management"],
                "default_filters": {},
                "persona_profile": {
                    "decision_style": "Methodical"
                },
                "communication_style": "Detailed"
            }
        }
    
    async def set_principal_context(self, principal_id: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Set principal context.
        
        Args:
            principal_id: Identifier of the principal.
            context_data: Additional context data.
            
        Returns:
            Principal context information.
        """
        try:
            # Get principal profile
            profile = await self.fetch_principal_profile(principal_id)
            if not profile:
                self.logger.warning(f"Principal profile not found: {principal_id}")
                return {}
                
            # Merge with context data
            if context_data:
                # Update profile with context data
                # This would be expanded in a full implementation
                pass
                
            return profile
        except Exception as e:
            self.logger.error(f"Error setting principal context: {str(e)}")
            return {}
    
    async def fetch_principal_profile(self, principal_id: str) -> Dict[str, Any]:
        """
        Fetch principal profile.
        
        Args:
            principal_id: Identifier of the principal.
            
        Returns:
            Principal profile information.
        """
        try:
            if not self._principal_provider:
                self.logger.warning("Principal profile provider not initialized")
                return {}
            
            # Try to get the profile directly from the provider
            profile = self._principal_provider.get(principal_id)
            
            if profile:
                # Convert Pydantic model to dict if needed (prefer Pydantic v2 API)
                if hasattr(profile, 'model_dump'):
                    profile_dict = profile.model_dump()
                elif hasattr(profile, '__dict__'):
                    profile_dict = vars(profile)
                else:
                    profile_dict = {}
                
                return {
                    "principal_id": profile_dict.get("id", principal_id),
                    "name": profile_dict.get("name", principal_id),
                    "business_processes": profile_dict.get("business_processes", []),
                    "default_filters": profile_dict.get("default_filters", {}),
                    "communication_style": profile_dict.get("communication_style", "direct"),
                    "decision_timeframe": profile_dict.get("decision_timeframe", "monthly")
                }
            
            # Fall back to checking self.principal_profiles if provider lookup failed
            if principal_id in self.principal_profiles:
                profile = self.principal_profiles[principal_id]
                return {
                    "principal_id": principal_id,
                    "name": profile.get("name", principal_id),
                    "business_processes": profile.get("business_processes", []),
                    "default_filters": profile.get("default_filters", {}),
                    "communication_style": profile.get("communication_style", "direct"),
                    "decision_timeframe": profile.get("decision_timeframe", "monthly")
                }
            else:
                self.logger.warning(f"Principal profile not found: {principal_id}")
                # Return a default profile instead of empty dict
                return {
                    "principal_id": principal_id,
                    "name": principal_id.replace('_', ' ').title(),
                    "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"],
                    "default_filters": {},
                    "communication_style": "direct",
                    "decision_timeframe": "monthly"
                }
        except Exception as e:
            self.logger.error(f"Error fetching principal profile: {str(e)}")
            return {"principal_id": principal_id, "name": principal_id.replace('_', ' ').title()}

    async def identify_data_product_owner(
        self, request: PrincipalOwnershipRequest
    ) -> PrincipalOwnershipResponse:
        """Resolve the accountable principal for a newly onboarded data product."""

        request_id = request.request_id
        notes: List[str] = []
        ownership_chain: List[OwnershipChainEntry] = []
        owner_principal_id: Optional[str] = None
        owner_profile: Dict[str, Any] = {}
        client_id = request.client_id

        def _record_chain(principal_id: str, role: Optional[str], reason: str) -> None:
            ownership_chain.append(
                OwnershipChainEntry(
                    principal_id=principal_id,
                    role=role,
                    reason=reason,
                )
            )

        # TENANT ISOLATION (CLAUDE.md Rule 7 / 8) — principal IDs like "coo_001" are
        # reused across clients BY DESIGN (uniqueness is the composite (client_id, id)
        # key). Every branch below must strict-match client_id, not just "is not None".
        # Found live, Aug 2026: without this, a Lubricants data product's ownership
        # resolved to a Hess principal via the bare-ID candidate lookup. Fail closed
        # when client_id is missing — skip auto-matching entirely rather than guess
        # across every loaded tenant.
        if not client_id:
            self.logger.warning(
                "identify_data_product_owner called without client_id for data "
                "product '%s' — skipping auto-matching to avoid a cross-tenant "
                "owner assignment; manual assignment required.",
                request.data_product_id,
            )
            notes.append(
                "No client_id provided — auto-matching skipped to avoid a "
                "cross-tenant assignment. Manual assignment required."
            )
            return PrincipalOwnershipResponse.pending(
                request_id=request_id,
                owner_principal_id=None,
                owner_profile={},
                ownership_chain=ownership_chain,
                notes=notes,
            )

        # 1. Direct nominee lookup by principal ID
        if self._principal_provider and request.candidate_owner_ids:
            for candidate_id in request.candidate_owner_ids:
                if not candidate_id:
                    continue
                try:
                    # Prefer a client_id-scoped lookup — DatabaseRegistryProvider
                    # supports it directly and resolves the RIGHT tenant's copy of
                    # a colliding ID deterministically, rather than whichever one
                    # happens to be returned by a bare id-only lookup (confirmed
                    # live: get('cfo_001') with no client_id returned a different
                    # tenant's profile). Falls back to the bare call for any
                    # provider that doesn't accept the kwarg (e.g. the degraded,
                    # unregistered local fallback in connect()) — the strict
                    # client_id check just below still guards that path.
                    try:
                        provider_profile = self._principal_provider.get(candidate_id, client_id=client_id)
                    except TypeError:
                        provider_profile = self._principal_provider.get(candidate_id)
                except Exception as err:
                    self.logger.warning(f"Candidate lookup failed for {candidate_id}: {err}")
                    provider_profile = None
                if provider_profile and getattr(provider_profile, "client_id", None) != client_id:
                    self.logger.warning(
                        "Candidate owner '%s' belongs to client_id '%s', not the "
                        "requesting client_id '%s' — rejected, not a valid nominee "
                        "for this tenant.",
                        candidate_id, getattr(provider_profile, "client_id", None), client_id,
                    )
                    continue
                if provider_profile:
                    owner_profile = self._normalize_profile_data(provider_profile)
                    owner_principal_id = owner_profile.get("id", candidate_id)
                    owner_profile.setdefault("principal_id", owner_principal_id)
                    _record_chain(owner_principal_id, owner_profile.get("role"), "Direct nominee match")
                    notes.append(f"Matched nominated owner '{owner_principal_id}'.")
                    break

        # 2. Fallback to role-based resolution when no direct nominee found
        if not owner_principal_id and request.fallback_roles:
            for role in request.fallback_roles:
                profile = self._get_profile_case_insensitive(role, client_id=client_id)
                if profile:
                    owner_profile = self._normalize_profile_data(profile)
                    owner_principal_id = owner_profile.get("id") or owner_profile.get("principal_id") or role
                    owner_profile.setdefault("principal_id", owner_principal_id)
                    _record_chain(owner_principal_id, owner_profile.get("role", role), "Role-based fallback match")
                    notes.append(f"Selected role-based fallback '{owner_principal_id}'.")
                    break

        # 3. Examine business process context for the best available owner
        if not owner_principal_id and request.business_process_context:
            target_processes = {bp.lower() for bp in request.business_process_context if bp}
            best_candidate: Optional[Dict[str, Any]] = None
            best_match_count = 0
            for profile_data in self._iter_principal_profiles(client_id=client_id):
                business_processes = profile_data.get("business_processes", []) or []
                overlap = target_processes.intersection({bp.lower() for bp in business_processes})
                if overlap and len(overlap) > best_match_count:
                    best_candidate = profile_data
                    best_match_count = len(overlap)
            if best_candidate:
                owner_profile = best_candidate
                owner_principal_id = best_candidate.get("id") or best_candidate.get("principal_id")
                owner_profile.setdefault("principal_id", owner_principal_id)
                _record_chain(
                    owner_principal_id or "unknown",
                    owner_profile.get("role"),
                    "Matched via business process context",
                )
                notes.append(
                    "Matched owner based on business process overlap: "
                    + ", ".join(request.business_process_context)
                )

        # 4. Last-resort fallback to the first available profile for THIS tenant
        if not owner_principal_id:
            fallback_profile = next(self._iter_principal_profiles(client_id=client_id), None)
            if fallback_profile:
                owner_profile = fallback_profile
                owner_principal_id = fallback_profile.get("id") or fallback_profile.get("principal_id")
                owner_profile.setdefault("principal_id", owner_principal_id)
                _record_chain(
                    owner_principal_id or "unknown",
                    owner_profile.get("role"),
                    "Default registry fallback",
                )
                notes.append("Applied default principal registry fallback.")

        if owner_principal_id:
            owner_profile.setdefault("principal_id", owner_principal_id)
            return PrincipalOwnershipResponse.success(
                request_id=request_id,
                owner_principal_id=owner_principal_id,
                owner_profile=owner_profile,
                ownership_chain=ownership_chain,
                notes=notes,
            )

        notes.append("No owner could be resolved automatically; manual assignment required.")
        return PrincipalOwnershipResponse.pending(
            request_id=request_id,
            owner_principal_id=None,
            owner_profile={},
            ownership_chain=ownership_chain,
            notes=notes,
        )
    
    async def get_context_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get context-based recommendations.
        
        Returns:
            List of recommendations.
        """
        # This would be implemented in a full version
        return []
    
    async def get_context_history(self) -> List[Dict[str, Any]]:
        """
        Get context history.
        
        Returns:
            List of context history items.
        """
        # This would be implemented in a full version
        return []
    
    async def clear_context(self) -> None:
        """
        Clear current context.
        """
        # This would be implemented in a full version
        pass
        
    def _normalize_profile_data(self, profile: Any) -> Dict[str, Any]:
        """Normalize a principal profile into a flat, .get()-able dict.

        PrincipalProfileProvider.get()/.get_all() return validated PrincipalProfile
        Pydantic instances, not dicts — .get() is not defined on them. This was the
        root cause of a live AttributeError in identify_data_product_owner (found
        running the real onboarding pipeline end to end, Aug 2026): this method was
        called but never defined, written against an assumed dict-shaped profile
        that predates the current Supabase-backed PrincipalProfile model.

        Accepts a PrincipalProfile, a plain dict (defensive — some callers may
        already have one), or None.
        """
        if profile is None:
            return {}
        if isinstance(profile, dict):
            data = dict(profile)
        elif hasattr(profile, "model_dump"):
            data = profile.model_dump()
        else:
            data = dict(getattr(profile, "__dict__", {}) or {})

        data.setdefault("id", data.get("id") or data.get("principal_id"))
        # PrincipalProfile has no "role" field — "title" (e.g. "Chief Financial
        # Officer") is the closest analogue, and is NOT the same convention as the
        # short role codes ("CFO") used elsewhere in this codebase (KPI.owner_role
        # etc). Aliased here so existing .get("role") call sites get something
        # rather than nothing; does not resolve that naming mismatch — a caller
        # matching fallback_roles=["CFO"] against this will not match "Chief
        # Financial Officer". Known, not silently papered over.
        data.setdefault("role", data.get("title"))
        return data

    def _iter_principal_profiles(self, client_id: Optional[str] = None):
        """Yield every loaded principal profile normalized to a flat dict.

        self.principal_profiles is a List[PrincipalProfile] in the common case
        (see _load_principal_profiles), but has historically also been populated
        as a dict keyed by id/role — handled here too. Also called-but-undefined
        before this fix, same root cause as _normalize_profile_data.

        client_id, when given, STRICT-matches (CLAUDE.md Rule 7) — principal_profiles
        holds every loaded tenant's profiles, not just the caller's, so an unfiltered
        iteration is a cross-tenant leak risk for any caller that doesn't filter
        results itself. Pass None only when the caller genuinely needs every tenant
        (rare — verify that's actually intended, not an oversight).
        """
        profiles = self.principal_profiles
        if isinstance(profiles, dict):
            profiles = profiles.values()
        for profile in (profiles or []):
            normalized = self._normalize_profile_data(profile)
            if client_id and normalized.get("client_id") != client_id:
                continue
            yield normalized

    def _get_profile_case_insensitive(
        self, role_key: str, client_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a profile using case-insensitive matching with multiple format attempts.

        Matches against each profile's id AND role (aliased from title — see
        _normalize_profile_data). Previously matched via `hasattr(profile, 'get')`
        guards that were always False against real PrincipalProfile instances, so
        this silently returned None on every call — no exception, no match, ever.

        client_id, when given, STRICT-matches (CLAUDE.md Rule 7) — principal_profiles
        holds every loaded tenant's profiles, so an unfiltered match risks returning
        a different tenant's principal for the same role name (e.g. "CFO" exists for
        every client). Pass None only when a cross-tenant match is genuinely intended.

        Args:
            role_key: The role key to look up (can be in any case format)
            client_id: Restrict matches to this tenant

        Returns:
            The normalized profile dict if found, or None if not found
        """
        if not role_key:
            return None

        # Try different formats of the role key
        formats_to_try = [
            role_key,                              # Original format
            role_key.lower(),                      # lowercase
            role_key.upper(),                      # UPPERCASE
            role_key.replace(" ", "_").upper(),     # UPPERCASE_WITH_UNDERSCORES
            role_key.title(),                      # Title Case
            role_key.replace("_", " ").title(),     # Title Case With Spaces
        ]
        fmt_lower_set = {fmt.lower() for fmt in formats_to_try if fmt}

        profiles = self.principal_profiles
        items = profiles.items() if isinstance(profiles, dict) else enumerate(profiles or [])
        for key, raw_profile in items:
            profile = self._normalize_profile_data(raw_profile)
            if client_id and profile.get("client_id") != client_id:
                continue
            candidates = {
                str(key).lower() if isinstance(profiles, dict) else "",
                str(profile.get("id") or "").lower(),
                str(profile.get("role") or "").lower(),
            }
            candidates.discard("")
            if candidates & fmt_lower_set:
                return profile

        # No match found
        return None
        
    def _get_role_string(self, role):
        """
        Ensure role is a string.
        
        Args:
            role: Role string or enum value
            
        Returns:
            Role as a string
        """
        # If it has a value attribute (like an enum), get the value
        if hasattr(role, 'value'):
            return role.value
        
        # Otherwise convert to string
        return str(role)
        
    async def _map_business_processes_to_strings(self, business_processes: List[Any]) -> List[str]:
        """
        Convert business process objects to string values.
        
        Args:
            business_processes: List of business process objects or strings
            
        Returns:
            List of business process strings
        """
        result = []
        
        for bp in business_processes:
            if isinstance(bp, str):
                # Already a string, use directly
                result.append(bp)
            elif hasattr(bp, 'display_name') and bp.display_name:
                # Business process object with display_name
                result.append(bp.display_name)
            elif hasattr(bp, 'name') and bp.name:
                # Business process object with name
                result.append(bp.name)
            else:
                # Try to convert to string
                try:
                    result.append(str(bp))
                except Exception as e:
                    self.logger.warning(f"Could not convert business process to string: {e}")
        
        # Filter out None values
        return [bp for bp in result if bp is not None]
        
    async def get_principal_context(self, principal_role) -> Dict[str, Any]:
        """
        Get principal context for a given role.
        
        Args:
            principal_role: Role of the principal (string or PrincipalRole enum value)
            
        Returns:
            Principal context containing preferences and relevant business processes
        """
        from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame
        
        try:
            # Log the request
            self.logger.info(f"Getting principal context for role: {principal_role}")

            # Infra A4-a: refresh principal profiles per request so newly seeded
            # principals become visible without a service restart. The provider's
            # load() does a fresh read from the configured data source.
            if self._principal_provider:
                try:
                    await self._principal_provider.load()
                except Exception as e:
                    self.logger.warning(f"Principal provider refresh failed; falling back to cached profiles: {e}")
            await self._load_principal_profiles()
            
            # Convert enum to string if needed
            role_str = self._get_role_string(principal_role)
            
            # Try to find profile by role string
            profile = None
            
            # Try to find profile with matching role
            if isinstance(self.principal_profiles, list):
                for p in self.principal_profiles:
                    if isinstance(p, dict) and p.get('role', '').lower() == role_str.lower():
                        profile = p
                        break
            elif isinstance(self.principal_profiles, dict):
                for p in self.principal_profiles.values():
                    if isinstance(p, dict) and p.get('role', '').lower() == role_str.lower():
                        profile = p
                        break
            
            # If no profile found by direct match, try case-insensitive lookup
            if not profile:
                profile = self._get_profile_case_insensitive(role_str)
            
            if profile:
                # Create and return PrincipalContext
                business_processes = []
                
                # If profile is a dictionary and has business_processes
                if hasattr(profile, 'get') and profile.get('business_processes'):
                    for bp in profile.get('business_processes', []):
                        # Add business process as string
                        business_processes.append(bp)
                
                # Get role string from profile
                role_str = profile.get('role', 'CFO')
                
                # Create context with defaults if values are missing
                principal_context = PrincipalContext(
                    role=role_str,  # Use role string directly
                    principal_id=profile.get('id', role_str.lower().replace(' ', '_')),
                    client_id=profile.get('client_id', None),
                    business_processes=business_processes or [],
                    default_filters=profile.get('default_filters', {}) if hasattr(profile, 'get') else {},
                    decision_style=_extract_decision_style(profile) if hasattr(profile, 'get') else "Analytical",
                    communication_style=_extract_communication_style(profile) if hasattr(profile, 'get') else "Concise",
                    preferred_timeframes=_extract_preferred_timeframes(profile) if hasattr(profile, 'get') else [TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE],
                )

                # Return as dictionary for JSON serialization
                return principal_context.model_dump()
            
            # If no matching profile is found, return a default context
            self.logger.warning(f"No principal profile found for role {principal_role}, using default")
            # Use the input role string or default to CFO
            default_role = "CFO"
            default_id = role_str.lower().replace(' ', '_') if 'role_str' in locals() else "cfo_001"
            
            principal_context = PrincipalContext(
                role=default_role,
                principal_id=default_id,
                client_id=None,
                business_processes=[],
                default_filters={},
                decision_style="Analytical",
                communication_style="Concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
            )

            return principal_context.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in get_principal_context: {str(e)}")
            raise
            
    async def get_business_process_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get a business process by name from the registry.
        
        Args:
            name: Name of the business process
            
        Returns:
            Business process object as a dictionary
        """
        try:
            # Log the request
            self.logger.info(f"Getting business process by name: {name}")
            
            # Get the business process provider
            if self.registry_factory is None:
                self.logger.error("Registry factory is not initialized")
                return None
                
            business_process_provider = self.registry_factory.get_provider("business_process")
            if business_process_provider is None:
                self.logger.error("Business process provider not found in registry factory")
                return None
            
            # Try to find the business process by name
            business_process = business_process_provider.get_by_name(name)
            if business_process is None:
                # Try by display name
                business_process = business_process_provider.get_by_display_name(name)
            
            if business_process is None:
                # Try by ID
                business_process = business_process_provider.get_by_id(name)
                
            if business_process is None:
                self.logger.warning(f"Business process not found: {name}")
                # Return the name directly as a string
                business_process = name
            
            # Convert to dictionary
            if hasattr(business_process, 'model_dump'):
                return business_process.model_dump()
            else:
                return business_process
                
        except Exception as e:
            self.logger.error(f"Error in get_business_process_by_name: {str(e)}")
            return None
            
    async def get_principal_context_by_id(self, principal_id: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get principal context for a given principal ID.

        Args:
            principal_id: ID of the principal
            client_id: Optional client/tenant ID for composite key lookup.
                       Required when multiple clients share the same principal_id.

        Returns:
            Principal context containing preferences and relevant business processes
        """
        from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame
        from src.agents.models.principal_context_models import PrincipalProfileResponse

        try:
            # Log the request
            self.logger.info(f"Getting principal context for ID: {principal_id} (client_id={client_id})")

            # Infra A4-a: refresh principal profiles per request so newly seeded
            # principals (e.g. when onboarding a new client) become visible
            # without a service restart. Provider load() does a fresh read.
            if self._principal_provider:
                try:
                    await self._principal_provider.load()
                except Exception as e:
                    self.logger.warning(f"Principal provider refresh failed; falling back to cached profiles: {e}")
            await self._load_principal_profiles()

            # Try to get profile directly from the provider first
            profile_data = None
            if self._principal_provider:
                # When client_id is known, try the composite key first to avoid
                # returning the wrong principal when multiple clients share the same id.
                profile_obj = None
                if client_id:
                    composite_key = f"{client_id}:{principal_id}"
                    profile_obj = self._principal_provider._items.get(composite_key)
                    if profile_obj:
                        self.logger.info(f"Found profile via composite key {composite_key}")
                if not profile_obj:
                    profile_obj = self._principal_provider.get(principal_id)
                if profile_obj:
                    # Convert to dict if it's a model (prefer Pydantic v2 API)
                    if hasattr(profile_obj, 'model_dump'):
                        profile_data = profile_obj.model_dump()
                    elif hasattr(profile_obj, '__dict__'):
                        profile_data = vars(profile_obj)
                    else:
                        profile_data = {}
                    
                    self.logger.info(f"Found profile for {principal_id} in provider")
            
            # If not found in provider, check principal_profiles
            if not profile_data:
                # Check if principal_profiles is a list or dict and handle accordingly
                if isinstance(self.principal_profiles, list):
                    for p in self.principal_profiles:
                        if isinstance(p, dict) and p.get('id') == principal_id:
                            profile_data = p
                            break
                elif isinstance(self.principal_profiles, dict):
                    if principal_id in self.principal_profiles:
                        profile_data = self.principal_profiles[principal_id]
            
            if profile_data:
                # Create and return PrincipalContext
                business_processes = []
                
                # Extract business processes — Supabase stores them as 'business_process_ids'
                bp_list = profile_data.get('business_processes') or profile_data.get('business_process_ids', [])
                for bp in bp_list:
                    # Try to get the business process from the registry provider
                    if self._business_process_provider:
                        bp_obj = self._business_process_provider.get(bp)
                        if bp_obj:
                            business_processes.append(bp_obj)
                        else:
                            # Try to find by display name or similar name
                            found = False
                            for process in self._business_process_provider.get_all():
                                if bp.lower() in process.name.lower() or \
                                   (process.display_name and bp.lower() in process.display_name.lower()):
                                    business_processes.append(process)
                                    found = True
                                    self.logger.info(f"Found similar business process: {process.name} for {bp}")
                                    break
                            
                            if not found:
                                self.logger.warning(f"Unknown business process: {bp} for principal {principal_id}")
                                # Add the business process as a string directly
                                business_processes.append(bp)
                    else:
                        # Fallback to using the string directly
                        self.logger.warning(f"No business process provider available, using string directly: {bp}")
                        business_processes.append(bp)
                
                # Get role string from profile; YAML to model conversion may omit 'role'
                # Fallback to 'title' or 'name' before defaulting to 'CFO'
                role_str = profile_data.get('role') or profile_data.get('title') or profile_data.get('name') or 'CFO'
                
                # Convert business process objects to string values directly
                string_business_processes = []
                for bp in business_processes:
                    if isinstance(bp, str):
                        string_business_processes.append(bp)
                    elif hasattr(bp, 'display_name') and bp.display_name:
                        string_business_processes.append(bp.display_name)
                    elif hasattr(bp, 'name') and bp.name:
                        string_business_processes.append(bp.name)
                    else:
                        try:
                            string_business_processes.append(str(bp))
                        except Exception as e:
                            self.logger.warning(f"Could not convert business process to string: {e}")
                
                # Filter out None values
                string_business_processes = [bp for bp in string_business_processes if bp is not None]
                
                # Create context with defaults if values are missing
                principal_context = PrincipalContext(
                    role=role_str,  # Use role string directly
                    principal_id=principal_id,
                    client_id=profile_data.get('client_id', None),
                    business_processes=string_business_processes,
                    default_filters=profile_data.get('default_filters', {}),
                    decision_style=_extract_decision_style(profile_data),
                    communication_style=_extract_communication_style(profile_data),
                    preferred_timeframes=_extract_preferred_timeframes(profile_data),
                )
                # Build and return a protocol-compliant response immediately
                try:
                    import uuid as _uuid
                    from src.agents.models.principal_context_models import PrincipalProfileResponse as _PPR
                    response = _PPR(
                        request_id=str(_uuid.uuid4()),
                        status="success",
                        profile=profile_data,
                        context=principal_context.model_dump()
                    )
                    return response.model_dump()
                except Exception:
                    # Fallback to dict if model construction fails
                    return {
                        "request_id": str(_uuid.uuid4()) if '_uuid' in locals() else "",
                        "status": "success",
                        "profile": profile_data,
                        "context": principal_context.model_dump()
                    }
            
            # Create a default profile
            default_profile = {
                "id": principal_id,
                "name": principal_id.replace('_', ' ').title(),
                "role": "CFO",
                "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"]
            }
            
            # Create default context with business processes as strings
            default_business_processes = [
                "Finance: Profitability Analysis",
                "Finance: Revenue Growth Analysis",
                "Finance: Expense Management",
                "Finance: Cash Flow Management",
                "Finance: Budget vs. Actuals"
            ]
            
            principal_context = PrincipalContext(
                role="CFO",  # Default role as string
                principal_id=principal_id,
                client_id=None,
                business_processes=default_business_processes,
                default_filters={},
                decision_style="Analytical",
                communication_style="Concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
            )

            # Create response object (uuid is imported at module level — a local
            # `import uuid` here previously shadowed it for this ENTIRE function,
            # including the except block below, causing "cannot access local
            # variable 'uuid'" whenever an exception was raised before this line
            # executed — found live in production 2026-07-29)
            response = PrincipalProfileResponse(
                request_id=str(uuid.uuid4()),
                status="success",
                profile=default_profile,
                context=principal_context.model_dump()
            )
            
            return response.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in get_principal_context_by_id: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Return a minimal valid response even in case of error
            default_profile = {"id": principal_id, "name": principal_id.replace('_', ' ').title(), "role": "CFO"}
            
            # Try to get some business processes from registry for the error case
            default_business_processes = []
            try:
                if self._business_process_provider:
                    # Get a couple of finance processes if available
                    finance_processes = self._business_process_provider.find_by_domain("Finance")
                    if finance_processes:
                        # Convert business process objects to strings
                        for bp in finance_processes[:2]:  # Just use 2 in error case
                            if hasattr(bp, 'display_name') and bp.display_name:
                                default_business_processes.append(bp.display_name)
                            elif hasattr(bp, 'name') and bp.name:
                                default_business_processes.append(bp.name)
                            else:
                                default_business_processes.append(str(bp))
            except Exception:
                # Ignore any errors in the error handler
                pass
                
            # Fallback to hardcoded strings if we couldn't get any
            if not default_business_processes:
                default_business_processes = [
                    "Finance: Profitability Analysis",
                    "Finance: Revenue Growth Analysis"
                ]
                
            principal_context = PrincipalContext(
                role="CFO",
                principal_id=principal_id,
                client_id=None,
                business_processes=default_business_processes,
                default_filters={},
                decision_style="Analytical",
                communication_style="Concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER]
            )
            response = PrincipalProfileResponse(
                request_id=str(uuid.uuid4()),
                status="success",
                profile=default_profile, 
                context=principal_context
            )
            return response.model_dump()
