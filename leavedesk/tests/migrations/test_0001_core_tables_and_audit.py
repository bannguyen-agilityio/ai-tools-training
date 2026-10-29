"""C-18: RLS on every table with no policies; the anon key reads nothing.

Supabase's REST API runs as `anon`/`authenticated` with default grants on `public`.
We reproduce that worst case (GRANT ALL) and assert RLS alone still hides every row.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import MakeLogin


async def _tables(engine: AsyncEngine) -> list[str]:
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        )
        return [r[0] for r in rows]


async def test_every_table_has_rls_enabled_and_no_policies(owner_engine: AsyncEngine) -> None:
    tables = await _tables(owner_engine)
    assert {"employee", "team", "session", "audit_log"} <= set(tables)
    async with owner_engine.connect() as conn:
        for table in tables:
            enabled = await conn.scalar(
                text("SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass(:t)"),
                {"t": f'public."{table}"'},
            )
            assert enabled, f"RLS not enabled on {table}"
        policies = await conn.scalar(
            text("SELECT count(*) FROM pg_policies WHERE schemaname='public'")
        )
        assert policies == 0


async def test_anon_reads_nothing_from_any_table(
    owner_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    await make_login("hr")
    async with owner_engine.connect() as conn:
        await conn.execute(text("INSERT INTO audit_log (action, target_type) VALUES ('seed', 't')"))
        await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO anon"))
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO anon"))
    try:
        for table in await _tables(owner_engine):
            async with owner_engine.connect() as conn:
                total = await conn.scalar(text(f'SELECT count(*) FROM "{table}"'))
                await conn.execute(text("SET ROLE anon"))
                try:
                    seen = await conn.scalar(text(f'SELECT count(*) FROM "{table}"'))
                finally:
                    await conn.execute(text("RESET ROLE"))
            if table in {"employee", "session", "audit_log"}:
                assert total and total >= 1, f"seed row missing in {table}"
            assert seen == 0, f"anon read {seen} rows from {table}"
    finally:
        async with owner_engine.connect() as conn:
            await conn.execute(text("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon"))


async def test_anon_cannot_write(owner_engine: AsyncEngine) -> None:
    async with owner_engine.connect() as conn:
        await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO anon"))
    try:
        async with owner_engine.connect() as conn:
            await conn.execute(text("SET ROLE anon"))
            try:
                with pytest.raises(DBAPIError):
                    await conn.execute(
                        text("INSERT INTO audit_log (action, target_type) VALUES ('x','t')")
                    )
            finally:
                await conn.execute(text("RESET ROLE"))
    finally:
        async with owner_engine.connect() as conn:
            await conn.execute(text("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon"))
