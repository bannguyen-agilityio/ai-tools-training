import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.modules.audit import service
from app.modules.audit.service import AuditDetailError


def test_app_connects_as_restricted_role(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        assert conn.scalar(text("SELECT current_user")) == "leavedesk_app"
        assert (
            conn.scalar(text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")) is False
        )


def test_record_appends_with_all_fields(app_engine: Engine, make_login) -> None:  # type: ignore[no-untyped-def]
    actor, cover = make_login("manager"), make_login("manager")
    with Session(app_engine) as db:
        service.record(
            db,
            actor_id=actor.employee_id,
            acting_for_id=cover.employee_id,
            action="request.approve",
            target_type="leave_request",
            target_id="abc",
            detail={"before": {"status": "pending"}, "after": {"status": "approved"}},
            ip="203.0.113.7",
        )
        db.commit()
        row = db.execute(text("SELECT * FROM audit_log")).mappings().one()
    assert row["actor_id"] == actor.employee_id
    assert row["acting_for_id"] == cover.employee_id
    assert row["detail"]["after"] == {"status": "approved"}
    assert row["ip"] == "203.0.113.7"
    assert row["at"] is not None


@pytest.mark.parametrize("key", ["note", "reason", "token", "password", "sick_type", "Password"])
def test_forbidden_detail_key_raises(app_engine: Engine, key: str) -> None:
    with Session(app_engine) as db, pytest.raises(AuditDetailError):
        service.record(db, actor_id=None, action="x", target_type="t", detail={key: "anything"})


def test_forbidden_key_nested_in_before_after_raises(app_engine: Engine) -> None:
    with Session(app_engine) as db, pytest.raises(AuditDetailError):
        service.record(
            db,
            actor_id=None,
            action="x",
            target_type="t",
            detail={"before": {"status": "pending"}, "after": {"decision_reason": "no"}},
        )


def test_unknown_detail_key_raises(app_engine: Engine) -> None:
    with Session(app_engine) as db, pytest.raises(AuditDetailError):
        service.record(db, actor_id=None, action="x", target_type="t", detail={"free_text": "hi"})


def _insert_one(app_engine: Engine) -> None:
    with Session(app_engine) as db:
        service.record(db, actor_id=None, action="login.failure", target_type="employee")
        db.commit()


@pytest.mark.parametrize(
    "statement",
    ["UPDATE audit_log SET action = 'tampered'", "DELETE FROM audit_log", "TRUNCATE audit_log"],
)
def test_audit_log_is_append_only_for_app_role(app_engine: Engine, statement: str) -> None:
    _insert_one(app_engine)
    with app_engine.connect() as conn, pytest.raises(ProgrammingError, match="permission denied"):
        conn.execute(text(statement))
    with app_engine.connect() as conn:
        assert conn.scalar(text("SELECT count(*) FROM audit_log")) == 1
