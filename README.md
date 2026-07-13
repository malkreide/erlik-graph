# Erlik Graph

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Type](https://img.shields.io/badge/OSINT-graph-black)

> An OSINT link-analysis graph with one shared transform core and two front-ends: a visual FastAPI + Cytoscape app **and** an MCP server for LLM-driven investigation.

[🇩🇪 Deutsche Version](README.de.md)

Part of the **[Erlik](#the-erlik-portfolio)** portfolio of open-source AI OSINT tools.

## Overview

Erlik Graph implements the classic link-analysis workflow — **Entities** (nodes) connected by **Transforms** (functions that take one entity and return related ones) on an interactive **Graph** — as a small, hackable Python project.

The point is the architecture: transform logic is written **once** as plain Python functions and exposed through **two adapters** that share the same graph store:

- **FastAPI + Cytoscape** — a visual, clickable investigation graph. *You* drive it, every step is deterministic and auditable.
- **MCP** — the same transforms as tools an LLM agent (e.g. Claude) calls autonomously to enrich and follow leads.

Add a transform once, and it appears in both.

## Features

- 🔗 **Entity/Transform/Graph** model with automatic node de-duplication
- 🧩 **7 transforms out of the box** — DNS (A/MX/NS/TXT), certificate-transparency subdomains (crt.sh), Shodan services, username enumeration across 10 platforms
- 🖥️ **Visual graph** front-end (Cytoscape.js), click a node → run applicable transforms → the graph grows
- 🤖 **MCP adapter** exposing every transform as a tool for LLM-driven OSINT
- ♻️ **Shared core** — one `@transform` decorator, both adapters pick it up automatically
- 🔌 **Pluggable storage** — in-memory `networkx` today, swap for Neo4j by reimplementing one class

## Prerequisites

- Python 3.11+
- Optional: a `SHODAN_API_KEY` for the Shodan transform

## Installation

```bash
git clone https://github.com/malkreide/erlik-graph.git
cd erlik-graph
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   Unix: source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Variant A — visual graph (FastAPI)

```bash
python -m uvicorn erlik_graph.adapters.api_server:app --reload
```

Open http://127.0.0.1:8000 → add a seed entity → click a node → run a transform → the graph expands.

### Variant B — MCP (LLM-driven)

Register the server (see [.mcp.json](.mcp.json)) with your MCP client. The transforms appear as tools (`domain_to_subdomains`, `username_to_profiles`, `get_graph`, …) and the agent decides which leads to follow.

```jsonc
{
  "mcpServers": {
    "erlik-graph": {
      "command": "python",
      "args": ["-m", "erlik_graph.adapters.mcp_server"],
      "cwd": "/path/to/erlik-graph"
    }
  }
}
```

## Configuration

| Variable | Purpose | Required |
|---|---|---|
| `SHODAN_API_KEY` | Enables the `ipv4_to_services` transform | No (transform returns a hint if unset) |

## Adding a transform

1. Write a function decorated with `@transform(name, input_type, description)` in a file under `erlik_graph/transforms/`.
2. Import that file in `erlik_graph/transforms/__init__.py`.

It now appears in **both** adapters automatically.

```python
@transform("domain_to_ipv4", "domain", "Resolves a domain to its IPv4 addresses.")
def domain_to_ipv4(value: str, properties: dict) -> list[Entity]:
    return [Entity(type="ipv4", value=ip, link_label="resolves_to")
            for ip in query(value, "A")]
```

## Project Structure

```
erlik_graph/
├── core/                 Data model, registry, graph store
│   ├── entity.py         Entity / Edge, de-dup key
│   ├── registry.py       @transform decorator + registry
│   └── graph_store.py    networkx store, expand(), Cytoscape export
├── transforms/           the actual logic — this is where the system grows
│   ├── dns_transforms.py
│   ├── crtsh_transforms.py
│   ├── shodan_transforms.py
│   └── username_transforms.py
├── adapters/
│   ├── api_server.py     FastAPI endpoints
│   └── mcp_server.py     MCP tools
└── web/index.html        Cytoscape front-end
```

## The Erlik Portfolio

**Erlik** — named after the lord of the underworld in Turkic-Mongolic (Tengrist) mythology — is a growing family of small, focused, open-source AI OSINT tools. Each tool lives in its **own** repository and shares the `erlik` topic for discoverability. `erlik-graph` is the link-analysis flagship; further tools (scouts, enrichers, monitors) join the portfolio as separate repos.

## Legal Notice

For use only against systems and data you are authorized to investigate. When aggregating personal data, comply with the GDPR and applicable law.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT License — see [LICENSE](LICENSE).

## Author

Hayal Özkan · [@malkreide](https://github.com/malkreide)
