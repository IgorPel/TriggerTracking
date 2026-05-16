import os
from celery import Celery


REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery(
    'crypto_project',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.tasks']
)

celery_app.conf.update(
    worker_log_format='%(asctime)s [%(levelname)s] %(message)s',
    worker_task_log_format='%(asctime)s [%(levelname)s] %(message)s',
)
celery_app.conf.beat_schedule = {
    'check-crypto-prices-every-minute': {
        'task': 'src.tasks.cheacking_triggers',
        'schedule': 120.0,
    },

}

celery_app.conf.timezone = 'UTC'
