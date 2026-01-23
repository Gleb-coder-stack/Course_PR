import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

def get_db_connection():
    """Создает подключение к вашей БД cinema_management"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="cinema_management",  # Изменено с cinema2
            user="postgres",
            port=5432,
            client_encoding='UTF8',
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД cinema_management: {e}")
        raise

@contextmanager
def get_db():
    """Контекстный менеджер для работы с БД"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        if conn:
            conn.close()