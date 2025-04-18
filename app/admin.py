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

ADMIN_IDS = [753755508, 1582399282, 7854337092, 7854337092, 7363212828]  # ID администраторов (оставляем без изменений)

admin = Router()

class Admin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS

@admin.message(Admin(), Command("A1"))
async def admin_start(message: Message):
    """Главное меню админ-панели"""
    await message.answer(
        "ยินดีต้อนรับสู่แผงควบคุมผู้ดูแล กรุณาเลือกการดำเนินการ:",  # "Добро пожаловать в админ-панель. Выберите действие:"
        reply_markup=admin_keyboard()
    )

@admin.callback_query(Admin(), F.data == 'report')
async def cmd_report(callback: CallbackQuery, state: FSMContext):
    """Меню отчетов"""
    await callback.message.answer('กรุณาเลือกรูปแบบรายงาน:', reply_markup=report_keyboard())  # "Выберите тип отчета:"
    await state.set_state(Reports.report_type)

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_zone")
async def process_zones_report(callback: CallbackQuery):
    """Отчет по зонам"""
    zones = await get_all_zones()
    
    if not zones:
        await callback.message.answer('ไม่มีข้อมูลโซน')  # "Нет данных по зонам."
        return
    
    report_messages = ["รายงานตามโซน:\n\n"]  # "Отчет по зонам:"
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
    
    await callback.message.answer('กรุณาเลือกการดำเนินการ:', reply_markup=admin_keyboard())  # "Выберите действие:"

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_region")
async def process_regions_report(callback: CallbackQuery):
    """Отчет по регионам"""
    regions = await get_all_regions()
    
    if not regions:
        await callback.message.answer('ไม่มีข้อมูลภูมิภาค')  # "Нет данных по регионам."
        return
    
    report_messages = ["รายงานตามภูมิภาค:\n\n"]  # "Отчет по регионам:"
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
            f"ภูมิภาค ID: {region.region_id}\n"  # "Регион ID:"
            f"จำนวนโซน: {zone_count}\n"  # "Зон:"
            f"จำนวนจุด: {point_count}\n"  # "Точек:"
            f"จำนวนถุงทั้งหมด: {total_bags}\n\n"  # "Всего мешков:"
        )
        
        if len(report_messages[-1]) + len(region_info) > 4000:
            report_messages.append(region_info)
        else:
            report_messages[-1] += region_info
    
    for msg in report_messages:
        await callback.message.answer(msg)
    
    await callback.message.answer('กรุณาเลือกการดำเนินการ:', reply_markup=admin_keyboard())  # "Выберите действие:"

@admin.callback_query(Admin(), Reports.report_type, F.data == "report_region_detail")
async def ask_region_id(callback: CallbackQuery, state: FSMContext):
    """Запрос ID региона для детального отчета"""
    await callback.message.answer("กรุณากรอก ID ภูมิภาคสำหรับรายงาน:")  # "Введите ID региона для отчета:"
    await state.set_state(Reports.waiting_region_id)

@admin.message(Admin(), Reports.waiting_region_id)
async def generate_region_detail_report(message: Message, state: FSMContext):
    """Генерация детального отчета по региону"""
    try:
        region_id = int(message.text.strip())
    except ValueError:
        await message.answer("กรุณากรอก ID ภูมิภาคเป็นตัวเลข")  # "Пожалуйста, введите числовой ID региона."
        return
    
    # Получаем данные по региону
    region = await get_region_by_id(region_id)
    if not region:
        await message.answer(f"ไม่พบภูมิภาค ID {region_id}")  # f"Регион с ID {region_id} не найден."
        await state.clear()
        return
    
    # Получаем все зоны в регионе
    zones = await get_zones_by_region(region_id)
    if not zones:
        await message.answer(f"ไม่มีโซนในภูมิภาค {region_id}")  # f"В регионе {region_id} нет зон."
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
        
        if zone_points > 0:
            zones_data.append((zone.zone_id, zone_points, zone_bags))
    
    # Формируем сообщения с учетом лимита
    header = (
        f"📊 รายงานภูมิภาค {region_id}:\n"  # f"📊 Отчет по региону {region_id}:"
        f"จำนวนจุดทั้งหมด: {total_points}\n"  # f"Всего точек: {total_points}"
        f"จำนวนถุงทั้งหมด: {total_bags}\n\n"  # f"Всего мешков готово: {total_bags}"
        f"รายละเอียดโซน:\n"  # f"Детали по зонам:"
    )
    
    report_messages = [header]
    
    # Добавляем информацию по зонам
    for zone_id, zone_points, zone_bags in zones_data:
        zone_info = f"▪️ โซน {zone_id} - {zone_points} จุด ({zone_bags} ถุง)\n"  # f"▪️ Зона {zone_id} - {zone_points} точек ({zone_bags} мешков)"
        
        if len(report_messages[-1]) + len(zone_info) > 4000:
            report_messages.append(zone_info)
        else:
            report_messages[-1] += zone_info
    
    for msg in report_messages:
        await message.answer(msg)
    
    await message.answer('กรุณาเลือกการดำเนินการ:', reply_markup=admin_keyboard())  # "Выберите действие:"
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
    
    # 1. Лист с заявками (тайский + английский)
    if requests:
        ws_requests = wb.create_sheet("Requests")
        headers_requests = [
            "Date", 
            "Point ID", 
            "User ID", 
            "Activity Type",
            "PET Bags", 
            "Aluminum Bags", 
            "Glass Bags", 
            "Other Bags",
            "Total Quantity"
        ]
        ws_requests.append(headers_requests)
        
        for req in requests:
            ws_requests.append([
                req.timestamp.strftime('%Y-%m-%d %H:%M'),
                req.point_id,
                req.user_id,
                req.activity,
                req.pet_bag or 0,
                req.aluminum_bag or 0,
                req.glass_bag or 0,
                req.other or 0,
                (req.pet_bag or 0) + (req.aluminum_bag or 0) + 
                (req.glass_bag or 0) + (req.other or 0)
            ])
    
    # 2. Лист с отгрузками (тайский + английский)
    if shipments:
        ws_shipments = wb.create_sheet("Shipments")
        headers_shipments = [
            "Date", 
            "Point ID", 
            "Driver ID", 
            "Total Payment",
            # PET
            "PET kg", "PET Price", "PET Total",
            # Алюминий
            "Aluminum kg", "Aluminum Price", "Aluminum Total",
            # Стекло
            "Glass kg", "Glass Price", "Glass Total",
            # Бумага
            "Paper kg", "Paper Price", "Paper Total",
            # Металл
            "Metal kg", "Metal Price", "Metal Total",
            # Масло
            "Oil kg", "Oil Price", "Oil Total",
            # Другое
            "Other kg", "Other Price", "Other Total",
            # Смеси
            "Alum+Plastic kg", "Alum+Plastic Price", "Alum+Plastic Total",
            "Alum+Plastic+Glass kg", "Alum+Plastic+Glass Price", "Alum+Plastic+Glass Total",
            "Alum+Iron kg", "Alum+Iron Price", "Alum+Iron Total",
            "PET Mix kg", "PET Mix Price", "PET Mix Total",
            "Other Mix kg", "Other Mix Price", "Other Mix Total"
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
    
    # 3. Общий лист (тайский + английский)
    if combined:
        ws_combined = wb.create_sheet("All Data")
        headers_combined = [
            "Type", 
            "Date", 
            "Point ID", 
            "User ID",
            # Основные материалы
            "PET (Bags/kg)", "PET Price", "PET Total",
            "Aluminum (Bags/kg)", "Aluminum Price", "Aluminum Total",
            "Glass (Bags/kg)", "Glass Price", "Glass Total",
            # Дополнительные материалы
            "Paper kg", "Paper Price", "Paper Total",
            "Metal kg", "Metal Price", "Metal Total",
            "Oil kg", "Oil Price", "Oil Total",
            "Other kg", "Other Price", "Other Total",
            # Смеси
            "Alum+Plastic kg", "Alum+Plastic Price", "Alum+Plastic Total",
            "Alum+Plastic+Glass kg", "Alum+Plastic+Glass Price", "Alum+Plastic+Glass Total",
            "Alum+Iron kg", "Alum+Iron Price", "Alum+Iron Total",
            "PET Mix kg", "รPET Mix Price", "PET Mix Total",
            "Other Mix kg", "Other Mix Price", "Other Mix Total",
            # Итоги
            "Total Amount", 
            "Activity Type (for requests)"
        ]
        ws_combined.append(headers_combined)
        
        for item in combined:
            if item["type"] == "request":
                row = [
                    "Request",
                    item["timestamp"].strftime('%Y-%m-%d %H:%M'),
                    item["point_id"],
                    item["user_id"],
                    item["total"],
                    item["activity"],
                    "",
                    *([""] * 33)
                ]
            else:
                row = [
                    "Shipment",
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
                    ""
                ]
            ws_combined.append(row)
    
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    await callback.message.answer_document(FSInputFile(filename), reply_markup=admin_keyboard())
    os.remove(filename)

# Основное меню водителя
@admin.message(Command('D1'))
async def cmd_driver(message: Message):
    await message.answer("กรุณาเลือกการดำเนินการ:", reply_markup=driver_keyboard())  # "Выберите действие:"

@admin.callback_query(F.data == "add_shipment")
async def process_add_shipment(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('กรุณากรอก ID จุด:')  # "Введите ID точки:"
    await state.set_state(ShipmentStates.point_id)
    await callback.answer()

@admin.message(ShipmentStates.point_id)
async def process_point_id(message: Message, state: FSMContext):
    try:
        point_id = int(message.text)
        # Проверяем существование точки
        point = await get_point_by_id(point_id)
        if not point:
            await message.answer("ข้อผิดพลาด: ไม่พบจุดนี้ในระบบ กรุณากรอกใหม่")  # "Ошибка: Точка не найдена в системе. Пожалуйста, введите ID точки заново."
            return
            
        await state.update_data(point_id=point_id)
        await message.answer('กรุณาเลือกประเภท:', reply_markup=get_category_keyboard()) #Пожалуйста, выберите тип
    except ValueError:
        await message.answer("ข้อผิดพลาด: ID จุดต้องเป็นตัวเลขเต็ม กรุณากรอกใหม่") #Ошибка: идентификатор точки должен быть целым числом. пожалуйста, введите новый.

# Обработчики выбора категорий
@admin.callback_query(F.data == "category_main")
async def select_main_materials(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("กรุณาเลือกวัสดุ:", reply_markup=get_main_materials_keyboard())  # "Выберите материал:"
    await callback.answer()

@admin.callback_query(F.data == "category_secondary")
async def select_secondary_materials(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("กรุณาเลือกวัสดุ:", reply_markup=get_secondary_materials_keyboard())  # "Выберите материал:"
    await callback.answer()

@admin.callback_query(F.data == "category_mix")
async def select_mix_materials(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("กรุณาเลือกวัสดุผสม:", reply_markup=get_mix_materials_keyboard())  # "Выберите смешанный материал:"
    await callback.answer()

@admin.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("กรุณาเลือกประเภท:", reply_markup=get_category_keyboard())  # "Выберите категорию:"
    await callback.answer()

# Обработчики для основных материалов
@admin.callback_query(F.data == "material_alum")
async def process_alum_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักอลูมิเนียม (กก.):")  # "Введите вес алюминия (кг):"
    await state.set_state(ShipmentStates.alum_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_kg)
async def process_alum_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        alum_kg = float(text)
        if alum_kg < 0:
            raise ValueError
        await state.update_data(alum_kg=alum_kg)
        
        if alum_kg == 0:
            await state.update_data(alum_price=0.0)
            await message.answer("น้ำหนักอลูมิเนียมเป็น 0", reply_markup=get_category_keyboard())  # "Вес алюминия равен 0."
        else:
            await message.answer("กรุณากรอกราคาต่อกก. อลูมิเนียม:")  # "Введите цену за кг алюминия:"
            await state.set_state(ShipmentStates.alum_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Вес должен быть положительным числом. Введите вес заново:"

@admin.message(ShipmentStates.alum_price)
async def process_alum_price(message: Message, state: FSMContext):
    try:
        alum_price = float(message.text)
        if alum_price < 0:
            raise ValueError
        await state.update_data(alum_price=alum_price)
        await message.answer("บันทึกข้อมูลอลูมิเนียมเรียบร้อย", reply_markup=get_category_keyboard())  # "Данные по алюминию сохранены."
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Цена должна быть положительным числом. Введите цену заново:"

# Обработчики для PET (пластика)
@admin.callback_query(F.data == "material_pet")
async def process_pet_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนัก PET (กก.):")  # "Введите вес PET (кг):"
    await state.set_state(ShipmentStates.pet_kg)
    await callback.answer()

@admin.message(ShipmentStates.pet_kg)
async def process_pet_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        pet_kg = float(text)
        if pet_kg < 0:
            raise ValueError
        await state.update_data(pet_kg=pet_kg)
        
        if pet_kg == 0:
            await state.update_data(pet_price=0.0)
            await message.answer("น้ำหนัก PET เป็น 0", reply_markup=get_category_keyboard())  # "Вес PET равен 0."
        else:
            await message.answer("กรุณากรอกราคาต่อกก. PET:")  # "Введите цену за кг PET:"
            await state.set_state(ShipmentStates.pet_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Вес должен быть положительным числом. Введите вес заново:"

@admin.message(ShipmentStates.pet_price)
async def process_pet_price(message: Message, state: FSMContext):
    try:
        pet_price = float(message.text)
        if pet_price < 0:
            raise ValueError
        await state.update_data(pet_price=pet_price)
        await message.answer("บันทึกข้อมูล PET เรียบร้อย", reply_markup=get_category_keyboard())  # "Данные по PET сохранены."
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Цена должна быть положительным числом. Введите цену заново:"

# Обработчики для стекла
@admin.callback_query(F.data == "material_glass")
async def process_glass_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักแก้ว (กก.):")  # "Введите вес стекла (кг):"
    await state.set_state(ShipmentStates.glass_kg)
    await callback.answer()

@admin.message(ShipmentStates.glass_kg)
async def process_glass_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        glass_kg = float(text)
        if glass_kg < 0:
            raise ValueError
        await state.update_data(glass_kg=glass_kg)
        
        if glass_kg == 0:
            await state.update_data(glass_price=0.0)
            await message.answer("น้ำหนักแก้วเป็น 0", reply_markup=get_category_keyboard())  # "Вес стекла равен 0."
        else:
            await message.answer("กรุณากรอกราคาต่อกก. แก้ว:")  # "Введите цену за кг стекла:"
            await state.set_state(ShipmentStates.glass_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Вес должен быть положительным числом. Введите вес заново:"

@admin.message(ShipmentStates.glass_price)
async def process_glass_price(message: Message, state: FSMContext):
    try:
        glass_price = float(message.text)
        if glass_price < 0:
            raise ValueError
        await state.update_data(glass_price=glass_price)
        await message.answer("บันทึกข้อมูลแก้วเรียบร้อย", reply_markup=get_category_keyboard())  # "Данные по стеклу сохранены."
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Цена должна быть положительным числом. Введите цену заново:"

# Обработчики для бумаги
@admin.callback_query(F.data == "material_paper")
async def process_paper_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักกระดาษ (กก.):")  # "Введите вес бумаги (кг):"
    await state.set_state(ShipmentStates.paper_kg)
    await callback.answer()

@admin.message(ShipmentStates.paper_kg)
async def process_paper_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        paper_kg = float(text)
        if paper_kg < 0:
            raise ValueError
        await state.update_data(paper_kg=paper_kg)
        
        if paper_kg == 0:
            await state.update_data(paper_price=0.0)
            await message.answer("น้ำหนักกระดาษเป็น 0", reply_markup=get_category_keyboard())  # "Вес бумаги равен 0."
        else:
            await message.answer("กรุณากรอกราคาต่อกก. กระดาษ:")  # "Введите цену за кг бумаги:"
            await state.set_state(ShipmentStates.paper_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Вес должен быть положительным числом. Введите вес заново:"

@admin.message(ShipmentStates.paper_price)
async def process_paper_price(message: Message, state: FSMContext):
    try:
        paper_price = float(message.text)
        if paper_price < 0:
            raise ValueError
        await state.update_data(paper_price=paper_price)
        await message.answer("บันทึกข้อมูลกระดาษเรียบร้อย", reply_markup=get_category_keyboard())  # "Данные по бумаге сохранены."
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Цена должна быть положительным числом. Введите цену заново:"

# Обработчики для металла
@admin.callback_query(F.data == "material_metal")
async def process_metal_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักโลหะ (กก.):")  # "Введите вес металла (кг):"
    await state.set_state(ShipmentStates.metal_kg)
    await callback.answer()

@admin.message(ShipmentStates.metal_kg)
async def process_metal_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        metal_kg = float(text)
        if metal_kg < 0:
            raise ValueError
        await state.update_data(metal_kg=metal_kg)
        
        if metal_kg == 0:
            await state.update_data(metal_price=0.0)
            await message.answer("น้ำหนักโลหะเป็น 0", reply_markup=get_category_keyboard())  # "Вес металла равен 0."
        else:
            await message.answer("กรุณากรอกราคาต่อกก. โลหะ:")  # "Введите цену за кг металла:"
            await state.set_state(ShipmentStates.metal_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Вес должен быть положительным числом. Введите вес заново:"

@admin.message(ShipmentStates.metal_price)
async def process_metal_price(message: Message, state: FSMContext):
    try:
        metal_price = float(message.text)
        if metal_price < 0:
            raise ValueError
        await state.update_data(metal_price=metal_price)
        await message.answer("บันทึกข้อมูลโลหะเรียบร้อย", reply_markup=get_category_keyboard())  # "Данные по металлу сохранены."
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Цена должна быть положительным числом. Введите цену заново:"

# Обработчики для масла
@admin.callback_query(F.data == "material_oil")
async def process_oil_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักน้ำมัน (กก.):")  # "Введите вес масла (кг):"
    await state.set_state(ShipmentStates.oil_kg)
    await callback.answer()

@admin.message(ShipmentStates.oil_kg)
async def process_oil_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        oil_kg = float(text)
        if oil_kg < 0:
            raise ValueError
        await state.update_data(oil_kg=oil_kg)
        
        if oil_kg == 0:
            await state.update_data(oil_price=0.0)
            await message.answer("น้ำหนักน้ำมันเป็น 0", reply_markup=get_category_keyboard())  # "Вес масла равен 0."
        else:
            await message.answer("กรุณากรอกราคาต่อกก. น้ำมัน:")  # "Введите цену за кг масла:"
            await state.set_state(ShipmentStates.oil_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Вес должен быть положительным числом. Введите вес заново:"

@admin.message(ShipmentStates.oil_price)
async def process_oil_price(message: Message, state: FSMContext):
    try:
        oil_price = float(message.text)
        if oil_price < 0:
            raise ValueError
        await state.update_data(oil_price=oil_price)
        await message.answer("บันทึกข้อมูลน้ำมันเรียบร้อย", reply_markup=get_category_keyboard())  # "Данные по маслу сохранены."
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Цена должна быть положительным числом. Введите цену заново:"

# Обработчики для прочих материалов
@admin.callback_query(F.data == "material_other")
async def process_other_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักวัสดุอื่นๆ (กก.):")  # "Введите вес прочих материалов (кг):"
    await state.set_state(ShipmentStates.other_kg)
    await callback.answer()

@admin.message(ShipmentStates.other_kg)
async def process_other_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        other_kg = float(text)
        if other_kg < 0:
            raise ValueError
        await state.update_data(other_kg=other_kg)
        
        if other_kg == 0:
            await state.update_data(other_price=0.0)
            await message.answer("น้ำหนักวัสดุอื่นๆ เป็น 0", reply_markup=get_category_keyboard())  # "Вес прочих материалов равен 0."
        else:
            await message.answer("กรุณากรอกราคาต่อกก. วัสดุอื่นๆ:")  # "Введите цену за кг прочих материалов:"
            await state.set_state(ShipmentStates.other_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Вес должен быть положительным числом. Введите вес заново:"

@admin.message(ShipmentStates.other_price)
async def process_other_price(message: Message, state: FSMContext):
    try:
        other_price = float(message.text)
        if other_price < 0:
            raise ValueError
        await state.update_data(other_price=other_price)
        await message.answer("บันทึกข้อมูลวัสดุอื่นๆ เรียบร้อย", reply_markup=get_category_keyboard())  # "Данные по прочим материалам сохранены."
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")  # "Ошибка: Цена должна быть положительным числом. Введите цену заново:"

        
        
# Фиксированные цены для смешанных материалов (оставляем без изменений)
MIX_PRICES = {
    'alum_pl_mix': 8.0,        # อลูมิเนียม+พลาสติก
    'alum_pl_glass_mix': 2.0,  # อลูมิเนียม+พลาสติก+แก้ว
    'alum_iron_cans_mix': 3.0, # อลูมิเนียม+กระป๋องเหล็ก
    'pet_mix': 5.0,            # พลาสติกผสม
    'other_mix': 1.0           # อื่นๆ ผสม
}


# Фиксированные цены для смешанных материалов (оставляем без изменений)
MIX_PRICES = {
    'alum_pl_mix': 8.0,        # อลูมิเนียม+พลาสติก
    'alum_pl_glass_mix': 2.0,  # อลูมิเนียม+พลาสติก+แก้ว
    'alum_iron_cans_mix': 3.0, # อลูมิเนียม+กระป๋องเหล็ก
    'pet_mix': 5.0,            # พลาสติกผสม
    'other_mix': 1.0           # อื่นๆ ผสม
}

# Обработчики для алюм-пластика
@admin.callback_query(F.data == "material_alum_pl_mix")
async def process_alum_pl_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักอลูมิเนียม+พลาสติก (กก.):")
    await state.set_state(ShipmentStates.alum_pl_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_pl_mix_kg)
async def process_alum_pl_mix_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        alum_pl_mix_kg = float(text)
        if alum_pl_mix_kg < 0:
            raise ValueError
        await state.update_data(alum_pl_mix_kg=alum_pl_mix_kg)
        
        if alum_pl_mix_kg == 0:
            await state.update_data(alum_pl_mix_price=0.0)
            await message.answer("น้ำหนักอลูมิเนียม+พลาสติกเป็น 0", reply_markup=get_category_keyboard())
        else:
            await message.answer("กรุณากรอกราคาต่อกก. อลูมิเนียม+พลาสติก:")
            await state.set_state(ShipmentStates.alum_pl_mix_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

@admin.message(ShipmentStates.alum_pl_mix_price)
async def process_alum_pl_mix_price(message: Message, state: FSMContext):
    try:
        alum_pl_mix_price = float(message.text)
        if alum_pl_mix_price < 0:
            raise ValueError
        await state.update_data(alum_pl_mix_price=alum_pl_mix_price)
        await message.answer("บันทึกข้อมูลอลูมิเนียม+พลาสติกเรียบร้อย", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

# Обработчики для алюм-пластик-стекло
@admin.callback_query(F.data == "material_alum_pl_glass_mix")
async def process_alum_pl_glass_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักอลูมิเนียม+พลาสติก+แก้ว (กก.):")
    await state.set_state(ShipmentStates.alum_pl_glass_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_pl_glass_mix_kg)
async def process_alum_pl_glass_mix_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        alum_pl_glass_mix_kg = float(text)
        if alum_pl_glass_mix_kg < 0:
            raise ValueError
        await state.update_data(alum_pl_glass_mix_kg=alum_pl_glass_mix_kg)
        
        if alum_pl_glass_mix_kg == 0:
            await state.update_data(alum_pl_glass_mix_price=0.0)
            await message.answer("น้ำหนักอลูมิเนียม+พลาสติก+แก้วเป็น 0", reply_markup=get_category_keyboard())
        else:
            await message.answer("กรุณากรอกราคาต่อกก. อลูมิเนียม+พลาสติก+แก้ว:")
            await state.set_state(ShipmentStates.alum_pl_glass_mix_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

@admin.message(ShipmentStates.alum_pl_glass_mix_price)
async def process_alum_pl_glass_mix_price(message: Message, state: FSMContext):
    try:
        alum_pl_glass_mix_price = float(message.text)
        if alum_pl_glass_mix_price < 0:
            raise ValueError
        await state.update_data(alum_pl_glass_mix_price=alum_pl_glass_mix_price)
        await message.answer("บันทึกข้อมูลอลูมิเนียม+พลาสติก+แก้วเรียบร้อย", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")


# Обработчики для алюм-железные банки
@admin.callback_query(F.data == "material_alum_iron_cans_mix")
async def process_alum_iron_cans_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักอลูมิเนียม+กระป๋องเหล็ก (กก.):")
    await state.set_state(ShipmentStates.alum_iron_cans_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.alum_iron_cans_mix_kg)
async def process_alum_iron_cans_mix_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        alum_iron_cans_mix_kg = float(text)
        if alum_iron_cans_mix_kg < 0:
            raise ValueError
        await state.update_data(alum_iron_cans_mix_kg=alum_iron_cans_mix_kg)
        
        if alum_iron_cans_mix_kg == 0:
            await state.update_data(alum_iron_cans_mix_price=0.0)
            await message.answer("น้ำหนักอลูมิเนียม+กระป๋องเหล็กเป็น 0", reply_markup=get_category_keyboard())
        else:
            await message.answer("กรุณากรอกราคาต่อกก. อลูมิเนียม+กระป๋องเหล็ก:")
            await state.set_state(ShipmentStates.alum_iron_cans_mix_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

@admin.message(ShipmentStates.alum_iron_cans_mix_price)
async def process_alum_iron_cans_mix_price(message: Message, state: FSMContext):
    try:
        alum_iron_cans_mix_price = float(message.text)
        if alum_iron_cans_mix_price < 0:
            raise ValueError
        await state.update_data(alum_iron_cans_mix_price=alum_iron_cans_mix_price)
        await message.answer("บันทึกข้อมูลอลูมิเนียม+กระป๋องเหล็กเรียบร้อย", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

# Обработчики для смешанного пластика
@admin.callback_query(F.data == "material_pet_mix")
async def process_pet_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักพลาสติกผสม (กก.):")
    await state.set_state(ShipmentStates.pet_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.pet_mix_kg)
async def process_pet_mix_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        pet_mix_kg = float(text)
        if pet_mix_kg < 0:
            raise ValueError
        await state.update_data(pet_mix_kg=pet_mix_kg)
        
        if pet_mix_kg == 0:
            await state.update_data(pet_mix_price=0.0)
            await message.answer("น้ำหนักพลาสติกผสมเป็น 0", reply_markup=get_category_keyboard())
        else:
            await message.answer("กรุณากรอกราคาต่อกก. พลาสติกผสม:")
            await state.set_state(ShipmentStates.pet_mix_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

@admin.message(ShipmentStates.pet_mix_price)
async def process_pet_mix_price(message: Message, state: FSMContext):
    try:
        pet_mix_price = float(message.text)
        if pet_mix_price < 0:
            raise ValueError
        await state.update_data(pet_mix_price=pet_mix_price)
        await message.answer("บันทึกข้อมูลพลาสติกผสมเรียบร้อย", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

# Обработчики для прочего микса
@admin.callback_query(F.data == "material_other_mix")
async def process_other_mix_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("กรุณากรอกน้ำหนักอื่นๆ ผสม (กก.):")
    await state.set_state(ShipmentStates.other_mix_kg)
    await callback.answer()

@admin.message(ShipmentStates.other_mix_kg)
async def process_other_mix_kg(message: Message, state: FSMContext):
    try:
        text = message.text.replace(',', '.').strip()
        other_mix_kg = float(text)
        if other_mix_kg < 0:
            raise ValueError
        await state.update_data(other_mix_kg=other_mix_kg)
        
        if other_mix_kg == 0:
            await state.update_data(other_mix_price=0.0)
            await message.answer("น้ำหนักอื่นๆ ผสมเป็น 0", reply_markup=get_category_keyboard())
        else:
            await message.answer("กรุณากรอกราคาต่อกก. อื่นๆ ผสม:")
            await state.set_state(ShipmentStates.other_mix_price)
    except ValueError:
        await message.answer("ข้อผิดพลาด: น้ำหนักต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

@admin.message(ShipmentStates.other_mix_price)
async def process_other_mix_price(message: Message, state: FSMContext):
    try:
        other_mix_price = float(message.text)
        if other_mix_price < 0:
            raise ValueError
        await state.update_data(other_mix_price=other_mix_price)
        await message.answer("บันทึกข้อมูลอื่นๆ ผสมเรียบร้อย", reply_markup=get_category_keyboard())
    except ValueError:
        await message.answer("ข้อผิดพลาด: ราคาต้องเป็นตัวเลขบวก กรุณากรอกใหม่")

# Обработчик завершения ввода
@admin.callback_query(F.data == "finish_shipment")
async def finish_shipment(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    # Формируем сводку по всем введенным данным
    summary = "📋 สรุปการจัดส่ง:\n\n"  # "📋 Сводка по отгрузке:"
    total_weight = 0
    total_cost = 0
    
    # Основные материалы
    if 'alum_kg' in user_data:
        alum_cost = user_data.get('alum_kg', 0) * user_data.get('alum_price', 0)
        summary += f"🔹 อลูมิเนียม: {user_data['alum_kg']} กก., {alum_cost:.2f} บาท\n"  # "🔹 Алюминий: кг, руб."
        total_weight += user_data['alum_kg']
        total_cost += alum_cost
    
    if 'pet_kg' in user_data:
        pet_cost = user_data.get('pet_kg', 0) * user_data.get('pet_price', 0)
        summary += f"🔹 พลาสติก (PET): {user_data['pet_kg']} กก., {pet_cost:.2f} บาท\n"  # "🔹 Пластик (PET):"
        total_weight += user_data['pet_kg']
        total_cost += pet_cost
    
    if 'glass_kg' in user_data:
        glass_cost = user_data.get('glass_kg', 0) * user_data.get('glass_price', 0)
        summary += f"🔹 แก้ว: {user_data['glass_kg']} กก., {glass_cost:.2f} บาท\n"  # "🔹 Стекло:"
        total_weight += user_data['glass_kg']
        total_cost += glass_cost
    
    # Дополнительные материалы
    if 'paper_kg' in user_data:
        paper_cost = user_data.get('paper_kg', 0) * user_data.get('paper_price', 0)
        summary += f"🔸 กระดาษ: {user_data['paper_kg']} กก., {paper_cost:.2f} บาท\n"  # "🔸 Бумага:"
        total_weight += user_data['paper_kg']
        total_cost += paper_cost
    
    if 'metal_kg' in user_data:
        metal_cost = user_data.get('metal_kg', 0) * user_data.get('metal_price', 0)
        summary += f"🔸 โลหะ: {user_data['metal_kg']} กก., {metal_cost:.2f} บาท\n"  # "🔸 Металл:"
        total_weight += user_data['metal_kg']
        total_cost += metal_cost
    
    if 'oil_kg' in user_data:
        oil_cost = user_data.get('oil_kg', 0) * user_data.get('oil_price', 0)
        summary += f"🔸 น้ำมัน: {user_data['oil_kg']} กก., {oil_cost:.2f} บาท\n"  # "🔸 Масло:"
        total_weight += user_data['oil_kg']
        total_cost += oil_cost
    
    if 'other_kg' in user_data:
        other_cost = user_data.get('other_kg', 0) * user_data.get('other_price', 0)
        summary += f"🔸 อื่นๆ: {user_data['other_kg']} กก., {other_cost:.2f} บาท\n"  # "🔸 Прочие:"
        total_weight += user_data['other_kg']
        total_cost += other_cost
    
    # Смешанные материалы
    if 'alum_pl_mix_kg' in user_data:
        alum_pl_mix_cost = user_data.get('alum_pl_mix_kg', 0) * user_data.get('alum_pl_mix_price', 0)
        summary += f"🔺 อลูมิเนียม+พลาสติก: {user_data['alum_pl_mix_kg']} กก., {alum_pl_mix_cost:.2f} บาท\n"  # "🔺 Алюм-пластик:"
        total_weight += user_data['alum_pl_mix_kg']
        total_cost += alum_pl_mix_cost
    
    if 'alum_pl_glass_mix_kg' in user_data:
        alum_pl_glass_mix_cost = user_data.get('alum_pl_glass_mix_kg', 0) * user_data.get('alum_pl_glass_mix_price', 0)
        summary += f"🔺 อลูมิเนียม+พลาสติก+แก้ว: {user_data['alum_pl_glass_mix_kg']} กก., {alum_pl_glass_mix_cost:.2f} บาท\n"  # "🔺 Алюм-пластик-стекло:"
        total_weight += user_data['alum_pl_glass_mix_kg']
        total_cost += alum_pl_glass_mix_cost
    
    if 'alum_iron_cans_mix_kg' in user_data:
        alum_iron_cans_mix_cost = user_data.get('alum_iron_cans_mix_kg', 0) * user_data.get('alum_iron_cans_mix_price', 0)
        summary += f"🔺 อลูมิเนียม+กระป๋องเหล็ก: {user_data['alum_iron_cans_mix_kg']} กก., {alum_iron_cans_mix_cost:.2f} บาท\n"  # "🔺 Алюм-железные банки:"
        total_weight += user_data['alum_iron_cans_mix_kg']
        total_cost += alum_iron_cans_mix_cost
    
    if 'pet_mix_kg' in user_data:
        pet_mix_cost = user_data.get('pet_mix_kg', 0) * user_data.get('pet_mix_price', 0)
        summary += f"🔺 พลาสติกผสม: {user_data['pet_mix_kg']} กก., {pet_mix_cost:.2f} บาท\n"  # "🔺 Смешанный пластик:"
        total_weight += user_data['pet_mix_kg']
        total_cost += pet_mix_cost
    
    if 'other_mix_kg' in user_data:
        other_mix_cost = user_data.get('other_mix_kg', 0) * user_data.get('other_mix_price', 0)
        summary += f"🔺 อื่นๆ ผสม: {user_data['other_mix_kg']} กก., {other_mix_cost:.2f} บาท\n"  # "🔺 Прочий микс:"
        total_weight += user_data['other_mix_kg']
        total_cost += other_mix_cost
    
    summary += f"\n💎 รวม: {total_weight:.2f} กก., {total_cost:.2f} บาท"  # "💎 Итого: кг, руб."
    
    await callback.message.edit_text(summary, reply_markup=get_confirmation_keyboard())
    await callback.answer()

# Обработчик подтверждения
@admin.callback_query(F.data == "confirm_shipment")
async def confirm_shipment(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    try:
        user = await get_user_by_tg_id(callback.from_user.id)
        if not user:
            await callback.answer()  # Просто закрываем callback без сообщения
            return  # Выходим из функции, если пользователь не найден
        
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
        
        # Отправляем уведомление пользователю, если он существует
        point = await get_point_by_id(user_data['point_id'])
        if point:
            point_user = await get_user_by_point_id(user_data['point_id'])
            if point_user:
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
                    f"✅ การจัดส่งขยะของคุณได้รับการประมวลผลแล้ว\n\n"  # "Ваш мешок с мусором был обработан"
                    f"📦 น้ำหนักรวม: {total_weight:.2f} กก.\n"  # "Общий вес: кг"
                    f"💰 ราคารวม: {total_pay:.2f} บาท\n\n"  # "Общая стоимость: руб."
                    f"ขอบคุณค่ะ/ครับ!"  # "Спасибо вам!"
                )
        
        await callback.message.edit_text(
            '✅ บันทึกข้อมูลการจัดส่งเรียบร้อย! จำนวนถุงถูกรีเซ็ตเป็นศูนย์',  # "Данные об отгрузке успешно добавлены! Количество мешков обнулено."
            reply_markup=driver_keyboard()
        )
    except ValueError as e:
        await callback.message.edit_text(f"❌ ข้อผิดพลาด: {str(e)}")  # "❌ Ошибка:"
    except Exception as e:
        await callback.message.edit_text(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}")  # "❌ Произошла непредвиденная ошибка:"
    finally:
        await state.clear()
        await callback.answer()

# Обработчик отмены
@admin.callback_query(F.data == "cancel_shipment")
async def cancel_shipment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ ยกเลิกการจัดส่ง ข้อมูลทั้งหมดถูกลบแล้ว",  # "❌ Отгрузка отменена. Все данные удалены."
    )
    await callback.answer()

# Обработчик для кнопки "Отменить" в процессе ввода
@admin.callback_query(F.data == "cancel_during_input")
async def cancel_during_input(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ ยกเลิกการป้อนข้อมูล ข้อมูลชั่วคราวทั้งหมดถูกลบ",  # "❌ Ввод данных прерван. Все временные данные удалены."
    )
    await callback.answer()


@admin.callback_query(F.data == "create_point")
async def start_create_point(callback: CallbackQuery, state: FSMContext):
    """Начало процесса создания точки"""
    await callback.message.answer(
        "กรุณากรอก ID จุดใหม่ในรูปแบบ RZZN โดยที่:\n"  # "Введите ID новой точки в формате RZZN, где:"
        "R - หมายเลขภูมิภาค (1 หลัก)\n"  # "R - номер региона (1 цифра)"
        "ZZ - หมายเลขโซน (2 หลัก)\n"  # "ZZ - номер зоны (2 цифры)"
        "N - หมายเลขจุดในโซน (1 หลัก)\n"  # "N - номер точки в зоне (1 цифра)"
        "ตัวอย่าง: 1021 - จุดในภูมิภาค 1 โซน 02 จุดที่ 1",  # "Пример: 1021 - точка в регионе 1, зоне 02, номер точки 1"
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.point_id)
    await callback.answer()

@admin.message(CreatePoint.point_id, F.text.regexp(r'^\d{4}$'))
async def process_point_id(message: Message, state: FSMContext):
    """Обработка ID точки с проверкой формата"""
    point_id = message.text
    region_id = int(point_id[0])
    zone_num = int(point_id[1:3])
    zone_id = int(f"{region_id}{zone_num:02d}")
    point_num = int(point_id[3])
    
    # Проверяем, существует ли уже точка с таким ID
    if await get_point_by_id(point_id):
        await message.answer(
            "มีจุดนี้อยู่แล้ว! กรุณากรอก ID อื่น",  # "Точка с таким ID уже существует! Пожалуйста, введите другой ID."
            reply_markup=cancel_keyboard()
        )
        return
    
    await state.update_data(
        point_id=point_id,
        region_id=region_id,
        zone_num=zone_num,
        zone_id=zone_id,
        point_num=point_num
    )
    
    await message.answer(
        f"ID จุด: {point_id}\n"
        f"ภูมิภาค: {region_id}\n"
        f"หมายเลขโซน: {zone_num}\n"
        f"หมายเลขจุด: {point_num}\n\n"
        "กรุณากรอกชื่อจุด:",  # "Введите название точки:"
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.point_name)

@admin.message(CreatePoint.point_id)
async def process_point_id_invalid(message: Message):
    """Обработка неверного формата ID точки"""
    await message.answer(
        "รูปแบบ ID จุดไม่ถูกต้อง! ต้องเป็นตัวเลข 4 หลักในรูปแบบ RZZN\n"
        "ตัวอย่าง: 1021 - จุดในภูมิภาค 1 โซน 02 จุดที่ 1",  # "Неверный формат ID точки! Должно быть 4 цифры в формате RZZN"
        reply_markup=cancel_keyboard()
    )

@admin.message(CreatePoint.point_name)
async def process_point_name(message: Message, state: FSMContext):
    """Обработка названия точки"""
    await state.update_data(point_name=message.text)
    await message.answer(
        "กรุณากรอกชื่อเจ้าของจุด:",  # "Введите имя владельца точки:"
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.point_owner_name)

@admin.message(CreatePoint.point_owner_name)
async def process_owner_name(message: Message, state: FSMContext):
    """Обработка имени владельца"""
    await state.update_data(point_owner_name=message.text)
    await message.answer(
        "กรุณากรอกเบอร์โทรเจ้าของจุด:",  # "Введите номер телефона владельца:"
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreatePoint.phone_number)

@admin.message(CreatePoint.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    await state.update_data(phone_number=message.text)
    await message.answer(
        "กรุณากรอกที่อยู่จุด:",  # "Введите адрес точки:"
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
        "กรุณาตรวจสอบข้อมูลที่ป้อน:\n\n"  # "Проверьте введенные данные:"
        f"ID จุด: {data['point_id']}\n"
        f"ภูมิภาค: {data['region_id']}\n"
        f"โซน: {data['zone_num']}\n"
        f"หมายเลขจุด: {data['point_num']}\n"
        f"ชื่อ: {data['point_name']}\n"
        f"เจ้าของ: {data['point_owner_name']}\n"
        f"โทรศัพท์: {data['phone_number']}\n"
        f"ที่อยู่: {data['address']}\n\n"
        "ถูกต้องทั้งหมดหรือไม่?"  # "Все верно?"
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
            zone_id=data['zone_id']
        )
        
        await callback.message.answer(
            "✅ สร้างจุดเรียบร้อยแล้ว!",  # "✅ Точка успешно создана!"
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"❌ ข้อผิดพลาดในการสร้างจุด: {str(e)}",  # "❌ Ошибка при создании точки:"
            reply_markup=admin_keyboard()
        )
    finally:
        await state.clear()

@admin.callback_query(CreatePoint.confirmation, F.data == "cancel")
async def cancel_point_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания точки"""
    await callback.message.answer(
        "❌ ยกเลิกการสร้างจุด",  # "❌ Создание точки отменено."
        reply_markup=admin_keyboard()
    )
    await state.clear()

@admin.callback_query(StateFilter(CreatePoint), F.data == "cancel_operation")
async def cancel_creation_process(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса создания на любом этапе"""
    await callback.message.answer(
        "❌ ยกเลิกกระบวนการสร้างจุด",  # "❌ Создание точки прервано."
        reply_markup=admin_keyboard()
    )
    await state.clear()