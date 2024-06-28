import math
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command

from bot.db_service import tasks_collection
from bot.config import Config
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

bot = Bot(token=Config.TELEGRAM_TOKEN)

scheduler = AsyncIOScheduler()
dp = Dispatcher()


def forgetting_curve(days):
    return math.exp(-0.1 * days)  # Это пример формулы кривой забывания


def next_review_date(last_review_date, acceptance_rate):
    days_since_last_review = (datetime.datetime.now() - last_review_date).days
    curve_value = forgetting_curve(days_since_last_review)
    interval = int((1 / curve_value) * acceptance_rate)
    return last_review_date + datetime.timedelta(days=interval)


async def send_reminder(chat_id, task):
    try:
        await bot.send_message(chat_id, f"Пора повторить задачу: {task['name']}")
    except TelegramBadRequest as e:
        print(f"Failed to send message: {e}")


@dp.message(Command(commands=["add"]))
async def add_task(message: types.Message):
    try:
        args = message.text.split(' ', 1)[1].split(',')
    except IndexError:
        await message.reply("Использование: /add <название задачи>, <дата последнего повторения>, <acceptance rate>")
        return
    if len(args) < 3:
        await message.reply("Использование: /add <название задачи>, <дата последнего повторения>, <acceptance rate>")
        return
    task_name, last_review_date, acceptance_rate = args[0].strip(), args[1].strip(), float(args[2].strip())
    last_review_date = datetime.datetime.strptime(last_review_date, '%Y-%m-%d')
    next_date = next_review_date(last_review_date, acceptance_rate)

    task = {
        'chat_id': message.chat.id,
        'name': task_name,
        'last_review_date': last_review_date,
        'acceptance_rate': acceptance_rate,
        'next_review_date': next_date
    }

    tasks_collection.insert_one(task)
    scheduler.add_job(send_reminder, 'date', run_date=next_date, args=[message.chat.id, task])
    await message.reply(f"Задача '{task_name}' добавлена. Следующее повторение: {next_date.date()}")


# Handler for listing tasks
@dp.message(Command(commands=["list"]))
async def list_tasks(message: types.Message):
    tasks = tasks_collection.find({'chat_id': message.chat.id})
    response = "Ваши задачи:\n"
    for task in tasks:
        response += f"{task['name']} - Следующее повторение: {task['next_review_date'].date()}\n"
    await message.reply(response)


@dp.message(Command(commands=["update"]))
async def update_task(message: types.Message):
    args = message.text.split(' ', 1)[1].split(',')
    if len(args) < 2:
        await message.reply("Использование: /update <название задачи>, <acceptance rate>")
        return
    task_name, acceptance_rate = args[0].strip(), float(args[1].strip())
    task = tasks_collection.find_one({'chat_id': message.chat.id, 'name': task_name})
    if not task:
        await message.reply(f"Задача '{task_name}' не найдена.")
        return
    last_review_date = task['last_review_date']
    next_date = next_review_date(last_review_date, acceptance_rate)

    tasks_collection.update_one({'_id': task['_id']},
                                {'$set': {'acceptance_rate': acceptance_rate, 'next_review_date': next_date}})
    scheduler.add_job(send_reminder, 'date', run_date=next_date, args=[message.chat.id, task])
    await message.reply(f"Задача '{task_name}' обновлена. Следующее повторение: {next_date.date()}")


@dp.message(Command(commands=["delete"]))
async def delete_task(message: types.Message):
    task_name = message.text.split(' ', 1)[1].strip()
    task = tasks_collection.find_one({'chat_id': message.chat.id, 'name': task_name})
    if not task:
        await message.reply(f"Задача '{task_name}' не найдена.")
        return
    tasks_collection.delete_one({'_id': task['_id']})
    await message.reply(f"Задача '{task_name}' удалена.")


@dp.message(Command(commands=["delete_all"]))
async def delete_all_tasks(message: types.Message):
    tasks_collection.delete_many({'chat_id': message.chat.id})
    await message.reply("Все задачи удалены.")


@dp.message(Command(commands=["help"]))
async def help_command(message: types.Message):
    response = ("Вы можете использовать следующие команды:\n"
                "/add <название задачи>, <дата последнего повторения>, <acceptance rate> - Добавить новую задачу\n"
                "/list - Показать все задачи\n"
                "/update <название задачи>, <acceptance rate> - Обновить acceptance rate задачи"
                "/delete <название задачи> - Удалить задачу"
                "/delete_all - Удалить все задачи")
    await message.reply(response)


@dp.message(Command(commands=["start"]))
async def start_command(message: types.Message):
    response = ("Привет! Я бот для управления задачами с использованием кривой забывания.\n"
                "Вы можете использовать следующие команды:\n"
                "/add <название задачи>, <дата последнего повторения>, <acceptance rate> - Добавить новую задачу\n"
                "/list - Показать все задачи\n"
                "/update <название задачи>, <acceptance rate> - Обновить acceptance rate задачи"
                "/delete <название задачи> - Удалить задачу")
    await message.reply(response)


async def main():
    # Schedule the reminder task
    # scheduler.add_job(send_reminder, "interval", minutes=2, id="my job 1")
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
