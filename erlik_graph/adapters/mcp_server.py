"""MCP-Adapter: registriert jeden Transform als MCP-Tool.

Derselbe GraphStore wie beim FastAPI-Adapter wird befuellt, sodass ein
LLM-Agent autonom anreichern kann und du das Ergebnis danach visuell
inspizierst. Start (stdio):  python -m erlik_graph.adapters.mcp_server

Eintrag fuer claude mcp / .mcp.json:
  command: python   args: ["-m", "erlik_graph.adapters.mcp_server"]
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

import erlik_graph  # noqa: F401  (registriert alle Transforms)
from erlik_graph.core import GraphStore, TransformSpec, all_transforms

mcp = FastMCP("erlik_graph")
STORE = GraphStore()


def _make_tool(spec: TransformSpec):
    """Erzeugt eine Tool-Funktion fuer einen Transform (mit Typ-Annotationen,
    damit FastMCP das Schema ableiten kann)."""

    def _tool(value: str) -> dict:
        result = STORE.expand(spec.input_type, value, spec.name)
        return {
            "transform": spec.name,
            "input": {"type": spec.input_type, "value": value},
            "new_nodes": result["new_nodes"],
            "new_edges": result["new_edges"],
            "graph_stats": STORE.stats(),
        }

    _tool.__name__ = spec.name
    _tool.__doc__ = f"{spec.description} Input-Typ: {spec.input_type}."
    return _tool


for _spec in all_transforms():
    mcp.add_tool(_make_tool(_spec), name=_spec.name,
                 description=f"{_spec.description} Input-Typ: {_spec.input_type}.")


@mcp.tool()
def list_transforms() -> list[dict]:
    """Listet alle verfuegbaren Transforms mit Input-Typ und Beschreibung."""
    return [{"name": t.name, "input_type": t.input_type,
             "description": t.description} for t in all_transforms()]


@mcp.tool()
def get_graph() -> dict:
    """Gibt den aktuellen Ermittlungs-Graphen im Cytoscape-Format zurueck."""
    return {"elements": STORE.to_cytoscape(), "stats": STORE.stats()}


@mcp.tool()
def clear_graph() -> dict:
    """Leert den Graphen (neue Ermittlung starten)."""
    STORE.clear()
    return {"stats": STORE.stats()}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
