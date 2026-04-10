import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from task_graph_waves import (
    execution_waves,
    topological_order,
    waves_from_task_graph_json,
)


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for d in [p, *p.parents]:
        if (d / "pyproject.toml").is_file():
            return d
    raise RuntimeError("pyproject.toml not found from test file")


def _all_skill_scripts_pythonpath() -> str:
    root = _repo_root()
    skills = root / "research projects" / "skills"
    dirs = sorted(p for p in skills.glob("*/scripts") if p.is_dir())
    return os.pathsep.join(str(p) for p in dirs)


def test_linear_chain_waves() -> None:
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [("a", "b"), ("b", "c")]
    assert execution_waves(nodes, edges) == [["a"], ["b"], ["c"]]
    assert topological_order(nodes, edges) == ["a", "b", "c"]


def test_two_parallel_roots_merge() -> None:
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [("a", "c"), ("b", "c")]
    assert execution_waves(nodes, edges) == [["a", "b"], ["c"]]
    topo = topological_order(nodes, edges)
    assert topo.index("a") < topo.index("c")
    assert topo.index("b") < topo.index("c")


def test_diamond() -> None:
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}]
    edges = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
    assert execution_waves(nodes, edges) == [["a"], ["b", "c"], ["d"]]


def test_cycle_raises_topological_order() -> None:
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [("a", "b"), ("b", "a")]
    with pytest.raises(ValueError, match="cycle"):
        topological_order(nodes, edges)


def test_cycle_raises_execution_waves() -> None:
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [("a", "b"), ("b", "a")]
    with pytest.raises(ValueError, match="cycle"):
        waves_from_task_graph_json({"nodes": nodes, "edges": edges})


def test_completed_skips_and_correct_next_waves() -> None:
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [("a", "b"), ("b", "c")]
    assert execution_waves(nodes, edges, completed={"a"}) == [["b"], ["c"]]
    assert execution_waves(nodes, edges, completed={"a", "b"}) == [["c"]]
    assert execution_waves(nodes, edges, completed={"a", "b", "c"}) == []


def test_completed_unknown_id_raises() -> None:
    nodes = [{"id": "a"}]
    edges: list[tuple[str, str]] = []
    with pytest.raises(ValueError, match="unknown"):
        execution_waves(nodes, edges, completed={"x"})


def test_self_loop_raises() -> None:
    nodes = [{"id": "a"}]
    edges = [("a", "a")]
    with pytest.raises(ValueError, match="self-loop"):
        execution_waves(nodes, edges)


def test_unknown_edge_endpoint_raises() -> None:
    nodes = [{"id": "a"}]
    edges = [("a", "b")]
    with pytest.raises(ValueError, match="unknown node"):
        execution_waves(nodes, edges)


def test_duplicate_node_id_raises() -> None:
    nodes = [{"id": "a"}, {"id": "a"}]
    edges: list[tuple[str, str]] = []
    with pytest.raises(ValueError, match="duplicate"):
        execution_waves(nodes, edges)


def test_nodes_as_string_ids() -> None:
    nodes = ["a", "b"]
    edges = [("a", "b")]
    assert execution_waves(nodes, edges) == [["a"], ["b"]]


def test_graph_extended_after_partial_completion() -> None:
    """Re-plan adds new nodes; completed set excludes finished work."""
    nodes_v1 = [{"id": "a"}, {"id": "b"}]
    edges_v1 = [("a", "b")]
    assert execution_waves(nodes_v1, edges_v1, completed={"a"}) == [["b"]]

    nodes_v2 = [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}]
    edges_v2 = [("a", "b"), ("b", "c"), ("b", "d")]
    assert execution_waves(nodes_v2, edges_v2, completed={"a", "b"}) == [["c", "d"]]


def test_waves_from_task_graph_json_shape() -> None:
    data = {
        "nodes": [{"id": "a", "description": "root"}, {"id": "b", "description": "leaf"}],
        "edges": [["a", "b"]],
        "completed": [],
    }
    out = waves_from_task_graph_json(data)
    assert out["waves"] == [["a"], ["b"]]
    assert out["topological_order"] == ["a", "b"]
    assert out["remaining_node_ids"] == ["a", "b"]
    assert out["remaining_count"] == 2


def test_waves_from_task_graph_json_completed() -> None:
    data = {
        "nodes": [{"id": "a"}, {"id": "b"}],
        "edges": [["a", "b"]],
        "completed": ["a"],
    }
    out = waves_from_task_graph_json(data)
    assert out["waves"] == [["b"]]
    assert out["remaining_count"] == 1
    assert out["remaining_node_ids"] == ["b"]


def test_cli_stdin_json() -> None:
    payload = json.dumps(
        {"nodes": [{"id": "x"}], "edges": [], "completed": []}
    )
    env = {**os.environ, "PYTHONPATH": _all_skill_scripts_pythonpath()}
    proc = subprocess.run(
        [sys.executable, "-m", "task_graph_waves"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(_repo_root()),
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["waves"] == [["x"]]
