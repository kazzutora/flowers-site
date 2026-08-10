class TransientError(Exception):
    """A dependency failed in a way that is worth retrying.

    Celery tasks list this in `autoretry_for`; anything else is a permanent
    failure and must not be retried.
    """
