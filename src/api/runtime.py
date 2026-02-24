from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
    from src.registry.factory import RegistryFactory


class AgentRuntime:
    """Shared runtime that owns the orchestrator and registry factory."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(__name__)
        self._initialized_at: datetime | None = None
        self._agent_activity: Dict[str, datetime] = {}
        self._connected_agents: set[str] = set()
        self._agents: Dict[str, object] = {}
        self._orchestrator: A9_Orchestrator_Agent | None = None
        self._registry_factory: "RegistryFactory" | None = None
        self._orchestrator_connected: bool = False
        self._orchestrator_activity: datetime | None = None

    async def initialize(self) -> None:
        if self._orchestrator is not None:
            return

        async with self._lock:
            if self._orchestrator is not None:
                return

            self._logger.info("Initializing AgentRuntime orchestrator")
            self._registry_factory = await self._build_registry_factory()
            self._orchestrator = await self._create_orchestrator()
            await self._create_core_agents()
            await self._refresh_agent_index()
            self._initialized_at = datetime.now(timezone.utc)
            self._logger.info("AgentRuntime initialization complete")

    def get_registry_factory(self) -> "RegistryFactory":
        if self._registry_factory is None:
            raise RuntimeError("Registry factory has not been initialized")
        return self._registry_factory

    def get_orchestrator(self) -> "A9_Orchestrator_Agent":
        if self._orchestrator is None:
            raise RuntimeError("Orchestrator has not been initialized")
        return self._orchestrator

    async def _build_registry_factory(self):
        from src.registry.bootstrap import RegistryBootstrap

        await RegistryBootstrap.initialize()
        return RegistryBootstrap._factory

    async def _create_orchestrator(self):
        from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent

        orchestrator = await A9_Orchestrator_Agent.create({})
        await orchestrator.connect()
        self._orchestrator_connected = True
        self._orchestrator_activity = datetime.now(timezone.utc)
        return orchestrator

    async def _create_core_agents(self) -> None:
        from src.agents.new.a9_orchestrator_agent import initialize_agent_registry

        await initialize_agent_registry()

        agent_plan = [
            (
                "A9_Data_Governance_Agent",
                {
                    "orchestrator": self._orchestrator,
                    "registry_factory": self._registry_factory,
                },
            ),
            (
                "A9_Principal_Context_Agent",
                {
                    "orchestrator": self._orchestrator,
                    "registry_factory": self._registry_factory,
                },
            ),
            (
                "A9_Data_Product_Agent",
                {
                    "orchestrator": self._orchestrator,
                    "registry_factory": self._registry_factory,
                    "data_directory": "data",
                    "database": {
                        "type": "duckdb",
                        "path": "agent9-hermes-api.duckdb",
                    },
                    "registry_path": "src/registry/data_product",
                },
            ),
            (
                "A9_Situation_Awareness_Agent",
                {
                    "orchestrator": self._orchestrator,
                    "registry_factory": self._registry_factory,
                    "target_domains": ["Finance"],
                },
            ),
            (
                "A9_Deep_Analysis_Agent",
                {
                    "orchestrator": self._orchestrator,
                    "registry_factory": self._registry_factory,
                },
            ),
            (
                "A9_NLP_Interface_Agent",
                {
                    "orchestrator": self._orchestrator,
                    "registry_factory": self._registry_factory,
                },
            ),
            (
                "A9_LLM_Service_Agent",
                {
                    "orchestrator": self._orchestrator,
                    "registry_factory": self._registry_factory,
                },
            ),
        ]

        for agent_name, config in agent_plan:
            agent = await self._orchestrator.create_agent_with_dependencies(agent_name, config)
            self._agents[agent_name] = agent
            await self._connect_agent(agent_name, agent)

    async def _refresh_agent_index(self) -> None:
        from src.agents.new.a9_orchestrator_agent import agent_registry

        agent_names = agent_registry.list_agents()
        for name in agent_names:
            if name not in self._agents:
                agent = await self._orchestrator.get_agent(name, resolve_dependencies=False)
                self._agents[name] = agent
            self._agent_activity.setdefault(name, datetime.now(timezone.utc))

    async def _connect_agent(self, agent_name: str, agent: object) -> None:
        connect_method = getattr(agent, "connect", None)
        if not callable(connect_method):
            return

        try:
            result = connect_method(self._orchestrator)
        except TypeError:
            result = connect_method()

        if inspect.isawaitable(result):
            await result

        self._connected_agents.add(agent_name)
        self._agent_activity[agent_name] = datetime.now(timezone.utc)

    async def get_agent_states(self) -> List[Dict[str, str]]:
        from src.agents.new.a9_orchestrator_agent import agent_registry

        await self.initialize()

        states: List[Dict[str, str]] = []
        now = datetime.now(timezone.utc)
        if self._orchestrator is not None:
            states.append(
                {
                    "name": "A9_Orchestrator_Agent",
                    "state": "connected" if self._orchestrator_connected else "initializing",
                    "last_activity": (self._orchestrator_activity or self._initialized_at or now).isoformat(),
                }
            )
        for name in sorted(agent_registry.list_agents()):
            agent = self._agents.get(name)
            initialized = agent_registry.get_agent_initialization_status(name)
            state_value = self._derive_state(name, agent, initialized)
            last_activity = self._agent_activity.get(name, self._initialized_at or now)
            states.append(
                {
                    "name": name,
                    "state": state_value,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                }
            )
        return states

    def _derive_state(self, name: str, agent: object, initialized: bool) -> str:
        if name in self._connected_agents:
            return "connected"

        status_attr = None
        if agent is not None:
            status_attr = getattr(agent, "status", None) or getattr(agent, "state", None)
        if isinstance(status_attr, str):
            return status_attr

        if initialized:
            return "ready"
        return "initializing"


agent_runtime = AgentRuntime()


async def get_agent_runtime() -> AgentRuntime:
    await agent_runtime.initialize()
    return agent_runtime
