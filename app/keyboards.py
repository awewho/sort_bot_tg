from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                            InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder

def user_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="เราพร้อมส่งสินค้าแล้ว", callback_data="bag_full")],  # "Мы готовы к отгрузке"
        [InlineKeyboardButton(text="ขอโทรกลับจากผู้จัดการ", callback_data="adm_help")],  # "Запросить звонок менеджера"
    ])

def help_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ขอโทรกลับจากผู้จัดการ", callback_data="adm_help")],  # "Запросить звонок менеджера"
    ])

def bags_count_keyboard():
    # Цифры оставлены без перевода
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="0"), KeyboardButton(text="1"), KeyboardButton(text="2")],
            [KeyboardButton(text="3"), KeyboardButton(text="4"), KeyboardButton(text="5")],
            [KeyboardButton(text="6"), KeyboardButton(text="7")]
        ],
        resize_keyboard=True
    )

def notification_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ ยืนยัน: วัสดุถูกจัดเรียงและพร้อมส่งแล้ว",  # "Подтверждаю: материал отсортирован и готов к отправке"
                callback_data="confirm_bags"
            )],
            [InlineKeyboardButton(text="❌ ยกเลิก", callback_data="cancel_bags")]  # "Отменить"
        ]
    )

def admin_keyboard():
    """Клавиатура администратора"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="รายงาน", callback_data="report"),  # "Отчеты"
        InlineKeyboardButton(text="สร้างรายงานบันทึก", callback_data="generate_log_report"),  # "Сформировать лог"
        InlineKeyboardButton(text="สร้างจุด", callback_data="create_point"),  # "Создать точку"
        InlineKeyboardButton(text="ลบจุด", callback_data="delete_point")
    )
    builder.adjust(2)
    return builder.as_markup()

def report_keyboard():
    """Клавиатура отчетов"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="ตามโซน", callback_data="report_zone"),  # "По зонам"
        InlineKeyboardButton(text="ตามภูมิภาค", callback_data="report_region"),  # "По регионам"
        InlineKeyboardButton(text="รายละเอียดภูมิภาค", callback_data="report_region_detail"),  # "Детально по региону"
    )
    builder.adjust(2)
    return builder.as_markup()

def driver_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="เพิ่มการจัดส่ง", callback_data="add_shipment")]  # "Добавить отгрузку"
        ]
    )

def confirm_keyboard():
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ ยืนยัน", callback_data="confirm"),  # "Подтвердить"
        InlineKeyboardButton(text="❌ ยกเลิก", callback_data="cancel")  # "Отменить"
    )
    return builder.as_markup()

def cancel_keyboard():
    """Клавиатура отмены операции"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ ยกเลิกการดำเนินการ", callback_data="cancel_operation")  # "Отменить операцию"
    )
    return builder.as_markup()
    
def get_category_keyboard():
    buttons = [
        [InlineKeyboardButton(text="วัสดุหลัก", callback_data="category_main")],
        [InlineKeyboardButton(text="วัสดุอื่นๆ", callback_data="category_other")],
        [InlineKeyboardButton(text="ยืนยัน", callback_data="confirm_shipment")],  # "Подтвердить"
        [InlineKeyboardButton(text="ยกเลิก", callback_data="cancel_shipment")]  # "Отменить"
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_main_materials_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Plastic PET", callback_data="material_pet")],
        [InlineKeyboardButton(text="Paper", callback_data="material_paper")],
        [InlineKeyboardButton(text="Aluminum", callback_data="material_alum")],
        [InlineKeyboardButton(text="Glass", callback_data="material_glass")],
        [InlineKeyboardButton(text="Small Beer Box", callback_data="material_small_beer_box")],
        [InlineKeyboardButton(text="Large Beer Box", callback_data="material_large_beer_box")],
        [InlineKeyboardButton(text="Mixed Beer Box", callback_data="material_mixed_beer_box")],
        [InlineKeyboardButton(text="← กลับ", callback_data="back_to_categories")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard



def get_other_materials_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Oil", callback_data="material_oil")],
        [InlineKeyboardButton(text="Colored Plastic", callback_data="material_colored_plastic")],
        [InlineKeyboardButton(text="Iron", callback_data="material_iron")],
        [InlineKeyboardButton(text="Plastic Bag or Container", callback_data="material_plastic_bag")],
        [InlineKeyboardButton(text="Mix", callback_data="material_mix")],
        [InlineKeyboardButton(text="Other", callback_data="material_other")],
        [InlineKeyboardButton(text="← กลับ", callback_data="back_to_categories")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ยืนยัน", callback_data="confirm_shipment")],  # "Подтвердить"
        [InlineKeyboardButton(text="ยกเลิก", callback_data="cancel_shipment")]  # "Отменить"
    ])

def get_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ยกเลิกการป้อนข้อมูล", callback_data="cancel_during_input")]  # "Отменить ввод"
    ])