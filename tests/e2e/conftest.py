"""pytest-playwright keeps an asyncio event loop alive in the test
thread even when a test uses Playwright's sync API, which trips Django's
``async_unsafe`` guard on ordinary ORM calls made from fixtures (e.g.
factory-boy factories). This is a known interaction between the two
libraries, not an actual async-context bug in test code — safe to allow
explicitly, and scoped to e2e tests only via this directory-local
conftest.
"""

import os

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
