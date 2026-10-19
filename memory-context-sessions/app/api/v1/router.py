"""Register version 1 API routes."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.todo.router import router as todo_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(todo_router, prefix="/todos", tags=["Todos"])
