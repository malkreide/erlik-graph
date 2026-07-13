"""In-Memory-Graph auf Basis von networkx.

Dedupliziert Knoten ueber entity_key. Kann einen Transform ausfuehren
und das Ergebnis direkt in den Graphen mergen. to_cytoscape() liefert
das Format, das das Web-Frontend rendert.

Spaeter austauschbar gegen Neo4j: nur diese Klasse neu implementieren,
die Adapter bleiben unveraendert.
"""

from __future__ import annotations

import networkx as nx

from .entity import Edge, Entity, entity_key
from .registry import get_transform


class GraphStore:
    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

    # --- Mutation -------------------------------------------------------
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

    # --- Transform-Ausfuehrung -----------------------------------------
    def expand(self, entity_type: str, value: str, transform_name: str) -> dict:
        """Fuehrt einen Transform auf einer Entity aus und merged das Ergebnis.

        Gibt die neu hinzugefuegten Knoten/Kanten zurueck (fuer inkrementelles
        UI-Update). Der Input-Knoten wird angelegt, falls er noch fehlt.
        """
        spec = get_transform(transform_name)
        if spec is None:
            raise KeyError(f"Unbekannter Transform: {transform_name}")

        source_key = self.add_entity(Entity(type=entity_type, value=value))
        results = spec.run(value, self.g.nodes[source_key].get("properties", {}))

        new_nodes, new_edges = [], []
        for ent in results:
            existed = self.g.has_node(ent.key)
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
