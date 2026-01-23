from fastapi import APIRouter, HTTPException, Depends
import database
from contextlib import contextmanager
from modules.auth import get_current_user, check_permission

router = APIRouter()


@contextmanager
def get_db():
    conn = database.get_db_connection()
    try:
        yield conn
    finally:
        if conn:
            conn.close()


@router.get("/api/halls")
async def get_halls(current_user: dict = Depends(get_current_user)):
    if not check_permission(current_user, "halls:read"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT h.*, 
                           COUNT(s.id_seat) as total_seats,
                           COUNT(CASE WHEN s.is_active THEN 1 END) as active_seats
                    FROM halls h
                    LEFT JOIN seats s ON h.id_hall = s.id_hall
                    GROUP BY h.id_hall
                    ORDER BY h.hall_name
                """)
                halls_data = cur.fetchall()

                halls = []
                for hall in halls_data:
                    halls.append({
                        "id": hall["id_hall"],
                        "name": hall["hall_name"],
                        "capacity": hall["capacity"],
                        "description": hall["description"],
                        "has_3d": hall["has_3d"],
                        "has_dolby": hall["has_dolby"],
                        "is_active": hall["is_active"],
                        "total_seats": hall["total_seats"],
                        "active_seats": hall["active_seats"]
                    })

                return halls
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения залов: {str(e)}")