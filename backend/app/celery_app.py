from celery import Celery

from .config import REDIS_URL

celery_app = Celery(
    "meam_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

# Optional configuration, see the application user guide.
celery_app.conf.update(
    result_expires=3600,
)

if __name__ == "__main__":
    celery_app.start()
