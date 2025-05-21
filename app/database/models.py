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
    
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey('points.point_id'), nullable=True)  # Внешний ключ на точку

    # Отношение к точке
    point: Mapped["Point"] = relationship("Point", back_populates="users")


class Point(Base):
    __tablename__ = 'points'
    
    point_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    point_name: Mapped[str] = mapped_column(String(50))
    point_owner_name: Mapped[str] = mapped_column(String(50))
    phone_number: Mapped[str] = mapped_column(String(15))
    address: Mapped[str] = mapped_column(String(100))
    bags_count: Mapped[int] = mapped_column(Integer)

    zone_id: Mapped[int] = mapped_column(ForeignKey('zones.zone_id'))

    # Отношение к пользователям
    zone: Mapped["Zone"] = relationship("Zone", back_populates="points")
    users: Mapped[list["User"]] = relationship("User", back_populates="point")
    requests: Mapped[list["Request"]] = relationship("Request")
    shipments: Mapped[list["Shipment"]] = relationship("Shipment")


class Zone(Base):
    __tablename__ = 'zones'
    
    zone_id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[int] = mapped_column(ForeignKey('regions.region_id'))

    #Отношение к точке
    points: Mapped[list["Point"]] = relationship("Point", back_populates="zone")



class Region(Base):
    __tablename__ = 'regions'
    
    region_id: Mapped[int] = mapped_column(primary_key=True)
    

class Request(Base):
    __tablename__ = 'requests'

    request_id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Время записи
    point_id: Mapped[int] = mapped_column(ForeignKey('points.point_id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id')) 
    activity: Mapped[str] = mapped_column(String(50))  # Тип активности
    pet_bag: Mapped[int] = mapped_column(Integer, nullable=True)  # Количество мешков с пластиком
    aluminum_bag: Mapped[int] = mapped_column(Integer, nullable=True)  # Количество мешков с алюминием
    glass_bag: Mapped[int] = mapped_column(Integer, nullable=True)  # Количество мешков со стеклом
    other: Mapped[int] = mapped_column(Integer, nullable=True)  # Количество мешков с другим


class Shipment(Base):
    __tablename__ = 'shipments'
    
    shipment_id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    point_id: Mapped[int] = mapped_column(ForeignKey('points.point_id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'))
    
    # Основные материалы (категория 1)
    pet_kg: Mapped[float] = mapped_column(Float, default=0.0)
    pet_price: Mapped[float] = mapped_column(Float, default=0.0)
    pet_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    paper_kg: Mapped[float] = mapped_column(Float, default=0.0)
    paper_price: Mapped[float] = mapped_column(Float, default=0.0)
    paper_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    alum_kg: Mapped[float] = mapped_column(Float, default=0.0)
    alum_price: Mapped[float] = mapped_column(Float, default=0.0)
    alum_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    glass_kg: Mapped[float] = mapped_column(Float, default=0.0)
    glass_price: Mapped[float] = mapped_column(Float, default=0.0)
    glass_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    small_beer_box_kg: Mapped[float] = mapped_column(Float, default=0.0)
    small_beer_box_price: Mapped[float] = mapped_column(Float, default=0.0)
    small_beer_box_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    large_beer_box_kg: Mapped[float] = mapped_column(Float, default=0.0)
    large_beer_box_price: Mapped[float] = mapped_column(Float, default=0.0)
    large_beer_box_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    mixed_beer_box_kg: Mapped[float] = mapped_column(Float, default=0.0)
    mixed_beer_box_price: Mapped[float] = mapped_column(Float, default=0.0)
    mixed_beer_box_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Другие материалы (категория 2)
    oil_kg: Mapped[float] = mapped_column(Float, default=0.0)
    oil_price: Mapped[float] = mapped_column(Float, default=0.0)
    oil_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    colored_plastic_kg: Mapped[float] = mapped_column(Float, default=0.0)
    colored_plastic_price: Mapped[float] = mapped_column(Float, default=0.0)
    colored_plastic_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    iron_kg: Mapped[float] = mapped_column(Float, default=0.0)  # Заменил metal на iron
    iron_price: Mapped[float] = mapped_column(Float, default=0.0)
    iron_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    plastic_bag_kg: Mapped[float] = mapped_column(Float, default=0.0)
    plastic_bag_price: Mapped[float] = mapped_column(Float, default=0.0)
    plastic_bag_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    mix_kg: Mapped[float] = mapped_column(Float, default=0.0)
    mix_price: Mapped[float] = mapped_column(Float, default=0.0)
    mix_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    other_kg: Mapped[float] = mapped_column(Float, default=0.0)
    other_price: Mapped[float] = mapped_column(Float, default=0.0)
    other_total: Mapped[float] = mapped_column(Float, default=0.0)
    
    total_pay: Mapped[float] = mapped_column(Float, default=0.0)
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)