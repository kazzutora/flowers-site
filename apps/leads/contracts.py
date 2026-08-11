"""Payload models of the lead tasks (section 8.1)."""

from pydantic import BaseModel, ConfigDict, Field


class LeadNotificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_id: int = Field(gt=0)
