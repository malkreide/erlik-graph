# Erlik Graph

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Type](https://img.shields.io/badge/OSINT-graph-black)
[![CI](https://github.com/malkreide/erlik-graph/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/erlik-graph/actions/workflows/ci.yml)

> Ein OSINT-Link-Analyse-Graph mit **einer** geteilten Transform-Logik und **zwei** Oberflächen: einer visuellen FastAPI-+-Cytoscape-App **und** einem MCP-Server für LLM-gesteuerte Ermittlung.

[🇬🇧 English Version](README.md)

Teil des **[Erlik](#das-erlik-portfolio)**-Portfolios quelloffener AI-OSINT-Tools.

## Übersicht

Erlik Graph setzt die klassische Idee der Link-Analyse um — **Entities** (Knoten), verbunden durch **Transforms** (Funktionen, die eine Entity nehmen und verwandte zurückgeben), auf einem interaktiven **Graphen** — als kleines, hackbares Python-Projekt.

Der Clou ist die Architektur: Die Transform-Logik wird **einmal** als schlichte Python-Funktion geschrieben und über **zwei Adapter** verfügbar gemacht, die sich denselben Graph-Store teilen:

- **FastAPI + Cytoscape** — ein visueller, klickbarer Ermittlungs-Graph. *Du* steuerst, jeder Schritt ist deterministisch und nachvollziehbar.
- **MCP** — dieselben Transforms als Tools, die ein LLM-Agent (z.B. Claude) autonom aufruft, um anzureichern und Spuren zu verfolgen.

Einen Transform einmal hinzufügen — und er erscheint in beiden.

## Funktionen

- 🔗 **Entity/Transform/Graph**-Modell mit automatischer Knoten-Deduplizierung
- 🧩 **13 Transforms von Haus aus** — DNS (A/MX/NS/TXT), Reverse DNS, Subdomains via Certificate Transparency (crt.sh), RDAP/WHOIS, Wayback Machine, IP-Geolocation, HIBP-Datenlecks, Gravatar, Shodan-Dienste, Username-Enumeration über 10 Plattformen
- 🖥️ **Visueller Graph** (Cytoscape.js): Knoten anklicken → passende Transforms ausführen → der Graph wächst
- 🤖 **MCP-Adapter**, der jeden Transform als Tool für LLM-gesteuertes OSINT bereitstellt
- ♻️ **Geteilter Kern** — ein `@transform`-Dekorator, beide Adapter greifen ihn automatisch auf
- 🔌 **Austauschbarer Speicher** — standardmäßig In-Memory-`networkx`, oder ein geteiltes **Neo4j**-Backend, sodass MCP- und FastAPI-Adapter denselben Graphen lesen/schreiben (Claude reichert an, du inspizierst live im Browser)

## Voraussetzungen

- Python 3.11+
- Optional: ein `SHODAN_API_KEY` für den Shodan-Transform und ein `HIBP_API_KEY` für den Datenleck-Transform
- Optional: eine laufende **Neo4j**-Instanz, um einen Graphen über beide Adapter zu teilen

## Installation

```bash
git clone https://github.com/malkreide/erlik-graph.git
cd erlik-graph
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   Unix: source .venv/bin/activate
pip install -r requirements.txt
```

## Verwendung

### Variante A — visueller Graph (FastAPI)

```bash
python -m uvicorn erlik_graph.adapters.api_server:app --reload
```

http://127.0.0.1:8000 öffnen → Seed-Entity anlegen → Knoten anklicken → Transform ausführen → der Graph wächst.

### Variante B — MCP (LLM-gesteuert)

Server registrieren (siehe [.mcp.json](.mcp.json)). Die Transforms erscheinen als Tools (`domain_to_subdomains`, `username_to_profiles`, `get_graph`, …), und der Agent entscheidet selbst, welche Spuren er verfolgt.

```jsonc
{
  "mcpServers": {
    "erlik-graph": {
      "command": "python",
      "args": ["-m", "erlik_graph.adapters.mcp_server"],
      "cwd": "/pfad/zu/erlik-graph"
    }
  }
}
```

## Konfiguration

| Variable | Zweck | Erforderlich |
|---|---|---|
| `SHODAN_API_KEY` | Aktiviert den `ipv4_to_services`-Transform | Nein (ohne Key liefert der Transform einen Hinweis) |
| `HIBP_API_KEY` | Aktiviert den `email_to_breaches`-Transform (Have I Been Pwned) | Nein (ohne Key liefert der Transform einen Hinweis) |
| `ERLIK_GRAPH_BACKEND` | Graph-Backend: `memory` (Standard) oder `neo4j` | Nein |
| `NEO4J_URI` | Bolt-URI, wenn das Backend `neo4j` ist | Nur für `neo4j` (Standard `bolt://localhost:7687`) |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Neo4j-Zugangsdaten | Nur für `neo4j` |

### Geteilter Graph via Neo4j

Standardmäßig hält jeder Prozess seinen eigenen In-Memory-Graphen — MCP- und FastAPI-Adapter sehen sich also gegenseitig nicht. Beide auf Neo4j zeigen lassen teilt **einen** Graphen — genau die Schleife „Claude reichert an, du inspizierst visuell":

```bash
export ERLIK_GRAPH_BACKEND=neo4j
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=dein-passwort

# Adapter 1 — das LLM reichert über MCP an
python -m erlik_graph.adapters.mcp_server
# Adapter 2 — du siehst denselben Graphen im Browser wachsen
python -m uvicorn erlik_graph.adapters.api_server:app --reload
```

Ein anderes Backend einbinden: `BaseGraphStore` ableiten und in `create_store()` zurückgeben.

## Neuen Transform hinzufügen

1. Eine Funktion mit `@transform(name, input_type, description)` in einer Datei unter `erlik_graph/transforms/` schreiben.
2. Diese Datei in `erlik_graph/transforms/__init__.py` importieren.

Sie erscheint jetzt automatisch in **beiden** Adaptern.

```python
@transform("domain_to_ipv4", "domain", "Loest eine Domain zu ihren IPv4-Adressen auf.")
def domain_to_ipv4(value: str, properties: dict) -> list[Entity]:
    return [Entity(type="ipv4", value=ip, link_label="resolves_to")
            for ip in query(value, "A")]
```

## Projektstruktur

```
erlik_graph/
├── core/                 Datenmodell, Registry, Graph-Stores
│   ├── entity.py         Entity / Edge, Dedup-Schluessel
│   ├── registry.py       @transform-Dekorator + Registry
│   ├── base_store.py     BaseGraphStore — geteilte expand()-Logik
│   ├── graph_store.py    In-Memory-networkx-Store
│   ├── neo4j_store.py    geteilter Neo4j-Store
│   └── factory.py        create_store() — waehlt Backend per Env
├── transforms/           die eigentliche Logik — hier waechst das System
│   ├── dns_transforms.py
│   ├── rdns_transforms.py
│   ├── crtsh_transforms.py
│   ├── whois_transforms.py
│   ├── wayback_transforms.py
│   ├── geo_transforms.py
│   ├── breach_transforms.py
│   ├── gravatar_transforms.py
│   ├── shodan_transforms.py
│   └── username_transforms.py
├── adapters/
│   ├── api_server.py     FastAPI-Endpoints
│   └── mcp_server.py     MCP-Tools
└── web/index.html        Cytoscape-Oberflaeche

tests/                    Offline-pytest-Suite (laeuft in CI)
.github/workflows/ci.yml  Install + Import-Check + pytest auf 3.11 / 3.12
```

## Das Erlik-Portfolio

**Erlik** — benannt nach dem Herrn der Unterwelt in der türkisch-mongolischen (tengristischen) Mythologie — ist eine wachsende Familie kleiner, fokussierter, quelloffener AI-OSINT-Tools. Jedes Tool lebt in seinem **eigenen** Repository und teilt sich das Topic `erlik` für die Auffindbarkeit. `erlik-graph` ist das Link-Analyse-Flaggschiff; weitere Tools (Scouts, Enricher, Monitore) kommen als separate Repos hinzu.

## Rechtlicher Hinweis

Nur gegen Systeme und Daten einsetzen, für die eine Berechtigung besteht. Beim Aggregieren personenbezogener Daten gilt die DSGVO und geltendes Recht.

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md).

## Lizenz

MIT License — siehe [LICENSE](LICENSE).

## Autor

Hayal Özkan · [@malkreide](https://github.com/malkreide)
