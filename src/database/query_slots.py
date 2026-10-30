"""Warehouse query limits shared by Deep Analysis and the Situation Awareness scan (2026-10-30).

A run (one analysis, one scan) keeps at most QUERIES_PER_RUN queries in flight, and this server
process at most QUERIES_PER_SERVER across every run, so overlapping scans and analyses cannot flood
a client's warehouse. The limit that matters is the client's: a Snowflake warehouse runs about 8
queries at once by default (MAX_CONCURRENCY_LEVEL) and queues the rest, and it carries the client's
own workload. Only BigQuery and Snowflake run queries in parallel; SQL Server and DuckDB hold one
connection that runs one query at a time.
"""
import asyncio
from typing import Dict, Optional

QUERIES_PER_RUN = 8
QUERIES_PER_SERVER = 16
PARALLEL_SOURCES = ("bigquery", "snowflake")

_SERVER_SLOTS: Dict[int, asyncio.Semaphore] = {}


def server_query_slots() -> asyncio.Semaphore:
    """The process-wide cap, one semaphore per event loop (a semaphore belongs to one loop)."""
    loop = asyncio.get_running_loop()
    slots = _SERVER_SLOTS.get(id(loop))
    if slots is None:
        slots = _SERVER_SLOTS[id(loop)] = asyncio.Semaphore(QUERIES_PER_SERVER)
    return slots


def runs_in_parallel(source_system: Optional[str]) -> bool:
    """True for a backend that can run several queries at once."""
    return str(source_system or "").lower() in PARALLEL_SOURCES
