from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                            InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import InlineKeyboardBuilder


def user_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мы готовы к отгрузке", callback_data="bag_full")],
        [InlineKeyboardButton(text="Запросить звонок менеджера", callback_data="adm_help")],
    ])


def help_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Запросить звонок менеджера", callback_data="adm_help")],
    ])

def bags_count_keyboard():
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
            [InlineKeyboardButton(text="✅ Подтверждаю: материал отсортирован и готов к отправке", callback_data="confirm_bags")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_bags")]
        ]
    )




def admin_keyboard():
    """Клавиатура администратора"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Отчеты", callback_data="report"),
        InlineKeyboardButton(text="Сформировать лог", callback_data="generate_log_report"),
        InlineKeyboardButton(text="Создать точку", callback_data="create_point")
    )
    builder.adjust(2)
    return builder.as_markup()

def report_keyboard():
    """Клавиатура отчетов"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="По зонам", callback_data="report_zone"),
        InlineKeyboardButton(text="По регионам", callback_data="report_region"),
        InlineKeyboardButton(text="Детально по региону", callback_data="report_region_detail"),
    )
    builder.adjust(2)
    return builder.as_markup()


def driver_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
           # [InlineKeyboardButton(text="Сформировать маршрут", callback_data="form_route")],
            [InlineKeyboardButton(text="Добавить отгрузку", callback_data="add_shipment")]
        ]
    )

def confirm_keyboard():
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
    )
    return builder.as_markup()

def cancel_keyboard():
    """Клавиатура отмены операции"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_operation")
    )
    return builder.as_markup()

def get_category_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Основные", callback_data="category_main")],
        [InlineKeyboardButton(text="Дополнительные", callback_data="category_secondary")],
        [InlineKeyboardButton(text="Микс", callback_data="category_mix")],
        [InlineKeyboardButton(text="Завершить", callback_data="finish_shipment")],
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_shipment")]
    ])

def get_main_materials_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Алюминий", callback_data="material_alum")],
        [InlineKeyboardButton(text="Пластик (PET)", callback_data="material_pet")],
        [InlineKeyboardButton(text="Стекло", callback_data="material_glass")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_categories")]
    ])

def get_secondary_materials_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бумага", callback_data="material_paper")],
        [InlineKeyboardButton(text="Металл", callback_data="material_metal")],
        [InlineKeyboardButton(text="Масло", callback_data="material_oil")],
        [InlineKeyboardButton(text="Прочие", callback_data="material_other")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_categories")]
    ])

def get_mix_materials_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Алюм-пластик", callback_data="material_alum_pl_mix")],
        [InlineKeyboardButton(text="Алюм-пластик-стекло", callback_data="material_alum_pl_glass_mix")],
        [InlineKeyboardButton(text="Алюм-железные банки", callback_data="material_alum_iron_cans_mix")],
        [InlineKeyboardButton(text="Смешанный пластик", callback_data="material_pet_mix")],
        [InlineKeyboardButton(text="Прочий микс", callback_data="material_other_mix")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_categories")]
    ])

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_shipment")],
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_shipment")]
    ])

def get_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить ввод", callback_data="cancel_during_input")]
    ])
