"""Who may decide a request (R17, R22). Called from the service layer on every decision."""

import uuid

from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest


def can_decide(actor: Employee, req: LeaveRequest, on_behalf_of: uuid.UUID | None = None) -> bool:
    """Never your own request, nor one you entered for someone else (HR entry), whatever the
    role. A manager-queue item is for its assigned direct
    manager, or for any other manager covering them (`on_behalf_of` names the direct manager, R20;
    absence is not tracked, audit and email are the controls). The HR queue is for HR admins and
    the deputy; the deputy queue (an HR admin's own request, plan 17) is for the deputy."""
    if actor.id == req.employee_id or actor.id == req.entered_by:
        return False
    if req.queue == "manager":
        if req.assigned_to == actor.id:
            return True
        return (
            actor.role == "manager" and on_behalf_of is not None and req.assigned_to == on_behalf_of
        )
    if req.queue == "hr":
        return actor.role == "hr" or actor.is_hr_deputy
    return actor.is_hr_deputy
