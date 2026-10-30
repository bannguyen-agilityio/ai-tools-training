"""Who may decide a request (R17, R22). Called from the service layer on every decision."""

from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest


def can_decide(actor: Employee, req: LeaveRequest) -> bool:
    """Never your own request, whatever the role. A manager-queue item is for its assigned direct
    manager only (cover is plan 14); the HR queue is for HR admins and the deputy; the deputy
    queue (an HR admin's own request, plan 17) is for the deputy."""
    if actor.id == req.employee_id:
        return False
    if req.queue == "manager":
        return req.assigned_to == actor.id
    if req.queue == "hr":
        return actor.role == "hr" or actor.is_hr_deputy
    return actor.is_hr_deputy
