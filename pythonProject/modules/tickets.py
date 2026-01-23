# modules/tickets.py
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


# В функции get_tickets заменить запрос:
@router.get("/api/tickets")
async def get_tickets(current_user: dict = Depends(get_current_user)):
    if not check_permission(current_user, "tickets:read"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.id_ticket, t.status, t.price, t.category,
                           t.purchase_date, t.place, t.row_num,
                           m.movie_title, s.data_session, s.start_time,
                           h.hall_name, sc.category_name as seat_category,
                           u.username as sold_by
                    FROM tickets t 
                    JOIN movie m ON t.id_movie = m.id_movie 
                    JOIN session s ON t.id_session = s.id_session
                    JOIN halls h ON s.id_hall = h.id_hall
                    LEFT JOIN seat_categories sc ON t.category = sc.category_name
                    LEFT JOIN users u ON t.id_user = u.id
                    ORDER BY t.id_ticket
                """)
                tickets_data = cur.fetchall()

                tickets = []
                for ticket in tickets_data:
                    tickets.append({
                        "id": ticket["id_ticket"],
                        "session_id": ticket["id_session"],
                        "film_title": ticket["movie_title"],
                        "film_id": ticket["id_movie"],
                        "category": ticket["category"],
                        "status": ticket["status"],
                        "seat": ticket["place"],
                        "row": ticket["row_num"],
                        "price": float(ticket["price"]) if ticket["price"] else 0.0,
                        "date": ticket["data_session"].strftime("%Y-%m-%d") if ticket["data_session"] else None,
                        "time": str(ticket["start_time"])[:5] if ticket["start_time"] else None,
                        "hall": ticket["hall_name"],
                        "seat_category": ticket["seat_category"],
                        "sold_by": ticket["sold_by"],
                        "purchase_date": ticket["purchase_date"].strftime("%Y-%m-%d %H:%M") if ticket["purchase_date"] else None
                    })

                return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения билетов: {str(e)}")


@router.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: int, current_user: dict = Depends(get_current_user)):
    """Получить информацию о конкретном билете"""
    if not check_permission(current_user, "tickets:read"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.*, m.movie_title, s.data_session
                    FROM tickets t 
                    JOIN movie m ON t.id_movie = m.id_movie 
                    JOIN session s ON t.id_session = s.id_session
                    WHERE t.id_ticket = %s
                """, (ticket_id,))

                ticket = cur.fetchone()

                if not ticket:
                    raise HTTPException(status_code=404, detail="Билет не найден")

                return {
                    "id": ticket["id_ticket"],
                    "session_id": ticket["id_session"],
                    "film_title": ticket["movie_title"],
                    "film_id": ticket["id_movie"],
                    "category": ticket["category"],
                    "status": ticket["sold"],
                    "seat": ticket["place"],
                    "row": ticket["row"],
                    "price": float(ticket["price"]) if ticket["price"] else 0.0,
                    "date": ticket["data_session"].strftime("%Y-%m-%d") if ticket["data_session"] else None
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения билета: {str(e)}")


@router.post("/api/tickets")
async def create_ticket(ticket_data: dict, current_user: dict = Depends(get_current_user)):
    """Создать новый билет"""
    if not check_permission(current_user, "tickets:create"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Проверяем существование фильма
                cur.execute("SELECT id_movie FROM movie WHERE movie_title = %s",
                            (ticket_data.get('film_title'),))
                movie = cur.fetchone()

                if not movie:
                    raise HTTPException(status_code=404, detail="Фильм не найден")

                cur.execute("""
                    INSERT INTO tickets (id_session, id_movie, category, price, sold, place, row) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_ticket
                """, (
                    ticket_data.get('session_id'),
                    movie["id_movie"],
                    ticket_data.get('category'),
                    ticket_data.get('price'),
                    ticket_data.get('status', 'free'),
                    ticket_data.get('seat'),
                    ticket_data.get('row')
                ))

                new_id = cur.fetchone()["id_ticket"]
                conn.commit()

                return {"message": "Билет успешно добавлен", "id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания билета: {str(e)}")


@router.put("/api/tickets/{ticket_id}")
async def update_ticket(ticket_id: int, ticket_data: dict, current_user: dict = Depends(get_current_user)):
    """Обновить информацию о билете"""
    if not check_permission(current_user, "tickets:update"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Проверяем существование фильма
                cur.execute("SELECT id_movie FROM movie WHERE movie_title = %s",
                            (ticket_data.get('film_title'),))
                movie = cur.fetchone()

                if not movie:
                    raise HTTPException(status_code=404, detail="Фильм не найден")

                cur.execute("""
                    UPDATE tickets 
                    SET id_session = %s, id_movie = %s, category = %s, price = %s, 
                        sold = %s, place = %s, row = %s 
                    WHERE id_ticket = %s
                """, (
                    ticket_data.get('session_id'),
                    movie["id_movie"],
                    ticket_data.get('category'),
                    ticket_data.get('price'),
                    ticket_data.get('status'),
                    ticket_data.get('seat'),
                    ticket_data.get('row'),
                    ticket_id
                ))

                conn.commit()

                return {"message": "Билет успешно обновлен"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления билета: {str(e)}")


@router.delete("/api/tickets/{ticket_id}")
async def delete_ticket(ticket_id: int, current_user: dict = Depends(get_current_user)):
    """Удалить билет"""
    if not check_permission(current_user, "tickets:delete"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Проверяем существование билета
                cur.execute("SELECT id_ticket FROM tickets WHERE id_ticket = %s", (ticket_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Билет не найден")

                cur.execute("DELETE FROM tickets WHERE id_ticket = %s", (ticket_id,))
                conn.commit()

                return {"message": "Билет успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления билета: {str(e)}")


# Получить билеты по сеансу
@router.get("/api/sessions/{session_id}/tickets")
async def get_tickets_by_session(session_id: int, current_user: dict = Depends(get_current_user)):
    """Получить все билеты для конкретного сеанса"""
    if not check_permission(current_user, "tickets:read"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.*, m.movie_title 
                    FROM tickets t 
                    JOIN movie m ON t.id_movie = m.id_movie 
                    WHERE t.id_session = %s
                    ORDER BY t.row, t.place
                """, (session_id,))

                tickets_data = cur.fetchall()
                tickets = []

                for ticket in tickets_data:
                    tickets.append({
                        "id": ticket["id_ticket"],
                        "session_id": ticket["id_session"],
                        "film_title": ticket["movie_title"],
                        "film_id": ticket["id_movie"],
                        "category": ticket["category"],
                        "status": ticket["sold"],
                        "seat": ticket["place"],
                        "row": ticket["row"],
                        "price": float(ticket["price"]) if ticket["price"] else 0.0
                    })

                return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения билетов: {str(e)}")


# Продать билет (изменить статус на 'sold')
@router.post("/api/tickets/{ticket_id}/sell")
async def sell_ticket(ticket_id: int, current_user: dict = Depends(get_current_user)):
    """Продать билет (изменить статус на 'sold')"""
    if not check_permission(current_user, "tickets:update"):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Проверяем существование билета
                cur.execute("SELECT id_ticket, sold FROM tickets WHERE id_ticket = %s", (ticket_id,))
                ticket = cur.fetchone()

                if not ticket:
                    raise HTTPException(status_code=404, detail="Билет не найден")

                if ticket["sold"] == "sold":
                    raise HTTPException(status_code=400, detail="Билет уже продан")

                cur.execute("""
                    UPDATE tickets 
                    SET sold = 'sold' 
                    WHERE id_ticket = %s
                """, (ticket_id,))

                conn.commit()

                return {"message": "Билет успешно продан"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка продажи билета: {str(e)}")