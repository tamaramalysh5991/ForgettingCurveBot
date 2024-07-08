import math
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command

from bot.db_service import tasks_collection, archived_tasks_collection
from bot.config import Config
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

bot = Bot(token=Config.TELEGRAM_TOKEN)

scheduler = AsyncIOScheduler()
dp = Dispatcher()
DEFAULT_ACCEPTANCE_RATE = 2.0


def forgetting_curve(days):
    return math.exp(-0.1 * days)  # Это пример формулы кривой забывания


def next_review_date(last_review_date, acceptance_rate):
    days_since_last_review = (datetime.datetime.now() - last_review_date).days
    curve_value = forgetting_curve(days_since_last_review)
    interval = int((1 / curve_value) * acceptance_rate)
    return last_review_date + datetime.timedelta(days=interval)


async def send_reminder(chat_id: str, task: dict):
    try:
        reminder_message = await bot.send_message(chat_id, f"Пора повторить задачу: {task['name']}")
        tasks_collection.update_one({"_id": task["_id"]}, {"$set": {"message_id": reminder_message.message_id}})
        print(
            f"Reminder sent for task: {task['_id']} {task['name']} at {datetime.datetime.now()} reminder message id: {reminder_message.message_id}"
        )
        await bot.send_message(chat_id, f"Пора повторить задачу: {task['name']}")
    except TelegramBadRequest as e:
        print(f"Failed to send message: {e}")


@dp.message(Command(commands=["add"]))
async def add_task(message: types.Message):
    try:
        task_name, *args = message.text.split(",")
    except IndexError:
        await message.reply(
            "Использование: /add <название задачи>, <дата последнего повторения (сегодня)>, "
            "<acceptance rate - 1.0 по умолчанию> - название задачи обязательно"
        )
        return

    task_name = task_name.strip()
    last_review_date = args[0].strip() if len(args) > 1 else datetime.datetime.now().strftime("%Y-%m-%d")
    last_review_date = datetime.datetime.strptime(last_review_date, "%Y-%m-%d")
    acceptance_rate = float(args[1].strip()) if len(args) > 1 else DEFAULT_ACCEPTANCE_RATE
    next_date = next_review_date(last_review_date, acceptance_rate)

    task = {
        "chat_id": message.chat.id,
        "name": task_name,
        "last_review_date": last_review_date,
        "acceptance_rate": acceptance_rate,
        "next_review_date": next_date,
        "message_id": message.message_id,
        "created_at": datetime.datetime.now(),
    }

    tasks_collection.insert_one(task)
    scheduler.add_job(send_reminder, "date", run_date=next_date, args=[message.chat.id, task])
    await message.reply(f"Задача '{task_name}' добавлена. Следующее повторение: {next_date.date()}")


# Handler for listing tasks
@dp.message(Command(commands=["list"]))
async def list_tasks(message: types.Message):
    tasks = tasks_collection.find({"chat_id": message.chat.id})
    response = "Ваши задачи:\n"
    for task in tasks:
        response += f"{task['name']} - Следующее повторение: {task['next_review_date'].date()}\n"
    await message.reply(response)


@dp.message(Command(commands=["update"]))
async def update_task(message: types.Message):
    args = message.text.split(" ", 1)[1].split(",")
    if len(args) < 2:
        await message.reply("Использование: /update <название задачи>, <acceptance rate>")
        return
    task_name, acceptance_rate = args[0].strip(), float(args[1].strip())
    task = tasks_collection.find_one({"chat_id": message.chat.id, "name": task_name})
    if not task:
        await message.reply(f"Задача '{task_name}' не найдена.")
        return
    last_review_date = task["last_review_date"]
    next_date = next_review_date(last_review_date, acceptance_rate)

    tasks_collection.update_one(
        {"_id": task["_id"]},
        {"$set": {"acceptance_rate": acceptance_rate, "next_review_date": next_date}},
    )
    scheduler.add_job(send_reminder, "date", run_date=next_date, args=[message.chat.id, task])
    await message.reply(f"Задача '{task_name}' обновлена. Следующее повторение: {next_date.date()}")


@dp.message(Command(commands=["delete"]))
async def delete_task(message: types.Message):
    task_name = message.text.split(" ", 1)[1].strip()
    task = tasks_collection.find_one({"chat_id": message.chat.id, "name": task_name})
    if not task:
        await message.reply(f"Задача '{task_name}' не найдена.")
        return
    tasks_collection.delete_one({"_id": task["_id"]})
    await message.reply(f"Задача '{task_name}' удалена.")


@dp.message(Command(commands=["delete_all"]))
async def delete_all_tasks(message: types.Message):
    tasks_collection.delete_many({"chat_id": message.chat.id})
    await message.reply("Все задачи удалены.")


@dp.message(Command(commands=["help"]))
async def help_command(message: types.Message):
    response = (
        "Вы можете использовать следующие команды:\n"
        "/add <название задачи>, <дата последнего повторения>, <acceptance rate> - Добавить новую задачу\n"
        "acceptance rate - число от 0 до 1, 1 по умолчанию\n"
        "Это вероятность, что вы вспомните задачу через определенное количество дней\n"
        "Чем выше acceptance rate, тем больше вероятность, что вы вспомните задачу\n"
        "/list - Показать все задачи\n"
        "/update <название задачи>, <acceptance rate> - Обновить acceptance rate задачи"
        "/delete <название задачи> - Удалить задачу"
        "/delete_all - Удалить все задачи"
    )
    await message.reply(response)


@dp.message(Command(commands=["start"]))
async def start_command(message: types.Message):
    response = (
        "Привет! Я бот для управления задачами с использованием кривой забывания.\n"
        "Вы можете использовать следующие команды:\n"
        "/add <название задачи>, <дата последнего повторения>, <acceptance rate> - Добавить новую задачу\n"
        "/list - Показать все задачи\n"
        "/update <название задачи>, <acceptance rate> - Обновить acceptance rate задачи"
        "/delete <название задачи> - Удалить задачу"
    )
    await message.reply(response)


@dp.message(Command(commands=["test_scheduler"]))
async def scheduler_check(message: types.Message):
    # Schedule a task to run in 1 minute
    test_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
    # get last task
    task = tasks_collection.find_one({"chat_id": message.chat.id})

    # Add job to scheduler
    scheduler.add_job(send_reminder, "date", run_date=test_time, args=[message.chat.id, task])

    await message.reply(f"Test task scheduled to run at {test_time}.")


@dp.message(Command(commands=["today_tasks"]))
async def send_reminders_command(message: types.Message):
    await send_daily_reminders()
    await message.reply("Отправлены напоминания.")


@dp.message()
async def mark_task_done(message: types.Message):
    if message.text.lower().strip() == "done" and message.reply_to_message:
        original_message_id = message.reply_to_message.message_id
        task = tasks_collection.find_one({"message_id": original_message_id})

        if not task:
            await message.reply(
                "Не удалось найти задачу. Убедитесь, что вы отвечаете на правильное сообщение напоминания."
            )
            return

        archived_tasks_collection.insert_one(task)
        tasks_collection.delete_one({"_id": task["_id"]})
        await message.reply(f"Задача '{task['name']}' отмечена как выполненная и архивирована.")
    else:
        # If not a "done" message, treat as a new task
        await add_task(message)


async def send_daily_reminders():
    now = datetime.datetime.now()
    # get all tasks
    tasks = tasks_collection.find({"next_review_date": {"$lte": now}})
    for task in tasks:
        await send_reminder(task["chat_id"], task)


def schedule_cron_job():
    scheduler.add_job(send_daily_reminders, "cron", hour=8, minute=0)  # Run every day at 8:00 AM


async def main():
    # Schedule the reminder task
    scheduler.start()
    schedule_cron_job()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
