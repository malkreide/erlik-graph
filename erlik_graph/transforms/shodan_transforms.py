"""Shodan-Transforms. Benoetigt SHODAN_API_KEY als Umgebungsvariable.

Ohne Key liefern die Transforms einen Hinweis-Knoten statt zu crashen,
damit der Rest des Systems auch ohne Key lauffaehig bleibt.
"""

from __future__ import annotations

import os

import httpx

from ..core.entity import Entity
from ..core.registry import transform

_API = "https://api.shodan.io"


def _key() -> str | None:
    return os.environ.get("SHODAN_API_KEY")


@transform("ipv4_to_services", "ipv4",
           "Offene Ports und Dienste einer IP (Shodan). Braucht SHODAN_API_KEY.")
def ipv4_to_services(value: str, properties: dict) -> list[Entity]:
    key = _key()
    if not key:
        return [Entity(type="note", value="SHODAN_API_KEY nicht gesetzt",
                       link_label="config")]
    try:
        resp = httpx.get(f"{_API}/shodan/host/{value}", params={"key": key}, timeout=20.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [Entity(type="note", value=f"Shodan-Fehler: {e}", link_label="error")]

    out: list[Entity] = []
    for item in data.get("data", []):
        port = item.get("port")
        product = item.get("product") or item.get("_shodan", {}).get("module", "")
        label = f"port {port}" + (f" ({product})" if product else "")
        out.append(Entity(type="service", value=f"{value}:{port}",
                          link_label="exposes",
                          properties={"port": port, "product": product,
                                      "transport": item.get("transport")}))
        _ = label
    for host in data.get("hostnames", []):
        out.append(Entity(type="domain", value=host, link_label="ptr_hostname"))
    return out
