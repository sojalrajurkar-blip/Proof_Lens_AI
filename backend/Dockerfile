FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI via uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
