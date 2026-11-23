from datetime import UTC, datetime
from uuid import uuid4

import storage
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

storage.init_storage()

app = FastAPI(title="Notes REST API", description="Мини-модуль управления заметками")


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Заголовок заметки")
    text: str = Field(..., description="Текст заметки")


class NoteResponse(BaseModel):
    id: str
    title: str
    text: str
    created_at: datetime


@app.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(note_data: NoteCreate):
    new_note = {
        "id": str(uuid4()),
        "title": note_data.title,
        "text": note_data.text,
        "created_at": datetime.now(UTC).isoformat(),
    }
    await storage.add_note(new_note)
    return new_note


@app.get("/notes", response_model=list[NoteResponse])
async def get_all_notes():
    return await storage.read_notes()


@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    note = await storage.find_note(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str):
    if not await storage.delete_note(note_id):
        raise HTTPException(status_code=404, detail="Заметка не найдена")
