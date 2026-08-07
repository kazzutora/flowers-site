import os

from celery import Celery
from kombu import Queue

# Standard Django bootstrap variable, not an application config value —
# exempt from the "os.getenv only in env.py" rule (config/settings/env.py
# docstring explains the distinction).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("flowers")
app.config_from_object("django.conf:settings", namespace="CELERY")

# tech.md §7: four queues, workers split so slow media rendering never
# blocks manager notifications.
app.conf.task_queues = (
    Queue("default"),
    Queue("notifications"),
    Queue("payments"),
    Queue("media"),
)
app.conf.task_default_queue = "default"

app.autodiscover_tasks()
