from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


Role = Literal["user", "assistant", "system"]


class ChatCreate(BaseModel):
    chat_id: str = Field(..., description="Client-provided chat/session id")


class MessageCreate(BaseModel):
    id: str
    chat_id: str
    role: Role
    content: str
    parent_message_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class MessageOut(BaseModel):
    id: str
    chat_id: str
    role: Role
    content: str
    created_at: str
    parent_message_id: Optional[str] = None
    metadata_json: Optional[str] = None


class AnswerFeedbackCreate(BaseModel):
    id: str
    chat_id: str
    message_id: str
    thumbs: Literal[1, -1]
    comment: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class FreeformFeedbackCreate(BaseModel):
    id: str
    chat_id: Optional[str] = None
    text: str
    metadata: Optional[dict[str, Any]] = None
