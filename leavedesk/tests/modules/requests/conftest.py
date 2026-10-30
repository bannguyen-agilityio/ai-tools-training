from datetime import date

import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.balances.me_router import get_today
from tests.conftest import Login, MakeLogin
from tests.modules.balances.test_ledger_jobs import seed_year

TODAY = date(2026, 6, 1)  # a Monday


@pytest.fixture(autouse=True)
def fixed_today(app: FastAPI) -> None:
    app.dependency_overrides[get_today] = lambda: TODAY


async def set_manager(owner: AsyncEngine, emp: Login, mgr: Login) -> None:
    async with owner.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET manager_id = :m WHERE id = :e"),
            {"m": mgr.employee_id, "e": emp.employee_id},
        )


@pytest.fixture
async def staff(make_login: MakeLogin, owner_engine: AsyncEngine) -> tuple[Login, Login]:
    """An employee with a manager and 12 Annual days."""
    emp, mgr = await make_login(), await make_login("manager")
    await set_manager(owner_engine, emp, mgr)
    await seed_year(owner_engine, emp.employee_id, "entitlement", "12")
    return emp, mgr
