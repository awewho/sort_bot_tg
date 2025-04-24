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
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="หลัก", callback_data="category_main")],  # "Основные"
        [InlineKeyboardButton(text="เสริม", callback_data="category_secondary")],  # "Дополнительные"
        [InlineKeyboardButton(text="ผสม", callback_data="category_mix")],  # "Микс"
        [InlineKeyboardButton(text="เสร็จสิ้น", callback_data="finish_shipment")],  # "Завершить"
        [InlineKeyboardButton(text="ยกเลิก", callback_data="cancel_shipment")]  # "Отменить"
    ])

def get_main_materials_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="อลูมิเนียม", callback_data="material_alum")],  # "Алюминий"
        [InlineKeyboardButton(text="พลาสติก (PET)", callback_data="material_pet")],  # "Пластик (PET)"
        [InlineKeyboardButton(text="แก้ว", callback_data="material_glass")],  # "Стекло"
        [InlineKeyboardButton(text="กลับ", callback_data="back_to_categories")]  # "Назад"
    ])

def get_secondary_materials_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="กระดาษ", callback_data="material_paper")],  # "Бумага"
        [InlineKeyboardButton(text="โลหะ", callback_data="material_metal")],  # "Металл"
        [InlineKeyboardButton(text="น้ำมัน", callback_data="material_oil")],  # "Масло"
        [InlineKeyboardButton(text="อื่นๆ", callback_data="material_other")],  # "Прочие"
        [InlineKeyboardButton(text="กลับ", callback_data="back_to_categories")]  # "Назад"
    ])

def get_mix_materials_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="อลูมิเนียม-พลาสติก", callback_data="material_alum_pl_mix")],  # "Алюм-пластик"
        [InlineKeyboardButton(text="อลูมิเนียม-พลาสติก-แก้ว", callback_data="material_alum_pl_glass_mix")],  # "Алюм-пластик-стекло"
        [InlineKeyboardButton(text="กระป๋องอลูมิเนียม-เหล็ก", callback_data="material_alum_iron_cans_mix")],  # "Алюм-железные банки"
        [InlineKeyboardButton(text="พลาสติกผสม", callback_data="material_pet_mix")],  # "Смешанный пластик"
        [InlineKeyboardButton(text="อื่นๆ ผสม", callback_data="material_other_mix")],  # "Прочий микс"
        [InlineKeyboardButton(text="กลับ", callback_data="back_to_categories")]  # "Назад"
    ])

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ยืนยัน", callback_data="confirm_shipment")],  # "Подтвердить"
        [InlineKeyboardButton(text="ยกเลิก", callback_data="cancel_shipment")]  # "Отменить"
    ])

def get_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ยกเลิกการป้อนข้อมูล", callback_data="cancel_during_input")]  # "Отменить ввод"
    ])