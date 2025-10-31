"""DuckDB view creation smoke tests for Data Product Agent."""

import textwrap

import pytest


@pytest.mark.asyncio
async def test_create_view_from_contract(data_product_agent, tmp_path):
    """Data Product Agent should create a DuckDB view from a minimal contract."""

    contract_path = tmp_path / "test_contract.yaml"
    view_name = "test_contract_view"
    contract_path.write_text(
        textwrap.dedent(
            f"""
            views:
              - name: {view_name}
                sql: |
                  SELECT 1 AS metric_value, 'ok' AS metric_status
            """
        ),
        encoding="utf-8",
    )

    result = await data_product_agent.create_view_from_contract(str(contract_path), view_name)

    assert result.get("success") is True
    assert result.get("view_name") == view_name

    query = await data_product_agent.execute_sql(f'SELECT * FROM "{view_name}"')

    assert query.get("success") is True
    assert query.get("row_count") == 1
    rows = query.get("rows") or query.get("data")
    assert rows and rows[0]["metric_value"] == 1
    assert rows[0]["metric_status"] == "ok"
