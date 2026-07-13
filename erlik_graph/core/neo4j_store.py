"""Neo4j-Graph-Store: prozessuebergreifend geteilter Ermittlungs-Graph.

Damit zeigen FastAPI- und MCP-Adapter auf *dieselbe* Datenbank: ein LLM-Agent
reichert ueber MCP an, du inspizierst dasselbe Ergebnis im Browser. Der
in-memory GraphStore kann das nicht, weil jeder Prozess seine eigene Instanz
haelt.

Aktivieren ueber Umgebungsvariablen (siehe create_store):
    ERLIK_GRAPH_BACKEND=neo4j
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=...

Modell: jeder Knoten ist ein (:Entity {key,type,value,props_json}), jede Kante
eine [:LINK {label,transform}]. `key` ist unique (siehe _ensure_constraint).
Properties werden als JSON-String abgelegt, damit auch verschachtelte Werte
verlustfrei runden.
"""

from __future__ import annotations

import json

from .base_store import BaseGraphStore
from .entity import Edge, Entity


class Neo4jGraphStore(BaseGraphStore):
    def __init__(self, uri: str, user: str, password: str) -> None:
        # Lazy-Import: der neo4j-Treiber ist nur noetig, wenn dieser Store
        # tatsaechlich benutzt wird (in-memory bleibt ohne Extra-Dependency).
        from neo4j import GraphDatabase

        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_constraint()

    def _ensure_constraint(self) -> None:
        with self._driver.session() as session:
            session.run(
                "CREATE CONSTRAINT erlik_entity_key IF NOT EXISTS "
                "FOR (n:Entity) REQUIRE n.key IS UNIQUE"
            )

    def close(self) -> None:
        self._driver.close()

    # --- Primitive ------------------------------------------------------
    def add_entity(self, entity: Entity) -> str:
        key = entity.key
        with self._driver.session() as session:
            # Bestehende Properties lesen, mergen, zurueckschreiben -> kein
            # Verlust bei wiederholtem Anlegen desselben Knotens.
            existing = session.run(
                "MATCH (n:Entity {key: $key}) RETURN n.props_json AS props",
                key=key,
            ).single()
            props: dict = {}
            if existing and existing["props"]:
                try:
                    props = json.loads(existing["props"])
                except (TypeError, ValueError):
                    props = {}
            props.update(entity.properties)
            session.run(
                "MERGE (n:Entity {key: $key}) "
                "SET n.type = $type, n.value = $value, n.props_json = $props",
                key=key, type=entity.type, value=entity.value,
                props=json.dumps(props),
            )
        return key

    def add_edge(self, edge: Edge) -> None:
        with self._driver.session() as session:
            session.run(
                "MATCH (a:Entity {key: $source}) "
                "MATCH (b:Entity {key: $target}) "
                "MERGE (a)-[r:LINK {label: $label, transform: $transform}]->(b)",
                source=edge.source, target=edge.target,
                label=edge.label, transform=edge.transform,
            )

    def _has_node(self, key: str) -> bool:
        with self._driver.session() as session:
            rec = session.run(
                "MATCH (n:Entity {key: $key}) RETURN count(n) AS c", key=key
            ).single()
            return bool(rec and rec["c"] > 0)

    def _node_properties(self, key: str) -> dict:
        with self._driver.session() as session:
            rec = session.run(
                "MATCH (n:Entity {key: $key}) RETURN n.props_json AS props", key=key
            ).single()
        if not rec or not rec["props"]:
            return {}
        try:
            return json.loads(rec["props"])
        except (TypeError, ValueError):
            return {}

    # --- Ausgabe --------------------------------------------------------
    def to_cytoscape(self) -> list[dict]:
        elements: list[dict] = []
        with self._driver.session() as session:
            for rec in session.run(
                "MATCH (n:Entity) RETURN n.key AS key, n.value AS value, n.type AS type"
            ):
                elements.append({"data": {
                    "id": rec["key"],
                    "label": rec["value"] if rec["value"] is not None else rec["key"],
                    "etype": rec["type"] or "unknown",
                }})
            for rec in session.run(
                "MATCH (a:Entity)-[r:LINK]->(b:Entity) "
                "RETURN a.key AS source, b.key AS target, r.label AS label"
            ):
                label = rec["label"] or ""
                elements.append({"data": {
                    "id": f"{rec['source']}->{rec['target']}:{label}",
                    "source": rec["source"], "target": rec["target"],
                    "label": label,
                }})
        return elements

    def stats(self) -> dict:
        with self._driver.session() as session:
            nodes = session.run(
                "MATCH (n:Entity) RETURN count(n) AS c"
            ).single()["c"]
            edges = session.run(
                "MATCH (:Entity)-[r:LINK]->() RETURN count(r) AS c"
            ).single()["c"]
        return {"nodes": nodes, "edges": edges}

    def clear(self) -> None:
        with self._driver.session() as session:
            session.run("MATCH (n:Entity) DETACH DELETE n")
