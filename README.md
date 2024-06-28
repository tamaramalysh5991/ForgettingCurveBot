
# Interval Repetition Telegram Bot for Task Management

This is a Telegram bot for managing tasks using the forgetting curve. It's written in Python and uses MongoDB for data storage.

## Features

- Add tasks with a name, last review date, and acceptance rate.
- List all tasks.
- Update the acceptance rate of a task.
- Delete a task.
- Delete all tasks.
- Help command to show all available commands.
- Start command to introduce the bot and its commands.

## Installation

1. Clone this repository.
2. Install the required dependencies with `pip install -r requirements.txt`.
3. Set up your MongoDB database and add your connection string to the `bot/config.py` file.
4. Add your Telegram bot token to the `bot/config.py` file.
5. Run the bot with `python bot/main.py`.

## Usage

- `/add <task name>, <last review date>, <acceptance rate>`: Adds a new task.
- `/list`: Lists all tasks.
- `/update <task name>, <acceptance rate>`: Updates the acceptance rate of a task.
- `/delete <task name>`: Deletes a task.
- `/delete_all`: Deletes all tasks.
- `/help`: Shows all available commands.
- `/start`: Introduces the bot and its commands.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
