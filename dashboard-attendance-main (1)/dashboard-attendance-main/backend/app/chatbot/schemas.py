
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=4000)
    session_id: Optional[str] = Field(default="default", max_length=100)


class SourceItem(BaseModel):
    module: str
    description: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[SourceItem] = []
