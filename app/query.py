"""
API query interface.
"""
from pydantic import BaseModel, Field
from typing import Annotated
from fastapi import Depends, Query

class QueryParams(BaseModel):
    """
    Query interface used for search queries.
    """
    search: str | None = None
    skip: int = Field(default=0, ge=0)
    size: int = Field(default=100, gt=0, le=10000)
    sort: list[str] | None = None
    summary: list[str] | None = None

QueryParamsDep = Annotated[QueryParams, Depends(), Query()]
