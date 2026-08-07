from django.db import models


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PingRecord(BaseModel):
    """Side effect written by the ``common.ping`` task body.

    Deliberately *not* unique on ``nonce`` — uniqueness must come from the
    Redis idempotency guard in ``apps.common.tasks.ping``, not from a DB
    constraint, so the idempotency test actually exercises that guard.
    """

    nonce = models.CharField(max_length=64)

    class Meta:
        indexes = [models.Index(fields=["nonce"])]

    def __str__(self) -> str:
        return f"ping({self.nonce})"
