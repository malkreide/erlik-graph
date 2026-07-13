"""Kern-Datenmodell: Entity, Edge, TransformResult.

Eine Entity ist ein Knoten im Graphen (E-Mail, Domain, IP, ...).
Ein Transform nimmt eine Entity und liefert neue, verbundene Entities.
Der Kante-Text (link_label) beschreibt die Beziehung zur Input-Entity.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def entity_key(entity_type: str, value: str) -> str:
    """Stabiler Dedup-Schlüssel. Gleicher Typ + gleicher Wert = ein Knoten."""
    return f"{entity_type.lower()}::{value.strip().lower()}"


@dataclass
class Entity:
    type: str                 # z.B. "domain", "ipv4", "email", "person"
    value: str                # der eigentliche Wert
    properties: dict = field(default_factory=dict)
    link_label: str | None = None   # Beschriftung der Kante vom Input zu dieser Entity

    @property
    def key(self) -> str:
        return entity_key(self.type, self.value)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "type": self.type,
            "value": self.value,
            "properties": self.properties,
        }


@dataclass
class Edge:
    source: str               # entity_key des Ausgangsknotens
    target: str               # entity_key des Zielknotens
    label: str                # Beziehung, z.B. "resolves_to"
    transform: str            # welcher Transform diese Kante erzeugt hat

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "transform": self.transform,
        }
