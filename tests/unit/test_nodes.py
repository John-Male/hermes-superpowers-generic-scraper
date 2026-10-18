from generic_scraper.distributed.nodes import Node, NodeRegistry, default_registry


def test_find_matching_node_respects_memory_and_browser():
    registry = NodeRegistry()
    registry.register(Node("n1", has_gpu=False, memory_gb=1, browsers=frozenset({"chrome"})))
    registry.register(Node("n2", has_gpu=False, memory_gb=4, browsers=frozenset({"chrome", "firefox"})))
    match = registry.find_matching_node(min_memory_gb=2, browser="chrome")
    assert match.node_id == "n2"


def test_find_matching_node_returns_none_when_no_node_qualifies():
    registry = NodeRegistry()
    registry.register(Node("n1", has_gpu=False, memory_gb=1))
    assert registry.find_matching_node(requires_gpu=True) is None


def test_default_registry_has_a_node_satisfying_chrome_2gb_no_gpu():
    registry = default_registry()
    match = registry.find_matching_node(requires_gpu=False, min_memory_gb=2, browser="chrome")
    assert match is not None
