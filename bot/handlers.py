from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from .db_service import  update_user, add_user, get_user

router = Router()


@router.message(Command("start"))
async def command_start_handler(message: Message) -> None:

    """
    This handler receives messages with `/start` command
    """
    user_id = message.from_user.id
    user = get_user(user_id)

    if user:
        update_user(message.from_user.id, message)
        await message.reply("C возвращением!")

    add_user(user_id, message)
    await message.answer(f"Привет {message.from_user.full_name}!")


@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """
    This handler receives messages with `/help` command
    """
    await message.answer(
        "Press /start."
    )


@router.message()
async def echo_message(message: Message) -> None:
    """
    This handler is called when the bot receives any message
    """
    await message.answer(f"Вы написали: {message.text}")


@router.message(Command("set_time"))
async def set_time(message: Message) -> None:
    """
    This handler is called when user set time for reminder to do kundalini yoga
    """
    user_id = message.from_user.id
    user = get_user(user_id)
    update_user(user_id, message)
    await message.answer(f"Время установлено на {user['reminder_time']}")