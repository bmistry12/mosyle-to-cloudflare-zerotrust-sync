FROM python:3.11.4-slim-buster

RUN pip install poetry==1.6.1

COPY app/pyproject.toml app/poetry.lock  /
RUN poetry install

WORKDIR /app
COPY app /app
VOLUME /app

CMD ["python", "main.py"]
