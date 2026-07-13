"""Gemeinsame Basis fuer alle Graph-Stores.

Die Transform-Ausfuehrung (`expand`) ist store-unabhaengig: sie braucht nur
ein paar Primitive (Knoten anlegen, Existenz pruefen, Properties lesen, Kante
anlegen). Konkrete Stores (in-memory networkx, Neo4j, ...) implementieren diese
Primitive; die Merge-Logik lebt hier genau einmal.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .entity import Edge, Entity
from .registry import get_transform


class BaseGraphStore(ABC):
    # --- Von konkreten Stores zu implementieren -------------------------
    @abstractmethod
    def add_entity(self, entity: Entity) -> str:
        """Legt eine Entity an (oder merged Properties) und liefert ihren Key."""

    @abstractmethod
    def add_edge(self, edge: Edge) -> None:
        """Legt eine gerichtete Kante zwischen zwei bestehenden Knoten an."""

    @abstractmethod
    def _has_node(self, key: str) -> bool:
        """True, wenn ein Knoten mit diesem Key existiert."""

    @abstractmethod
    def _node_properties(self, key: str) -> dict:
        """Liefert die Properties eines Knotens (leer, falls keine)."""

    @abstractmethod
    def to_cytoscape(self) -> list[dict]:
        """Serialisiert den Graphen in das Cytoscape-Element-Format."""

    @abstractmethod
    def stats(self) -> dict:
        """Liefert {"nodes": n, "edges": m}."""

    @abstractmethod
    def clear(self) -> None:
        """Leert den Graphen."""

    # --- Gemeinsame Transform-Ausfuehrung -------------------------------
    def expand(self, entity_type: str, value: str, transform_name: str) -> dict:
        """Fuehrt einen Transform auf einer Entity aus und merged das Ergebnis.

        Gibt die neu hinzugefuegten Knoten/Kanten zurueck (fuer inkrementelles
        UI-Update). Der Input-Knoten wird angelegt, falls er noch fehlt.
        """
        spec = get_transform(transform_name)
        if spec is None:
            raise KeyError(f"Unbekannter Transform: {transform_name}")

        source_key = self.add_entity(Entity(type=entity_type, value=value))
        results = spec.run(value, self._node_properties(source_key))

        new_nodes, new_edges = [], []
        for ent in results:
            existed = self._has_node(ent.key)
            self.add_entity(ent)
            if not existed:
                new_nodes.append(ent.to_dict())
            edge = Edge(
                source=source_key, target=ent.key,
                label=ent.link_label or spec.name, transform=spec.name,
            )
            self.add_edge(edge)
            new_edges.append(edge.to_dict())

        return {"new_nodes": new_nodes, "new_edges": new_edges,
                "source": source_key, "transform": transform_name}
