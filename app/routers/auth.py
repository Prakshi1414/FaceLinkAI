#api auth

# app/routers/auth.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /register-user
# POST /login-user
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
from app.schemas.schemas import ApiResponse, RegisterUserResponse , TokenResponse
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
    response_model=ApiResponse[RegisterUserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new studio account",    
)   
def register_user(
    payload: RegisterUserRequest,
    db: Session = Depends(get_db),
):
    # Check uniqueness
    if db.query(User).filter(User.mobile_number == payload.mobile_number).first():

         return {
            "status": False,
            "message": "Mobile number already registered",
            "data": None
        }
 
        
    if payload.email:
        if db.query(User).filter(User.email == payload.email).first():
            return {
            "status": False,
            "message": "Email already registered",
            "data": None
        }
    allowed_roles = ["studio", "client", "relative"]

    if payload.role not in allowed_roles:
        return {
            "status": False,
            "message": "Invalid role",
            "data": None
        }
    
    if payload.role == "studio" and not payload.studio_name:
        return {
            "status": False,
            "message": "Studio name is required",
            "data": None
        }
    
    user = User(
        studio_name = payload.studio_name if payload.role == "studio" else None,
        mobile_number=payload.mobile_number,
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New studio registered: %s (id=%s)", user.studio_name, user.id)
    return {
        "status": True,
        "message": "User registered successfully",
        "data": {
            "id": user.id,
            "studio_name": user.studio_name,
            "mobile_number": user.mobile_number,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /login-user
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/login-user",
    response_model=ApiResponse[dict],
)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.mobile_number == payload.mobile_number
    ).first()

    if not user:
        return {
            "status": False,
            "message": "User not found",
            "data": {
                "field": "mobile_number",
                "type": "user_not_found"
            }
        }

    if not verify_password(payload.password, user.password_hash):
        return {
            "status": False,
            "message": "Invalid password",
            "data": {
                "field": "password",
                "type": "invalid_credentials"
            }
        }

    token = create_access_token(subject=str(user.id), role=user.role)

    return {
        "status": True,
        "message": "Login successful",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "studio_name": user.studio_name,
            "user_id": str(user.id),
            "username": user.username,
            "role":user.role
        }
    }
