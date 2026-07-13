"""In-Memory-Graph auf Basis von networkx.

Dedupliziert Knoten ueber entity_key. Die Transform-Ausfuehrung (`expand`)
kommt aus BaseGraphStore; hier werden nur die networkx-spezifischen Primitive
und die Cytoscape-Serialisierung implementiert.

Fuer einen prozessuebergreifend geteilten Graphen (MCP reichert an, du
inspizierst visuell) siehe Neo4jGraphStore und create_store().
"""

from __future__ import annotations

import networkx as nx

from .base_store import BaseGraphStore
from .entity import Edge, Entity


class GraphStore(BaseGraphStore):
    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

    # --- Primitive ------------------------------------------------------
    def add_entity(self, entity: Entity) -> str:
        key = entity.key
        if self.g.has_node(key):
            # Properties zusammenfuehren, ohne bestehende zu verlieren
            self.g.nodes[key]["properties"].update(entity.properties)
        else:
            self.g.add_node(
                key, type=entity.type, value=entity.value,
                properties=dict(entity.properties),
            )
        return key

    def add_edge(self, edge: Edge) -> None:
        self.g.add_edge(
            edge.source, edge.target, label=edge.label, transform=edge.transform
        )

    def _has_node(self, key: str) -> bool:
        return self.g.has_node(key)

    def _node_properties(self, key: str) -> dict:
        return self.g.nodes[key].get("properties", {})

    # --- Ausgabe --------------------------------------------------------
    def to_cytoscape(self) -> list[dict]:
        elements = []
        for key, data in self.g.nodes(data=True):
            elements.append({"data": {
                "id": key, "label": data.get("value", key),
                "etype": data.get("type", "unknown"),
            }})
        for src, dst, data in self.g.edges(data=True):
            elements.append({"data": {
                "id": f"{src}->{dst}:{data.get('label')}",
                "source": src, "target": dst,
                "label": data.get("label", ""),
            }})
        return elements

    def stats(self) -> dict:
        return {"nodes": self.g.number_of_nodes(),
                "edges": self.g.number_of_edges()}

    def clear(self) -> None:
        self.g.clear()
