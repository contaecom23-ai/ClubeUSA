from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from asyncpg import Connection

from app.database import get_conn
from app.models.user import ProfileResponse, ProfileUpdateRequest, MessageResponse
from app.utils.security import decode_access_token

router = APIRouter(prefix="/api/profile", tags=["profile"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Valida o Bearer token JWT e retorna o user_id. Nunca confiar no ID do request body."""
    token = credentials.credentials
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_verified_user(
    user_id: str = Depends(get_current_user_id),
    conn: Connection = Depends(get_conn),
):
    """Busca o usuário ativo no banco. Retorna 404 se não existir (IDOR-safe)."""
    row = await conn.fetchrow(
        """
        SELECT id, email, email_confirmed, full_name, zip_code, phone,
               created_at, last_login_at
        FROM users
        WHERE id = $1 AND is_active = TRUE
        """,
        user_id,  # vem do token, nunca do request
    )
    if not row:
        # 404 intencional: não revela se conta foi desativada vs. nunca existiu
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return row


# ---------------------------------------------------------------------------
# GET /api/profile/me
# ---------------------------------------------------------------------------
@router.get("/me", response_model=ProfileResponse)
async def get_profile(user=Depends(get_verified_user)):
    return ProfileResponse(
        id=str(user["id"]),
        email=user["email"],
        email_confirmed=user["email_confirmed"],
        full_name=user["full_name"],
        zip_code=user["zip_code"],
        phone=user["phone"],
        created_at=user["created_at"],
        last_login_at=user["last_login_at"],
    )


# ---------------------------------------------------------------------------
# PUT /api/profile/me
# ---------------------------------------------------------------------------
@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    conn: Connection = Depends(get_conn),
):
    # Só atualiza campos enviados (PATCH semântico via PUT parcial)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar.",
        )

    set_clauses = ", ".join(f"{col} = ${i + 2}" for i, col in enumerate(updates.keys()))
    values = list(updates.values())

    row = await conn.fetchrow(
        f"""
        UPDATE users
        SET {set_clauses}
        WHERE id = $1 AND is_active = TRUE
        RETURNING id, email, email_confirmed, full_name, zip_code, phone, created_at, last_login_at
        """,
        user_id,
        *values,
    )

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    return ProfileResponse(
        id=str(row["id"]),
        email=row["email"],
        email_confirmed=row["email_confirmed"],
        full_name=row["full_name"],
        zip_code=row["zip_code"],
        phone=row["phone"],
        created_at=row["created_at"],
        last_login_at=row["last_login_at"],
    )
