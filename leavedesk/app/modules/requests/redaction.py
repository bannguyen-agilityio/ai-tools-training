"""Server-side redaction of a request for one viewer (spec §8, R12, R26).

Visible to the owner and HR admins always; to any other permitted viewer only while the request is
Pending (they are deciding). Otherwise the note is dropped and Sick shows as "Off".
"""

from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest
from app.modules.requests.schemas import RequestOut

SENSITIVE_TYPES = frozenset({"sick"})  # leave_type.is_sensitive; Sick is the only seeded one


def can_view(viewer: Employee, req: LeaveRequest) -> bool:
    """Owner, assigned approver, HR admin, or the deputy for HR-queue items. Cover managers decide
    from the `scope=cover` list, which carries what they need; detail stays closed to them."""
    if viewer.id == req.employee_id or viewer.role == "hr" or req.assigned_to == viewer.id:
        return True
    return viewer.is_hr_deputy and req.queue in ("hr", "deputy")


def redact(viewer: Employee, req: LeaveRequest) -> RequestOut:
    full = viewer.id == req.employee_id or viewer.role == "hr" or req.status == "pending"
    masked = req.leave_type_code in SENSITIVE_TYPES and not full
    return RequestOut(
        id=req.id,
        employee_id=req.employee_id,
        leave_type=None if masked else req.leave_type_code,
        start_date=req.start_date,
        start_part=req.start_part,
        end_date=req.end_date,
        end_part=req.end_part,
        working_days=float(req.working_days),
        note=req.note if full else None,
        status=req.status,
        queue=req.queue,
        assigned_to=req.assigned_to,
        submitted_at=req.submitted_at,
        notice_warning=req.notice_warning,
        version=req.version,
        label="Off" if masked else None,
    )
