"""Gravatar-Transforms (kostenlos, kein API-Key noetig).

Gravatar bildet E-Mails ueber einen MD5-Hash auf oeffentliche Avatare/Profile
ab. Ein Treffer verraet, dass die Adresse aktiv genutzt wurde, und liefert oft
Benutzername, Anzeigename und verknuepfte Konten. Rein passiv (HTTP-GET).
"""

from __future__ import annotations

import hashlib

import httpx

from ..core.entity import Entity
from ..core.registry import transform


def _hash(email: str) -> str:
    return hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()


@transform("email_to_gravatar", "email",
           "Gravatar-Avatar/Profil zu einer E-Mail (kostenlos, passiver GET).")
def email_to_gravatar(value: str, properties: dict) -> list[Entity]:
    digest = _hash(value)
    headers = {"User-Agent": "osint-graph/0.1"}
    avatar = f"https://www.gravatar.com/avatar/{digest}"

    # d=404 -> Gravatar liefert 404 statt eines Default-Bildes, wenn es zu
    # dieser Adresse keinen Avatar gibt. So unterscheiden wir Treffer/kein Treffer.
    try:
        resp = httpx.get(avatar, params={"d": "404"}, timeout=10.0,
                         follow_redirects=True, headers=headers)
    except Exception as e:
        return [Entity(type="note", value=f"Gravatar-Fehler: {e}", link_label="error")]

    if resp.status_code != 200:
        return []  # kein Gravatar zu dieser Adresse

    out: list[Entity] = [Entity(
        type="profile", value=avatar, link_label="gravatar",
        properties={"site": "Gravatar", "hash": digest},
    )]

    # Optional: oeffentliches Profil-JSON (Username/Anzeigename/Konten).
    try:
        prof = httpx.get(f"https://www.gravatar.com/{digest}.json", timeout=10.0,
                         follow_redirects=True, headers=headers)
        if prof.status_code == 200:
            entry = (prof.json().get("entry") or [{}])[0]
            username = entry.get("preferredUsername")
            display = entry.get("displayName")
            if username:
                out.append(Entity(
                    type="username", value=username, link_label="gravatar_username",
                    properties={"display_name": display, "source": "gravatar"},
                ))
    except Exception:
        pass  # Profil ist optionaler Bonus; Avatar-Treffer reicht.

    return out
