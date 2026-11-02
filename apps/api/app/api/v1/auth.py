from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenOut, UserOut
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token(subject=user.id, role=user.role, extra={"email": user.email})
    write_audit(
        db,
        event_type="LOGIN",
        summary=f"Demo login successful for {user.email}",
        status="SUCCESS",
        user_id=user.id,
        user_role=user.role,
    )
    db.commit()

    data = TokenOut(
        access_token=token,
        user=UserOut(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
        ),
    )
    return ok(data.model_dump())


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(
        UserOut(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
        ).model_dump()
    )


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    write_audit(
        db,
        event_type="LOGOUT",
        summary=f"Demo logout for {user.email}",
        status="SUCCESS",
        user_id=user.id,
        user_role=user.role,
    )
    db.commit()
    return ok({"message": "Logged out"})
