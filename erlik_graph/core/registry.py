"""Transform-Registry.

Jeder Transform ist eine Funktion (value, properties) -> list[Entity].
Der @transform-Dekorator registriert sie mit Metadaten, damit beide
Adapter (FastAPI + MCP) dieselbe Liste automatisch aufgreifen koennen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .entity import Entity

TransformFn = Callable[[str, dict], list[Entity]]


@dataclass
class TransformSpec:
    name: str
    input_type: str           # welcher Entity-Typ als Input erwartet wird
    description: str
    fn: TransformFn

    def run(self, value: str, properties: dict | None = None) -> list[Entity]:
        return self.fn(value, properties or {})


_REGISTRY: dict[str, TransformSpec] = {}


def transform(name: str, input_type: str, description: str):
    """Dekorator zum Registrieren eines Transforms."""

    def wrapper(fn: TransformFn) -> TransformFn:
        if name in _REGISTRY:
            raise ValueError(f"Transform '{name}' bereits registriert")
        _REGISTRY[name] = TransformSpec(
            name=name, input_type=input_type, description=description, fn=fn
        )
        return fn

    return wrapper


def all_transforms() -> list[TransformSpec]:
    return list(_REGISTRY.values())


def get_transform(name: str) -> TransformSpec | None:
    return _REGISTRY.get(name)


def transforms_for(input_type: str) -> list[TransformSpec]:
    return [t for t in _REGISTRY.values() if t.input_type == input_type]
