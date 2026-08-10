"""Celery application.

Broker and backend come from Django settings lazily, so importing this module
never triggers a settings import cycle. Everything else is static.
"""

from celery import Celery, Task

from apps.core.exceptions import TransientError


class RetryTask(Task):
    """Retry policy of section 8: transient failures only, with backoff.

    A payload that fails validation is not transient and is not retried.
    """

    autoretry_for = (TransientError,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    max_retries = 5
    acks_late = True


app = Celery("flowers", task_cls=RetryTask)
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_default_queue = "default"
# Image work must not sit behind notifications, and the other way round.
app.conf.task_routes = {
    "catalog.generate_renditions": {"queue": "media"},
    "catalog.regenerate_all_renditions": {"queue": "media"},
}
app.conf.task_track_started = True
app.conf.worker_hijack_root_logger = False

# Section 8: the schedule holds only tasks that exist. flush-view-counters
# arrives with S1-5 and expire-banner with S2-1; core.ping goes away with the
# skeleton.
app.conf.beat_schedule = {
    "ping": {
        "task": "core.ping",
        "schedule": 60.0,
        "kwargs": {"payload": {}},
    },
}

app.autodiscover_tasks()
