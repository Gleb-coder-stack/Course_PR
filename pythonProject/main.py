from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from modules import auth, films, sessions, tickets, reports
from excel_reports import router as excel_router
from models import create_tables, test_connection

app = FastAPI()

# Подключаем все маршруты
app.include_router(auth.router)
app.include_router(films.router)
app.include_router(sessions.router)
app.include_router(tickets.router)
app.include_router(reports.router)
app.include_router(excel_router)

# Статические файлы
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("templates"):
    os.makedirs("templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


# Главная страница (публичная)
@app.get("/")
async def read_root():
    return FileResponse("templates/index.html")


# Панель администратора (только для авторизованных)
@app.get("/admin")
async def admin_dashboard():
    return FileResponse("templates/admin-dashboard.html")


# Панель кассира (только для авторизованных)
@app.get("/cashier")
async def cashier_dashboard():
    return FileResponse("templates/cashier-dashboard.html")


# Страница с детальной информацией о фильме (публичная)
@app.get("/film/{film_id}")
async def film_details(film_id: int):
    # Можно создать отдельный шаблон
    return FileResponse("templates/index.html")


# Проверка здоровья API
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Система управления кинотеатром работает"}


# Инициализация БД при запуске
@app.on_event("startup")
async def startup_event():
    print("🚀 Запуск приложения...")

    # Проверяем подключение к БД
    if test_connection():
        print("✅ Подключение к БД успешно")

        # Создаем таблицы если их нет
        try:
            create_tables()
            print("✅ Таблицы БД проверены/созданы")
        except Exception as e:
            print(f"⚠️ Ошибка создания таблиц: {e}")
    else:
        print("❌ Не удалось подключиться к БД")


# Запуск приложения
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)