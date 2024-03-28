from aiogram import Bot, Dispatcher

from db_service import users_collection
from bot.config import Config
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

bot = Bot(token=Config.TELEGRAM_TOKEN)


scheduler = AsyncIOScheduler()


async def send_reminder():
    users = users_collection.find()
    message_content = "Привет! Делай йогу!"
    for user in users:
        try:
            await bot.send_message(user["chat_id"], message_content)
        except Exception as e:
            print(f"Failed to send message to {user}: {e}")


async def main():
    # Bot and Dispatcher setup
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Schedule the reminder task
    scheduler.add_job(send_reminder, "interval", minutes=2, id="my job 1")
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
