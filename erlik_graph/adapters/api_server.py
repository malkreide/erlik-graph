"""FastAPI-Adapter: HTTP-Endpoints + Auslieferung des Cytoscape-Frontends.

Start:  python -m uvicorn erlik_graph.adapters.api_server:app --reload
Dann:   http://127.0.0.1:8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import erlik_graph  # noqa: F401  (registriert alle Transforms)
from erlik_graph.core import GraphStore, all_transforms

app = FastAPI(title="erlik_graph", version="0.1.0")
STORE = GraphStore()
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class SeedIn(BaseModel):
    type: str
    value: str


class ExpandIn(BaseModel):
    type: str
    value: str
    transform: str


@app.get("/api/transforms")
def list_transforms() -> list[dict]:
    return [{"name": t.name, "input_type": t.input_type,
             "description": t.description} for t in all_transforms()]


@app.post("/api/seed")
def seed(item: SeedIn) -> dict:
    from erlik_graph.core import Entity
    key = STORE.add_entity(Entity(type=item.type, value=item.value))
    return {"key": key, "stats": STORE.stats()}


@app.post("/api/expand")
def expand(item: ExpandIn) -> dict:
    try:
        result = STORE.expand(item.type, item.value, item.transform)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    result["stats"] = STORE.stats()
    return result


@app.get("/api/graph")
def graph() -> dict:
    return {"elements": STORE.to_cytoscape(), "stats": STORE.stats()}


@app.post("/api/clear")
def clear() -> dict:
    STORE.clear()
    return {"stats": STORE.stats()}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
