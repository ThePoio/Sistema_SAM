import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import get_database, lifespan
from .schemas import (
    AnalysisResponse,
    EvaluationCreate,
    EvaluationProgressUpdate,
    EvaluationResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from .services import cpu_heavy_task, parse_object_id, serialize_evaluation, utc_now

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"]
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


def require_role(role: str, x_role: str | None, x_user_id: str | None) -> str:
    if not x_role or not x_user_id or x_role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Se requiere el rol {role} para esta operacion",
        )
    return x_user_id


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    valid_users = {
        "admin": {"password": "admin123", "role": "admin", "email": "admin@organismo.gov"},
        "encargado": {"password": "encargado123", "role": "encargado", "email": "encargado@organismo.gov"},
    }
    user = valid_users.get(payload.username.lower())
    if not user or user["password"] != payload.password or user["role"] != payload.role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciales o rol invalidos")
    return LoginResponse(
        message="Autenticacion simulada exitosa",
        user=UserResponse(
            username=payload.username.lower(),
            email=user["email"],
            role=user["role"],
            display_name="Administrador" if user["role"] == "admin" else "Encargado de Area",
        ),
    )


@app.post("/api/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    payload: EvaluationCreate,
    request: Request,
    x_role: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> dict[str, Any]:
    require_role("admin", x_role, x_user_id)
    now = utc_now()
    document = payload.model_dump()
    document.update({"progress": 0, "evidence": "", "status": "Pendiente", "created_at": now, "updated_at": now})
    result = await get_database(request).evaluations.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize_evaluation(document)


@app.get("/api/evaluations", response_model=list[EvaluationResponse])
async def list_evaluations(
    request: Request,
    x_role: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    if x_role not in {"admin", "encargado"} or not x_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sesion requerida")
    query: dict[str, Any] = {} if x_role == "admin" else {"assigned_to": x_user_id}
    cursor = get_database(request).evaluations.find(query).sort("created_at", -1)
    return [serialize_evaluation(item) async for item in cursor]


@app.put("/api/evaluations/{evaluation_id}/progress", response_model=EvaluationResponse)
async def update_progress(
    evaluation_id: str,
    payload: EvaluationProgressUpdate,
    request: Request,
    x_role: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> dict[str, Any]:
    user_id = require_role("encargado", x_role, x_user_id)
    collection = get_database(request).evaluations
    object_id = parse_object_id(evaluation_id)
    evaluation = await collection.find_one({"_id": object_id, "assigned_to": user_id})
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada o no asignada")
    status_text = "Completada" if payload.progress == 100 else "En progreso" if payload.progress > 0 else "Pendiente"
    await collection.update_one(
        {"_id": object_id},
        {"$set": {**payload.model_dump(), "status": status_text, "updated_at": utc_now()}},
    )
    updated = await collection.find_one({"_id": object_id})
    return serialize_evaluation(updated)


@app.post("/api/evaluations/{evaluation_id}/analyze", response_model=AnalysisResponse)
async def analyze_evidence(
    evaluation_id: str,
    request: Request,
    x_role: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> dict[str, Any]:
    user_id = require_role("encargado", x_role, x_user_id)
    evaluation = await get_database(request).evaluations.find_one(
        {"_id": parse_object_id(evaluation_id), "assigned_to": user_id}
    )
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada o no asignada")
    evidence = evaluation.get("evidence", "")
    if not evidence:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registra evidencia antes de analizarla")
    analysis = await asyncio.to_thread(cpu_heavy_task, evidence)
    return {"evaluation_id": evaluation_id, **analysis}
