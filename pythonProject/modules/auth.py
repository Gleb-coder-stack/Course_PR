from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import database
from contextlib import contextmanager

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

import bcrypt


def authenticate_user(username: str, password: str):
    """Проверяет логин и пароль пользователя с использованием bcrypt"""
    try:
        with database.get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, role, full_name, hashed_password 
                    FROM users 
                    WHERE username = %s AND is_active = TRUE
                """, (username,))
                user = cur.fetchone()

                if not user:
                    return None

                # Проверяем пароль с bcrypt
                stored_hash = user["hashed_password"]
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode('utf-8')

                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return {
                        "id": user["id"],
                        "username": user["username"],
                        "role": user["role"],
                        "full_name": user["full_name"]
                    }
                else:
                    return None
    except Exception as e:
        print(f"Ошибка аутентификации: {e}")
        return None


# Простая проверка ролей
def check_permission(user: dict, required_permission: str):
    """Проверяет разрешения пользователя"""
    role = user.get("role", "guest")

    # Простая логика проверки прав
    if role == "admin":
        return True  # Админ имеет все права
    elif role == "cashier":
        # Кассир может только читать и создавать билеты
        allowed_permissions = ["films:read", "sessions:read", "tickets:read", "tickets:create"]
        return required_permission in allowed_permissions
    else:
        # Гость может только читать
        allowed_permissions = ["films:read", "sessions:read"]
        return required_permission in allowed_permissions


# Зависимость для получения текущего пользователя
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Получает текущего пользователя по токену"""
    # В упрощенной версии токен = username
    try:
        with database.get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, role, full_name 
                    FROM users 
                    WHERE username = %s AND is_active = TRUE
                """, (token,))
                user = cur.fetchone()

                if not user:
                    raise HTTPException(status_code=401, detail="Недействительные учетные данные")

                return {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "full_name": user["full_name"]
                }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Ошибка аутентификации: {str(e)}")


# Эндпоинты аутентификации
@router.post("/api/auth/login")
async def login(username: str, password: str):
    """Упрощенный вход в систему"""
    user = authenticate_user(username, password)

    if not user:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    # Возвращаем токен = username
    return {
        "access_token": user["username"],
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"],
        "full_name": user["full_name"]
    }


@router.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Получает информацию о текущем пользователе"""
    return current_user
