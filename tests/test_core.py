"""Offline-Tests fuer Kern und Registrierung (kein Netzwerk noetig)."""

from __future__ import annotations

import erlik_graph  # noqa: F401  (registriert alle Transforms)
from erlik_graph.core import (
    BaseGraphStore,
    Entity,
    GraphStore,
    all_transforms,
    create_store,
    get_transform,
    registry,
)

EXPECTED_TRANSFORMS = {
    "domain_to_ipv4", "domain_to_mx", "domain_to_ns", "domain_to_txt",
    "domain_to_subdomains", "domain_to_whois", "domain_to_wayback",
    "ipv4_to_services", "ipv4_to_geo", "ipv4_to_reverse_dns",
    "username_to_profiles", "email_to_breaches", "email_to_gravatar",
}


def test_all_expected_transforms_registered():
    names = {t.name for t in all_transforms()}
    missing = EXPECTED_TRANSFORMS - names
    assert not missing, f"nicht registriert: {missing}"


def test_transform_specs_have_metadata():
    for spec in all_transforms():
        assert spec.name and spec.input_type and spec.description
        assert callable(spec.fn)


def test_create_store_defaults_to_memory():
    store = create_store()
    assert isinstance(store, GraphStore)
    assert isinstance(store, BaseGraphStore)


def test_create_store_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv("ERLIK_GRAPH_BACKEND", "postgres")
    try:
        create_store()
        raise AssertionError("erwartete ValueError")
    except ValueError:
        pass


def test_entity_dedup_by_key():
    store = GraphStore()
    store.add_entity(Entity(type="domain", value="Example.COM"))
    store.add_entity(Entity(type="domain", value="example.com", properties={"x": 1}))
    assert store.stats()["nodes"] == 1


def test_expand_merges_results(monkeypatch):
    store = GraphStore()

    def _stub(value, props):
        return [Entity(type="ipv4", value="1.2.3.4", link_label="resolves_to")]

    spec = registry.TransformSpec("_stub_expand", "domain", "stub", _stub)
    monkeypatch.setitem(registry._REGISTRY, "_stub_expand", spec)

    res = store.expand("domain", "example.com", "_stub_expand")
    assert len(res["new_nodes"]) == 1
    assert len(res["new_edges"]) == 1
    assert store.stats() == {"nodes": 2, "edges": 1}


def test_expand_unknown_transform_raises():
    store = GraphStore()
    try:
        store.expand("domain", "example.com", "does_not_exist")
        raise AssertionError("erwartete KeyError")
    except KeyError:
        pass


def test_key_gated_transforms_degrade_without_key(monkeypatch):
    monkeypatch.delenv("SHODAN_API_KEY", raising=False)
    monkeypatch.delenv("HIBP_API_KEY", raising=False)
    shodan = get_transform("ipv4_to_services").run("8.8.8.8", {})
    hibp = get_transform("email_to_breaches").run("a@b.com", {})
    assert shodan and shodan[0].type == "note"
    assert hibp and hibp[0].type == "note"


def test_to_cytoscape_shape():
    store = GraphStore()
    store.add_entity(Entity(type="domain", value="example.com"))
    elements = store.to_cytoscape()
    assert elements and "data" in elements[0]
    assert elements[0]["data"]["etype"] == "domain"
