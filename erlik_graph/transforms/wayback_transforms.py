"""Wayback-Machine-Transforms (kostenlos, kein API-Key noetig).

Fragt das Internet Archive ab: gab es Snapshots einer Domain? Nutzt die
CDX-API fuer eine kleine Auswahl archivierter URLs. Rein passiv.
"""

from __future__ import annotations

import httpx

from ..core.entity import Entity
from ..core.registry import transform

_CDX = "https://web.archive.org/cdx/search/cdx"


@transform("domain_to_wayback", "domain",
           "Archivierte Snapshots einer Domain aus der Wayback Machine (kostenlos).")
def domain_to_wayback(value: str, properties: dict) -> list[Entity]:
    params = {
        "url": value,
        "matchType": "domain",
        "output": "json",
        "fl": "original,timestamp,statuscode",
        "collapse": "urlkey",
        "limit": "25",
    }
    try:
        resp = httpx.get(_CDX, params=params, timeout=20.0,
                         headers={"User-Agent": "osint-graph/0.1"})
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        return [Entity(type="note", value=f"Wayback-Fehler: {e}", link_label="error")]

    # Erste Zeile ist der Header (['original','timestamp','statuscode']).
    if not rows or len(rows) < 2:
        return []

    out: list[Entity] = []
    seen: set[str] = set()
    for row in rows[1:]:
        original = row[0]
        timestamp = row[1] if len(row) > 1 else ""
        status = row[2] if len(row) > 2 else ""
        if original in seen:
            continue
        seen.add(original)
        snapshot = f"https://web.archive.org/web/{timestamp}/{original}"
        out.append(Entity(
            type="archived_url", value=snapshot, link_label="archived",
            properties={"original": original, "timestamp": timestamp,
                        "statuscode": status, "source": "wayback"},
        ))
    return out
