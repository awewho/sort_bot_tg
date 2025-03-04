from sqlalchemy import ForeignKey, String, BigInteger, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()

engine = create_async_engine(url=os.getenv('DB_URL'))
    
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass



class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[str] = mapped_column(String(20), default="user")  # Значение по умолчанию
    point_id: Mapped[int] = mapped_column(ForeignKey('points.id'), nullable=True)  # Внешний ключ на точку

    # Отношение к точке
    point: Mapped["Point"] = relationship("Point", back_populates="users")


class Point(Base):
    __tablename__ = 'points'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(5), unique=True)  # Уникальный номер точки
    shop_name: Mapped[str] = mapped_column(String(50))
    shop_owner_name: Mapped[str] = mapped_column(String(50))
    phone_number: Mapped[str] = mapped_column(String(15))
    address: Mapped[str] = mapped_column(String(100))
    bags_count: Mapped[int] = mapped_column(Integer)

    cluster_id: Mapped[int] = mapped_column(ForeignKey('clusters.id'))

    # Отношение к пользователям
    users: Mapped[list["User"]] = relationship("User", back_populates="point")


class Cluster(Base):
    __tablename__ = 'clusters'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))




class Log(Base):
    __tablename__ = 'logs'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer)  # ID клиента
    activity: Mapped[str] = mapped_column(String(50))  # Тип активности (например, registration, bag_full, shipment, admin_call)
    question: Mapped[str] = mapped_column(String(255), nullable=True)  # Вопрос (может быть пустым)
    bags_count: Mapped[int] = mapped_column(Integer, nullable=True)  # Количество мешков (может быть пустым)
    alum_kg: Mapped[float] = mapped_column(Float, nullable=True)  # Алюминий (кг)
    alum_price: Mapped[float] = mapped_column(Float, nullable=True)  # Цена алюминия
    alum_total: Mapped[float] = mapped_column(Float, nullable=True)  # Сумма алюминия
    pet_kg: Mapped[float] = mapped_column(Float, nullable=True)  # PET (кг)
    pet_price: Mapped[float] = mapped_column(Float, nullable=True)  # Цена PET
    pet_total: Mapped[float] = mapped_column(Float, nullable=True)  # Сумма PET
    glass_kg: Mapped[float] = mapped_column(Float, nullable=True)  # Стекло (кг)
    glass_price: Mapped[float] = mapped_column(Float, nullable=True)  # Цена стекла
    glass_total: Mapped[float] = mapped_column(Float, nullable=True)  # Сумма стекла
    mixed_kg: Mapped[float] = mapped_column(Float, nullable=True)  # Смешанный мусор (кг)
    mixed_price: Mapped[float] = mapped_column(Float, nullable=True)  # Цена смешанного мусора
    mixed_total: Mapped[float] = mapped_column(Float, nullable=True)  # Сумма смешанного мусора
    total_pay: Mapped[float] = mapped_column(Float, nullable=True)  # Итого к оплате
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Время записи
    

class Shipment(Base):
    __tablename__ = 'shipments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey('points.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    alum_kg: Mapped[float] = mapped_column(Float, default=0.0)
    alum_price: Mapped[float] = mapped_column(Float, default=0.0)
    alum_total: Mapped[float] = mapped_column(Float, default=0.0)
    pet_kg: Mapped[float] = mapped_column(Float, default=0.0)
    pet_price: Mapped[float] = mapped_column(Float, default=0.0)
    pet_total: Mapped[float] = mapped_column(Float, default=0.0)
    glass_kg: Mapped[float] = mapped_column(Float, default=0.0)
    glass_price: Mapped[float] = mapped_column(Float, default=0.0)
    glass_total: Mapped[float] = mapped_column(Float, default=0.0)
    mixed_kg: Mapped[float] = mapped_column(Float, default=0.0)
    mixed_price: Mapped[float] = mapped_column(Float, default=0.0)
    mixed_total: Mapped[float] = mapped_column(Float, default=0.0)
    total_pay: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)