from pydantic import BaseModel, ConfigDict


class EmptyPayload(BaseModel):
    """Payload of tasks that take no arguments.

    Extras are forbidden: a task called with unexpected keys is a contract
    breach and must fail on validation instead of silently ignoring them.
    """

    model_config = ConfigDict(extra="forbid")
