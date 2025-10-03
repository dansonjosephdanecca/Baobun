from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = datetime.now()
    requires_search: bool = False
    search_results: Optional[List[dict]] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    enable_search: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime
    search_performed: bool = False
    search_query: Optional[str] = None

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str = "DuckDuckGo"

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime