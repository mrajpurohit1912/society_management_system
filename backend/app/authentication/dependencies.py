import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.authentication.security import TokenService
from app.authentication.repository import UserRepository
from app.authentication.models import UserModel
from app.societies.models import UserSocietyRoleModel, SocietyRole

security_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> UserModel:
    """
    FastAPI dependency that extracts the bearer token, decodes it,
    verifies its signature and expiry, and retrieves the UserModel from the DB.
    """
    token = credentials.credentials
    try:
        payload = TokenService.verify_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token: Missing subject claim."
            )
        user_id = uuid.UUID(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired."
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token."
        )
        
    repo = UserRepository(db)
    user = await repo.check_user_exist(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    return user


async def require_platform_admin(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    FastAPI dependency requiring the user to be a global platform admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Platform administrative privileges required."
        )
    return current_user


async def require_society_admin(
    society_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> UserModel:
    """
    FastAPI dependency requiring the user to be either a global platform admin
    OR a local society administrator for the specified society.
    """
    # 1. Global Admin bypass
    if current_user.role == "admin":
        return current_user
        
    # 2. Check society-specific role mapping
    query = select(UserSocietyRoleModel).where(
        UserSocietyRoleModel.user_id == current_user.user_id,
        UserSocietyRoleModel.society_id == society_id
    )
    result = await db.execute(query)
    role_mapping = result.scalar_one_or_none()
    
    if not role_mapping or role_mapping.role != SocietyRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Society administrative privileges required for this action."
        )
        
    return current_user

