"""Username-Enumeration (Sherlock-Prinzip, kleine Auswahl an Seiten).

Prueft, ob ein Benutzername auf gaengigen Plattformen existiert, indem
die Profil-URL abgefragt wird. Bewusst klein gehalten; erweiterbar ueber
die SITES-Tabelle. Rein passiv (nur GET auf oeffentliche Profilseiten).
"""

from __future__ import annotations

import httpx

from ..core.entity import Entity
from ..core.registry import transform

# name -> (url-template, "existiert wenn"-Bedingung)
SITES: dict[str, str] = {
    "GitHub": "https://github.com/{u}",
    "GitLab": "https://gitlab.com/{u}",
    "Reddit": "https://www.reddit.com/user/{u}",
    "Instagram": "https://www.instagram.com/{u}/",
    "X": "https://x.com/{u}",
    "Telegram": "https://t.me/{u}",
    "Keybase": "https://keybase.io/{u}",
    "Pastebin": "https://pastebin.com/u/{u}",
    "HackerNews": "https://news.ycombinator.com/user?id={u}",
    "Medium": "https://medium.com/@{u}",
}


@transform("username_to_profiles", "username",
           "Prueft gaengige Plattformen auf ein vorhandenes Profil (passiv, HTTP-GET).")
def username_to_profiles(value: str, properties: dict) -> list[Entity]:
    out: list[Entity] = []
    headers = {"User-Agent": "Mozilla/5.0 (osint-graph/0.1)"}
    with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
        for site, tmpl in SITES.items():
            url = tmpl.format(u=value)
            try:
                resp = client.get(url)
            except Exception:
                continue
            # Heuristik: 200 = Profil existiert vermutlich. 404 = nein.
            if resp.status_code == 200:
                out.append(Entity(
                    type="profile", value=url, link_label=f"on {site}",
                    properties={"site": site, "status": resp.status_code},
                ))
    return out
