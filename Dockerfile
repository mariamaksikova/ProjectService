# Образ для запуска сервиса (CI/CD и прод). Для локальной разработки с hot-reload
# можно переопределить команду: docker run ... uvicorn app.main:app --reload ...
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
