# modules/sessions.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
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


# В функции get_sessions заменить запрос:
@router.get("/api/sessions")
async def get_sessions(date: str = None, current_user: dict = Depends(get_current_user)):
    if not check_permission(current_user, "sessions:read"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                if date:
                    cur.execute("""
                        SELECT s.id_session, s.data_session, s.start_time, s.end_time,
                               s.ticket_price, s.session_type, s.sold_tickets, s.max_tickets,
                               m.movie_title, m.duration_minutes,
                               h.hall_name, h.capacity
                        FROM session s 
                        JOIN movie m ON s.id_movie = m.id_movie 
                        JOIN halls h ON s.id_hall = h.id_hall
                        WHERE s.data_session = %s 
                        ORDER BY s.start_time
                    """, (date,))
                else:
                    cur.execute("""
                        SELECT s.id_session, s.data_session, s.start_time, s.end_time,
                               s.ticket_price, s.session_type, s.sold_tickets, s.max_tickets,
                               m.movie_title, m.duration_minutes,
                               h.hall_name, h.capacity
                        FROM session s 
                        JOIN movie m ON s.id_movie = m.id_movie 
                        JOIN halls h ON s.id_hall = h.id_hall
                        ORDER BY s.data_session, s.start_time
                    """)

                sessions_data = cur.fetchall()
                sessions = []
                for session in sessions_data:
                    sessions.append({
                        "id": session["id_session"],
                        "film_title": session["movie_title"],
                        "film_id": session["id_movie"],
                        "date": session["data_session"].strftime("%Y-%m-%d"),
                        "start": str(session["start_time"]),
                        "end": str(session["end_time"]),
                        "duration": session["duration_minutes"],
                        "hall": session["hall_name"],
                        "hall_id": session["id_hall"],
                        "capacity": session["capacity"],
                        "price": float(session["ticket_price"]) if session["ticket_price"] else 0,
                        "type": session["session_type"],
                        "sold_tickets": session["sold_tickets"],
                        "max_tickets": session["max_tickets"]
                    })

                return sessions
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: int, current_user: dict = Depends(get_current_user)):
    """Получить информацию о конкретном сеансе"""
    if not check_permission(current_user, "sessions:read"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.*, m.movie_title 
                    FROM session s 
                    JOIN movie m ON s.id_movie = m.id_movie 
                    WHERE s.id_session = %s
                """, (session_id,))
                session = cur.fetchone()

                if not session:
                    raise HTTPException(status_code=404, detail="Сеанс не найден")

                return {
                    "id": session["id_session"],
                    "film_title": session["movie_title"],
                    "film_id": session["id_movie"],
                    "date": session["data_session"].strftime("%Y-%m-%d"),
                    "start": str(session["start"]),
                    "end": str(session["final"]),
                    "hall": session["hall"]
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения сеанса: {str(e)}")


@router.post("/api/sessions")
async def create_session(session_data: dict, current_user: dict = Depends(get_current_user)):
    """Создать новый сеанс"""
    if not check_permission(current_user, "sessions:create"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Проверяем существование фильма
                cur.execute("SELECT id_movie FROM movie WHERE movie_title = %s",
                            (session_data.get('film_title'),))
                movie = cur.fetchone()

                if not movie:
                    raise HTTPException(status_code=404, detail="Фильм не найден")

                cur.execute("""
                    INSERT INTO session (id_movie, data_session, start, final, hall) 
                    VALUES (%s, %s, %s, %s, %s) RETURNING id_session
                """, (
                    movie["id_movie"],
                    session_data.get('date'),
                    session_data.get('start'),
                    session_data.get('end'),
                    session_data.get('hall', 1)
                ))

                new_id = cur.fetchone()["id_session"]
                conn.commit()

                return {"message": "Сеанс успешно добавлен", "id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания сеанса: {str(e)}")


@router.put("/api/sessions/{session_id}")
async def update_session(session_id: int, session_data: dict, current_user: dict = Depends(get_current_user)):
    """Обновить информацию о сеансе"""
    if not check_permission(current_user, "sessions:update"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Проверяем существование фильма
                cur.execute("SELECT id_movie FROM movie WHERE movie_title = %s",
                            (session_data.get('film_title'),))
                movie = cur.fetchone()

                if not movie:
                    raise HTTPException(status_code=404, detail="Фильм не найден")

                cur.execute("""
                    UPDATE session 
                    SET id_movie = %s, data_session = %s, start = %s, final = %s, hall = %s 
                    WHERE id_session = %s
                """, (
                    movie["id_movie"],
                    session_data.get('date'),
                    session_data.get('start'),
                    session_data.get('end'),
                    session_data.get('hall', 1),
                    session_id
                ))

                conn.commit()

                return {"message": "Сеанс успешно обновлен"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления сеанса: {str(e)}")


@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int, current_user: dict = Depends(get_current_user)):
    """Удалить сеанс"""
    if not check_permission(current_user, "sessions:delete"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Проверяем существование сеанса
                cur.execute("SELECT id_session FROM session WHERE id_session = %s", (session_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Сеанс не найден")

                cur.execute("DELETE FROM tickets WHERE id_session = %s", (session_id,))
                cur.execute("DELETE FROM session WHERE id_session = %s", (session_id,))

                conn.commit()

                return {"message": "Сеанс успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления сеанса: {str(e)}")


# Получить сеансы по дате
@router.get("/api/sessions/date/{date}")
async def get_sessions_by_date(date: str, current_user: dict = Depends(get_current_user)):
    """Получить сеансы на определенную дату"""
    if not check_permission(current_user, "sessions:read"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.*, m.movie_title 
                    FROM session s 
                    JOIN movie m ON s.id_movie = m.id_movie 
                    WHERE s.data_session = %s 
                    ORDER BY s.start
                """, (date,))

                sessions_data = cur.fetchall()
                sessions = []

                for session in sessions_data:
                    sessions.append({
                        "id": session["id_session"],
                        "film_title": session["movie_title"],
                        "film_id": session["id_movie"],
                        "date": session["data_session"].strftime("%Y-%m-%d"),
                        "start": str(session["start"]),
                        "end": str(session["final"]),
                        "hall": session["hall"]
                    })

                return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения сеансов: {str(e)}")