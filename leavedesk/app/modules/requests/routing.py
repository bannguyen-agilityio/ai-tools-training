"""Who decides a new request (R17). Pure choice over the rows the caller loaded."""

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.identity.models import Employee


@dataclass(frozen=True)
class Route:
    queue: str  # 'manager' | 'hr'
    assigned_to: Employee | None
    recipients: list[Employee]  # who is emailed and notified


async def hr_approvers(db: AsyncSession, excluding: Employee) -> list[Employee]:
    """HR admins and the deputy (A-14), never the requester."""
    result = await db.scalars(
        select(Employee)
        .where(
            Employee.is_active,
            or_(Employee.role == "hr", Employee.is_hr_deputy),
            Employee.id != excluding.id,
        )
        .order_by(Employee.name, Employee.id)
    )
    return list(result)


async def route_for(db: AsyncSession, employee: Employee) -> Route:
    """Employee -> direct manager; manager -> HR queue. Unspecified cases are refused (A-10)."""
    if employee.role == "hr":
        # An HR admin's own request goes to the deputy (R36, plan 17); not built yet.
        raise ProblemError(
            422,
            "Requests from HR admins cannot be submitted yet.",
            code="ROUTE_UNAVAILABLE",
        )
    if employee.role == "manager":
        approvers = await hr_approvers(db, employee)
        if not approvers:
            raise ProblemError(422, "No HR approver is available. Ask HR.", code="NO_APPROVER")
        return Route("hr", None, approvers)
    manager = await db.get(Employee, employee.manager_id) if employee.manager_id else None
    if manager is None or not manager.is_active:
        raise ProblemError(
            422, "You have no active manager to approve this. Ask HR.", code="NO_APPROVER"
        )
    return Route("manager", manager, [manager])
