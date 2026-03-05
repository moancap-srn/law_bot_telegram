from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from aiogram.fsm.context import FSMContext
from database.queries import (
    get_application_by_id,
    update_application_status,
    get_stats,
    get_all_applications,
)
from config import ADMIN_IDS
import io
from tabulate import tabulate

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


@router.callback_query(F.data.startswith("accept_"))
async def accept_application(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    application_id = int(callback.data.split("_")[1])

    application = await get_application_by_id(application_id)

    if not application:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return

    await update_application_status(application_id, "accepted")

    try:
        from bot import bot

        await bot.send_message(
            chat_id=application["user_id"],
            text="✅ Ваша заявка подтверждена!\n"
            "Юрист свяжется с вами в удобное время, указанное вами: "
            f"{application['call_time']}",
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения клиенту: {e}")

    await callback.message.edit_text(
        text=callback.message.text.replace("⏳ Новая", "✅ Принята"), reply_markup=None
    )

    await callback.answer("✅ Заявка принята")


@router.callback_query(F.data.startswith("reject_"))
async def reject_application(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    application_id = int(callback.data.split("_")[1])

    application = await get_application_by_id(application_id)

    if not application:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return

    await update_application_status(application_id, "rejected")

    try:
        from bot import bot

        await bot.send_message(
            chat_id=application["user_id"],
            text="❌ Ваша заявка отклонена.\n"
            "К сожалению, в настоящее время мы не можем принять вашу заявку.\n"
            "Попробуйте повторить попытку позже.",
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения клиенту: {e}")

    await callback.message.edit_text(
        text=callback.message.text.replace("⏳ Новая", "❌ Отклонена"),
        reply_markup=None,
    )

    await callback.answer("❌ Заявка отклонена")


@router.message(Command("stats"))
async def stats_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    stats = await get_stats()

    stats_text = (
        "📊 Статистика заявок:\n\n"
        f"• Сегодня: {stats['today']}\n"
        f"• За неделю: {stats['week']}\n"
        f"• Всего: {stats['total']}\n\n"
        f"✅ Принято: {stats['accepted']}\n"
        f"❌ Отклонено: {stats['rejected']}\n"
        f"⏳ В ожидании: {stats['pending']}"
    )

    await message.answer(stats_text)


@router.message(Command("export"))
async def export_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    applications = await get_all_applications()

    if not applications:
        await message.answer("📭 Нет заявок для выгрузки")
        return

    headers = ["ID", "Имя", "Телефон", "Вопрос", "Время", "Статус", "Дата"]
    rows = [
        [
            app["id"],
            app["name"],
            app["phone"],
            (
                app["question"][:30] + "..."
                if len(app["question"]) > 30
                else app["question"]
            ),
            app["call_time"],
            app["status"],
            app["created_at"],
        ]
        for app in applications
    ]

    file_content = tabulate(rows, headers=headers, tablefmt="grid").encode("utf-8")

    document = BufferedInputFile(file=file_content, filename="applications.txt")

    await message.answer_document(
        document=document, caption=f"📄 Выгрузка всех заявок ({len(applications)} шт.)"
    )


@router.message(Command("start"))
async def admin_start_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "👋 Добро пожаловать, администратор!\n\n"
        "Доступные команды:\n"
        "/stats — Статистика заявок\n"
        "/export — Выгрузить все заявки\n\n"
        "Новые заявки приходят в чат уведомлений."
    )
