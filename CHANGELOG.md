# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-13

### Added
- Initial release of Erlik Graph.
- Shared core: `Entity`/`Edge` model, `@transform` registry, `networkx` graph store with node de-duplication.
- 7 transforms: `domain_to_ipv4`, `domain_to_mx`, `domain_to_ns`, `domain_to_txt`, `domain_to_subdomains` (crt.sh), `ipv4_to_services` (Shodan), `username_to_profiles`.
- FastAPI adapter with Cytoscape.js visual graph front-end.
- MCP adapter exposing every transform plus `list_transforms`, `get_graph`, `clear_graph`.
- Bilingual documentation (EN/DE).
