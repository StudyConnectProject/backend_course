import uuid
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token

bearer_scheme = HTTPBearer()


@dataclass
class CurrentUser:
    id: uuid.UUID
    role: str  # "student" | "tutor" | "admin"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": "Token inválido o expirado",
                "status_code": 401,
            },
        )
    user_id = payload.get("sub")
    # JWT from auth-service stores roles as array (e.g. ["STUDENT"]).
    # Support both `roles` (array) and `role` (single string).
    raw_roles = payload.get("roles") or []
    if isinstance(raw_roles, list) and raw_roles:
        role = raw_roles[0].lower()
    else:
        role = str(payload.get("role") or "").lower()
    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": "Token no contiene los claims requeridos",
                "status_code": 401,
            },
        )
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": "El claim sub no es un UUID válido",
                "status_code": 401,
            },
        )
    return CurrentUser(id=uid, role=role)


def require_role(allowed_roles: list[str]) -> Callable:
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "No tienes permisos para realizar esta operación",
                    "status_code": 403,
                },
            )
        return current_user

    return role_checker
