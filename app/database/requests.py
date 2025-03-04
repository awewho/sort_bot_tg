from app.database.models import async_session
from app.database.models import User, Point, Cluster, Log, Shipment
from sqlalchemy import select, update, delete, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            session.add(User(tg_id=tg_id, role="user"))  # Указываем значение по умолчанию для role
            await session.commit()

async def register_user(tg_id, name, phone_number, address, role):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            session.add(User(tg_id=tg_id, name=name, phone_number=phone_number, address=address, role=role))
            await session.commit()

async def add_point(address, latitude, longitude, cluster_id):
    async with async_session() as session:
        session.add(Point(address=address, latitude=latitude, longitude=longitude, cluster_id=cluster_id))
        await session.commit()

async def add_cluster(name, driver_id):
    async with async_session() as session:
        session.add(Cluster(name=name, driver_id=driver_id))
        await session.commit()

async def add_event(point_id, driver_id, event_type, weight, price):
    async with async_session() as session:
        session.add(Event(point_id=point_id, driver_id=driver_id, event_type=event_type, weight=weight, price=price))
        await session.commit()

async def add_log(event_id, details):
    async with async_session() as session:
        session.add(Log(event_id=event_id, details=details))
        await session.commit()

async def get_point_by_address(address):
    async with async_session() as session:
        point = await session.scalar(select(Point).where(Point.address == address))
        return point

async def bind_point_to_user(point_id, tg_id):
    """Привязывает точку к пользователю по ID точки."""
    async with async_session() as session:
        # Находим пользователя
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            # Автоматически создаём пользователя, если он отсутствует
            user = User(tg_id=tg_id, role="user")  # Указываем роль по умолчанию
            session.add(user)
            await session.commit()

        # Находим точку по ID
        point = await session.scalar(select(Point).where(Point.id == point_id))
        if not point:
            raise ValueError(f"Точка с ID {point_id} не найдена.")

        # Привязываем точку к пользователю
        user.point_id = point.id
        await session.commit()


async def get_user_points(tg_id):
    """Возвращает список точек, привязанных к пользователю по его tg_id."""
    async with async_session() as session:
        # Ищем пользователя по tg_id и загружаем связанную точку
        user = await session.scalar(
            select(User)
            .where(User.tg_id == tg_id)
            .options(selectinload(User.point))
        )
        
        # Если пользователь найден и у него есть привязанная точка, возвращаем её
        if user and user.point:
            return [user.point]
        return []


async def update_bags_count(point_id, bags_count):
    async with async_session() as session:
        await session.execute(update(Point).where(Point.id == point_id).values(bags_count=bags_count))
        await session.commit()

async def get_driver_clusters(driver_id):
    async with async_session() as session:
        clusters = await session.scalars(select(Cluster).where(Cluster.driver_id == driver_id))
        return clusters.all()

async def get_points_by_cluster(cluster_id):
    async with async_session() as session:
        points = await session.scalars(select(Point).where(Point.cluster_id == cluster_id))
        return points.all()

async def update_point_status(point_id, bags_count):
    async with async_session() as session:
        await session.execute(update(Point).where(Point.id == point_id).values(bags_count=bags_count))
        await session.commit()

async def get_point_by_id(point_id):
    async with async_session() as session:
        point = await session.scalar(select(Point).where(Point.id == point_id))
        return point

async def get_all_points():
    async with async_session() as session:
        points = await session.scalars(select(Point))
        return points.all()

async def get_all_clusters():
    async with async_session() as session:
        clusters = await session.scalars(select(Cluster))
        return clusters.all()

async def get_all_drivers():
    async with async_session() as session:
        drivers = await session.scalars(select(User).where(User.role == "driver"))
        return drivers.all()

async def get_user_by_id(user_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        return user

async def get_point_by_number(point_number: str):
    async with async_session() as session:
        point = await session.scalar(select(Point).where(Point.number == point_number))
        return point

async def get_user_by_tg_id(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user

async def is_point_available(point_id: int):
    async with async_session() as session:
        # Проверяем, есть ли у точки привязанные пользователи
        users = await session.scalars(select(User).where(User.point_id == point_id))
        return not users.first()  # True, если точка не привязана к пользователю





async def add_log(client_id, activity, bags_count=None, question=None, alum_kg=None, alum_price=None, alum_total=None, pet_kg=None, pet_price=None, pet_total=None, glass_kg=None, glass_price=None, glass_total=None, mixed_kg=None, mixed_price=None, mixed_total=None, total_pay=None):
    async with async_session() as session:
        log = Log(
            client_id=client_id,
            activity=activity,
            bags_count=bags_count,
            question=question,
            alum_kg=alum_kg,
            alum_price=alum_price,
            alum_total=alum_total,
            pet_kg=pet_kg,
            pet_price=pet_price,
            pet_total=pet_total,
            glass_kg=glass_kg,
            glass_price=glass_price,
            glass_total=glass_total,
            mixed_kg=mixed_kg,
            mixed_price=mixed_price,
            mixed_total=mixed_total,
            total_pay=total_pay
        )
        session.add(log)
        await session.commit()

async def add_shipment(point_id, user_id, alum_kg, alum_price, pet_kg, pet_price, glass_kg, glass_price, mixed_kg, mixed_price):
    async with async_session() as session:
        # Рассчитываем итоговые суммы
        alum_total = alum_kg * alum_price
        pet_total = pet_kg * pet_price
        glass_total = glass_kg * glass_price
        mixed_total = mixed_kg * mixed_price
        total_pay = alum_total + pet_total + glass_total + mixed_total
        
        shipment = Shipment(
            point_id=point_id,
            user_id=user_id,
            alum_kg=alum_kg,
            alum_price=alum_price,
            alum_total=alum_total,
            pet_kg=pet_kg,
            pet_price=pet_price,
            pet_total=pet_total,
            glass_kg=glass_kg,
            glass_price=glass_price,
            glass_total=glass_total,
            mixed_kg=mixed_kg,
            mixed_price=mixed_price,
            mixed_total=mixed_total,
            total_pay=total_pay
        )
        session.add(shipment)
        await session.commit()
        
        # Добавляем запись в лог
        await add_log(
            client_id=user_id,
            activity="shipment",
            alum_kg=alum_kg,
            alum_price=alum_price,
            alum_total=alum_total,
            pet_kg=pet_kg,
            pet_price=pet_price,
            pet_total=pet_total,
            glass_kg=glass_kg,
            glass_price=glass_price,
            glass_total=glass_total,
            mixed_kg=mixed_kg,
            mixed_price=mixed_price,
            mixed_total=mixed_total,
            total_pay=total_pay
        )

        
async def get_report_data():
    async with async_session() as session:
        logs = await session.scalars(select(Log))
        report_data = []
        
        for log in logs:
            report_data.append({
                "date": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),  # Используем timestamp вместо date
                "client_id": log.client_id,
                "activity": log.activity,
                "question": log.question,
                "bags_count": log.bags_count,
                "alum_kg": log.alum_kg,
                "alum_price": log.alum_price,
                "alum_total": log.alum_total,
                "pet_kg": log.pet_kg,
                "pet_price": log.pet_price,
                "pet_total": log.pet_total,
                "glass_kg": log.glass_kg,
                "glass_price": log.glass_price,
                "glass_total": log.glass_total,
                "mixed_kg": log.mixed_kg,
                "mixed_price": log.mixed_price,
                "mixed_total": log.mixed_total,
                "total_pay": log.total_pay
            })
        
        return report_data