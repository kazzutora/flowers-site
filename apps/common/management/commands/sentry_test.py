"""S0.1 checklist: "Sentry принимает тестовое событие" — a one-command
way to verify SENTRY_DSN actually works after it's set to a real DSN.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send a test event to Sentry to verify SENTRY_DSN is wired up."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.SENTRY_DSN:
            self.stderr.write(self.style.ERROR("SENTRY_DSN is not set — nothing to send."))
            return

        import sentry_sdk

        sentry_sdk.capture_message("flowers-site: test event from manage.py sentry_test")
        sentry_sdk.flush()
        self.stdout.write(self.style.SUCCESS("Test event sent — check your Sentry project."))
