"""Admin endpoints for user management"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.auth.dependencies import AdminUser

router = APIRouter(prefix="/admin", tags=["admin"])


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    is_approved: bool
    is_admin: bool
    created_at: str

    class Config:
        from_attributes = True


class UserApprovalRequest(BaseModel):
    """Request to approve/reject a user"""
    user_id: str
    approved: bool


class BulkApprovalRequest(BaseModel):
    """Request to approve/reject multiple users"""
    user_ids: List[str]
    approved: bool


@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    admin: AdminUser,
    db: Session = Depends(get_db),
    pending_only: bool = False,
):
    """
    List all users (admin only).

    Args:
        pending_only: If True, only return users pending approval
    """
    stmt = select(User)
    if pending_only:
        stmt = stmt.where(User.is_approved == False)
    stmt = stmt.order_by(User.created_at.desc())

    result = db.execute(stmt)
    users = result.scalars().all()

    return [
        UserResponse(
            id=u.id,
            email=u.email,
            is_approved=u.is_approved,
            is_admin=u.is_admin,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.get("/users/pending", response_model=List[UserResponse])
def list_pending_users(
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """List users pending approval (admin only)."""
    stmt = select(User).where(User.is_approved == False).order_by(User.created_at.desc())
    result = db.execute(stmt)
    users = result.scalars().all()

    return [
        UserResponse(
            id=u.id,
            email=u.email,
            is_approved=u.is_approved,
            is_admin=u.is_admin,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.post("/users/approve")
def approve_user(
    request: UserApprovalRequest,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """Approve or reject a user (admin only)."""
    stmt = select(User).where(User.id == request.user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_approved = request.approved
    db.commit()

    action = "approved" if request.approved else "rejected"
    return {"message": f"User {user.email} has been {action}"}


@router.post("/users/approve/bulk")
def bulk_approve_users(
    request: BulkApprovalRequest,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """Approve or reject multiple users (admin only)."""
    stmt = select(User).where(User.id.in_(request.user_ids))
    result = db.execute(stmt)
    users = result.scalars().all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found"
        )

    for user in users:
        user.is_approved = request.approved

    db.commit()

    action = "approved" if request.approved else "rejected"
    return {"message": f"{len(users)} users have been {action}"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """Delete a user (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin users"
        )

    email = user.email
    db.delete(user)
    db.commit()

    return {"message": f"User {email} has been deleted"}


@router.post("/users/{user_id}/make-admin")
def make_admin(
    user_id: str,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """Grant admin privileges to a user (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_admin = True
    user.is_approved = True  # Admins are always approved
    db.commit()

    return {"message": f"User {user.email} is now an admin"}


@router.post("/users/{user_id}/remove-admin")
def remove_admin(
    user_id: str,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """Remove admin privileges from a user (admin only)."""
    # Prevent removing your own admin status
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin privileges"
        )

    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_admin = False
    db.commit()

    return {"message": f"User {user.email} is no longer an admin"}
