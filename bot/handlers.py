from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from .db_service import update_user, get_user

router = Router()


@router.message(Command("set_time"))
async def set_time(message: Message) -> None:
    """
    This handler is called when user set time for reminder to do kundalini yoga
    """
    user_id = message.from_user.id
    user = get_user(user_id)
    update_user(user_id, message)
    await message.answer(f"Время установлено на {user['reminder_time']}")
