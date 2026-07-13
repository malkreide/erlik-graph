# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Shared graph backend: `Neo4jGraphStore` plus a `create_store()` factory selected via `ERLIK_GRAPH_BACKEND`. With `neo4j`, the MCP and FastAPI adapters read/write the same graph (LLM enriches, you inspect it live).
- `BaseGraphStore` base class holding the store-agnostic `expand()` logic; `GraphStore` and `Neo4jGraphStore` share it.
- 3 new free transforms: `domain_to_whois` (RDAP), `ipv4_to_geo` (ipwho.is), `email_to_breaches` (Have I Been Pwned, needs `HIBP_API_KEY`).
- New entity types `organization`, `location`, `breach` with front-end colors.

### Changed
- Both adapters now build their store through `create_store()` instead of instantiating `GraphStore` directly.

## [0.1.0] - 2026-07-13

### Added
- Initial release of Erlik Graph.
- Shared core: `Entity`/`Edge` model, `@transform` registry, `networkx` graph store with node de-duplication.
- 7 transforms: `domain_to_ipv4`, `domain_to_mx`, `domain_to_ns`, `domain_to_txt`, `domain_to_subdomains` (crt.sh), `ipv4_to_services` (Shodan), `username_to_profiles`.
- FastAPI adapter with Cytoscape.js visual graph front-end.
- MCP adapter exposing every transform plus `list_transforms`, `get_graph`, `clear_graph`.
- Bilingual documentation (EN/DE).
