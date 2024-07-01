FROM python:3.11

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

COPY . .

CMD ["python", "bot/main.py"]