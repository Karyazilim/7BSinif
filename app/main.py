from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, create_engine, Session, select
from typing import List, Optional
import os

from app.models import User, Memory, Comment, MemoryLike, CommentLike
from app.utils.humanize import humanize_time

# Database setup
DATABASE_URL = "sqlite:///./memories.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# FastAPI app setup
app = FastAPI(title="7B Anı Defteri", description="7B sınıfı için anı defteri uygulaması")

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Current user (simplified - no auth)
CURRENT_USER_NAME = "Misafir"
CURRENT_USER_AVATAR = "https://via.placeholder.com/64x64/8b5cf6/ffffff?text=M"

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Create seed data
    create_seed_data()

def create_seed_data():
    """Create initial seed data for testing"""
    with Session(engine) as session:
        # Check if data already exists
        existing_user = session.exec(select(User)).first()
        if existing_user:
            return
        
        # Create sample users
        users = [
            User(name="Ahmet Yılmaz", avatar_url="https://via.placeholder.com/64x64/3b82f6/ffffff?text=AY"),
            User(name="Elif Kaya", avatar_url="https://via.placeholder.com/64x64/f59e0b/ffffff?text=EK"),
            User(name="Mehmet Demir", avatar_url="https://via.placeholder.com/64x64/10b981/ffffff?text=MD"),
            User(name="Zeynep Şahin", avatar_url="https://via.placeholder.com/64x64/ef4444/ffffff?text=ZS"),
        ]
        
        for user in users:
            session.add(user)
        session.commit()
        
        # Refresh to get IDs
        for user in users:
            session.refresh(user)
        
        # Create sample memories
        memories = [
            Memory(
                author_id=users[0].id,
                text="Bugün okulda çok eğlendik! Matematik dersinde öğretmenimizle güldük. 📚😄",
                image_url="https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=400&h=400&fit=crop",
                like_count=5
            ),
            Memory(
                author_id=users[1].id,
                text="Teneffüste arkadaşlarımla oynadığımız oyun çok güzeldi. Herkes çok mutluydu! 🎮✨",
                image_url="https://images.unsplash.com/photo-1606112219348-204d7d8b94ee?w=400&h=400&fit=crop",
                like_count=8
            ),
            Memory(
                author_id=users[2].id,
                text="Fen bilgisi deneyimiz harika geçti. Kimya çok ilginçmiş! 🧪⚗️",
                image_url="https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400&h=400&fit=crop",
                like_count=3
            ),
            Memory(
                author_id=users[3].id,
                text="Okul bahçesinde çiçekler açmış. Bahar geldi! 🌸🌺",
                image_url="https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=400&h=400&fit=crop",
                like_count=12
            ),
        ]
        
        for memory in memories:
            session.add(memory)
        session.commit()
        
        # Refresh to get IDs
        for memory in memories:
            session.refresh(memory)
        
        # Create sample comments
        comments = [
            Comment(memory_id=memories[0].id, author_id=users[1].id, text="Çok güzel bir anı! 😊", like_count=2),
            Comment(memory_id=memories[0].id, author_id=users[2].id, text="Ben de oradaydım, gerçekten eğlenceliydi!", like_count=1),
            Comment(memory_id=memories[1].id, author_id=users[0].id, text="Hangi oyunu oynadınız?", like_count=0),
            Comment(memory_id=memories[2].id, author_id=users[3].id, text="Fen bilgisi deneyleri harika!", like_count=3),
            Comment(memory_id=memories[3].id, author_id=users[0].id, text="Çiçekler gerçekten çok güzel 🌸", like_count=5),
        ]
        
        for comment in comments:
            session.add(comment)
        session.commit()

# Routes
@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/memories", status_code=302)

@app.get("/memories", response_class=HTMLResponse)
async def list_memories(request: Request, session: Session = Depends(get_session)):
    # Get all memories with author info, ordered by created_at desc
    statement = select(Memory).order_by(Memory.created_at.desc())
    memories = session.exec(statement).all()
    
    # Prepare data for template
    memory_data = []
    for memory in memories:
        author = session.get(User, memory.author_id)
        comment_count = len(session.exec(select(Comment).where(Comment.memory_id == memory.id)).all())
        
        memory_data.append({
            'id': memory.id,
            'text': memory.text,
            'image_url': memory.image_url,
            'like_count': memory.like_count,
            'comment_count': comment_count,
            'created_at_human': humanize_time(memory.created_at),
            'author': author
        })
    
    return templates.TemplateResponse("memories_list.html", {
        "request": request,
        "memories": memory_data
    })

@app.get("/memories/new", response_class=HTMLResponse)
async def new_memory_form(request: Request):
    return templates.TemplateResponse("memory_new.html", {
        "request": request,
        "current_user": CURRENT_USER_NAME
    })

@app.post("/memories", response_class=RedirectResponse)
async def create_memory(
    author_name: str = Form(...),
    text: str = Form(...),
    image_url: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    # Get or create user
    user = session.exec(select(User).where(User.name == author_name)).first()
    if not user:
        user = User(name=author_name, avatar_url=f"https://via.placeholder.com/64x64/8b5cf6/ffffff?text={author_name[0].upper()}")
        session.add(user)
        session.commit()
        session.refresh(user)
    
    # Create memory
    memory = Memory(
        author_id=user.id,
        text=text,
        image_url=image_url if image_url else None
    )
    session.add(memory)
    session.commit()
    
    return RedirectResponse(url="/memories", status_code=302)

@app.get("/memories/{memory_id}", response_class=HTMLResponse)
async def memory_detail(request: Request, memory_id: int, session: Session = Depends(get_session)):
    memory = session.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    author = session.get(User, memory.author_id)
    
    # Get comments with authors
    comments_query = select(Comment).where(Comment.memory_id == memory_id).order_by(Comment.created_at.asc())
    comments = session.exec(comments_query).all()
    
    comment_data = []
    for comment in comments:
        comment_author = session.get(User, comment.author_id)
        comment_data.append({
            'id': comment.id,
            'text': comment.text,
            'like_count': comment.like_count,
            'author': comment_author.name,
            'avatar': comment_author.avatar_url,
            'created_human': humanize_time(comment.created_at)
        })
    
    return templates.TemplateResponse("memory_detail.html", {
        "request": request,
        "memory_id": memory.id,
        "memory_text": memory.text,
        "image_url": memory.image_url,
        "like_count": memory.like_count,
        "comment_count": len(comment_data),
        "author_name": author.name,
        "author_avatar": author.avatar_url,
        "created_at_human": humanize_time(memory.created_at),
        "comments": comment_data,
        "current_user_avatar": CURRENT_USER_AVATAR
    })

@app.post("/memories/{memory_id}/comments", response_class=RedirectResponse)
async def add_comment(
    memory_id: int,
    text: str = Form(...),
    session: Session = Depends(get_session)
):
    memory = session.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Get or create current user
    user = session.exec(select(User).where(User.name == CURRENT_USER_NAME)).first()
    if not user:
        user = User(name=CURRENT_USER_NAME, avatar_url=CURRENT_USER_AVATAR)
        session.add(user)
        session.commit()
        session.refresh(user)
    
    comment = Comment(
        memory_id=memory_id,
        author_id=user.id,
        text=text
    )
    session.add(comment)
    session.commit()
    
    return RedirectResponse(url=f"/memories/{memory_id}", status_code=302)

@app.post("/memories/{memory_id}/like", response_class=RedirectResponse)
async def like_memory(memory_id: int, session: Session = Depends(get_session)):
    memory = session.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    memory.like_count += 1
    session.add(memory)
    session.commit()
    
    # Redirect back to the referrer or memory detail
    return RedirectResponse(url=f"/memories/{memory_id}", status_code=302)

@app.post("/comments/{comment_id}/like", response_class=RedirectResponse)
async def like_comment(comment_id: int, session: Session = Depends(get_session)):
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.like_count += 1
    session.add(comment)
    session.commit()
    
    return RedirectResponse(url=f"/memories/{comment.memory_id}", status_code=302)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)