from pydantic import BaseModel, Field
from typing import List


class Product(BaseModel):
    name: str
    tagline: str
    description: str
    url: str
    website: str
    votes: int
    comments: int
    topics: List[str] = Field(default_factory=list)
    thumbnail: str
    rank: int
    ai_summary: str = ""
    ph_date: str
