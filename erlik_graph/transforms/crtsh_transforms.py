"""Certificate-Transparency-Transforms via crt.sh (kostenlos, kein Key)."""

from __future__ import annotations

import httpx

from ..core.entity import Entity
from ..core.registry import transform


@transform("domain_to_subdomains", "domain",
           "Findet Subdomains ueber Certificate-Transparency-Logs (crt.sh).")
def domain_to_subdomains(value: str, properties: dict) -> list[Entity]:
    url = f"https://crt.sh/?q=%25.{value}&output=json"
    try:
        resp = httpx.get(url, timeout=20.0, headers={"User-Agent": "osint-graph/0.1"})
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    seen: set[str] = set()
    out: list[Entity] = []
    for row in data:
        # name_value kann mehrere durch \n getrennte Namen enthalten
        for name in str(row.get("name_value", "")).splitlines():
            name = name.strip().lstrip("*.").lower()
            if not name or name in seen or name == value:
                continue
            if not name.endswith(value):
                continue
            seen.add(name)
            out.append(Entity(type="domain", value=name, link_label="subdomain",
                              properties={"source": "crt.sh"}))
    return out
