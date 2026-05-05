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
from app.models.models import User
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
    if db.query(User).filter(User.mobile_number == payload.mobile_number).first():

        raise HTTPException(
            status_code=200,
            detail={
                "status": False,
                "message": "Mobile number already registered",
                "data": None
            }
        )
    if payload.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(
                status_code=200,
                detail={
                    "status": False,
                    "message": "Email already registered",
                    "data": None
                }
           )

    user = User(
        studio_name=payload.studio_name if payload.studio_name else "User",
        mobile_number=payload.mobile_number,
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New studio registered: %s (id=%s)", user.studio_name, user.id)
    return {
    "status": True,
    "message": "User registered successfully",
    "data": {
        "user_id": str(user.id),
        "studio_name": user.studio_name,
        "mobile_number": user.mobile_number,
        "email": user.email
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# POST /login-user
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/login-user",
    summary="Login with mobile number + password",
)
def login_user(
    
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
    db.query(User)
    .filter(User.mobile_number == payload.mobile_number)
    .first()
    )
    
    if not user:
        raise HTTPException(
            status_code=200,
            detail={
                "status": False,
                "type": "USER_NOT_FOUND",
                "message": "User not found",
                "data": None
            }
        )

 
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=200,
            detail={
                "status": False,
                "type": "INVALID_CREDENTIALS",
                "message": "Invalid password",
                "data": None
            }
        )

    token = create_access_token(subject=str(user.id))
    return {
    "access_token": token,
    "token_type": "bearer",
    "studio_name": user.studio_name,
    "user_id": str(user.id),
    "username": user.username
}
