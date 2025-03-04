from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command, Filter
from aiogram.fsm.context import FSMContext

import os

from openpyxl import Workbook
from datetime import datetime

from app.database.requests import (
    get_driver_clusters, get_points_by_cluster, update_point_status, add_event, add_log, get_point_by_id,
    get_all_points, get_all_clusters, get_all_drivers, add_shipment, get_user_by_tg_id, get_report_data
)
from app.states import DriverRoute, Notifications, Reports, ShipmentStates
from app.keyboards import driver_keyboard, notification_keyboard, report_keyboard, admin_keyboard


ADMIN_ID = [753755508]
# Идентификатор администратора

admin = Router()


class Admin(Filter):
    """Фильтр для проверки, является ли пользователь администратором."""
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_ID



@admin.message(Admin(), Command("admin"))
async def admin_start(message: Message):
    """Обрабатывает команду /start для администратора."""
    await message.answer(
        "Добро пожаловать в админ-панель. Выберите действие:",
        reply_markup=admin_keyboard()
    )


@admin.callback_query(Admin(), F.data =='report')
async def cmd_report(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Выберите тип отчета:', reply_markup=report_keyboard())
    await state.set_state(Reports.report_type)


async def split_message(message: str, max_length: int = 4096):
    """Разбивает сообщение на части, не превышающие max_length символов."""
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_point")
async def process_points_report(callback: CallbackQuery, state: FSMContext):
    points = await get_all_points()
    
    if points:
        report_message = "Отчет по точкам:\n"
        for point in points:
            report_message += f"Точка: {point.address}, Мешков: {point.bags_count}, Кластер: {point.cluster_id}\n"
        
        # Разбиваем сообщение на части
        messages = await split_message(report_message)
        for msg in messages:
            await callback.message.answer(msg)
    else:
        await callback.message.answer('Нет данных по точкам.')
    
    await state.clear()

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_cluster")
async def process_clusters_report(callback: CallbackQuery, state: FSMContext):
    clusters = await get_all_clusters()
    
    if clusters:
        report_message = "Отчет по кластерам:\n"
        for cluster in clusters:
            report_message += f"Кластер: {cluster.name}, Водитель: {cluster.driver_id}\n"
        
        # Разбиваем сообщение на части
        messages = await split_message(report_message)
        for msg in messages:
            await callback.message.answer(msg)
    else:
        await callback.message.answer('Нет данных по кластерам.')
    
    await state.clear()

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_drivers")
async def process_drivers_report(callback: CallbackQuery, state: FSMContext):
    drivers = await get_all_drivers()
    
    if drivers:
        report_message = "Отчет по водителям:\n"
        for driver in drivers:
            report_message += f"Водитель: {driver.name}, Телефон: {driver.phone_number}\n"
        
        # Разбиваем сообщение на части
        messages = await split_message(report_message)
        for msg in messages:
            await callback.message.answer(msg)
    else:
        await callback.message.answer('Нет данных по водителям.')
    
    await state.clear()




@admin.callback_query(Admin(), F.data == 'generate_log_report')
async def cmd_generate_report(callback_query: CallbackQuery):
    # Получаем данные для отчета
    report_data = await get_report_data()

    # Проверяем, есть ли данные для отчета
    if not report_data:
        await callback_query.message.answer("Нет данных для формирования отчета.")
        return

    # Создаем Excel-файл
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет"

    # Заголовки столбцов
    headers = [
        "Дата", "Номер клиента", "Активность", "Вопрос", "Количество сумок",
        "Алюминий (кг)", "Цена алюминия", "Сумма алюминия",
        "PET (кг)", "Цена PET", "Сумма PET",
        "Стекло (кг)", "Цена стекла", "Сумма стекла",
        "Смешанный мусор (кг)", "Цена смешанного мусора", "Сумма смешанного мусора",
        "Итого к оплате"
    ]
    ws.append(headers)

    # Заполняем данные
    for row in report_data:
        ws.append([
            row["date"],
            row["client_id"],
            row["activity"],
            row["question"],
            row["bags_count"],
            row["alum_kg"],
            row["alum_price"],
            row["alum_total"],
            row["pet_kg"],
            row["pet_price"],
            row["pet_total"],
            row["glass_kg"],
            row["glass_price"],
            row["glass_total"],
            row["mixed_kg"],
            row["mixed_price"],
            row["mixed_total"],
            row["total_pay"]
        ])

    # Сохраняем файл
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)

    try:
        # Отправляем файл администратору
        await callback_query.message.answer_document(FSInputFile(filename))
    finally:
        # Удаляем файл после отправки
        if os.path.exists(filename):
            os.remove(filename)

# Основное меню водителя
@admin.message(Command('driver'))
async def cmd_driver(message: Message):
    await message.answer("Выберите действие:", reply_markup=driver_keyboard())

# Обработка колбеков
@admin.callback_query(F.data == "form_route")
async def process_form_route(callback: CallbackQuery):
    clusters = await get_driver_clusters(callback.from_user.id)
    
    if clusters:
        route_points = []
        for cluster in clusters:
            points = await get_points_by_cluster(cluster.id)
            route_points.extend(points)
        
        if route_points:
            route_message = "Ваш маршрут:\n"
            for point in route_points:
                route_message += f"Точка: {point.address}, Мешков: {point.bags_count}\n"
            
            await callback.message.answer(route_message)
        else:
            await callback.message.answer('Нет точек для сбора мусора в ваших кластерах.')
    else:
        await callback.message.answer('У вас нет закрепленных кластеров.')
    
    await callback.answer()

@admin.callback_query(F.data == "collect_bag")
async def process_collect_bag(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ID точки, на которой вы забрали мешок:')
    await state.set_state(Notifications.weight)
    await callback.answer()

@admin.message(Notifications.weight)
async def process_weight(message: Message, state: FSMContext):
    point_id = int(message.text)
    await state.update_data(point_id=point_id)
    await message.answer('Введите вес мешка:')
    await state.set_state(Notifications.price)

@admin.message(Notifications.price)
async def process_price(message: Message, state: FSMContext):
    weight = float(message.text)
    await state.update_data(weight=weight)
    await message.answer('Введите стоимость мешка:')
    await state.set_state(Notifications.new_bag)

@admin.message(Notifications.new_bag)
async def process_new_bag(message: Message, state: FSMContext):
    price = float(message.text)
    user_data = await state.get_data()
    point_id = user_data['point_id']
    weight = user_data['weight']
    
    # Добавляем событие в базу данных
    await add_event(point_id, message.from_user.id, "collect_bag", weight, price)
    
    # Обновляем статус точки
    await update_point_status(point_id, bags_count=0)
    
    # Отправляем уведомление пользователю
    point = await get_point_by_id(point_id)
    if point and point.user_id:
        await message.bot.send_message(point.user_id, f"Ваш мешок с мусором был забран. Вес: {weight} кг, Стоимость: {price} руб.")
    
    await message.answer('Мешок успешно забран. Выдан новый мешок.', reply_markup=confirm_keyboard())
    await state.clear()



@admin.callback_query(F.data == "add_shipment")
async def process_add_shipment(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ID точки:')
    await state.set_state(ShipmentStates.point_id)
    await callback.answer()

@admin.message(ShipmentStates.point_id)
async def process_point_id(message: Message, state: FSMContext):
    point_id = int(message.text)
    await state.update_data(point_id=point_id)
    await message.answer('Введите вес алюминия (кг):')
    await state.set_state(ShipmentStates.alum_kg)

@admin.message(ShipmentStates.alum_kg)
async def process_alum_kg(message: Message, state: FSMContext):
    alum_kg = float(message.text)
    await state.update_data(alum_kg=alum_kg)
    
    if alum_kg == 0:
        await state.update_data(alum_price=0.0)
        await message.answer('Вес алюминия равен 0. Переходим к PET.')
        await message.answer('Введите вес PET (кг):')
        await state.set_state(ShipmentStates.pet_kg)
    else:
        await message.answer('Введите цену за кг алюминия:')
        await state.set_state(ShipmentStates.alum_price)

@admin.message(ShipmentStates.alum_price)
async def process_alum_price(message: Message, state: FSMContext):
    alum_price = float(message.text)
    await state.update_data(alum_price=alum_price)
    await message.answer('Введите вес PET (кг):')
    await state.set_state(ShipmentStates.pet_kg)

@admin.message(ShipmentStates.pet_kg)
async def process_pet_kg(message: Message, state: FSMContext):
    pet_kg = float(message.text)
    await state.update_data(pet_kg=pet_kg)
    
    if pet_kg == 0:
        await state.update_data(pet_price=0.0)
        await message.answer('Вес PET равен 0. Переходим к стеклу.')
        await message.answer('Введите вес стекла (кг):')
        await state.set_state(ShipmentStates.glass_kg)
    else:
        await message.answer('Введите цену за кг PET:')
        await state.set_state(ShipmentStates.pet_price)

@admin.message(ShipmentStates.pet_price)
async def process_pet_price(message: Message, state: FSMContext):
    pet_price = float(message.text)
    await state.update_data(pet_price=pet_price)
    await message.answer('Введите вес стекла (кг):')
    await state.set_state(ShipmentStates.glass_kg)

@admin.message(ShipmentStates.glass_kg)
async def process_glass_kg(message: Message, state: FSMContext):
    glass_kg = float(message.text)
    await state.update_data(glass_kg=glass_kg)
    
    if glass_kg == 0:
        await state.update_data(glass_price=0.0)
        await message.answer('Вес стекла равен 0. Переходим к смешанному мусору.')
        await message.answer('Введите вес смешанного мусора (кг):')
        await state.set_state(ShipmentStates.mixed_kg)
    else:
        await message.answer('Введите цену за кг стекла:')
        await state.set_state(ShipmentStates.glass_price)

@admin.message(ShipmentStates.glass_price)
async def process_glass_price(message: Message, state: FSMContext):
    glass_price = float(message.text)
    await state.update_data(glass_price=glass_price)
    await message.answer('Введите вес смешанного мусора (кг):')
    await state.set_state(ShipmentStates.mixed_kg)

@admin.message(ShipmentStates.mixed_kg)
async def process_mixed_kg(message: Message, state: FSMContext):
    mixed_kg = float(message.text)
    await state.update_data(mixed_kg=mixed_kg)
    
    if mixed_kg == 0:
        await state.update_data(mixed_price=0.0)
        await finalize_shipment(message, state)
    else:
        await message.answer('Введите цену за кг смешанного мусора:')
        await state.set_state(ShipmentStates.mixed_price)

@admin.message(ShipmentStates.mixed_price)
async def process_mixed_price(message: Message, state: FSMContext):
    mixed_price = float(message.text)
    await state.update_data(mixed_price=mixed_price)
    await finalize_shipment(message, state)

async def finalize_shipment(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    try:
        # Получаем внутренний id пользователя
        user = await get_user_by_tg_id(message.from_user.id)
        if not user:
            raise ValueError("Пользователь не найден.")
        
        await add_shipment(
            point_id=user_data['point_id'],
            user_id=user.id,  # Используем внутренний id пользователя
            alum_kg=user_data['alum_kg'],
            alum_price=user_data.get('alum_price', 0.0),
            pet_kg=user_data['pet_kg'],
            pet_price=user_data.get('pet_price', 0.0),
            glass_kg=user_data['glass_kg'],
            glass_price=user_data.get('glass_price', 0.0),
            mixed_kg=user_data['mixed_kg'],
            mixed_price=user_data.get('mixed_price', 0.0)
        )
        await message.answer('Данные об отгрузке успешно добавлены!', reply_markup=notification_keyboard())
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}")
    finally:
        await state.clear()