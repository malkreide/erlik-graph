"""Geolocation-Transforms (kostenlos, kein API-Key noetig).

Nutzt ipwho.is: HTTPS, keine Registrierung, liefert Land/Stadt und ASN/ISP.
Daraus werden ein Standort-Knoten und (falls vorhanden) ein Hosting-/ISP-
Organisationsknoten. Bei Rate-Limit/Fehler wird ein note-Knoten zurueckgegeben.
"""

from __future__ import annotations

import httpx

from ..core.entity import Entity
from ..core.registry import transform


@transform("ipv4_to_geo", "ipv4",
           "Geolocation, Land/Stadt und ASN/ISP einer IP (ipwho.is, kostenlos).")
def ipv4_to_geo(value: str, properties: dict) -> list[Entity]:
    try:
        resp = httpx.get(f"https://ipwho.is/{value}", timeout=15.0,
                         headers={"User-Agent": "osint-graph/0.1"})
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [Entity(type="note", value=f"Geo-Fehler: {e}", link_label="error")]

    if not data.get("success", False):
        reason = data.get("message", "unbekannt")
        return [Entity(type="note", value=f"Geo fehlgeschlagen: {reason}",
                       link_label="error")]

    out: list[Entity] = []

    city = data.get("city")
    country = data.get("country")
    parts = [p for p in (city, country) if p]
    if parts:
        out.append(Entity(
            type="location", value=", ".join(parts), link_label="geolocated_in",
            properties={
                "country": country, "country_code": data.get("country_code"),
                "region": data.get("region"), "city": city,
                "latitude": data.get("latitude"), "longitude": data.get("longitude"),
            },
        ))

    conn = data.get("connection") or {}
    org = conn.get("org") or conn.get("isp")
    if org:
        out.append(Entity(
            type="organization", value=org, link_label="hosted_by",
            properties={"asn": conn.get("asn"), "isp": conn.get("isp"),
                        "domain": conn.get("domain")},
        ))

    return out
