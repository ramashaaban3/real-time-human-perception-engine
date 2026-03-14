FROM python:3.11-slim

WORKDIR /app
COPY reasoning_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reasoning_service/app ./app
COPY shared ./shared

EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]