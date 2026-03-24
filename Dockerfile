# 1. Беремо за основу "напівфабрикат" — офіційний Python
FROM python:3.11-slim

# 2. Створюємо папку для програми всередині контейнера
WORKDIR /app

# 3. Копіюємо файл із списком бібліотек (ми його зараз створимо)
COPY requirements.txt .

# 4. Встановлюємо бібліотеки
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install "uvicorn[standard]"


# 5. Копіюємо весь твій код всередину контейнера
COPY . .

# 6. Команда, яка запустить твій сервер
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]