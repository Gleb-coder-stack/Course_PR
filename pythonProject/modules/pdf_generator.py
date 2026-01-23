# pdf_generator.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import database
from contextlib import contextmanager
from datetime import datetime
import io
import os

router = APIRouter()


@contextmanager
def get_db():
    conn = database.get_db_connection()
    try:
        yield conn
    finally:
        if conn:
            conn.close()


def create_simple_pdf(ticket):
    """Создает PDF билет с поддержкой русских букв"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A6
    from reportlab.lib.colors import black, white, red, blue, yellow
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Регистрируем шрифты с поддержкой кириллицы
    try:
        # Попробуем использовать стандартные системные шрифты
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux Bold
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux Bold
            "C:/Windows/Fonts/arial.ttf",  # Windows
            "C:/Windows/Fonts/arialbd.ttf",  # Windows Bold
            "C:/Windows/Fonts/tahoma.ttf",  # Windows
            "C:/Windows/Fonts/tahomabd.ttf",  # Windows Bold
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/System/Library/Fonts/Arial Bold.ttf",  # macOS Bold
        ]

        registered_fonts = False
        regular_font = None
        bold_font = None

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    if 'Bold' in font_path or 'bd' in font_path.lower():
                        if not bold_font:
                            pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', font_path))
                            bold_font = True
                    else:
                        if not regular_font:
                            pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
                            regular_font = True

                    if regular_font and bold_font:
                        registered_fonts = True
                        break
                except Exception as e:
                    print(f"Ошибка регистрации шрифта {font_path}: {e}")
                    continue

        # Если не нашли подходящие шрифты, используем встроенные
        if not registered_fonts:
            print("Используются стандартные шрифты Helvetica")
            # Будем использовать Helvetica, которая поддерживает базовую кириллицу в ReportLab

    except Exception as e:
        print(f"Font registration warning: {e}")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A6)
    width, height = A6

    # Фон
    p.setFillColor(white)
    p.rect(0, 0, width, height, fill=1)
    p.setFillColor(black)

    # Заголовок - БИЛЕТ В КИНО
    try:
        p.setFont("CyrillicFont-Bold", 18)
    except:
        p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 35, "БИЛЕТ В КИНО")

    # Разделительная линия
    p.setStrokeColor(red)
    p.setLineWidth(1)
    p.line(20, height - 50, width - 20, height - 50)

    # Основная информация о фильме
    try:
        p.setFont("CyrillicFont-Bold", 12)
    except:
        p.setFont("Helvetica-Bold", 12)

    # Название фильма
    movie_title = str(ticket.get('movie_title', 'Название не указано'))
    p.drawCentredString(width / 2, height - 70, movie_title[:30])

    # Информация о сеансе
    try:
        p.setFont("CyrillicFont", 10)
    except:
        p.setFont("Helvetica", 10)

    y_position = height - 90

    # Дата
    p.drawString(20, y_position, "ДАТА:")
    date_str = ticket['data_session'].strftime("%d.%m.%Y") if ticket.get('data_session') else "N/A"
    p.drawString(60, y_position, date_str)

    # Время
    y_position -= 15
    p.drawString(20, y_position, "ВРЕМЯ:")
    start_time = str(ticket['start'])[:5] if ticket.get('start') else "N/A"
    end_time = str(ticket['final'])[:5] if ticket.get('final') else "N/A"
    p.drawString(60, y_position, f"{start_time}-{end_time}")

    # Зал и тип
    y_position -= 15
    p.drawString(20, y_position, "ЗАЛ:")
    hall = str(ticket.get('hall', 'N/A'))
    p.drawString(60, y_position, hall)

    p.drawString(width / 2, y_position, "ТИП:")
    category_text = str(ticket.get('category', 'N/A'))
    # Перевод статусов на русский
    if category_text.lower() == "sold":
        category_text = "Продан"
    elif category_text.lower() == "free":
        category_text = "Свободен"
    elif category_text.lower() == "premium":
        category_text = "Премиум"
    p.drawString(width / 2 + 30, y_position, category_text[:10])

    # Место - только РЯД X МЕСТО Y по центру
    y_position -= 25
    try:
        p.setFont("CyrillicFont-Bold", 14)
    except:
        p.setFont("Helvetica-Bold", 14)

    row = ticket.get('row', 'N/A')
    place = ticket.get('place', 'N/A')
    p.drawCentredString(width / 2, y_position, f"РЯД {row} МЕСТО {place}")

    # Цена - выделенный блок
    y_position -= 35
    p.setFillColor(blue)
    p.rect(20, y_position, width - 40, 25, fill=1, stroke=0)
    p.setFillColor(white)
    try:
        p.setFont("CyrillicFont-Bold", 14)
    except:
        p.setFont("Helvetica-Bold", 14)

    price = float(ticket.get('price', 0))
    p.drawCentredString(width / 2, y_position + 8, f"ЦЕНА: {price:.2f} РУБ")

    # Посадочный талон
    y_position -= 40
    p.setFillColor(yellow)
    p.rect(20, y_position, width - 40, 35, fill=1, stroke=0)
    p.setFillColor(black)

    try:
        p.setFont("CyrillicFont-Bold", 12)
    except:
        p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2, y_position + 20, "ПОСАДОЧНЫЙ ТАЛОН")

    try:
        p.setFont("CyrillicFont", 10)
    except:
        p.setFont("Helvetica", 10)
    p.drawCentredString(width / 2, y_position + 5, f"ЗАЛ {hall} РЯД {row} МЕСТО {place}")

    # ID и дата генерации
    y_position -= 25
    try:
        p.setFont("CyrillicFont", 8)
    except:
        p.setFont("Helvetica", 8)

    ticket_id = ticket.get('id_ticket', 'N/A')
    p.drawString(20, y_position, f"ID: {ticket_id}")
    p.drawString(20, y_position - 10, f"Сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


# Генерация PDF билета
@router.get("/ticket-pdf/{ticket_id}")
async def generate_ticket_pdf(ticket_id: int):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.*, m.movie_title, s.data_session, s.start, s.final, s.hall
                    FROM tickets t 
                    JOIN movie m ON t.id_movie = m.id_movie 
                    JOIN session s ON t.id_session = s.id_session
                    WHERE t.id_ticket = %s
                """, (ticket_id,))
                ticket = cur.fetchone()

        if not ticket:
            raise HTTPException(status_code=404, detail="Билет не найден")

        # Проверяем статус билета
        sold_status = ticket.get("sold")
        if sold_status != "sold" and sold_status != "Продан":
            raise HTTPException(status_code=400, detail="PDF доступен только для проданных билетов")

        # Создаем PDF
        pdf_buffer = create_simple_pdf(ticket)

        filename = f"ticket_{ticket_id}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации PDF: {str(e)}")


# Получить информацию о билете
@router.get("/api/ticket-info/{ticket_id}")
async def get_ticket_info(ticket_id: int):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.*, m.movie_title, s.data_session, s.start, s.final, s.hall
                    FROM tickets t 
                    JOIN movie m ON t.id_movie = m.id_movie 
                    JOIN session s ON t.id_session = s.id_session
                    WHERE t.id_ticket = %s
                """, (ticket_id,))
                ticket = cur.fetchone()

        if not ticket:
            raise HTTPException(status_code=404, detail="Билет не найден")

        # Перевод статусов на русский
        status = ticket.get("sold", "")
        if status == "sold":
            status = "Продан"
        elif status == "free":
            status = "Свободен"

        category = ticket.get("category", "")
        if category == "sold":
            category = "Продан"
        elif category == "free":
            category = "Свободен"
        elif category == "premium":
            category = "Премиум"

        return {
            "id": ticket.get("id_ticket"),
            "film_title": ticket.get("movie_title"),
            "date": ticket.get("data_session").strftime("%d.%m.%Y") if ticket.get("data_session") else "N/A",
            "start": str(ticket.get("start"))[:5] if ticket.get("start") else "N/A",
            "end": str(ticket.get("final"))[:5] if ticket.get("final") else "N/A",
            "hall": ticket.get("hall"),
            "category": category,
            "status": status,
            "seat": ticket.get("place"),
            "row": ticket.get("row"),
            "price": float(ticket.get("price", 0)),
            "can_generate_pdf": status == "Продан"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации: {str(e)}")