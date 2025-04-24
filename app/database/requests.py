from app.database.models import async_session
from app.database.models import User, Point, Zone, Region, Request, Shipment
from sqlalchemy import select, update, delete, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()

async def register_user(tg_id, point_id=None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            session.add(User(tg_id=tg_id, point_id=point_id))
            await session.commit()

async def add_point(point_id: int, point_name: str, point_owner_name: str, phone_number: str, address: str, bags_count: int, zone_id: int):
    async with async_session() as session:
        session.add(Point(
            point_id=int(point_id),  # Явное преобразование в int
            point_name=point_name,
            point_owner_name=point_owner_name,
            phone_number=phone_number,
            address=address,
            bags_count=bags_count,
            zone_id=int(zone_id)  # Явное преобразование в int
        ))
        await session.commit()

async def get_zone_by_id(zone_id):
    async with async_session() as session:
        zone = await session.scalar(select(Zone).where(Zone.zone_id == zone_id))
        return zone

async def get_region_by_id(region_id):
    async with async_session() as session:
        region = await session.scalar(select(Region).where(Region.region_id == region_id))
        return region

async def add_zone(zone_id, region_id):
    async with async_session() as session:
        session.add(Zone(zone_id=zone_id, region_id=region_id))
        await session.commit()

async def add_region(region_id):
    async with async_session() as session:
        session.add(Region(region_id=region_id))
        await session.commit()

async def add_request(point_id, user_id, activity, pet_bag=None, aluminum_bag=None, glass_bag=None, other=None):
    async with async_session() as session:
        session.add(Request(
            point_id=point_id,
            user_id=user_id,  # Добавленное поле
            activity=activity,
            pet_bag=pet_bag,
            aluminum_bag=aluminum_bag,
            glass_bag=glass_bag,
            other=other
        ))
        await session.commit()
        
async def bind_point_to_user(point_id, tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            user = User(tg_id=tg_id)
            session.add(user)
            await session.commit()

        point = await session.scalar(select(Point).where(Point.point_id == point_id))
        if not point:
            raise ValueError(f"Точка с ID {point_id} не найдена.")

        user.point_id = point.point_id
        await session.commit()

async def get_user_points(tg_id):
    async with async_session() as session:
        user = await session.scalar(
            select(User)
            .where(User.tg_id == tg_id)
            .options(selectinload(User.point)))
        
        if user and user.point:
            return [user.point]
        return []

async def update_bags_count(point_id, bags_count):
    async with async_session() as session:
        await session.execute(
            update(Point)
            .where(Point.point_id == point_id)
            .values(bags_count=bags_count))
        await session.commit()

async def get_user_by_point_id(point_id: str):
    """Получает пользователя по ID точки с приведением типов"""
    async with async_session() as session:
        user = await session.scalar(
            select(User)
            .where(User.point_id == int(point_id))  # Явное преобразование в int
            .options(selectinload(User.point))
        )
        return user

async def get_zones_by_region(region_id):
    async with async_session() as session:
        zones = await session.scalars(select(Zone).where(Zone.region_id == region_id))
        return zones.all()

async def get_points_by_zone(zone_id):
    async with async_session() as session:
        points = await session.scalars(select(Point).where(Point.zone_id == zone_id))
        return points.all()

async def get_point_by_id(point_id):
    async with async_session() as session:
        point = await session.scalar(select(Point).where(Point.point_id == int(point_id)))
        return point

async def get_all_points():
    async with async_session() as session:
        points = await session.scalars(select(Point))
        return points.all()

async def get_all_zones():
    async with async_session() as session:
        zones = await session.scalars(select(Zone))
        return zones.all()

async def get_all_regions():
    async with async_session() as session:
        regions = await session.scalars(select(Region))
        return regions.all()

async def get_user_by_tg_id(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user

async def is_point_available(point_id):
    async with async_session() as session:
        users = await session.scalars(select(User).where(User.point_id == point_id))
        return not users.first()

async def add_shipment(point_id, user_id, **materials):
    async with async_session() as session:
        # Удаляем все *_total поля из materials, если они там есть
        for field in ['alum_total', 'pet_total', 'glass_total', 'paper_total', 
                     'metal_total', 'oil_total', 'other_total',
                     'alum_pl_mix_total', 'alum_pl_glass_mix_total', 
                     'alum_iron_cans_mix_total', 'pet_mix_total', 
                     'other_mix_total', 'total_pay']:
            materials.pop(field, None)
        
        # Расчет всех total значений
        totals = {
            'alum': materials.get('alum_kg', 0.0) * materials.get('alum_price', 0.0),
            'pet': materials.get('pet_kg', 0.0) * materials.get('pet_price', 0.0),
            'glass': materials.get('glass_kg', 0.0) * materials.get('glass_price', 0.0),
            'paper': materials.get('paper_kg', 0.0) * materials.get('paper_price', 0.0),
            'metal': materials.get('metal_kg', 0.0) * materials.get('metal_price', 0.0),
            'oil': materials.get('oil_kg', 0.0) * materials.get('oil_price', 0.0),
            'other': materials.get('other_kg', 0.0) * materials.get('other_price', 0.0),
            'alum_pl_mix': materials.get('alum_pl_mix_kg', 0.0) * materials.get('alum_pl_mix_price', 0.0),
            'alum_pl_glass_mix': materials.get('alum_pl_glass_mix_kg', 0.0) * materials.get('alum_pl_glass_mix_price', 0.0),
            'alum_iron_cans_mix': materials.get('alum_iron_cans_mix_kg', 0.0) * materials.get('alum_iron_cans_mix_price', 0.0),
            'pet_mix': materials.get('pet_mix_kg', 0.0) * materials.get('pet_mix_price', 0.0),
            'other_mix': materials.get('other_mix_kg', 0.0) * materials.get('other_mix_price', 0.0)
        }
        
        total_pay = sum(totals.values())
        
        # Создаем shipment с явным указанием всех полей
        shipment = Shipment(
            point_id=point_id,
            user_id=user_id,
            # Основные поля
            alum_kg=materials.get('alum_kg', 0.0),
            alum_price=materials.get('alum_price', 0.0),
            alum_total=totals['alum'],
            pet_kg=materials.get('pet_kg', 0.0),
            pet_price=materials.get('pet_price', 0.0),
            pet_total=totals['pet'],
            glass_kg=materials.get('glass_kg', 0.0),
            glass_price=materials.get('glass_price', 0.0),
            glass_total=totals['glass'],
            # Дополнительные поля
            paper_kg=materials.get('paper_kg', 0.0),
            paper_price=materials.get('paper_price', 0.0),
            paper_total=totals['paper'],
            metal_kg=materials.get('metal_kg', 0.0),
            metal_price=materials.get('metal_price', 0.0),
            metal_total=totals['metal'],
            oil_kg=materials.get('oil_kg', 0.0),
            oil_price=materials.get('oil_price', 0.0),
            oil_total=totals['oil'],
            other_kg=materials.get('other_kg', 0.0),
            other_price=materials.get('other_price', 0.0),
            other_total=totals['other'],
            # Смешанные материалы
            alum_pl_mix_kg=materials.get('alum_pl_mix_kg', 0.0),
            alum_pl_mix_price=materials.get('alum_pl_mix_price', 0.0),
            alum_pl_mix_total=totals['alum_pl_mix'],
            alum_pl_glass_mix_kg=materials.get('alum_pl_glass_mix_kg', 0.0),
            alum_pl_glass_mix_price=materials.get('alum_pl_glass_mix_price', 0.0),
            alum_pl_glass_mix_total=totals['alum_pl_glass_mix'],
            alum_iron_cans_mix_kg=materials.get('alum_iron_cans_mix_kg', 0.0),
            alum_iron_cans_mix_price=materials.get('alum_iron_cans_mix_price', 0.0),
            alum_iron_cans_mix_total=totals['alum_iron_cans_mix'],
            pet_mix_kg=materials.get('pet_mix_kg', 0.0),
            pet_mix_price=materials.get('pet_mix_price', 0.0),
            pet_mix_total=totals['pet_mix'],
            other_mix_kg=materials.get('other_mix_kg', 0.0),
            other_mix_price=materials.get('other_mix_price', 0.0),
            other_mix_total=totals['other_mix'],
            # Итоговая сумма
            total_pay=total_pay
        )
        
        session.add(shipment)
        await session.commit()

async def get_report_data():
    async with async_session() as session:
        shipments = await session.scalars(select(Shipment))
        
        report_data = []
        for shipment in shipments:
            report_data.append({
                "date": shipment.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "point_id": shipment.point_id,
                "user_id": shipment.user_id,
                "total_pay": shipment.total_pay,
                # Добавьте другие нужные поля из Shipment
            })
        
        return report_data

async def get_requests_by_point(point_id):
    async with async_session() as session:
        requests = await session.scalars(
            select(Request)
            .where(Request.point_id == point_id)
            .order_by(desc(Request.timestamp)))
        return requests.all()

async def get_shipments_by_point(point_id):
    async with async_session() as session:
        shipments = await session.scalars(
            select(Shipment)
            .where(Shipment.point_id == point_id)
            .order_by(desc(Shipment.timestamp)))
        return shipments.all()

async def get_all_requests_sorted():
    """Получить все заявки, отсортированные по дате (от старых к новым)"""
    async with async_session() as session:
        requests = await session.scalars(
            select(Request)
            .order_by(Request.timestamp)
        )
        return requests.all()

async def get_all_shipments_sorted():
    """Получить все отгрузки, отсортированные по дате (от старых к новым)"""
    async with async_session() as session:
        shipments = await session.scalars(
            select(Shipment)
            .order_by(Shipment.timestamp)
        )
        return shipments.all()

async def get_combined_data_sorted():
    async with async_session() as session:
        requests = await session.scalars(
            select(Request)
            .order_by(Request.timestamp)
        )
        shipments = await session.scalars(
            select(Shipment)
            .order_by(Shipment.timestamp)
        )
        
        request_data = [
            {
                "type": "request",
                "timestamp": r.timestamp,
                "point_id": r.point_id,
                "user_id": r.user_id,  # Добавлено
                "activity": r.activity,
                "pet": r.pet_bag or 0,
                "aluminum": r.aluminum_bag or 0,
                "glass": r.glass_bag or 0,
                "other": r.other or 0,
                "total": (r.pet_bag or 0) + (r.aluminum_bag or 0) + 
                        (r.glass_bag or 0) + (r.other or 0)
            }
            for r in requests
        ]
        
        shipment_data = [
            {
                "type": "shipment",
                "timestamp": s.timestamp,
                "point_id": s.point_id,
                "user_id": s.user_id,
                "pet_kg": s.pet_kg,
                "pet_price": s.pet_price,
                "pet_total": s.pet_total,
                "alum_kg": s.alum_kg,
                "alum_price": s.alum_price,
                "alum_total": s.alum_total,
                "glass_kg": s.glass_kg,
                "glass_price": s.glass_price,
                "glass_total": s.glass_total,
                "paper_kg": s.paper_kg,
                "paper_price": s.paper_price,
                "paper_total": s.paper_total,
                "metal_kg": s.metal_kg,
                "metal_price": s.metal_price,
                "metal_total": s.metal_total,
                "oil_kg": s.oil_kg,
                "oil_price": s.oil_price,
                "oil_total": s.oil_total,
                "other_kg": s.other_kg,
                "other_price": s.other_price,
                "other_total": s.other_total,
                "alum_pl_mix_kg": s.alum_pl_mix_kg,
                "alum_pl_mix_price": s.alum_pl_mix_price,
                "alum_pl_mix_total": s.alum_pl_mix_total,
                "alum_pl_glass_mix_kg": s.alum_pl_glass_mix_kg,
                "alum_pl_glass_mix_price": s.alum_pl_glass_mix_price,
                "alum_pl_glass_mix_total": s.alum_pl_glass_mix_total,
                "alum_iron_cans_mix_kg": s.alum_iron_cans_mix_kg,
                "alum_iron_cans_mix_price": s.alum_iron_cans_mix_price,
                "alum_iron_cans_mix_total": s.alum_iron_cans_mix_total,
                "pet_mix_kg": s.pet_mix_kg,
                "pet_mix_price": s.pet_mix_price,
                "pet_mix_total": s.pet_mix_total,
                "other_mix_kg": s.other_mix_kg,
                "other_mix_price": s.other_mix_price,
                "other_mix_total": s.other_mix_total,
                "total_pay": s.total_pay
            }
            for s in shipments
        ]
        
        combined = request_data + shipment_data
        return sorted(combined, key=lambda x: x["timestamp"])

async def delete_point_and_related_data(point_id: str):
    """
    Удаляет точку и связанные данные:
    - Отгрузки сохраняем, переназначая на системного пользователя (tg_id=0)
    - Заявки (requests) удаляем полностью
    - Пользователя удаляем
    - Точку удаляем
    """
    async with async_session() as session:
        try:
            # 1. Находим пользователя, связанного с точкой
            user = await session.scalar(
                select(User)
                .where(User.point_id == int(point_id))
            )
            
            if not user:
                # Если пользователя нет, просто удаляем точку и заявки
                await session.execute(
                    delete(Request)
                    .where(Request.point_id == int(point_id))
                )
                await session.execute(
                    delete(Point)
                    .where(Point.point_id == int(point_id))
                )
                await session.commit()
                return True

            # 2. Создаем/проверяем системного пользователя
            system_user = await session.scalar(
                select(User)
                .where(User.tg_id == 0)
            )
            
            if not system_user:
                system_user = User(tg_id=0, point_id=None)
                session.add(system_user)
                await session.flush()  # Сохраняем, чтобы получить ID

            # 3. Переназначаем отгрузки на системного пользователя
            await session.execute(
                update(Shipment)
                .where(Shipment.user_id == user.tg_id)
                .values(user_id=system_user.tg_id)
            )

            # 4. Удаляем все заявки точки (requests)
            await session.execute(
                delete(Request)
                .where(Request.point_id == int(point_id))
            )

            # 5. Удаляем оригинального пользователя
            await session.delete(user)

            # 6. Удаляем саму точку
            await session.execute(
                delete(Point)
                .where(Point.point_id == int(point_id))
            )

            await session.commit()
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"Error deleting point {point_id}: {str(e)}")
            return False