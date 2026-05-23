FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .
COPY . .
EXPOSE 8004
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8004/health || exit 1
CMD ["python", "server.py"]
