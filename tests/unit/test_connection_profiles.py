import pytest
from types import SimpleNamespace

from src.config import connection_profiles as cp

ConnectionProfile = cp.ConnectionProfile


@pytest.fixture
def profiles_config_path(tmp_path, monkeypatch):
    config_path = tmp_path / "connection_profiles.yaml"
    monkeypatch.setenv("A9_CONNECTION_PROFILES_PATH", str(config_path))
    return config_path


def test_upsert_and_get_profiles(profiles_config_path):
    profile = ConnectionProfile(
        name="local-duckdb",
        system_type="duckdb",
        database_path="data/agent9-hermes.duckdb",
        description="Local DuckDB for Decision Studio",
        persist_secret=False,
    )

    cp.upsert_connection_profile(profile)
    state = cp.get_connection_profiles_state()

    assert len(state.profiles) == 1
    stored = state.profiles[0]
    assert stored.name == "local-duckdb"
    assert stored.database_path == "data/agent9-hermes.duckdb"
    assert stored.password is None


def test_set_active_profile(profiles_config_path):
    profile = ConnectionProfile(name="profile-a")
    cp.upsert_connection_profile(profile)
    cp.set_active_profile("profile-a")

    state = cp.get_connection_profiles_state()
    assert state.active_profile == "profile-a"


def test_delete_profile(profiles_config_path):
    profile_a = ConnectionProfile(name="profile-a")
    profile_b = ConnectionProfile(name="profile-b")
    cp.upsert_connection_profile(profile_a)
    cp.upsert_connection_profile(profile_b)
    cp.set_active_profile("profile-a")

    cp.delete_connection_profile("profile-a")

    state = cp.get_connection_profiles_state()
    assert len(state.profiles) == 1
    assert state.profiles[0].name == "profile-b"
    assert state.active_profile == "profile-b"


def test_test_connection_profile_duckdb(monkeypatch):
    profile = ConnectionProfile(name="duckdb", system_type="duckdb", database_path=":memory:")
    result = cp.test_connection_profile(profile)
    assert result.success
    assert "Connected to DuckDB" in result.message


def test_test_connection_profile_bigquery_not_installed(monkeypatch):
    monkeypatch.setattr("src.config.connection_profiles.bigquery", None)
    profile = ConnectionProfile(name="bq", system_type="bigquery")

    result = cp.test_connection_profile(profile)

    assert not result.success
    assert "not installed" in result.message


def test_test_connection_profile_bigquery_success(monkeypatch):
    closed_clients = []

    class FakeResult:
        def result(self, timeout=None):
            return None

    class FakeClient:
        def __init__(self, project=None):
            self.project = project or "default-project"

        def query(self, sql):
            assert sql == "SELECT 1"
            return FakeResult()

        def close(self):
            closed_clients.append(self.project)

    fake_bigquery = SimpleNamespace(Client=FakeClient)
    monkeypatch.setattr("src.config.connection_profiles.bigquery", fake_bigquery)

    profile = ConnectionProfile(
        name="bq",
        system_type="bigquery",
        database="test-project",
    )

    result = cp.test_connection_profile(profile)

    assert result.success
    assert "Connected to BigQuery project test-project" in result.message
    assert closed_clients == ["test-project"]


def test_test_connection_profile_bigquery_query_failure(monkeypatch):
    class FakeClient:
        def __init__(self, project=None):
            self.project = project

        def query(self, sql):
            raise RuntimeError("query failed")

        def close(self):
            pass

    fake_bigquery = SimpleNamespace(Client=FakeClient)
    monkeypatch.setattr("src.config.connection_profiles.bigquery", fake_bigquery)

    profile = ConnectionProfile(name="bq", system_type="bigquery", database="proj")

    result = cp.test_connection_profile(profile)

    assert not result.success
    assert "BigQuery connection failed" in result.message
