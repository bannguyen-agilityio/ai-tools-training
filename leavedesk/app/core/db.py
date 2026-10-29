from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str | None = None, role: str | None = None) -> Engine:
    settings = get_settings()
    # Pooled (pgbouncer) URLs do not support server-side prepared statements.
    engine = create_engine(
        url or settings.database_url,
        pool_pre_ping=True,
        connect_args={"prepare_threshold": None},
    )
    role = role if role is not None else settings.database_role
    if role:
        if not role.isidentifier():
            raise ValueError("invalid database role name")

        @event.listens_for(engine, "connect")
        def _set_role(dbapi_conn, _record):  # type: ignore[no-untyped-def]
            with dbapi_conn.cursor() as cur:
                cur.execute(f'SET ROLE "{role}"')
            dbapi_conn.commit()

    return engine


_session_factory: sessionmaker[Session] | None = None


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(make_engine(), expire_on_commit=False)
    return _session_factory


def get_db() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session
