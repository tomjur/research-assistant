from __future__ import annotations

import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "execution_waves",
    "topological_order",
    "waves_from_task_graph_json",
]


def _normalize_edges(edges: Sequence[tuple[str, str] | Sequence[str]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for e in edges:
        if len(e) != 2:
            raise ValueError(f"edge must be a pair, got {e!r}")
        a, b = str(e[0]), str(e[1])
        out.append((a, b))
    return out


def _node_ids(nodes: Sequence[Mapping[str, Any] | str]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for n in nodes:
        if isinstance(n, str):
            nid = n
        else:
            if "id" not in n:
                raise ValueError(f"node missing 'id' key: {n!r}")
            nid = str(n["id"])
        if nid in seen:
            raise ValueError(f"duplicate node id: {nid!r}")
        seen.add(nid)
        ids.append(nid)
    return ids


def _build_predecessors(
    node_set: set[str], edges: list[tuple[str, str]]
) -> dict[str, set[str]]:
    preds: dict[str, set[str]] = {n: set() for n in node_set}
    for u, v in edges:
        if u not in node_set or v not in node_set:
            raise ValueError(f"edge references unknown node: {u!r} -> {v!r}")
        if u == v:
            raise ValueError(f"self-loop not allowed: {u!r}")
        preds[v].add(u)
    return preds


def _validate_completed(completed: set[str], node_set: set[str]) -> None:
    unknown = completed - node_set
    if unknown:
        raise ValueError(f"completed contains unknown node ids: {sorted(unknown)}")


def topological_order(
    nodes: Sequence[Mapping[str, Any] | str],
    edges: Sequence[tuple[str, str] | Sequence[str]],
) -> list[str]:
    """
    Return a topological ordering of all node ids (deterministic: ties by sorted id).
    Raises ValueError if the graph has a cycle or invalid structure.
    """
    ids = _node_ids(nodes)
    node_set = set(ids)
    norm_edges = _normalize_edges(edges)
    # Side effect: validates edge endpoints and rejects self-loops.
    _ = _build_predecessors(node_set, norm_edges)

    in_degree: dict[str, int] = {n: 0 for n in node_set}
    succ: dict[str, list[str]] = defaultdict(list)
    for u, v in norm_edges:
        succ[u].append(v)
        in_degree[v] += 1

    for k in succ:
        succ[k].sort()

    queue = sorted([n for n in node_set if in_degree[n] == 0])
    order: list[str] = []
    while queue:
        u = queue.pop(0)
        order.append(u)
        for v in succ[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                queue.sort()
    if len(order) != len(node_set):
        raise ValueError("graph contains a cycle (topological sort impossible)")
    return order


def execution_waves(
    nodes: Sequence[Mapping[str, Any] | str],
    edges: Sequence[tuple[str, str] | Sequence[str]],
    completed: set[str] | frozenset[str] | None = None,
) -> list[list[str]]:
    """
    Partition not-yet-completed nodes into waves: each wave is all tasks whose
    every predecessor is in the working-completed set (initially ``completed``),
    then the wave is conceptually finished before the next wave is computed.

    Completed nodes never appear in any wave. Deterministic order within a wave
    (sorted ids). Raises ValueError on unknown ids, self-loops, or a cycle
    among remaining tasks.
    """
    ids = _node_ids(nodes)
    node_set = set(ids)
    norm_edges = _normalize_edges(edges)
    preds = _build_predecessors(node_set, norm_edges)

    done: set[str] = set(completed) if completed else set()
    _validate_completed(done, node_set)

    remaining = node_set - done
    working_done = set(done)
    waves: list[list[str]] = []

    while remaining:
        ready = [v for v in remaining if preds[v].issubset(working_done)]
        ready.sort()
        if not ready:
            raise ValueError(
                "graph contains a cycle among incomplete tasks, or unsatisfiable "
                "dependencies relative to completed set"
            )
        waves.append(ready)
        working_done.update(ready)
        remaining -= set(ready)

    return waves


def waves_from_task_graph_json(data: Mapping[str, Any]) -> dict[str, Any]:
    """
    Parse a TASK_GRAPH-shaped dict and return ``{"waves": [...], "topological_order": [...]}``.

    Expected keys: ``nodes``, ``edges``; optional ``completed`` (list of ids).
    """
    nodes = data.get("nodes")
    edges = data.get("edges")
    if nodes is None or edges is None:
        raise ValueError("TASK_GRAPH JSON must include 'nodes' and 'edges'")
    completed_raw = data.get("completed") or []
    if not isinstance(completed_raw, list):
        raise ValueError("'completed' must be a list of node id strings")
    completed = {str(x) for x in completed_raw}

    topo = topological_order(nodes, edges)  # validates DAG
    waves = execution_waves(nodes, edges, completed=completed)
    remaining_ids = [n for n in topo if n not in completed]
    return {
        "waves": waves,
        "topological_order": topo,
        "remaining_node_ids": remaining_ids,
        "remaining_count": len(remaining_ids),
    }


def _main(argv: list[str]) -> int:
    """Read JSON from stdin or ``--file path``. Print JSON result to stdout."""
    path: str | None = None
    if len(argv) > 2 and argv[1] == "--file":
        path = argv[2]
    elif len(argv) > 1:
        print("usage: python -m research_utils.task_graph_waves [--file path.json]", file=sys.stderr)
        return 2

    if path:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    if not isinstance(data, dict):
        print("JSON root must be an object", file=sys.stderr)
        return 1

    try:
        result = waves_from_task_graph_json(data)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
