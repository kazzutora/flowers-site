"""Payload models of the review tasks (section 8.6)."""

from pydantic import BaseModel, ConfigDict, Field


class ReviewNotificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: int = Field(gt=0)
