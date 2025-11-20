from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import os

# PUBLIC_INTERFACE
class NoteCreate(BaseModel):
    """Pydantic model for creating a note."""
    title: str = Field(..., description="Title of the note", min_length=1, max_length=200)
    content: str = Field(..., description="Content of the note", min_length=1)

# PUBLIC_INTERFACE
class NoteUpdate(BaseModel):
    """Pydantic model for updating a note. Fields are optional."""
    title: Optional[str] = Field(None, description="Updated title of the note", min_length=1, max_length=200)
    content: Optional[str] = Field(None, description="Updated content of the note", min_length=1)

# PUBLIC_INTERFACE
class Note(BaseModel):
    """Pydantic model representing a note with metadata."""
    id: int = Field(..., description="Unique identifier for the note")
    title: str = Field(..., description="Title of the note")
    content: str = Field(..., description="Content of the note")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")

app = FastAPI(
    title="Simple Notes Manager API",
    description="A minimal FastAPI service to create, read, update, and delete notes.",
    version="1.0.0",
    contact={
        "name": "Notes Manager",
        "url": "https://example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {"name": "health", "description": "Service health and info"},
        {"name": "notes", "description": "CRUD operations for notes"},
    ],
)

# Allow all origins by default (can be restricted via env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory data store
NOTES: Dict[int, Note] = {}
_next_id: int = 1


def _now() -> datetime:
    """Return current UTC datetime with tzinfo naive for consistency."""
    return datetime.utcnow()


@app.get("/", summary="Health Check", tags=["health"])
def health_check():
    """Health check endpoint to verify service is running."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get("/notes", response_model=List[Note], summary="List notes", tags=["notes"])
def list_notes() -> List[Note]:
    """List all notes currently stored."""
    return list(NOTES.values())


# PUBLIC_INTERFACE
@app.post(
    "/notes",
    response_model=Note,
    status_code=201,
    summary="Create a new note",
    tags=["notes"],
)
def create_note(payload: NoteCreate) -> Note:
    """Create a new note and return it."""
    global _next_id
    note_id = _next_id
    _next_id += 1
    now = _now()
    note = Note(
        id=note_id,
        title=payload.title,
        content=payload.content,
        created_at=now,
        updated_at=now,
    )
    NOTES[note_id] = note
    return note


# PUBLIC_INTERFACE
@app.get(
    "/notes/{note_id}",
    response_model=Note,
    summary="Get note by id",
    tags=["notes"],
)
def get_note(
    note_id: int = Path(..., description="ID of the note to retrieve", ge=1)
) -> Note:
    """Retrieve a note by its id."""
    note = NOTES.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# PUBLIC_INTERFACE
@app.put(
    "/notes/{note_id}",
    response_model=Note,
    summary="Update note by id",
    tags=["notes"],
)
def update_note(
    payload: NoteUpdate,
    note_id: int = Path(..., description="ID of the note to update", ge=1),
) -> Note:
    """Update an existing note. At least one field must be provided."""
    existing = NOTES.get(note_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")

    data = existing.model_dump()
    updated = False

    if payload.title is not None:
        data["title"] = payload.title
        updated = True
    if payload.content is not None:
        data["content"] = payload.content
        updated = True

    if not updated:
        # No changes submitted
        return existing

    data["updated_at"] = _now()
    new_note = Note(**data)
    NOTES[note_id] = new_note
    return new_note


# PUBLIC_INTERFACE
@app.delete(
    "/notes/{note_id}",
    status_code=204,
    summary="Delete note by id",
    tags=["notes"],
)
def delete_note(
    note_id: int = Path(..., description="ID of the note to delete", ge=1)
) -> None:
    """Delete a note by its id."""
    if note_id not in NOTES:
        raise HTTPException(status_code=404, detail="Note not found")
    del NOTES[note_id]
    return None


@app.on_event("startup")
def _startup() -> None:
    """Initialize optional seed data or perform setup."""
    # Optional: Seed a sample note for easier preview
    global _next_id
    if not NOTES:
        now = _now()
        NOTES[1] = Note(
            id=1,
            title="Welcome to Notes",
            content="This is your first note! You can create, update, and delete notes.",
            created_at=now,
            updated_at=now,
        )
        _next_id = 2
