FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini ./
COPY backend ./backend
EXPOSE 8000
# Migrationen vor dem Start anwenden (Basisschema kommt aus db/init/*.sql)
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"]
