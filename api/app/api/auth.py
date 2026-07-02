from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import DbSession
from app.schemas import RefreshRequest, TokenPair, UserCreate, UserOut
from app.services.auth import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession):
    service = AuthService(db)
    return await service.register(payload)


@router.post("/token", response_model=TokenPair)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: DbSession):
    service = AuthService(db)
    return await service.login(form_data.username, form_data.password)


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(payload: RefreshRequest, db: DbSession):
    service = AuthService(db)
    return await service.refresh_token(payload)
