"""Breach-Transforms via Have I Been Pwned (HIBP).

Die HIBP-Account-API braucht einen Key (HIBP_API_KEY). Ohne Key liefert der
Transform — wie der Shodan-Transform — einen Hinweis-Knoten statt zu crashen,
damit das System auch ohne Key lauffaehig bleibt.
"""

from __future__ import annotations

import os

import httpx

from ..core.entity import Entity
from ..core.registry import transform

_API = "https://haveibeenpwned.com/api/v3"


def _key() -> str | None:
    return os.environ.get("HIBP_API_KEY")


@transform("email_to_breaches", "email",
           "Datenlecks zu einer E-Mail (Have I Been Pwned). Braucht HIBP_API_KEY.")
def email_to_breaches(value: str, properties: dict) -> list[Entity]:
    key = _key()
    if not key:
        return [Entity(type="note", value="HIBP_API_KEY nicht gesetzt",
                       link_label="config")]
    try:
        resp = httpx.get(
            f"{_API}/breachedaccount/{value}",
            params={"truncateResponse": "false"},
            headers={"hibp-api-key": key, "User-Agent": "osint-graph/0.1"},
            timeout=20.0,
        )
        # 404 = keine Treffer (kein Leck), das ist ein gueltiges Ergebnis.
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [Entity(type="note", value=f"HIBP-Fehler: {e}", link_label="error")]

    out: list[Entity] = []
    for breach in data:
        name = breach.get("Name") or breach.get("Title")
        if not name:
            continue
        out.append(Entity(
            type="breach", value=name, link_label="found_in",
            properties={
                "title": breach.get("Title"),
                "domain": breach.get("Domain"),
                "breach_date": breach.get("BreachDate"),
                "pwn_count": breach.get("PwnCount"),
                "data_classes": breach.get("DataClasses"),
            },
        ))
    return out
