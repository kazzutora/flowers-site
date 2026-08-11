"""Payload models of the catalog tasks (section 8 of tech.md).

Every task takes one keyword argument, `payload: dict`, and parses it here
before touching anything else. A payload that fails validation is a contract
breach, not a transient failure, and is never retried.
"""

from pydantic import BaseModel, ConfigDict, Field


class RenditionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_image_id: int = Field(gt=0)
    force: bool = False


class RegenerateAllPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = False
    work_id: int | None = None
