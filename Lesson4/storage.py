import asyncio
import json
from pathlib import Path
from typing import Any

NOTES_FILE = Path(__file__).resolve().with_name("notes.json")
_file_lock = asyncio.Lock()


def init_storage() -> None:
    """Create the JSON file when it does not exist."""
    if not NOTES_FILE.exists():
        NOTES_FILE.write_text("[]", encoding="utf-8")


def _read_notes() -> list[dict[str, Any]]:
    with NOTES_FILE.open("r", encoding="utf-8") as file:
        notes = json.load(file)
    if not isinstance(notes, list) or not all(isinstance(note, dict) for note in notes):
        raise ValueError(f"Invalid notes data in {NOTES_FILE}")
    return notes


def _write_notes(notes: list[dict[str, Any]]) -> None:
    with NOTES_FILE.open("w", encoding="utf-8") as file:
        json.dump(notes, file, ensure_ascii=False, indent=4)


async def read_notes() -> list[dict[str, Any]]:
    async with _file_lock:
        return _read_notes()


async def add_note(note: dict[str, Any]) -> None:
    async with _file_lock:
        notes = _read_notes()
        notes.append(note)
        _write_notes(notes)


async def find_note(note_id: str) -> dict[str, Any] | None:
    async with _file_lock:
        return next(
            (note for note in _read_notes() if note.get("id") == note_id),
            None,
        )


async def delete_note(note_id: str) -> bool:
    async with _file_lock:
        notes = _read_notes()
        remaining_notes = [note for note in notes if note.get("id") != note_id]
        if len(remaining_notes) == len(notes):
            return False
        _write_notes(remaining_notes)
        return True
