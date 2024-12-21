from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class Message(BaseModel):
    role: str
    content: str

class MemoryItem(BaseModel):
    id: str = Field(..., description="The unique identifier for the text data")
    memory: str = Field(..., description="The memory deduced from the text data")
    hash: Optional[str] = Field(None, description="The hash of the memory")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the text data")
    score: Optional[float] = Field(None, description="The score associated with the text data")
    created_at: Optional[str] = Field(None, description="The timestamp when the memory was created")
    updated_at: Optional[str] = Field(None, description="The timestamp when the memory was updated")
