"""Store-Factory: waehlt das Graph-Backend anhand von Umgebungsvariablen.

Beide Adapter (FastAPI + MCP) rufen create_store() auf. Standard ist der
in-memory GraphStore (kein Setup noetig). Wird ERLIK_GRAPH_BACKEND=neo4j
gesetzt, zeigen beide Adapter auf dieselbe Neo4j-Instanz und teilen sich damit
den Ermittlungs-Graphen prozessuebergreifend.

    ERLIK_GRAPH_BACKEND   memory (default) | neo4j
    NEO4J_URI             bolt://localhost:7687
    NEO4J_USER            neo4j
    NEO4J_PASSWORD        (Passwort deiner Neo4j-Instanz)
"""

from __future__ import annotations

import os

from .base_store import BaseGraphStore
from .graph_store import GraphStore


def create_store() -> BaseGraphStore:
    backend = os.environ.get("ERLIK_GRAPH_BACKEND", "memory").strip().lower()

    if backend in ("neo4j", "neo"):
        from .neo4j_store import Neo4jGraphStore

        return Neo4jGraphStore(
            uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            user=os.environ.get("NEO4J_USER", "neo4j"),
            password=os.environ.get("NEO4J_PASSWORD", "neo4j"),
        )

    if backend in ("memory", "networkx", "inmemory", "in-memory", ""):
        return GraphStore()

    raise ValueError(
        f"Unbekanntes ERLIK_GRAPH_BACKEND: {backend!r} "
        "(erlaubt: 'memory', 'neo4j')"
    )
