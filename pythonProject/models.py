from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey, Numeric, Text, Boolean, DateTime, DECIMAL
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import sessionmaker
import bcrypt
from datetime import datetime

POSTGRESQL_DATABASE_URL = "postgresql+psycopg2://postgres@localhost:5432/cinema_management"
engine = create_engine(POSTGRESQL_DATABASE_URL)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="guest")
    is_active = Column(Boolean, default=True)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))


class Movie(Base):
    __tablename__ = "movie"

    id_movie = Column(Integer, primary_key=True, index=True)
    movie_title = Column(String(255))
    movie_description = Column(Text)
    duration_minutes = Column(Integer)
    genre = Column(String(100))
    age_rating = Column(String(10))
    release_year = Column(Integer)
    director = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="movie")


class Hall(Base):
    __tablename__ = "halls"

    id_hall = Column(Integer, primary_key=True, index=True)
    hall_name = Column(String(50))
    capacity = Column(Integer)
    description = Column(Text)
    has_3d = Column(Boolean, default=False)
    has_dolby = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    sessions = relationship("Session", back_populates="hall")
    seats = relationship("Seat", back_populates="hall")


class SeatCategory(Base):
    __tablename__ = "seat_categories"

    id_category = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(50))
    price_multiplier = Column(Numeric(3, 2), default=1.0)
    description = Column(Text)

    seats = relationship("Seat", back_populates="category")


class Seat(Base):
    __tablename__ = "seats"

    id_seat = Column(Integer, primary_key=True, index=True)
    id_hall = Column(Integer, ForeignKey('halls.id_hall'))
    row_number = Column(Integer)
    seat_number = Column(Integer)
    id_category = Column(Integer, ForeignKey('seat_categories.id_category'))
    is_active = Column(Boolean, default=True)

    hall = relationship("Hall", back_populates="seats")
    category = relationship("SeatCategory", back_populates="seats")
    tickets = relationship("Ticket", back_populates="seat")


class Session(Base):
    __tablename__ = "session"

    id_session = Column(Integer, primary_key=True, index=True)
    id_movie = Column(Integer, ForeignKey('movie.id_movie'))
    id_hall = Column(Integer, ForeignKey('halls.id_hall'))
    data_session = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    ticket_price = Column(Numeric(10, 2))
    session_type = Column(String(20), default='regular')
    max_tickets = Column(Integer)
    sold_tickets = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    movie = relationship("Movie", back_populates="sessions")
    hall = relationship("Hall", back_populates="sessions")
    tickets = relationship("Ticket", back_populates="session")


class Ticket(Base):
    __tablename__ = "tickets"

    id_ticket = Column(Integer, primary_key=True, index=True)
    id_session = Column(Integer, ForeignKey('session.id_session'))
    id_movie = Column(Integer, ForeignKey('movie.id_movie'))
    id_seat = Column(Integer, ForeignKey('seats.id_seat'))
    id_user = Column(Integer, ForeignKey('users.id'))
    category = Column(String(50))
    price = Column(Numeric(10, 2))
    status = Column(String(20), default='available')
    purchase_date = Column(DateTime)
    place = Column(Integer)
    row_num = Column(Integer)
    qr_code = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="tickets")
    movie = relationship("Movie")
    seat = relationship("Seat", back_populates="tickets")
    user = relationship("User")


class Sale(Base):
    __tablename__ = "sales"

    id_sale = Column(Integer, primary_key=True, index=True)
    id_ticket = Column(Integer, ForeignKey('tickets.id_ticket'))
    id_user = Column(Integer, ForeignKey('users.id'))
    sale_amount = Column(Numeric(10, 2))
    payment_method = Column(String(20), default='cash')
    sale_date = Column(DateTime, default=datetime.utcnow)
    is_returned = Column(Boolean, default=False)
    return_date = Column(DateTime)
    return_reason = Column(Text)


SessionLocal = sessionmaker(autoflush=False, bind=engine)


def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы успешно созданы")

        db = SessionLocal()
        try:
            import bcrypt

            # Проверяем есть ли администратор
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
                admin = User(
                    username="admin",
                    email="admin@cinema.ru",
                    hashed_password=hashed_pw.decode('utf-8'),
                    role="admin",
                    full_name="Администратор Системы"
                )
                db.add(admin)

            # Проверяем есть ли кассир
            cashier = db.query(User).filter(User.username == "cashier").first()
            if not cashier:
                hashed_pw = bcrypt.hashpw("cashier123".encode('utf-8'), bcrypt.gensalt())
                cashier = User(
                    username="cashier",
                    email="cashier@cinema.ru",
                    hashed_password=hashed_pw.decode('utf-8'),
                    role="cashier",
                    full_name="Кассир Иванова"
                )
                db.add(cashier)

            # Создаем тестовые категории мест
            categories = db.query(SeatCategory).all()
            if not categories:
                basic = SeatCategory(
                    category_name="Обычное",
                    price_multiplier=1.0,
                    description="Стандартное место"
                )
                vip = SeatCategory(
                    category_name="VIP",
                    price_multiplier=1.5,
                    description="Премиум место"
                )
                db.add(basic)
                db.add(vip)

            db.commit()
            print("✅ Тестовые данные созданы")

        except Exception as e:
            print(f"⚠️ Ошибка создания тестовых данных: {e}")
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")


def test_connection():
    try:
        with engine.connect() as connection:
            print("✅ Подключение к PostgreSQL успешно")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


if __name__ == "__main__":
    test_connection()
    create_tables()