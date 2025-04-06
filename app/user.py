from aiogram import Bot
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from datetime import datetime

from app.database.requests import (
    set_user, add_request, get_user_by_tg_id, get_user_points, get_point_by_id, 
    is_point_available, bind_point_to_user, update_bags_count
)
from app.states import Reg, BagFull, Help
from app.keyboards import bags_count_keyboard, user_command, help_command, notification_keyboard

user = Router()

@user.message(Command("menu"))
async def cmd_menu(message: Message):
    """Показывает меню пользователя"""
    await message.answer("Выберите действие:", reply_markup=user_command())


@user.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Проверяем, есть ли у пользователя привязанная точка
    user = await get_user_by_tg_id(message.from_user.id)
    
    if user and user.point_id:
        # Если точка уже привязана, показываем основное меню
        point = await get_point_by_id(user.point_id)
        if point:
            await message.answer(
                f'Вы уже привязаны к точке {point.point_id}. Выберите действие:',
                reply_markup=user_command()
            )
        else:
            await message.answer(
                'Ваша привязанная точка не найдена. Пожалуйста, обратитесь к администратору.',
                reply_markup=help_command()
            )
    else:
        # Если точки нет, начинаем процесс регистрации
        await set_user(message.from_user.id)
        await message.answer('Добро пожаловать в бот! Пожалуйста, введите номер точки:')
        await state.set_state(Reg.point)


@user.message(Reg.point)
async def process_point(message: Message, state: FSMContext):
    point_id = message.text.strip()
    
    if not point_id.isdigit():
        await message.answer('Номер точки должен содержать только цифры. Пожалуйста, попробуйте снова.')
        return
    
    point = await get_point_by_id(point_id)
    if not point:
        await message.answer('Точка с таким номером не найдена. Пожалуйста, проверьте номер и попробуйте снова.')
        return
        
    if not await is_point_available(point.point_id):
        await message.answer(
            'Эта точка уже привязана к другому пользователю. Пожалуйста, обратитесь к администратору.',
            reply_markup=help_command()
        )
        return
        
    try:
        await bind_point_to_user(point.point_id, message.from_user.id)
        await message.answer(
            f'Отлично, вы успешно привязаны к точке {point.point_id}!',
            reply_markup=user_command()
        )
    except ValueError as e:
        await message.answer(f'Ошибка: {e}')
    except Exception as e:
        await message.answer(
            'Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже или обратитесь к администратору.'
        )
        print(f"Error in process_point: {e}")
    
    await state.clear()

@user.callback_query(F.data == "bag_full")
async def cmd_bag_full(callback: CallbackQuery, state: FSMContext):
    points = await get_user_points(callback.from_user.id)
    if points:
        await callback.message.answer(
            'Сколько мешков алюминия заполнено?',
            reply_markup=bags_count_keyboard()
        )
        await state.set_state(BagFull.aluminum_count)
    else:
        await callback.message.answer('У вас нет привязанных точек сбора мусора.')

@user.message(BagFull.aluminum_count, F.text.in_(["0","1", "2", "3", "4", "5", "6", "7"]))
async def process_aluminum_count(message: Message, state: FSMContext):
    await state.update_data(aluminum_count=int(message.text))
    await message.answer(
        'Сколько мешков ПЭТ заполнено?',
        reply_markup=bags_count_keyboard()
    )
    await state.set_state(BagFull.pet_count)

@user.message(BagFull.pet_count, F.text.in_(["0","1", "2", "3", "4", "5", "6", "7"]))
async def process_pet_count(message: Message, state: FSMContext):
    await state.update_data(pet_count=int(message.text))
    await message.answer(
        'Сколько мешков стекла заполнено?',
        reply_markup=bags_count_keyboard()
    )
    await state.set_state(BagFull.glass_count)

@user.message(BagFull.glass_count, F.text.in_(["0","1", "2", "3", "4", "5", "6", "7"]))
async def process_glass_count(message: Message, state: FSMContext):
    await state.update_data(glass_count=int(message.text))
    await message.answer(
        'Сколько мешков прочих отходов заполнено?',
        reply_markup=bags_count_keyboard()
    )
    await state.set_state(BagFull.other_count)

@user.message(BagFull.other_count, F.text.in_(["0","1", "2", "3", "4", "5", "6", "7"]))
async def process_other_count(message: Message, state: FSMContext):
    data = await state.update_data(other_count=int(message.text))
    
    aluminum = data.get('aluminum_count', 0)
    pet = data.get('pet_count', 0)
    glass = data.get('glass_count', 0)
    other = data.get('other_count', 0)
    total = sum([aluminum, pet, glass, other])
    
    confirm_text = (
        f"Пожалуйста, подтвердите введенные данные:\n\n"
        f"Алюминий: {aluminum}\n"
        f"ПЭТ: {pet}\n"
        f"Стекло: {glass}\n"
        f"Прочие: {other}\n"
        f"Всего: {total}\n\n"
        f"Все верно?"
    )
    
    await message.answer(confirm_text, reply_markup=notification_keyboard())
    await state.set_state(BagFull.confirmation)

@user.callback_query(BagFull.confirmation, F.data == "confirm_bags")
async def confirm_bags(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    points = await get_user_points(callback.from_user.id)
    
    if points:
        total_bags = sum([
            data.get('aluminum_count', 0),
            data.get('pet_count', 0),
            data.get('glass_count', 0),
            data.get('other_count', 0)
        ])
        
        for point in points:
            await add_request(
                point_id=point.point_id,
                user_id=callback.from_user.id,  # Добавлен user_id
                activity="bag_full",
                pet_bag=data.get('pet_count'),
                aluminum_bag=data.get('aluminum_count'),
                glass_bag=data.get('glass_count'),
                other=data.get('other_count')
            )
            
            await update_bags_count(point.point_id, total_bags)
        
        await callback.message.answer(
            "✅ Спасибо, информация получена, мы пришлем грузовик в течении 5 дней",
            reply_markup=user_command()
        )
    else:
        await callback.message.answer(
            'У вас нет привязанных точек сбора мусора.',
            reply_markup=None
        )
    
    await state.clear()

@user.callback_query(BagFull.confirmation, F.data == "cancel_bags")
async def cancel_bags(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "❌ Ввод данных отменен. Вы можете начать заново.",
        reply_markup=None
    )
    await state.clear()

@user.callback_query(F.data == "adm_help")
async def call_admin(callback: CallbackQuery, bot: Bot):
    user = await get_user_by_tg_id(callback.from_user.id)
    
    if user and user.point_id:
        await add_request(
            point_id=user.point_id,
            user_id=callback.from_user.id,  # Добавлен user_id
            activity="admin_help"
        )
        
        admin_phone_number = "+799999999"
        ADMIN_TG_ID = 753755508
        
        admin_message = (
            f"🔔 **Запрос на помощь от пользователя!**\n"
            f"👤 Пользователь: @{callback.from_user.username} ({callback.from_user.id})\n"
            f"📍 Точка сбора ID: {user.point_id}\n"
            f"🕒 Время запроса: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        try:
            await bot.send_message(
                chat_id=ADMIN_TG_ID,
                text=admin_message,
                parse_mode="Markdown"
            )
            
            await callback.message.answer(
                f"✅ Ваш запрос на помощь отправлен администратору.\n"
                f"📞 Вы также можете позвонить по номеру: {admin_phone_number}", reply_markup=user_command()
            )
        except Exception as e:
            await callback.message.answer(
                "❌ Произошла ошибка при отправке запроса. Попробуйте позже."
            )
            print(f"Ошибка при отправке сообщения администратору: {e}")
    else:
        await callback.message.answer(
            '⚠️ Сначала привяжите точку сбора.',
            reply_markup=help_command()
        )