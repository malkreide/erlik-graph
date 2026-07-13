"""WHOIS-/RDAP-Transforms (kostenlos, kein API-Key noetig).

Nutzt RDAP (rdap.org als Router zum autoritativen Server) statt klassischem
Port-43-WHOIS: strukturiertes JSON, HTTPS, keine Extra-Dependency. Liefert
Registrar, Nameserver, Kontakt-E-Mails und Datums-Events als anknuepfbare
Knoten (z.B. E-Mail -> email_to_breaches).
"""

from __future__ import annotations

import httpx

from ..core.entity import Entity
from ..core.registry import transform


def _events(data: dict) -> dict:
    """Mappt RDAP-Events auf {aktion: datum}, z.B. registration/expiration."""
    out: dict[str, str] = {}
    for ev in data.get("events", []):
        action = ev.get("eventAction")
        date = ev.get("eventDate")
        if action and date:
            out[action] = date
    return out


def _vcard_field(entity: dict, field: str) -> str | None:
    """Zieht ein Feld (fn, email, ...) aus dem jCard/vcardArray einer Entity."""
    vcard = entity.get("vcardArray")
    if not isinstance(vcard, list) or len(vcard) < 2:
        return None
    for item in vcard[1]:
        if isinstance(item, list) and item and item[0] == field:
            return item[-1] if isinstance(item[-1], str) else None
    return None


@transform("domain_to_whois", "domain",
           "Registrar, Nameserver, Kontakt-E-Mails und Daten via RDAP (kostenlos).")
def domain_to_whois(value: str, properties: dict) -> list[Entity]:
    url = f"https://rdap.org/domain/{value}"
    try:
        resp = httpx.get(url, timeout=20.0, follow_redirects=True,
                         headers={"User-Agent": "osint-graph/0.1",
                                  "Accept": "application/rdap+json"})
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [Entity(type="note", value=f"RDAP-Fehler: {e}", link_label="error")]

    events = _events(data)
    out: list[Entity] = []
    seen_emails: set[str] = set()

    # Registrar + evtl. Kontakte aus den RDAP-Entities
    for ent in data.get("entities", []):
        roles = ent.get("roles", []) or []
        name = _vcard_field(ent, "fn")
        if "registrar" in roles and name:
            out.append(Entity(
                type="organization", value=name, link_label="registrar",
                properties={"roles": roles,
                            "registered": events.get("registration"),
                            "expires": events.get("expiration")},
            ))
        email = _vcard_field(ent, "email")
        if email and email.lower() not in seen_emails:
            seen_emails.add(email.lower())
            out.append(Entity(
                type="email", value=email, link_label="whois_contact",
                properties={"roles": roles},
            ))

    # Nameserver
    for ns in data.get("nameservers", []):
        host = ns.get("ldhName")
        if host:
            out.append(Entity(type="domain", value=host.rstrip(".").lower(),
                              link_label="name_server", properties={"source": "rdap"}))

    return out
