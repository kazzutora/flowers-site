"""DTO for the SmsClient boundary (tech.md §9.1). Not enumerated with a
field table in tech.md — kept to the minimum needed to type the frozen
``send() -> SmsResult`` signature. See CONTRACT GAP note in S0.7 PR.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class SmsStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"


class SmsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str
    status: SmsStatus
