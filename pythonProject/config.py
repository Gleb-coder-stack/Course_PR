import os
from datetime import timedelta

# Настройки безопасности
SECRET_KEY = "your-secret-key-for-jwt-tokens-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Роли пользователей
ROLES = {
    "admin": "Администратор",
    "cashier": "Кассир",
    "guest": "Гость"
}

# Разрешения для ролей
PERMISSIONS = {
    "admin": [
        "films:read", "films:create", "films:update", "films:delete",
        "sessions:read", "sessions:create", "sessions:update", "sessions:delete",
        "tickets:read", "tickets:create", "tickets:update", "tickets:delete",
        "reports:generate", "users:manage"
    ],
    "cashier": [
        "films:read", "sessions:read",
        "tickets:read", "tickets:create", "tickets:update",
        "reports:basic"
    ],
    "guest": [
        "films:read", "sessions:read"
    ]
}