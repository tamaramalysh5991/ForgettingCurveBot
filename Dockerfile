FROM python:3.11
RUN pip install poetry
WORKDIR /app
COPY . /app

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi
EXPOSE 80
ENV TELEGRAM_BOT_TOKEN=""
CMD python3 main.py ${TELEGRAM_BOT_TOKEN}