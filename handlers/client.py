from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.application import ApplicationForm
from database.queries import add_application
from config import NOTIFICATION_CHAT_ID
import re

router = Router()


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📝 Оставить заявку")]], resize_keyboard=True
    )


def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить телефон", request_contact=True)],
            [KeyboardButton(text="✍️ Ввести вручную"), KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def after_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True
    )


def time_keyboard():
    """Клавиатура для выбора временного интервала"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕘 9:00-12:00", callback_data="time_9-12")],
            [InlineKeyboardButton(text="🕛 12:00-15:00", callback_data="time_12-15")],
            [InlineKeyboardButton(text="🕒 15:00-18:00", callback_data="time_15-18")],
        ]
    )


def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r"[^\d\+]", "", phone)

    if not re.match(r"^\+?\d{10,15}$", cleaned):
        return False

    return True


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await message.answer(
        "👋 Здравствуйте! Я бот компании «ЮрПомощь».\n"
        "Я помогу вам оставить заявку на консультацию.\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=main_menu(),
    )
    await state.clear()


@router.message(F.text == "📝 Оставить заявку")
async def request_name(message: Message, state: FSMContext):
    await state.set_state(ApplicationForm.waiting_for_name)
    await message.answer(
        "👤 Введите ваше имя:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True
        ),
    )


@router.message(ApplicationForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("🏠 Главное меню:", reply_markup=main_menu())
        return

    await state.update_data(name=message.text)

    await state.set_state(ApplicationForm.waiting_for_phone)

    await message.answer(
        "📱 Пожалуйста, отправьте ваш номер телефона.\n"
        "Вы можете:\n"
        "• Нажать кнопку «📱 Отправить телефон»\n"
        "• Или ввести номер вручную",
        reply_markup=phone_keyboard(),
    )


@router.message(ApplicationForm.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.set_state(ApplicationForm.waiting_for_name)
        await message.answer(
            "👤 Введите ваше имя:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True
            ),
        )
        return

    if message.text == "✍️ Ввести вручную":
        await message.answer(
            "✍️ Введите ваш номер телефона:\n" "Пример: +7 (999) 123-45-67",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True
            ),
        )
        return

    if message.contact:
        phone = message.contact.phone_number

        await state.update_data(phone=phone)
        await state.set_state(ApplicationForm.waiting_for_question)
        await message.answer(
            "💬 Опишите суть вашего вопроса:", reply_markup=after_phone_keyboard()
        )
        return

    phone = message.text.strip()

    if not validate_phone(phone):
        await message.answer(
            "❌ Неверный формат телефона.\n"
            "Пожалуйста, введите корректный номер.\n"
            "Пример: +7 (999) 123-45-67",
            reply_markup=phone_keyboard(),
        )
        return

    await state.update_data(phone=phone)

    await state.set_state(ApplicationForm.waiting_for_question)
    await message.answer(
        "💬 Опишите суть вашего вопроса:", reply_markup=after_phone_keyboard()
    )


@router.message(ApplicationForm.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.set_state(ApplicationForm.waiting_for_phone)
        await message.answer(
            "📱 Пожалуйста, отправьте ваш номер телефона:",
            reply_markup=phone_keyboard(),
        )
        return

    await state.update_data(question=message.text)

    await state.set_state(ApplicationForm.waiting_for_time)
    await message.answer(
        "⏰ Укажите удобное время для звонка:", reply_markup=time_keyboard()
    )


@router.callback_query(F.data.startswith("time_"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора временного интервала"""
    time_interval = callback.data.split("_")[1]

    time_map = {"9-12": "9:00-12:00", "12-15": "12:00-15:00", "15-18": "15:00-18:00"}
    readable_time = time_map.get(time_interval, time_interval)

    await state.update_data(call_time=readable_time)

    data = await state.get_data()

    application_id = await add_application(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        name=data["name"],
        phone=data["phone"],
        question=data["question"],
        call_time=readable_time,
    )

    await send_notification_to_admins(callback.bot, application_id, data)

    await callback.message.answer(
        "✅ Заявка отправлена!\n" "Ожидайте подтверждения администратора.",
        reply_markup=main_menu(),
    )

    await callback.message.delete()

    await state.clear()

    await callback.answer()


async def send_notification_to_admins(bot, application_id, data):
    notification_text = (
        f"📋 Новая заявка #{application_id}\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"💬 Вопрос: {data['question']}\n"
        f"⏰ Удобное время: {data['call_time']}\n\n"
        f"Статус: ⏳ Новая"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"accept_{application_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"reject_{application_id}"
                ),
            ]
        ]
    )

    await bot.send_message(
        chat_id=NOTIFICATION_CHAT_ID, text=notification_text, reply_markup=keyboard
    )
