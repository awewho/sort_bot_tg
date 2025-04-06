from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext

import os
from openpyxl import Workbook
from datetime import datetime

from app.database.requests import (
    get_all_points, get_all_zones, get_all_regions, 
    get_points_by_zone, get_zones_by_region,
    get_report_data, get_user_by_tg_id, 
    add_point, add_region, add_zone, 
    get_point_by_id,get_region_by_id,get_zone_by_id, 
    add_shipment, get_user_by_point_id,
    update_bags_count, get_all_requests_sorted,
    get_all_shipments_sorted, get_combined_data_sorted
)
from app.states import Reports, ShipmentStates, CreatePoint
from app.keyboards import (
    report_keyboard, admin_keyboard, driver_keyboard,
    cancel_keyboard, confirm_keyboard, 
    get_cancel_keyboard, get_category_keyboard, get_confirmation_keyboard, 
    get_main_materials_keyboard, get_mix_materials_keyboard,
    get_secondary_materials_keyboard)

ADMIN_IDS = [753755508, 1582399282]  # ID администраторов

admin = Router()

class Admin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS

@admin.message(Admin(), Command("admin"))
async def admin_start(message: Message):
    """Главное меню админ-панели"""
    await message.answer(
        "Добро пожаловать в админ-панель. Выберите действие:",
        reply_markup=admin_keyboard()
    )

@admin.callback_query(Admin(), F.data == 'report')
async def cmd_report(callback: CallbackQuery, state: FSMContext):
    """Меню отчетов"""
    await callback.message.answer('Выберите тип отчета:', reply_markup=report_keyboard())
    await state.set_state(Reports.report_type)
@admin.callback_query(Admin(), Reports.report_type, F.data == "report_zone")
async def process_zones_report(callback: CallbackQuery):
    """Отчет по зонам"""
    zones = await get_all_zones()
    
    if not zones:
        await callback.message.answer('Нет данных по зонам.')
        return
    
    report_messages = ["Отчет по зонам:\n\n"]
    for zone in zones:
        points = await get_points_by_zone(zone.zone_id)
        total_bags = sum(p.bags_count for p in points) if points else 0
        
        zone_info = (
            f"Зона ID: {zone.zone_id}\n"
            f"Регион: {zone.region_id}\n"
            f"Точек: {len(points)}\n"
            f"Всего мешков: {total_bags}\n\n"
        )
        
        # Если добавление новой информации превысит лимит - создаем новое сообщение
        if len(report_messages[-1]) + len(zone_info) > 4000:
            report_messages.append(zone_info)
        else:
            report_messages[-1] += zone_info
    
    for msg in report_messages:
        await callback.message.answer(msg)
    
    await callback.message.answer('Выберите действие:', reply_markup=admin_keyboard())

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_region")
async def process_regions_report(callback: CallbackQuery):
    """Отчет по регионам"""
    regions = await get_all_regions()
    
    if not regions:
        await callback.message.answer('Нет данных по регионам.')
        return
    
    report_messages = ["Отчет по регионам:\n\n"]
    for region in regions:
        zones = await get_zones_by_region(region.region_id)
        zone_count = len(zones)
        point_count = 0
        total_bags = 0
        
        for zone in zones:
            points = await get_points_by_zone(zone.zone_id)
            point_count += len(points)
            total_bags += sum(p.bags_count for p in points)
        
        region_info = (
            f"Регион ID: {region.region_id}\n"
            f"Зон: {zone_count}\n"
            f"Точек: {point_count}\n"
            f"Всего мешков: {total_bags}\n\n"
        )
        
        if len(report_messages[-1]) + len(region_info) > 4000:
            report_messages.append(region_info)
        else:
            report_messages[-1] += region_info
    
    for msg in report_messages:
        await callback.message.answer(msg)
    
    await callback.message.answer('Выберите действие:', reply_markup=admin_keyboard())

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_region_detail")
async def ask_region_id(callback: CallbackQuery, state: FSMContext):
    """Запрос ID региона для детального отчета"""
    await callback.message.answer("Введите ID региона для отчета:")
    await state.set_state(Reports.waiting_region_id)

@admin.message(Admin(), Reports.waiting_region_id)
async def generate_region_detail_report(message: Message, state: FSMContext):
    """Генерация детального отчета по региону"""
    try:
        region_id = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите числовой ID региона.")
        return
    
    # Получаем данные по региону
    region = await get_region_by_id(region_id)
    if not region:
        await message.answer(f"Регион с ID {region_id} не найден.")
        await state.clear()
        return
    
    # Получаем все зоны в регионе
    zones = await get_zones_by_region(region_id)
    if not zones:
        await message.answer(f"В регионе {region_id} нет зон.")
        await state.clear()
        return
    
    # Считаем общую статистику по региону
    total_points = 0
    total_bags = 0
    zones_data = []
    
    for zone in zones:
        points = await get_points_by_zone(zone.zone_id)
        zone_points = len(points)
        zone_bags = sum(p.bags_count for p in points) if points else 0
        
        total_points += zone_points
        total_bags += zone_bags
        
        if zone_points > 0:  # Добавляем только зоны с точками
            zones_data.append((zone.zone_id, zone_points, zone_bags))
    
    # Формируем сообщения с учетом лимита
    header = (
        f"📊 Отчет по региону {region_id}:\n"
        f"Всего точек: {total_points}\n"
        f"Всего мешков готово: {total_bags}\n\n"
        f"Детали по зонам:\n"
    )
    
    report_messages = [header]
    
    # Добавляем информацию по зонам
    for zone_id, zone_points, zone_bags in zones_data:
        zone_info = f"▪️ Зона {zone_id} - {zone_points} точек ({zone_bags} мешков)\n"
        
        if len(report_messages[-1]) + len(zone_info) > 4000:
            report_messages.append(zone_info)
        else:
            report_messages[-1] += zone_info
    
    for msg in report_messages:
        await message.answer(msg)
    
    await message.answer('Выберите действие:', reply_markup=admin_keyboard())
    await state.clear()

@admin.callback_query(Admin(), F.data == "generate_log_report")
async def generate_log_report(callback: CallbackQuery):
    """Генерация Excel-отчета с тремя листами: заявки, отгрузки и объединенные данные"""
    requests = await get_all_requests_sorted()
    shipments = await get_all_shipments_sorted()
    combined = await get_combined_data_sorted()
    
    if not requests and not shipments:
        await callback.message.answer("Нет данных для формирования отчета.")
        return
    
    wb = Workbook()
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]
    
    # 1. Лист с заявками (обновлен с учетом user_id)
    if requests:
        ws_requests = wb.create_sheet("Заявки")
        headers_requests = [
            "Дата", "Точка ID", "Пользователь ID", "Тип активности",
            "PET мешки", "Алюминий мешки", "Стекло мешки", "Другие мешки",
            "Общее количество"
        ]
        ws_requests.append(headers_requests)
        
        for req in requests:
            ws_requests.append([
                req.timestamp.strftime('%Y-%m-%d %H:%M'),
                req.point_id,
                req.user_id,  # Теперь используем реальный user_id
                req.activity,
                req.pet_bag or 0,
                req.aluminum_bag or 0,
                req.glass_bag or 0,
                req.other or 0,
                (req.pet_bag or 0) + (req.aluminum_bag or 0) + 
                (req.glass_bag or 0) + (req.other or 0)
            ])
    

    # 2. Лист с отгрузками (оставляем без изменений)
    if shipments:
        ws_shipments = wb.create_sheet("Отгрузки")
        headers_shipments = [
            "Дата", "Точка ID", "Водитель ID", "Общая оплата",
            "PET кг", "Цена PET", "Сумма PET",
            "Алюминий кг", "Цена алюминия", "Сумма алюминия",
            "Стекло кг", "Цена стекла", "Сумма стекла",
            "Бумага кг", "Цена бумаги", "Сумма бумаги",
            "Металл кг", "Цена металла", "Сумма металла",
            "Масло кг", "Цена масла", "Сумма масла",
            "Другое кг", "Цена другого", "Сумма другого",
            "Алюм+пластик кг", "Цена смеси", "Сумма смеси",
            "Алюм+пластик+стекло кг", "Цена смеси", "Сумма смеси",
            "Алюм+жесть кг", "Цена смеси", "Сумма смеси",
            "PET смесь кг", "Цена смеси", "Сумма смеси",
            "Другая смесь кг", "Цена смеси", "Сумма смеси"
        ]
        ws_shipments.append(headers_shipments)
        
        for ship in shipments:
            ws_shipments.append([
                ship.timestamp.strftime('%Y-%m-%d %H:%M'),
                ship.point_id,
                ship.user_id,
                ship.total_pay,
                ship.pet_kg, ship.pet_price, ship.pet_total,
                ship.alum_kg, ship.alum_price, ship.alum_total,
                ship.glass_kg, ship.glass_price, ship.glass_total,
                ship.paper_kg, ship.paper_price, ship.paper_total,
                ship.metal_kg, ship.metal_price, ship.metal_total,
                ship.oil_kg, ship.oil_price, ship.oil_total,
                ship.other_kg, ship.other_price, ship.other_total,
                ship.alum_pl_mix_kg, ship.alum_pl_mix_price, ship.alum_pl_mix_total,
                ship.alum_pl_glass_mix_kg, ship.alum_pl_glass_mix_price, ship.alum_pl_glass_mix_total,
                ship.alum_iron_cans_mix_kg, ship.alum_iron_cans_mix_price, ship.alum_iron_cans_mix_total,
                ship.pet_mix_kg, ship.pet_mix_price, ship.pet_mix_total,
                ship.other_mix_kg, ship.other_mix_price, ship.other_mix_total
            ])
    
    # 3. Общий лист с ПОЛНЫМИ данными по отгрузкам
    if combined:
        ws_combined = wb.create_sheet("Все данные")
        headers_combined = [
            "Тип записи", "Дата", "ID точки", "ID пользователя",
            # Основные материалы
            "PET (мешки/кг)", "Цена PET", "Сумма PET",
            "Алюминий (мешки/кг)", "Цена алюминия", "Сумма алюминия",
            "Стекло (мешки/кг)", "Цена стекла", "Сумма стекла",
            # Дополнительные материалы
            "Бумага кг", "Цена бумаги", "Сумма бумаги",
            "Металл кг", "Цена металла", "Сумма металла",
            "Масло кг", "Цена масла", "Сумма масла",
            "Другое кг", "Цена другого", "Сумма другого",
            # Смеси
            "Алюм+пластик кг", "Цена смеси", "Сумма смеси",
            "Алюм+пласт+стекло кг", "Цена смеси", "Сумма смеси",
            "Алюм+жесть кг", "Цена смеси", "Сумма смеси",
            "PET смесь кг", "Цена смеси", "Сумма смеси",
            "Другая смесь кг", "Цена смеси", "Сумма смеси",
            # Итоги
            "Общая сумма", "Тип активности (для заявок)"
        ]
        ws_combined.append(headers_combined)
        
        for item in combined:
            if item["type"] == "request":
                row = [
                    "Заявка",
                    item["timestamp"].strftime('%Y-%m-%d %H:%M'),
                    item["point_id"],
                    item["user_id"],  # Теперь используем реальный user_id
                    item["total"],
                    item["activity"],
                    "",  # Для user_id в заявках
                    # PET
                    item["pet"], "", "",
                    # Алюминий
                    item["aluminum"], "", "",
                    # Стекло
                    item["glass"], "", "",
                    # Остальные поля для заявок пустые
                    *([""] * 33),  # 11 полей × 3 колонки
                    
                ]
            else:
                row = [
                    "Отгрузка",
                    item["timestamp"].strftime('%Y-%m-%d %H:%M'),
                    item["point_id"],
                    item["user_id"],
                    # PET
                    item["pet_kg"], item["pet_price"], item["pet_total"],
                    # Алюминий
                    item["alum_kg"], item["alum_price"], item["alum_total"],
                    # Стекло
                    item["glass_kg"], item["glass_price"], item["glass_total"],
                    # Бумага
                    item["paper_kg"], item["paper_price"], item["paper_total"],
                    # Металл
                    item["metal_kg"], item["metal_price"], item["metal_total"],
                    # Масло
                    item["oil_kg"], item["oil_price"], item["oil_total"],
                    # Другое
                    item["other_kg"], item["other_price"], item["other_total"],
                    # Смеси
                    item["alum_pl_mix_kg"], item["alum_pl_mix_price"], item["alum_pl_mix_total"],
                    item["alum_pl_glass_mix_kg"], item["alum_pl_glass_mix_price"], item["alum_pl_glass_mix_total"],
                    item["alum_iron_cans_mix_kg"], item["alum_iron_cans_mix_price"], item["alum_iron_cans_mix_total"],
                    item["pet_mix_kg"], item["pet_mix_price"], item["pet_mix_total"],
                    item["other_mix_kg"], item["other_mix_price"], item["other_mix_total"],
                    # Итоги
                    item["total_pay"],
                    ""  # Для activity в отгрузках
                ]
            ws_combined.append(row)
    
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    await callback.message.answer_document(FSInputFile(filename), reply_markup=admin_keyboard())
    os.remove(filename)
    

# Основное меню водителя
@admin.message(Command('driver'))
async def cmd_driver(message: Message):
    await message.answer("Выберите действие:", reply_markup=driver_keyboard())



@admin.callback_query(F.data == "add_shipment")
async def process_add_shipment(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ID точки:')
    await state.set_state(ShipmentStates.point_id)
    await callback.answer()

@admin.message(ShipmentStates.point_id)
async def process_point_id(message: Message, state: FSMContext):
    try:
        point_id = int(message.text)
        await state.update_data(point_id=point_id)
        await message.answer('Выберите категорию:', reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: ID точки должен быть целым числом. Пожалуйста, введите ID точки заново.")

# Обработчики выбора категорий
@admin.callback_query(F.data == "category_main")
async def select_main_materials(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите материал:", reply_markup=get_main_materials_keyboard())
    await callback.answer()

@admin.callback_query(F.data == "category_secondary")
async def select_secondary_materials(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите материал:", reply_markup=get_secondary_materials_keyboard())
    await callback.answer()

@admin.callback_query(F.data == "category_mix")
async def select_mix_materials(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите смешанный материал:", reply_markup=get_mix_materials_keyboard())
    await callback.answer()

@admin.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите категорию:", reply_markup=get_category_keyboard())
    await callback.answer()

# Обработчики для основных материалов
@admin.callback_query(F.data == "material_alum")
async def process_alum_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес алюминия (кг):")
    await state.set_state(ShipmentStates.alum_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_kg)
async def process_alum_kg(message: Message, state: FSMContext):
    try:
        alum_kg = float(message.text)
        if alum_kg < 0:
            raise ValueError
        await state.update_data(alum_kg=alum_kg)
        
        if alum_kg == 0:
            await state.update_data(alum_price=0.0)
            await message.answer("Вес алюминия равен 0.", reply_markup=get_category_keyboard())
        else:
            await message.answer("Введите цену за кг алюминия:")
            await state.set_state(ShipmentStates.alum_price)
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

@admin.message(ShipmentStates.alum_price)
async def process_alum_price(message: Message, state: FSMContext):
    try:
        alum_price = float(message.text)
        if alum_price < 0:
            raise ValueError
        await state.update_data(alum_price=alum_price)
        await message.answer("Данные по алюминию сохранены.", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: Цена должна быть положительным числом. Введите цену заново:")

# Обработчики для PET (пластика)
@admin.callback_query(F.data == "material_pet")
async def process_pet_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес PET (кг):")
    await state.set_state(ShipmentStates.pet_kg)
    await callback.answer()

@admin.message(ShipmentStates.pet_kg)
async def process_pet_kg(message: Message, state: FSMContext):
    try:
        pet_kg = float(message.text)
        if pet_kg < 0:
            raise ValueError
        await state.update_data(pet_kg=pet_kg)
        
        if pet_kg == 0:
            await state.update_data(pet_price=0.0)
            await message.answer("Вес PET равен 0.", reply_markup=get_category_keyboard())
        else:
            await message.answer("Введите цену за кг PET:")
            await state.set_state(ShipmentStates.pet_price)
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

@admin.message(ShipmentStates.pet_price)
async def process_pet_price(message: Message, state: FSMContext):
    try:
        pet_price = float(message.text)
        if pet_price < 0:
            raise ValueError
        await state.update_data(pet_price=pet_price)
        await message.answer("Данные по PET сохранены.", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: Цена должна быть положительным числом. Введите цену заново:")

# Обработчики для стекла
@admin.callback_query(F.data == "material_glass")
async def process_glass_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес стекла (кг):")
    await state.set_state(ShipmentStates.glass_kg)
    await callback.answer()

@admin.message(ShipmentStates.glass_kg)
async def process_glass_kg(message: Message, state: FSMContext):
    try:
        glass_kg = float(message.text)
        if glass_kg < 0:
            raise ValueError
        await state.update_data(glass_kg=glass_kg)
        
        if glass_kg == 0:
            await state.update_data(glass_price=0.0)
            await message.answer("Вес стекла равен 0.", reply_markup=get_category_keyboard())
        else:
            await message.answer("Введите цену за кг стекла:")
            await state.set_state(ShipmentStates.glass_price)
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

@admin.message(ShipmentStates.glass_price)
async def process_glass_price(message: Message, state: FSMContext):
    try:
        glass_price = float(message.text)
        if glass_price < 0:
            raise ValueError
        await state.update_data(glass_price=glass_price)
        await message.answer("Данные по стеклу сохранены.", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: Цена должна быть положительным числом. Введите цену заново:")

# Обработчики для бумаги
@admin.callback_query(F.data == "material_paper")
async def process_paper_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес бумаги (кг):")
    await state.set_state(ShipmentStates.paper_kg)
    await callback.answer()

@admin.message(ShipmentStates.paper_kg)
async def process_paper_kg(message: Message, state: FSMContext):
    try:
        paper_kg = float(message.text)
        if paper_kg < 0:
            raise ValueError
        await state.update_data(paper_kg=paper_kg)
        
        if paper_kg == 0:
            await state.update_data(paper_price=0.0)
            await message.answer("Вес бумаги равен 0.", reply_markup=get_category_keyboard())
        else:
            await message.answer("Введите цену за кг бумаги:")
            await state.set_state(ShipmentStates.paper_price)
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

@admin.message(ShipmentStates.paper_price)
async def process_paper_price(message: Message, state: FSMContext):
    try:
        paper_price = float(message.text)
        if paper_price < 0:
            raise ValueError
        await state.update_data(paper_price=paper_price)
        await message.answer("Данные по бумаге сохранены.", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: Цена должна быть положительным числом. Введите цену заново:")

# Обработчики для металла
@admin.callback_query(F.data == "material_metal")
async def process_metal_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес металла (кг):")
    await state.set_state(ShipmentStates.metal_kg)
    await callback.answer()

@admin.message(ShipmentStates.metal_kg)
async def process_metal_kg(message: Message, state: FSMContext):
    try:
        metal_kg = float(message.text)
        if metal_kg < 0:
            raise ValueError
        await state.update_data(metal_kg=metal_kg)
        
        if metal_kg == 0:
            await state.update_data(metal_price=0.0)
            await message.answer("Вес металла равен 0.", reply_markup=get_category_keyboard())
        else:
            await message.answer("Введите цену за кг металла:")
            await state.set_state(ShipmentStates.metal_price)
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

@admin.message(ShipmentStates.metal_price)
async def process_metal_price(message: Message, state: FSMContext):
    try:
        metal_price = float(message.text)
        if metal_price < 0:
            raise ValueError
        await state.update_data(metal_price=metal_price)
        await message.answer("Данные по металлу сохранены.", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: Цена должна быть положительным числом. Введите цену заново:")

# Обработчики для масла
@admin.callback_query(F.data == "material_oil")
async def process_oil_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес масла (кг):")
    await state.set_state(ShipmentStates.oil_kg)
    await callback.answer()

@admin.message(ShipmentStates.oil_kg)
async def process_oil_kg(message: Message, state: FSMContext):
    try:
        oil_kg = float(message.text)
        if oil_kg < 0:
            raise ValueError
        await state.update_data(oil_kg=oil_kg)
        
        if oil_kg == 0:
            await state.update_data(oil_price=0.0)
            await message.answer("Вес масла равен 0.", reply_markup=get_category_keyboard())
        else:
            await message.answer("Введите цену за кг масла:")
            await state.set_state(ShipmentStates.oil_price)
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

@admin.message(ShipmentStates.oil_price)
async def process_oil_price(message: Message, state: FSMContext):
    try:
        oil_price = float(message.text)
        if oil_price < 0:
            raise ValueError
        await state.update_data(oil_price=oil_price)
        await message.answer("Данные по маслу сохранены.", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: Цена должна быть положительным числом. Введите цену заново:")

# Обработчики для прочих материалов
@admin.callback_query(F.data == "material_other")
async def process_other_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес прочих материалов (кг):")
    await state.set_state(ShipmentStates.other_kg)
    await callback.answer()

@admin.message(ShipmentStates.other_kg)
async def process_other_kg(message: Message, state: FSMContext):
    try:
        other_kg = float(message.text)
        if other_kg < 0:
            raise ValueError
        await state.update_data(other_kg=other_kg)
        
        if other_kg == 0:
            await state.update_data(other_price=0.0)
            await message.answer("Вес прочих материалов равен 0.", reply_markup=get_category_keyboard())
        else:
            await message.answer("Введите цену за кг прочих материалов:")
            await state.set_state(ShipmentStates.other_price)
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

@admin.message(ShipmentStates.other_price)
async def process_other_price(message: Message, state: FSMContext):
    try:
        other_price = float(message.text)
        if other_price < 0:
            raise ValueError
        await state.update_data(other_price=other_price)
        await message.answer("Данные по прочим материалам сохранены.", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("Ошибка: Цена должна быть положительным числом. Введите цену заново:")

        
# Фиксированные цены для смешанных материалов
MIX_PRICES = {
    'alum_pl_mix': 8.0,        # алюм-пластик
    'alum_pl_glass_mix': 2.0,  # алюм-пластик-стекло
    'alum_iron_cans_mix': 3.0, # алюм-железные банки
    'pet_mix': 5.0,            # смешанный пластик
    'other_mix': 1.0           # прочий микс
}

# Обработчики для алюм-пластика
@admin.callback_query(F.data == "material_alum_pl_mix")
async def process_alum_pl_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес алюм-пластика (кг):")
    await state.set_state(ShipmentStates.alum_pl_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_pl_mix_kg)
async def process_alum_pl_mix_kg(message: Message, state: FSMContext):
    try:
        alum_pl_mix_kg = float(message.text)
        if alum_pl_mix_kg < 0:
            raise ValueError
        
        # Устанавливаем фиксированную цену
        alum_pl_mix_price = MIX_PRICES['alum_pl_mix']
        await state.update_data(
            alum_pl_mix_kg=alum_pl_mix_kg,
            alum_pl_mix_price=alum_pl_mix_price
        )
        
        await message.answer(
            f"Данные по алюм-пластику сохранены.\n"
            f"Вес: {alum_pl_mix_kg} кг\n"
            f"Цена: {alum_pl_mix_price} руб/кг (фиксированная)",
            reply_markup=get_category_keyboard()
        )
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

# Обработчики для алюм-пластик-стекло
@admin.callback_query(F.data == "material_alum_pl_glass_mix")
async def process_alum_pl_glass_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес алюм-пластик-стекло (кг):")
    await state.set_state(ShipmentStates.alum_pl_glass_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_pl_glass_mix_kg)
async def process_alum_pl_glass_mix_kg(message: Message, state: FSMContext):
    try:
        alum_pl_glass_mix_kg = float(message.text)
        if alum_pl_glass_mix_kg < 0:
            raise ValueError
        
        # Устанавливаем фиксированную цену
        alum_pl_glass_mix_price = MIX_PRICES['alum_pl_glass_mix']
        await state.update_data(
            alum_pl_glass_mix_kg=alum_pl_glass_mix_kg,
            alum_pl_glass_mix_price=alum_pl_glass_mix_price
        )
        
        await message.answer(
            f"Данные по алюм-пластик-стекло сохранены.\n"
            f"Вес: {alum_pl_glass_mix_kg} кг\n"
            f"Цена: {alum_pl_glass_mix_price} руб/кг (фиксированная)",
            reply_markup=get_category_keyboard()
        )
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

# Обработчики для алюм-железные банки
@admin.callback_query(F.data == "material_alum_iron_cans_mix")
async def process_alum_iron_cans_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес алюм-железные банки (кг):")
    await state.set_state(ShipmentStates.alum_iron_cans_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_iron_cans_mix_kg)
async def process_alum_iron_cans_mix_kg(message: Message, state: FSMContext):
    try:
        alum_iron_cans_mix_kg = float(message.text)
        if alum_iron_cans_mix_kg < 0:
            raise ValueError
        
        # Устанавливаем фиксированную цену
        alum_iron_cans_mix_price = MIX_PRICES['alum_iron_cans_mix']
        await state.update_data(
            alum_iron_cans_mix_kg=alum_iron_cans_mix_kg,
            alum_iron_cans_mix_price=alum_iron_cans_mix_price
        )
        
        await message.answer(
            f"Данные по алюм-железные банки сохранены.\n"
            f"Вес: {alum_iron_cans_mix_kg} кг\n"
            f"Цена: {alum_iron_cans_mix_price} руб/кг (фиксированная)",
            reply_markup=get_category_keyboard()
        )
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

# Обработчики для смешанного пластика
@admin.callback_query(F.data == "material_pet_mix")
async def process_pet_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес смешанного пластика (кг):")
    await state.set_state(ShipmentStates.pet_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.pet_mix_kg)
async def process_pet_mix_kg(message: Message, state: FSMContext):
    try:
        pet_mix_kg = float(message.text)
        if pet_mix_kg < 0:
            raise ValueError
        
        # Устанавливаем фиксированную цену
        pet_mix_price = MIX_PRICES['pet_mix']
        await state.update_data(
            pet_mix_kg=pet_mix_kg,
            pet_mix_price=pet_mix_price
        )
        
        await message.answer(
            f"Данные по смешанному пластику сохранены.\n"
            f"Вес: {pet_mix_kg} кг\n"
            f"Цена: {pet_mix_price} руб/кг (фиксированная)",
            reply_markup=get_category_keyboard()
        )
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

# Обработчики для прочего микса
@admin.callback_query(F.data == "material_other_mix")
async def process_other_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите вес прочего микса (кг):")
    await state.set_state(ShipmentStates.other_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.other_mix_kg)
async def process_other_mix_kg(message: Message, state: FSMContext):
    try:
        other_mix_kg = float(message.text)
        if other_mix_kg < 0:
            raise ValueError
        
        # Устанавливаем фиксированную цену
        other_mix_price = MIX_PRICES['other_mix']
        await state.update_data(
            other_mix_kg=other_mix_kg,
            other_mix_price=other_mix_price
        )
        
        await message.answer(
            f"Данные по прочему миксу сохранены.\n"
            f"Вес: {other_mix_kg} кг\n"
            f"Цена: {other_mix_price} руб/кг (фиксированная)",
            reply_markup=get_category_keyboard()
        )
    except ValueError:
        await message.answer("Ошибка: Вес должен быть положительным числом. Введите вес заново:")

# Обработчик завершения ввода
@admin.callback_query(F.data == "finish_shipment")
async def finish_shipment(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    # Формируем сводку по всем введенным данным
    summary = "📋 Сводка по отгрузке:\n\n"
    total_weight = 0
    total_cost = 0
    
    # Основные материалы
    if 'alum_kg' in user_data:
        alum_cost = user_data.get('alum_kg', 0) * user_data.get('alum_price', 0)
        summary += f"🔹 Алюминий: {user_data['alum_kg']} кг, {alum_cost:.2f} руб.\n"
        total_weight += user_data['alum_kg']
        total_cost += alum_cost
    
    if 'pet_kg' in user_data:
        pet_cost = user_data.get('pet_kg', 0) * user_data.get('pet_price', 0)
        summary += f"🔹 Пластик (PET): {user_data['pet_kg']} кг, {pet_cost:.2f} руб.\n"
        total_weight += user_data['pet_kg']
        total_cost += pet_cost
    
    if 'glass_kg' in user_data:
        glass_cost = user_data.get('glass_kg', 0) * user_data.get('glass_price', 0)
        summary += f"🔹 Стекло: {user_data['glass_kg']} кг, {glass_cost:.2f} руб.\n"
        total_weight += user_data['glass_kg']
        total_cost += glass_cost
    
    # Дополнительные материалы
    if 'paper_kg' in user_data:
        paper_cost = user_data.get('paper_kg', 0) * user_data.get('paper_price', 0)
        summary += f"🔸 Бумага: {user_data['paper_kg']} кг, {paper_cost:.2f} руб.\n"
        total_weight += user_data['paper_kg']
        total_cost += paper_cost
    
    if 'metal_kg' in user_data:
        metal_cost = user_data.get('metal_kg', 0) * user_data.get('metal_price', 0)
        summary += f"🔸 Металл: {user_data['metal_kg']} кг, {metal_cost:.2f} руб.\n"
        total_weight += user_data['metal_kg']
        total_cost += metal_cost
    
    if 'oil_kg' in user_data:
        oil_cost = user_data.get('oil_kg', 0) * user_data.get('oil_price', 0)
        summary += f"🔸 Масло: {user_data['oil_kg']} кг, {oil_cost:.2f} руб.\n"
        total_weight += user_data['oil_kg']
        total_cost += oil_cost
    
    if 'other_kg' in user_data:
        other_cost = user_data.get('other_kg', 0) * user_data.get('other_price', 0)
        summary += f"🔸 Прочие: {user_data['other_kg']} кг, {other_cost:.2f} руб.\n"
        total_weight += user_data['other_kg']
        total_cost += other_cost
    
    # Смешанные материалы
    if 'alum_pl_mix_kg' in user_data:
        alum_pl_mix_cost = user_data.get('alum_pl_mix_kg', 0) * user_data.get('alum_pl_mix_price', 0)
        summary += f"🔺 Алюм-пластик: {user_data['alum_pl_mix_kg']} кг, {alum_pl_mix_cost:.2f} руб.\n"
        total_weight += user_data['alum_pl_mix_kg']
        total_cost += alum_pl_mix_cost
    
    if 'alum_pl_glass_mix_kg' in user_data:
        alum_pl_glass_mix_cost = user_data.get('alum_pl_glass_mix_kg', 0) * user_data.get('alum_pl_glass_mix_price', 0)
        summary += f"🔺 Алюм-пластик-стекло: {user_data['alum_pl_glass_mix_kg']} кг, {alum_pl_glass_mix_cost:.2f} руб.\n"
        total_weight += user_data['alum_pl_glass_mix_kg']
        total_cost += alum_pl_glass_mix_cost
    
    if 'alum_iron_cans_mix_kg' in user_data:
        alum_iron_cans_mix_cost = user_data.get('alum_iron_cans_mix_kg', 0) * user_data.get('alum_iron_cans_mix_price', 0)
        summary += f"🔺 Алюм-железные банки: {user_data['alum_iron_cans_mix_kg']} кг, {alum_iron_cans_mix_cost:.2f} руб.\n"
        total_weight += user_data['alum_iron_cans_mix_kg']
        total_cost += alum_iron_cans_mix_cost
    
    if 'pet_mix_kg' in user_data:
        pet_mix_cost = user_data.get('pet_mix_kg', 0) * user_data.get('pet_mix_price', 0)
        summary += f"🔺 Смешанный пластик: {user_data['pet_mix_kg']} кг, {pet_mix_cost:.2f} руб.\n"
        total_weight += user_data['pet_mix_kg']
        total_cost += pet_mix_cost
    
    if 'other_mix_kg' in user_data:
        other_mix_cost = user_data.get('other_mix_kg', 0) * user_data.get('other_mix_price', 0)
        summary += f"🔺 Прочий микс: {user_data['other_mix_kg']} кг, {other_mix_cost:.2f} руб.\n"
        total_weight += user_data['other_mix_kg']
        total_cost += other_mix_cost
    
    summary += f"\n💎 Итого: {total_weight:.2f} кг, {total_cost:.2f} руб."
    
    await callback.message.edit_text(summary, reply_markup=get_confirmation_keyboard())
    await callback.answer()

# Обработчик подтверждения
@admin.callback_query(F.data == "confirm_shipment")
async def confirm_shipment(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    try:
        user = await get_user_by_tg_id(callback.from_user.id)
        if not user:
            raise ValueError("Пользователь не найден.")
        
        # Рассчитываем общие суммы для каждого материала
        alum_total = user_data.get('alum_kg', 0.0) * user_data.get('alum_price', 0.0)
        pet_total = user_data.get('pet_kg', 0.0) * user_data.get('pet_price', 0.0)
        glass_total = user_data.get('glass_kg', 0.0) * user_data.get('glass_price', 0.0)
        paper_total = user_data.get('paper_kg', 0.0) * user_data.get('paper_price', 0.0)
        metal_total = user_data.get('metal_kg', 0.0) * user_data.get('metal_price', 0.0)
        oil_total = user_data.get('oil_kg', 0.0) * user_data.get('oil_price', 0.0)
        other_total = user_data.get('other_kg', 0.0) * user_data.get('other_price', 0.0)
        alum_pl_mix_total = user_data.get('alum_pl_mix_kg', 0.0) * user_data.get('alum_pl_mix_price', 0.0)
        alum_pl_glass_mix_total = user_data.get('alum_pl_glass_mix_kg', 0.0) * user_data.get('alum_pl_glass_mix_price', 0.0)
        alum_iron_cans_mix_total = user_data.get('alum_iron_cans_mix_kg', 0.0) * user_data.get('alum_iron_cans_mix_price', 0.0)
        pet_mix_total = user_data.get('pet_mix_kg', 0.0) * user_data.get('pet_mix_price', 0.0)
        other_mix_total = user_data.get('other_mix_kg', 0.0) * user_data.get('other_mix_price', 0.0)

        # Общая сумма
        total_pay = (
            alum_total + pet_total + glass_total + paper_total + 
            metal_total + oil_total + other_total + alum_pl_mix_total + 
            alum_pl_glass_mix_total + alum_iron_cans_mix_total + 
            pet_mix_total + other_mix_total
        )

        # Добавляем отгрузку со всеми полями
        await add_shipment(
            point_id=user_data['point_id'],
            user_id=user.tg_id,
            alum_kg=user_data.get('alum_kg', 0.0),
            alum_price=user_data.get('alum_price', 0.0),
            alum_total=alum_total,
            pet_kg=user_data.get('pet_kg', 0.0),
            pet_price=user_data.get('pet_price', 0.0),
            pet_total=pet_total,
            glass_kg=user_data.get('glass_kg', 0.0),
            glass_price=user_data.get('glass_price', 0.0),
            glass_total=glass_total,
            paper_kg=user_data.get('paper_kg', 0.0),
            paper_price=user_data.get('paper_price', 0.0),
            paper_total=paper_total,
            metal_kg=user_data.get('metal_kg', 0.0),
            metal_price=user_data.get('metal_price', 0.0),
            metal_total=metal_total,
            oil_kg=user_data.get('oil_kg', 0.0),
            oil_price=user_data.get('oil_price', 0.0),
            oil_total=oil_total,
            other_kg=user_data.get('other_kg', 0.0),
            other_price=user_data.get('other_price', 0.0),
            other_total=other_total,
            alum_pl_mix_kg=user_data.get('alum_pl_mix_kg', 0.0),
            alum_pl_mix_price=user_data.get('alum_pl_mix_price', 0.0),
            alum_pl_mix_total=alum_pl_mix_total,
            alum_pl_glass_mix_kg=user_data.get('alum_pl_glass_mix_kg', 0.0),
            alum_pl_glass_mix_price=user_data.get('alum_pl_glass_mix_price', 0.0),
            alum_pl_glass_mix_total=alum_pl_glass_mix_total,
            alum_iron_cans_mix_kg=user_data.get('alum_iron_cans_mix_kg', 0.0),
            alum_iron_cans_mix_price=user_data.get('alum_iron_cans_mix_price', 0.0),
            alum_iron_cans_mix_total=alum_iron_cans_mix_total,
            pet_mix_kg=user_data.get('pet_mix_kg', 0.0),
            pet_mix_price=user_data.get('pet_mix_price', 0.0),
            pet_mix_total=pet_mix_total,
            other_mix_kg=user_data.get('other_mix_kg', 0.0),
            other_mix_price=user_data.get('other_mix_price', 0.0),
            other_mix_total=other_mix_total,
            total_pay=total_pay
        )
        
        # Очищаем количество мешков, так как отгрузка успешна
        await update_bags_count(user_data['point_id'], 0)
        
        # Отправляем уведомление пользователю
        point = await get_point_by_id(user_data['point_id'])
        if point:
            user = await get_user_by_point_id(user_data['point_id'])
            if user:
                total_weight = (
                    user_data.get('alum_kg', 0) +
                    user_data.get('pet_kg', 0) +
                    user_data.get('glass_kg', 0) +
                    user_data.get('paper_kg', 0) +
                    user_data.get('metal_kg', 0) +
                    user_data.get('oil_kg', 0) +
                    user_data.get('other_kg', 0) +
                    user_data.get('alum_pl_mix_kg', 0) +
                    user_data.get('alum_pl_glass_mix_kg', 0) +
                    user_data.get('alum_iron_cans_mix_kg', 0) +
                    user_data.get('pet_mix_kg', 0) +
                    user_data.get('other_mix_kg', 0)
                )
                
                await callback.bot.send_message(
                    user.tg_id,
                    f"✅ Ваш мешок с мусором был обработан\n\n"
                    f"📦 Общий вес: {total_weight:.2f} кг\n"
                    f"💰 Общая стоимость: {total_pay:.2f} руб.\n\n"
                    f"Спасибо вам!"
                )
        
        await callback.message.edit_text(
            '✅ Данные об отгрузке успешно добавлены! Количество мешков обнулено.', reply_markup=driver_keyboard()
        )
    except ValueError as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        await callback.message.edit_text(f"❌ Произошла непредвиденная ошибка: {str(e)}")
    finally:
        await state.clear()
        await callback.answer()

# Обработчик отмены
@admin.callback_query(F.data == "cancel_shipment")
async def cancel_shipment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Отгрузка отменена. Все данные удалены.",
       
    )
    await callback.answer()

# Обработчик для кнопки "Отменить" в процессе ввода
@admin.callback_query(F.data == "cancel_during_input")
async def cancel_during_input(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Ввод данных прерван. Все временные данные удалены.",
        
    )
    await callback.answer()


@admin.callback_query(F.data == "create_point")
async def start_create_point(callback: CallbackQuery, state: FSMContext):
    """Начало процесса создания точки"""
    await callback.message.answer(
        "Введите ID новой точки в формате RZZN, где:\n"
        "R - номер региона (1 цифра)\n"
        "ZZ - номер зоны (2 цифры)\n"
        "N - номер точки в зоне (1 цифра)\n"
        "Пример: 1021 - точка в регионе 1, зоне 02, номер точки 1",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.point_id)
    await callback.answer()

@admin.message(CreatePoint.point_id, F.text.regexp(r'^\d{4}$'))
async def process_point_id(message: Message, state: FSMContext):
    """Обработка ID точки с проверкой формата"""
    point_id = message.text
    region_id = int(point_id[0])
    zone_num = int(point_id[1:3])  # Номер зоны (2 цифры)
    zone_id = int(f"{region_id}{zone_num:02d}")  # Полный ID зоны (3 цифры)
    point_num = int(point_id[3])
    
    # Проверяем, существует ли уже точка с таким ID
    if await get_point_by_id(point_id):
        await message.answer(
            "Точка с таким ID уже существует! Пожалуйста, введите другой ID.",
            reply_markup=cancel_keyboard()
        )
        return
    
    await state.update_data(
        point_id=point_id,
        region_id=region_id,
        zone_num=zone_num,  # Сохраняем номер зоны (2 цифры)
        zone_id=zone_id,     # Сохраняем полный ID зоны (3 цифры)
        point_num=point_num
    )
    
    await message.answer(
        f"ID точки: {point_id}\n"
        f"Регион: {region_id}\n"
        f"Номер зоны: {zone_num}\n"
        f"Номер точки: {point_num}\n\n"
        "Введите название точки:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.point_name)

@admin.message(CreatePoint.point_id)
async def process_point_id_invalid(message: Message):
    """Обработка неверного формата ID точки"""
    await message.answer(
        "Неверный формат ID точки! Должно быть 4 цифры в формате RZZN.\n"
        "Пример: 1021 - точка в регионе 1, зоне 02, номер точки 1",
        reply_markup=cancel_keyboard()
    )

@admin.message(CreatePoint.point_name)
async def process_point_name(message: Message, state: FSMContext):
    """Обработка названия точки"""
    await state.update_data(point_name=message.text)
    await message.answer(
        "Введите имя владельца точки:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.point_owner_name)

@admin.message(CreatePoint.point_owner_name)
async def process_owner_name(message: Message, state: FSMContext):
    """Обработка имени владельца"""
    await state.update_data(point_owner_name=message.text)
    await message.answer(
        "Введите номер телефона владельца:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.phone_number)

@admin.message(CreatePoint.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    await state.update_data(phone_number=message.text)
    await message.answer(
        "Введите адрес точки:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.address)

@admin.message(CreatePoint.address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса"""
    await state.update_data(address=message.text)
    
    data = await state.get_data()
    
    # Формируем сообщение для подтверждения
    confirm_text = (
        "Проверьте введенные данные:\n\n"
        f"ID точки: {data['point_id']}\n"
        f"Регион: {data['region_id']}\n"
        f"Зона: {data['zone_num']}\n"
        f"Номер точки: {data['point_num']}\n"
        f"Название: {data['point_name']}\n"
        f"Владелец: {data['point_owner_name']}\n"
        f"Телефон: {data['phone_number']}\n"
        f"Адрес: {data['address']}\n\n"
        "Все верно?"
    )
    
    await message.answer(confirm_text, reply_markup=confirm_keyboard())
    await state.set_state(CreatePoint.confirmation)

@admin.callback_query(CreatePoint.confirmation, F.data == "confirm")
async def confirm_point_creation(callback: CallbackQuery, state: FSMContext):
    """Подтверждение создания точки"""
    data = await state.get_data()
    
    try:
        # Сначала проверяем/создаем регион
        if not await get_region_by_id(data['region_id']):
            await add_region(data['region_id'])
        
        # Затем проверяем/создаем зону (используем zone_id из 3 цифр)
        if not await get_zone_by_id(data['zone_id']):
            await add_zone(data['zone_id'], data['region_id'])
        
        # Создаем точку (используем point_id как строку)
        await add_point(
            point_id=data['point_id'],
            point_name=data['point_name'],
            point_owner_name=data['point_owner_name'],
            phone_number=data['phone_number'],
            address=data['address'],
            bags_count=0,
            zone_id=data['zone_id']  # Используем zone_id из 3 цифр
        )
        
        await callback.message.answer(
            "✅ Точка успешно создана!",
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка при создании точки: {str(e)}",
            reply_markup=admin_keyboard()
        )
    finally:
        await state.clear()

@admin.callback_query(CreatePoint.confirmation, F.data == "cancel")
async def cancel_point_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания точки"""
    await callback.message.answer(
        "❌ Создание точки отменено.",
        reply_markup=admin_keyboard()
    )
    await state.clear()

@admin.callback_query(StateFilter(CreatePoint), F.data == "cancel_operation")
async def cancel_creation_process(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса создания на любом этапе"""
    await callback.message.answer(
        "❌ Создание точки прервано.",
        reply_markup=admin_keyboard()
    )
    await state.clear()