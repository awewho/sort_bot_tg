from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                            InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import InlineKeyboardBuilder


def user_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сумка полная", callback_data="bag_full")],
        [InlineKeyboardButton(text="Позвать администратора", callback_data="adm_help")],
    ])


def help_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Позвать администратора", callback_data="adm_help")],
    ])

def bags_count_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6")],
            [KeyboardButton(text="7")]
        ],
        resize_keyboard=True
    )

def confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
        ],
        resize_keyboard=True
    )




def admin_keyboard():
    """Клавиатура для администратора."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отчеты", callback_data="report")],
        [InlineKeyboardButton(text="Сформировать лог", callback_data="generate_log_report")],
    ])


def report_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отчет по точкам", callback_data="report_point")],
            [InlineKeyboardButton(text="Отчет по кластерам", callback_data="report_cluster")],
            [InlineKeyboardButton(text="Отчет по водителям", callback_data="report_drivers")]
        ])



def driver_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
           # [InlineKeyboardButton(text="Сформировать маршрут", callback_data="form_route")],
            [InlineKeyboardButton(text="Добавить отгрузку", callback_data="add_shipment")]
        ]
    )

def notification_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data="confirm")]
        ]
    )