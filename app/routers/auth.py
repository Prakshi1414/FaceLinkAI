#api auth

# app/routers/auth.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /register-user
# POST /login-user
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import RegisterUser
from app.schemas.schemas import (
    LoginRequest,
    RegisterUserRequest,
    RegisterUserResponse,
    TokenResponse,
)
from app.utils.auth import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["Auth"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# POST /register-user
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/register-user",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new studio account",
)
def register_user(
    payload: RegisterUserRequest,
    db: Session = Depends(get_db),
):
    # Check uniqueness
    if db.query(RegisterUser).filter(RegisterUser.mobile_number == payload.mobile_number).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mobile number already registered.",
        )
    if payload.email:
        if db.query(RegisterUser).filter(RegisterUser.email == payload.email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

    user = RegisterUser(
        studio_name=payload.studio_name,
        mobile_number=payload.mobile_number,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New studio registered: %s (id=%s)", user.studio_name, user.id)
    return user


# ─────────────────────────────────────────────────────────────────────────────
# POST /login-user
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/login-user",
    response_model=TokenResponse,
    summary="Login with mobile number + password",
)
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(RegisterUser)
        .filter(RegisterUser.mobile_number == payload.mobile_number)
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number or password.",
        )

    token = create_access_token(subject=str(user.id))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        studio_name=user.studio_name,
        user_id=user.id,
    )
