import hashlib
import time
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def serialize_user(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "username": document["username"],
        "email": document["email"],
        "role": document["role"],
        "display_name": document["display_name"],
    }


def serialize_evaluation(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "title": document["title"],
        "description": document["description"],
        "area": document["area"],
        "assigned_to": document["assigned_to"],
        "due_date": document["due_date"],
        "progress": document.get("progress", 0),
        "evidence": document.get("evidence", ""),
        "status": document.get("status", "Pendiente"),
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
    }


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada")
    return ObjectId(value)


def cpu_heavy_task(data: str) -> dict[str, Any]:
    """Simula procesamiento intensivo sin bloquear el event loop de FastAPI."""
    started = time.perf_counter()
    time.sleep(3)
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    score = min(100, 40 + (sum(bytearray(digest.encode("ascii"))) % 61))
    return {
        "score": score,
        "summary": f"Evidencia procesada. Huella de analisis: {digest[:12]}",
        "processed_in_seconds": round(time.perf_counter() - started, 2),
    }
