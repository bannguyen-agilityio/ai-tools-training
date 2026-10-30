"""Build one calendar entry per viewer (R27, spec 6.1, §8).

The masked shape is built from scratch rather than stripped from the full one, so a forbidden
field cannot leak by being added to the full entry later.
"""

import uuid
from datetime import date

from app.modules.calendar.schemas import LeaveEntry, OffEntry
from app.modules.identity.models import Employee
from app.modules.requests.redaction import SENSITIVE_TYPES


def entry_for(
    viewer: Employee,
    *,
    employee_id: uuid.UUID,
    employee_name: str,
    day: date,
    slot: str,
    leave_type: str,
    status: str,
) -> OffEntry | LeaveEntry:
    full = viewer.role == "hr" or viewer.id == employee_id
    if leave_type in SENSITIVE_TYPES and not full:
        return OffEntry.model_validate(
            {"employee_id": employee_id, "employee_name": employee_name, "date": day, "slot": slot}
        )
    return LeaveEntry.model_validate(
        {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "date": day,
            "slot": slot,
            "leave_type": leave_type,
            "status": status,
        }
    )
