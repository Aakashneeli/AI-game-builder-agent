FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY . /app

ENTRYPOINT ["python", "-m", "agentic_game_builder"]
