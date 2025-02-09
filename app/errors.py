"""
Error handling.
"""
import inspect
from enum import Enum
from typing import Any
from pydantic import BaseModel

class ErrorType(Enum):
    """
    Valid error types.
    """
    DATABASE = "database"
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"

class Error(BaseModel):
    """
    A consistent type for reporting errors.
    """
    type: ErrorType | None = None
    msg: Any | None = None
    input: Any | None = None
    loc: Any | None = None
    ctx: Any | None = None

    def __init__(self,
        type=type,
        msg=msg,
        input=input,
        loc=loc,
        ctx=ctx,
    ):
        BaseModel.__init__(self,
            type=type,
            msg=msg,
            input=input,
            loc=loc,
            ctx=ctx)
        if not self.loc:
            self.loc = [
                inspect.stack()[1].filename,
                inspect.stack()[1].function,
            ]
