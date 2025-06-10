FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock .
RUN touch README.md

RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry install --no-root

COPY . .

CMD ["poetry","run","python", "app.py"]