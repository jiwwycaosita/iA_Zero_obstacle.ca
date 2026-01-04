FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py /app/
COPY connectors /app/connectors
COPY workers /app/workers

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
