"""Reverse-DNS-Transforms (kostenlos, keine API-Key noetig)."""

from __future__ import annotations

import dns.resolver
import dns.reversename

from ..core.entity import Entity
from ..core.registry import transform

_RESOLVER = dns.resolver.Resolver()
_RESOLVER.lifetime = 5.0


@transform("ipv4_to_reverse_dns", "ipv4",
           "Reverse-DNS-Lookup (PTR): welcher Hostname zeigt auf diese IP?")
def ipv4_to_reverse_dns(value: str, properties: dict) -> list[Entity]:
    try:
        rev = dns.reversename.from_address(value)
    except Exception:
        return []
    try:
        answers = _RESOLVER.resolve(rev, "PTR")
    except Exception:
        return []

    out: list[Entity] = []
    seen: set[str] = set()
    for r in answers:
        host = r.to_text().rstrip(".").lower()
        if not host or host in seen:
            continue
        seen.add(host)
        out.append(Entity(type="domain", value=host, link_label="ptr_record",
                          properties={"source": "reverse_dns"}))
    return out
