from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext


from app.database.requests import (
    set_user, get_point_by_number, bind_point_to_user, get_user_points, 
    update_bags_count, get_user_by_id, is_point_available, add_log
)
from app.states import Reg, BindPoint, BagFull, Help
from app.keyboards import confirm_keyboard, bags_count_keyboard, user_command

user = Router()

@user.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await set_user(message.from_user.id)
    await message.answer('Добро пожаловать в бот! Пожалуйста, введите номер точки:')
    await state.set_state(Reg.point)


@user.message(Reg.point)
async def process_point(message: Message, state: FSMContext):
    point_number = message.text.strip()  # Убираем лишние пробелы
    point = await get_point_by_number(point_number)  # Получаем точку по номеру

    if not point:
        await message.answer('Точка с таким номером не найдена. Пожалуйста, проверьте номер и попробуйте снова.')
        return

    # Проверяем, доступна ли точка для привязки
    if not await is_point_available(point.id):
        await message.answer('Эта точка уже привязана к другому пользователю. Пожалуйста, обратитесь к администратору.')
        return

    # Привязываем точку к пользователю
    try:
        await bind_point_to_user(point.id, message.from_user.id)
        await message.answer(f'Отлично, вы успешно привязаны к точке {point_number}!', reply_markup=user_command())
    except ValueError as e:
        await message.answer(f'Ошибка: {e}')
    
    await state.clear()  # Очищаем состояние после успешной привязки

@user.callback_query(F.data == "bag_full")
async def cmd_bag_full(callback: CallbackQuery, state: FSMContext):
    points = await get_user_points(callback.from_user.id)
    
    if points:
        await callback.message.answer('Пожалуйста, выберите количество заполненных мешков:', reply_markup=bags_count_keyboard())
        await state.set_state(BagFull.bags_count)
    else:
        await callback.message.answer('У вас нет привязанных точек сбора мусора.')


@user.message(BagFull.bags_count, F.text.in_(["1", "2", "3", "4", "5", "6", "7"]))
async def process_bags_count(message: Message, state: FSMContext):
    bags_count = int(message.text)
    points = await get_user_points(message.from_user.id)
    
    if points:
        for point in points:
            await update_bags_count(point.id, bags_count)
            # Добавляем запись в лог
            await add_log(
                client_id=message.from_user.id,
                activity="bag_full",
                bags_count=bags_count
            )
        await message.answer(f'Уведомление о {bags_count} заполненных мешках отправлено. Спасибо!', reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer('У вас нет привязанных точек сбора мусора.')
    
    await state.clear()

@user.message(F.text == "adm_help")
async def call_admin(message: Message):
    user = await get_user_by_id(message.from_user.id)
    points = await get_user_points(message.from_user.id)
    
    if user and points:
        # Добавляем запись в лог
        await add_log(
            client_id=message.from_user.id,
            activity="admin_call",
            question="Пользователь запросил помощь администратора"
        )
        await message.answer('Ваш запрос на помощь отправлен администратору.')
    else:
        await message.answer('У вас нет привязанных точек сбора мусора.')