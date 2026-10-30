import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.router import client_ip
from app.modules.employees.dependencies import HrUser
from app.modules.teams import service
from app.modules.teams.schemas import TeamCreate, TeamList, TeamOut, TeamPatch

router = APIRouter(prefix="/api/v1/hr/teams", tags=["teams"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=TeamList)
async def list_teams(user: HrUser, db: DB) -> TeamList:
    """Teams are few, so there is never a next page."""
    return TeamList(items=[TeamOut.model_validate(t) for t in await service.list_all(db, user)])


@router.post("", response_model=TeamOut, status_code=201)
async def create_team(
    body: TeamCreate, request: Request, response: Response, user: HrUser, db: DB
) -> TeamOut:
    team = await service.create(db, user, body, client_ip(request))
    response.headers["Location"] = f"/api/v1/hr/teams/{team.id}"
    return TeamOut.model_validate(team)


@router.patch("/{team_id}", response_model=TeamOut)
async def update_team(
    team_id: uuid.UUID, body: TeamPatch, request: Request, user: HrUser, db: DB
) -> TeamOut:
    return TeamOut.model_validate(await service.update(db, user, team_id, body, client_ip(request)))
