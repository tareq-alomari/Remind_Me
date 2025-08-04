from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class NoteType(str, Enum):
    text = "text"
    audio = "audio"

class Category(str, Enum):
    personal = "personal"
    work = "work" 
    study = "study"
    shopping = "shopping"
    health = "health"
    other = "other"

# Models
class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: Optional[str] = None
    audio_data: Optional[str] = None  # base64 encoded audio
    audio_duration: Optional[int] = None  # duration in seconds
    note_type: NoteType
    category: Category = Category.personal
    reminder_time: Optional[datetime] = None
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NoteCreate(BaseModel):
    title: str
    content: Optional[str] = None
    audio_data: Optional[str] = None
    audio_duration: Optional[int] = None
    note_type: NoteType
    category: Category = Category.personal
    reminder_time: Optional[datetime] = None

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    audio_data: Optional[str] = None
    audio_duration: Optional[int] = None
    category: Optional[Category] = None
    reminder_time: Optional[datetime] = None
    is_completed: Optional[bool] = None

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "ذكّرني بالمهم - Note Taking API"}

# Notes CRUD operations
@api_router.post("/notes", response_model=Note)
async def create_note(note_data: NoteCreate):
    """Create a new note (text or audio)"""
    try:
        note_dict = note_data.dict()
        note_obj = Note(**note_dict)
        result = await db.notes.insert_one(note_obj.dict())
        if result.inserted_id:
            return note_obj
        else:
            raise HTTPException(status_code=500, detail="Failed to create note")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notes", response_model=List[Note])
async def get_all_notes(category: Optional[str] = None):
    """Get all notes, optionally filtered by category"""
    try:
        query = {}
        if category and category != "all":
            query["category"] = category
        
        notes = await db.notes.find(query).sort("created_at", -1).to_list(1000)
        return [Note(**note) for note in notes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: str):
    """Get a specific note by ID"""
    try:
        note = await db.notes.find_one({"id": note_id})
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return Note(**note)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: str, note_update: NoteUpdate):
    """Update a note"""
    try:
        update_data = {k: v for k, v in note_update.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
        result = await db.notes.update_one(
            {"id": note_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        
        updated_note = await db.notes.find_one({"id": note_id})
        return Note(**updated_note)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a note"""
    try:
        result = await db.notes.delete_one({"id": note_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"message": "Note deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notes/reminders/upcoming")
async def get_upcoming_reminders():
    """Get notes with upcoming reminders"""
    try:
        now = datetime.utcnow()
        upcoming = now + timedelta(hours=24)  # Next 24 hours
        
        notes = await db.notes.find({
            "reminder_time": {"$gte": now, "$lte": upcoming},
            "is_completed": False
        }).sort("reminder_time", 1).to_list(100)
        
        return [Note(**note) for note in notes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/stats")
async def get_stats():
    """Get statistics about notes"""
    try:
        total_notes = await db.notes.count_documents({})
        text_notes = await db.notes.count_documents({"note_type": "text"})
        audio_notes = await db.notes.count_documents({"note_type": "audio"})
        completed_notes = await db.notes.count_documents({"is_completed": True})
        pending_reminders = await db.notes.count_documents({
            "reminder_time": {"$gte": datetime.utcnow()},
            "is_completed": False
        })
        
        return {
            "total_notes": total_notes,
            "text_notes": text_notes,
            "audio_notes": audio_notes,
            "completed_notes": completed_notes,
            "pending_reminders": pending_reminders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()