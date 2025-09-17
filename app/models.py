from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    avatar_url: str = Field(default="https://via.placeholder.com/64x64/8b5cf6/ffffff?text=U")
    
    # Relationships
    memories: List["Memory"] = Relationship(back_populates="author")
    comments: List["Comment"] = Relationship(back_populates="author")


class Memory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    text: str
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    like_count: int = Field(default=0)
    
    # Relationships
    author: Optional[User] = Relationship(back_populates="memories")
    comments: List["Comment"] = Relationship(back_populates="memory")


class MemoryLike(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    memory_id: int = Field(foreign_key="memory.id")
    user_id: int = Field(foreign_key="user.id")


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    memory_id: int = Field(foreign_key="memory.id")
    author_id: int = Field(foreign_key="user.id")
    text: str
    created_at: datetime = Field(default_factory=datetime.now)
    like_count: int = Field(default=0)
    
    # Relationships
    memory: Optional[Memory] = Relationship(back_populates="comments")
    author: Optional[User] = Relationship(back_populates="comments")


class CommentLike(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    comment_id: int = Field(foreign_key="comment.id")
    user_id: int = Field(foreign_key="user.id")