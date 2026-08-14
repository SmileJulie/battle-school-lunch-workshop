FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
RUN python -m pip install --no-cache-dir -e .

COPY src ./src

EXPOSE 8001
CMD ["python", "-m", "battle_lunch_mcp.server"]
