"""C-18: RLS on every table with no policies; the anon key reads nothing.

Supabase's REST API runs as `anon`/`authenticated` with default grants on `public`.
We reproduce that worst case (GRANT ALL) and assert RLS alone still hides every row.
"""

import pytest
from sqlalchemy import Engine, text


def _tables(engine: Engine) -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        )
        return [r[0] for r in rows]


def test_every_table_has_rls_enabled_and_no_policies(owner_engine: Engine) -> None:
    tables = _tables(owner_engine)
    assert {"employee", "team", "session", "audit_log"} <= set(tables)
    with owner_engine.connect() as conn:
        for table in tables:
            enabled = conn.scalar(
                text("SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass(:t)"),
                {"t": f'public."{table}"'},
            )
            assert enabled, f"RLS not enabled on {table}"
        assert conn.scalar(text("SELECT count(*) FROM pg_policies WHERE schemaname='public'")) == 0


def test_anon_reads_nothing_from_any_table(owner_engine: Engine, make_login) -> None:  # type: ignore[no-untyped-def]
    make_login("hr")
    with owner_engine.connect() as conn:
        conn.execute(text("INSERT INTO audit_log (action, target_type) VALUES ('seed', 't')"))
        conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO anon"))
        conn.execute(text("GRANT USAGE ON SCHEMA public TO anon"))
    try:
        for table in _tables(owner_engine):
            with owner_engine.connect() as conn:
                total = conn.scalar(text(f'SELECT count(*) FROM "{table}"'))
                conn.execute(text("SET ROLE anon"))
                try:
                    seen = conn.scalar(text(f'SELECT count(*) FROM "{table}"'))
                finally:
                    conn.execute(text("RESET ROLE"))
            if table in {"employee", "session", "audit_log"}:
                assert total >= 1, f"seed row missing in {table}"
            assert seen == 0, f"anon read {seen} rows from {table}"
    finally:
        with owner_engine.connect() as conn:
            conn.execute(text("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon"))


def test_anon_cannot_write(owner_engine: Engine) -> None:
    from sqlalchemy.exc import DBAPIError

    with owner_engine.connect() as conn:
        conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO anon"))
    try:
        with owner_engine.connect() as conn:
            conn.execute(text("SET ROLE anon"))
            try:
                with pytest.raises(DBAPIError):
                    conn.execute(
                        text("INSERT INTO audit_log (action, target_type) VALUES ('x','t')")
                    )
            finally:
                conn.execute(text("RESET ROLE"))
    finally:
        with owner_engine.connect() as conn:
            conn.execute(text("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon"))
