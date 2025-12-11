"""Connection profile management helpers for Decision Studio admin workflows."""

from __future__ import annotations

import os
from contextlib import closing
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency (DuckDB may be unavailable during some tests)
    import duckdb  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully by connection tests
    duckdb = None

try:  # pragma: no cover - optional dependency
    from google.cloud import bigquery  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully by connection tests
    bigquery = None

import yaml

CONFIG_ENV_VAR = "A9_CONNECTION_PROFILES_PATH"
DEFAULT_CONFIG_FILENAME = "connection_profiles.yaml"


@dataclass
class ConnectionProfile:
    """Encapsulates connection metadata for onboarding workflows."""

    name: str
    system_type: str = "duckdb"
    description: Optional[str] = None
    database_path: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    driver: Optional[str] = None
    default_schema: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)
    persist_secret: bool = False
    password_saved: bool = False

    def __post_init__(self) -> None:
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValueError("Connection profile name cannot be blank")

        self.system_type = (self.system_type or "duckdb").strip()
        self.description = (self.description or None) or None

        if isinstance(self.port, str) and self.port.strip():
            try:
                self.port = int(self.port)
            except ValueError:
                raise ValueError("Port must be an integer if provided") from None
        elif isinstance(self.port, str):
            self.port = None

        if not isinstance(self.extras, dict):
            raise ValueError("Extras must be a dictionary when provided")

        # Normalize empty strings to None for optional string fields
        for attr in ("database_path", "host", "database", "schema", "username", "driver", "default_schema"):
            value = getattr(self, attr)
            if isinstance(value, str):
                cleaned = value.strip()
                setattr(self, attr, cleaned or None)

        # Control password persistence flag
        if not self.persist_secret:
            self.password_saved = False
            if not self.password:
                self.password = None
        else:
            self.password_saved = bool(self.password)

    def to_storage_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if not self.persist_secret:
            data["password"] = None
            data["password_saved"] = False
        else:
            data["password_saved"] = bool(self.password)
        return data

    def connection_overrides(self, include_secret: bool = False) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        system = (self.system_type or "").lower()

        if system == "duckdb":
            if self.database_path:
                overrides["database_path"] = self.database_path
        else:
            if self.host:
                overrides["host"] = self.host
            if self.port is not None:
                overrides["port"] = self.port
            if self.database:
                overrides["database"] = self.database
            if self.schema:
                overrides["schema"] = self.schema
            if self.driver:
                overrides["driver"] = self.driver
            if self.default_schema:
                overrides["default_schema"] = self.default_schema

        if self.username:
            overrides["username"] = self.username
        if include_secret:
            if self.password:
                overrides["password"] = self.password
        elif self.persist_secret and self.password:
            overrides["password"] = self.password

        if self.extras:
            overrides.update(self.extras)

        return overrides

    def onboarding_defaults(self) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {"source_system": self.system_type}
        system = (self.system_type or "").lower()

        if system == "duckdb" and self.database_path:
            defaults["database"] = self.database_path
        elif self.database:
            defaults["database"] = self.database

        if self.schema:
            defaults["schema"] = self.schema

        overrides = self.connection_overrides()
        if overrides:
            defaults["connection_overrides"] = overrides

        return defaults


@dataclass
class ConnectionProfilesState:
    profiles: List[ConnectionProfile] = field(default_factory=list)
    active_profile: Optional[str] = None

    def to_storage_dict(self) -> Dict[str, Any]:
        return {
            "profiles": [profile.to_storage_dict() for profile in self.profiles],
            "active_profile": self.active_profile,
        }


@dataclass
class ConnectionTestResult:
    success: bool
    message: str


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_store_path() -> Path:
    return _project_root() / "config" / DEFAULT_CONFIG_FILENAME


def _store_path() -> Path:
    env_path = os.getenv(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path)
    return _default_store_path()


def _ensure_store_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_raw_data() -> Dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"profiles": [], "active_profile": None}

    with path.open("r", encoding="utf-8") as handle:
        try:
            data = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - configuration error surface to user
            raise ValueError(f"Connection profiles file {path} contains invalid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Connection profiles file {path} must contain a mapping at the root")

    return data


def _write_raw_data(state: ConnectionProfilesState) -> None:
    path = _store_path()
    _ensure_store_dir(path)

    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(state.to_storage_dict(), handle, sort_keys=True)

    # Restrict permissions on POSIX systems
    if os.name != "nt":  # pragma: no cover - platform specific
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def get_connection_profiles_state() -> ConnectionProfilesState:
    raw = _load_raw_data()
    raw_profiles = raw.get("profiles", []) or []
    profiles: List[ConnectionProfile] = []
    for entry in raw_profiles:
        if not isinstance(entry, dict):
            continue
        try:
            profiles.append(ConnectionProfile(**entry))
        except Exception:
            continue
    active = raw.get("active_profile")
    if active and not any(profile.name == active for profile in profiles):
        active = None
    return ConnectionProfilesState(profiles=profiles, active_profile=active)


def get_active_profile() -> Optional[ConnectionProfile]:
    state = get_connection_profiles_state()
    if not state.active_profile:
        return None
    return next((profile for profile in state.profiles if profile.name == state.active_profile), None)


def upsert_connection_profile(profile: ConnectionProfile) -> None:
    state = get_connection_profiles_state()
    existing = next((p for p in state.profiles if p.name == profile.name), None)

    stored_password: Optional[str] = None
    if profile.persist_secret:
        if profile.password:
            stored_password = profile.password
        elif existing and existing.persist_secret and existing.password:
            stored_password = existing.password
    profile.password = stored_password
    profile.password_saved = profile.persist_secret and bool(stored_password)

    # Replace or append profile
    if existing:
        state.profiles = [profile if p.name == profile.name else p for p in state.profiles]
    else:
        state.profiles.append(profile)

    _write_raw_data(state)


def delete_connection_profile(name: str) -> None:
    state = get_connection_profiles_state()
    state.profiles = [profile for profile in state.profiles if profile.name != name]
    if state.active_profile == name:
        state.active_profile = state.profiles[0].name if state.profiles else None
    _write_raw_data(state)


def set_active_profile(name: Optional[str]) -> None:
    state = get_connection_profiles_state()
    if name is not None and not any(profile.name == name for profile in state.profiles):
        raise ValueError(f"Connection profile '{name}' does not exist")
    state.active_profile = name
    _write_raw_data(state)


def test_connection_profile(profile: ConnectionProfile) -> ConnectionTestResult:
    system = (profile.system_type or "").lower()

    if system == "duckdb":
        if duckdb is None:
            return ConnectionTestResult(False, "DuckDB driver is not installed")

        db_path = profile.database_path or ":memory:"
        try:
            with closing(duckdb.connect(db_path)) as connection:
                connection.execute("SELECT 1")
            return ConnectionTestResult(True, f"Connected to DuckDB at {db_path}")
        except Exception as exc:  # pragma: no cover - direct duckdb failure path
            return ConnectionTestResult(False, f"DuckDB connection failed: {exc}")

    if system == "bigquery":
        if bigquery is None:
            return ConnectionTestResult(False, "google-cloud-bigquery package is not installed")

        project = None
        if profile.extras:
            project = profile.extras.get("project")
        if not project and profile.database:
            project = profile.database

        try:
            client = bigquery.Client(project=project) if project else bigquery.Client()
        except Exception as exc:
            return ConnectionTestResult(False, f"Failed to initialize BigQuery client: {exc}")

        try:
            query_job = client.query("SELECT 1")
            query_job.result(timeout=30)
            project_name = getattr(client, "project", project) or "(default project)"
            return ConnectionTestResult(True, f"Connected to BigQuery project {project_name}")
        except Exception as exc:  # pragma: no cover - direct BigQuery failure path
            return ConnectionTestResult(False, f"BigQuery connection failed: {exc}")
        finally:
            try:
                client.close()
            except Exception:
                pass

    return ConnectionTestResult(False, f"Connection testing for '{profile.system_type}' is not supported yet")


def profile_to_serializable(profile: ConnectionProfile, include_secret: bool = False) -> Dict[str, Any]:
    data = profile.to_storage_dict()
    overrides = profile.connection_overrides(include_secret=include_secret)
    data["connection_overrides"] = overrides
    return data
