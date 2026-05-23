FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml .
RUN pip install .

COPY server.py .
EXPOSE 8007

CMD ["python", "server.py"]
