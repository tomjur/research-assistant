from __future__ import annotations

import hashlib

__all__ = [
    "collect_unique_prompts",
    "prompt_fingerprint",
    "try_add_unique",
    "variant_collection_should_stop",
]
import re
from collections.abc import Iterable

_WS_RE = re.compile(r"\s+")


def normalize_for_dedup(text: str, *, casefold: bool = False) -> str:
    """Strip edges, collapse internal whitespace, optionally casefold for dedupe keys."""
    s = text.strip()
    s = _WS_RE.sub(" ", s)
    if casefold:
        s = s.casefold()
    return s


def try_add_unique(
    existing_keys: set[str],
    candidate: str,
    *,
    normalize: bool = True,
    casefold: bool = False,
) -> tuple[bool, str]:
    """
    If candidate's dedupe key is not in existing_keys, add it and return (True, key).
    Otherwise return (False, key) without mutating for duplicates (key still returned).
    """
    key = normalize_for_dedup(candidate, casefold=casefold) if normalize else candidate
    if key in existing_keys:
        return False, key
    existing_keys.add(key)
    return True, key


def collect_unique_prompts(
    candidates: Iterable[str],
    *,
    existing: set[str] | None = None,
    max_count: int,
    normalize: bool = True,
    casefold: bool = False,
) -> tuple[list[str], set[str]]:
    """
    Collect up to max_count unique prompts (order preserved for accepted strings).

    existing: optional set of **keys** already seen (same normalization as try_add_unique).

    Returns (accepted_original_strings_in_order, all_keys_after).
    """
    if max_count < 0:
        raise ValueError("max_count must be non-negative")

    keys = set(existing) if existing is not None else set()
    accepted: list[str] = []

    for raw in candidates:
        if len(accepted) >= max_count:
            break
        added, _key = try_add_unique(keys, raw, normalize=normalize, casefold=casefold)
        if added:
            accepted.append(raw)

    return accepted, keys


def variant_collection_should_stop(
    *,
    unique_count: int,
    generation_attempts: int,
    target_uniques: int,
    max_generation_attempts: int,
) -> tuple[bool, str | None]:
    """Whether to stop proposing new prompt variants.

    Returns (should_stop, reason) where reason is "target_met" or "attempt_budget".
    """
    if target_uniques < 0 or max_generation_attempts < 0:
        raise ValueError("target_uniques and max_generation_attempts must be non-negative")
    if unique_count < 0 or generation_attempts < 0:
        raise ValueError("unique_count and generation_attempts must be non-negative")
    if unique_count >= target_uniques:
        return True, "target_met"
    if generation_attempts >= max_generation_attempts:
        return True, "attempt_budget"
    return False, None


def prompt_fingerprint(text: str, *, n: int = 8, normalize: bool = True, casefold: bool = False) -> str:
    """Short stable hash for filenames (default: SHA-256 hex prefix)."""
    if n < 1:
        raise ValueError("n must be positive")
    basis = normalize_for_dedup(text, casefold=casefold) if normalize else text
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    return digest[:n]
