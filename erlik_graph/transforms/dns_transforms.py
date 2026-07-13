"""DNS-basierte Transforms (kostenlos, keine API-Key noetig)."""

from __future__ import annotations

import dns.resolver

from ..core.entity import Entity
from ..core.registry import transform

_RESOLVER = dns.resolver.Resolver()
_RESOLVER.lifetime = 5.0


def _query(domain: str, record: str) -> list[str]:
    try:
        answers = _RESOLVER.resolve(domain, record)
        return [r.to_text().strip('"') for r in answers]
    except Exception:
        return []


@transform("domain_to_ipv4", "domain", "Loest eine Domain zu IPv4-Adressen auf (A-Records).")
def domain_to_ipv4(value: str, properties: dict) -> list[Entity]:
    return [Entity(type="ipv4", value=ip, link_label="resolves_to")
            for ip in _query(value, "A")]


@transform("domain_to_mx", "domain", "Liefert die Mailserver einer Domain (MX-Records).")
def domain_to_mx(value: str, properties: dict) -> list[Entity]:
    out = []
    for mx in _query(value, "MX"):
        host = mx.split()[-1].rstrip(".")
        out.append(Entity(type="domain", value=host, link_label="mail_server"))
    return out


@transform("domain_to_ns", "domain", "Liefert die Nameserver einer Domain (NS-Records).")
def domain_to_ns(value: str, properties: dict) -> list[Entity]:
    return [Entity(type="domain", value=ns.rstrip("."), link_label="name_server")
            for ns in _query(value, "NS")]


@transform("domain_to_txt", "domain", "Liefert TXT-Records (SPF, Verifizierungen, ...).")
def domain_to_txt(value: str, properties: dict) -> list[Entity]:
    return [Entity(type="txt_record", value=txt, link_label="txt")
            for txt in _query(value, "TXT")]
