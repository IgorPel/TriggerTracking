import os
from celery import Celery

# 1. Налаштування URL
# УВАГА: Якщо ти запускаєш через Docker, тут НЕ має бути localhost.
# Тут має бути назва сервісу з docker-compose.yml (у нас це 'redis' або 'crypto_redis')
# Використовуємо os.environ.get, щоб локально працювало через localhost, а в докері через ім'я сервісу
REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")

# 2. Створення екземпляру
celery_app = Celery(
    'crypto_project',
    broker=REDIS_URL,
    backend=REDIS_URL,
    # ВАЖЛИВО: вказуємо, де шукати функції з декоратором @task
    include=['src.tasks']
)

# 3. Налаштування розкладу (Beat)
# Замість app.tasks... напиши src.tasks...
# src/celery_app.py

celery_app.conf.update(
    worker_log_format='%(asctime)s [%(levelname)s] %(message)s',
    worker_task_log_format='%(asctime)s [%(levelname)s] %(message)s',
)
celery_app.conf.beat_schedule = {
    # Твоя основна задача (раз на хвилину)
    'check-crypto-prices-every-minute': {
        'task': 'src.tasks.cheacking_triggers',
        'schedule': 120.0,
    },

}

"""

    'heart-beat': {
        'task': 'src.tasks.health_check_task',
        'schedule': 10.0,
    }"""

# 4. Додаткові налаштування (опціонально)
celery_app.conf.timezone = 'UTC'