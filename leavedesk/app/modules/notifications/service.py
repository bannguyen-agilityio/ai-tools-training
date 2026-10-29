import uuid
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ProblemError
from app.modules.email import privacy
from app.modules.email.outbox_models import EmailOutbox
from app.modules.email.templates import Event, render
from app.modules.identity.models import Employee
from app.modules.notifications import repository
from app.modules.notifications.models import Notification

REQUEST_EVENTS = frozenset(e for e in Event if e not in (Event.INVITE, Event.PASSWORD_RESET))


async def emit(
    db: AsyncSession,
    event: Event,
    recipient: Employee,
    *,
    ref: privacy.RequestRef | None = None,
    link: str | None = None,
    rejection_reason: str | None = None,
    occurrence: str = "",
) -> bool:
    """Write the email (outbox) and the in-app notification in the caller's transaction (R26, R35).

    Request events take `ref`; invite and reset take `link` (built by the identity module).
    `occurrence` distinguishes repeats of the same event on one request. Returns False when
    the same event was already emitted (dedupe_key), so a retried caller sends nothing twice.
    A rejection reason is only accepted for the rejected event, addressed to the request owner.
    """
    settings = get_settings()
    payload: dict[str, str] = {"recipient_name": recipient.name}
    if event in REQUEST_EVENTS:
        if ref is None:
            raise ValueError(f"{event} needs a request reference")
        payload |= {
            "employee_name": ref.owner_name,
            "start_date": ref.start_date.isoformat(),
            "end_date": ref.end_date.isoformat(),
            "link": f"{settings.app_base_url}/requests/{ref.request_id}",
        }
        if rejection_reason is not None:
            if event is not Event.REQUEST_REJECTED or recipient.id != ref.owner_id:
                raise privacy.PrivacyError("rejection reason goes to the employee only")
            payload["rejection_reason"] = rejection_reason
        key = f"{event}:{ref.request_id}:{recipient.id}:{occurrence}"
    else:
        if link is None:
            raise ValueError(f"{event} needs a link")
        payload["link"] = link
        if not occurrence:
            # Without it a second invite or reset for the same person would be deduplicated away.
            raise ValueError(f"{event} needs an occurrence (e.g. the token id)")
        key = f"{event}:{recipient.id}:{occurrence}"

    privacy.check_payload(payload)
    render_in = dict(payload)
    if ref is not None:
        render_in["dates"] = privacy.date_range(ref.start_date, ref.end_date)
    out = render(event, render_in)
    # Names and the rejection reason are free text; only the template wording is checked, so a
    # reason that mentions "sick" cannot block the decision.
    probe = render(
        event,
        {**render_in, "recipient_name": "-", "employee_name": "-", "rejection_reason": None},
    )
    privacy.assert_clean(
        probe.subject, probe.body, probe.notification_title or "", probe.notification_body or ""
    )

    mocked = settings.email_backend == "mock"
    inserted = await db.scalar(
        insert(EmailOutbox)
        .values(
            recipient_employee_id=recipient.id,
            to_address=recipient.email,
            template=event.value,
            payload=payload,
            subject=out.subject,
            body=out.body,
            dedupe_key=key,
            status="mocked" if mocked else "pending",
        )
        .on_conflict_do_nothing(index_elements=["dedupe_key"])
        .returning(EmailOutbox.id)
    )
    if inserted is None:
        return False

    if out.notification_title is not None and out.notification_body is not None and ref:
        db.add(
            Notification(
                employee_id=recipient.id,
                kind=event.value,
                title=out.notification_title,
                body=out.notification_body,
                link=f"/requests/{ref.request_id}",
                request_id=ref.request_id,
                dedupe_key=key,
            )
        )
        await db.flush()
    return True


async def mark_read(db: AsyncSession, user: Employee, notification_id: uuid.UUID) -> Notification:
    n = await repository.get(db, notification_id)
    if n is None:
        raise ProblemError(404, "Notification not found")
    if n.employee_id != user.id:
        raise ProblemError(403, "Not allowed")
    if n.read_at is None:
        n.read_at = datetime.now(UTC)
        await db.commit()
    return n
