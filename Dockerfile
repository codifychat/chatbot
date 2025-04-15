# Використовуємо офіційний базовий образ Python
FROM python:3.9-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей до контейнера
COPY requirements.txt requirements.txt

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Копіюємо всі файли додатку до контейнера
COPY . .

# Змінна середовища (вона буде задаватися під час запуску контейнера)
ENV TELEGRAM_BOT_TOKEN=""

# Вказуємо команду запуску додатку
CMD ["python", "main.py"]
