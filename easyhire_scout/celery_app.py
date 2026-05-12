from celery import Celery
from easyhire_scout.core.config import settings

celery_app = Celery(
    "easyhire_scout",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["easyhire_scout.tasks.scraping_tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
