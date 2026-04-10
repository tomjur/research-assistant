import pytest

from prompt_variants import (
    collect_unique_prompts,
    normalize_for_dedup,
    prompt_fingerprint,
    try_add_unique,
    variant_collection_should_stop,
)


def test_normalize_for_dedup_strips_and_collapses_whitespace() -> None:
    assert normalize_for_dedup("  a \n\t b  ") == "a b"


def test_normalize_for_dedup_casefold() -> None:
    assert normalize_for_dedup("Ab C", casefold=True) == "ab c"


def test_try_add_unique_adds_once() -> None:
    keys: set[str] = set()
    assert try_add_unique(keys, "hello") == (True, "hello")
    assert keys == {"hello"}
    assert try_add_unique(keys, "hello") == (False, "hello")
    assert try_add_unique(keys, "  hello  ") == (False, "hello")


def test_try_add_unique_without_normalize() -> None:
    keys: set[str] = set()
    assert try_add_unique(keys, "a", normalize=False) == (True, "a")
    assert try_add_unique(keys, " a ", normalize=False) == (True, " a ")


def test_try_add_unique_casefold_distinct_without_flag() -> None:
    keys: set[str] = set()
    assert try_add_unique(keys, "Ab") == (True, "Ab")
    assert try_add_unique(keys, "ab") == (True, "ab")


def test_try_add_unique_casefold_treats_equal() -> None:
    keys: set[str] = set()
    assert try_add_unique(keys, "Ab", casefold=True) == (True, "ab")
    assert try_add_unique(keys, "ab", casefold=True) == (False, "ab")


def test_collect_unique_prompts_respects_max_and_order() -> None:
    seq = ["a", "b", "a", "  a  ", "c", "d"]
    accepted, keys = collect_unique_prompts(seq, max_count=3)
    assert accepted == ["a", "b", "c"]
    assert keys == {"a", "b", "c"}


def test_collect_unique_prompts_with_existing_keys() -> None:
    accepted, keys = collect_unique_prompts(
        ["x", "y"],
        existing={"x"},
        max_count=10,
    )
    assert accepted == ["y"]
    assert keys == {"x", "y"}


def test_collect_unique_prompts_max_zero() -> None:
    accepted, keys = collect_unique_prompts(["a", "b"], max_count=0)
    assert accepted == []
    assert keys == set()


def test_collect_unique_prompts_negative_max_raises() -> None:
    with pytest.raises(ValueError, match="max_count"):
        collect_unique_prompts([], max_count=-1)


def test_prompt_fingerprint_stable() -> None:
    a = prompt_fingerprint("What are SOTA VLA papers?")
    b = prompt_fingerprint("What are SOTA VLA papers?")
    assert a == b
    assert len(a) == 8


def test_prompt_fingerprint_whitespace_normalized() -> None:
    assert prompt_fingerprint("a  b") == prompt_fingerprint("a b")


def test_prompt_fingerprint_n() -> None:
    assert len(prompt_fingerprint("x", n=16)) == 16


def test_prompt_fingerprint_invalid_n() -> None:
    with pytest.raises(ValueError, match="n must be positive"):
        prompt_fingerprint("x", n=0)


def test_variant_collection_should_stop_target_met() -> None:
    stop, reason = variant_collection_should_stop(
        unique_count=3,
        generation_attempts=5,
        target_uniques=3,
        max_generation_attempts=100,
    )
    assert stop is True
    assert reason == "target_met"


def test_variant_collection_should_stop_attempt_budget() -> None:
    stop, reason = variant_collection_should_stop(
        unique_count=1,
        generation_attempts=10,
        target_uniques=5,
        max_generation_attempts=10,
    )
    assert stop is True
    assert reason == "attempt_budget"


def test_variant_collection_should_stop_continue() -> None:
    stop, reason = variant_collection_should_stop(
        unique_count=1,
        generation_attempts=3,
        target_uniques=5,
        max_generation_attempts=10,
    )
    assert stop is False
    assert reason is None


def test_variant_collection_should_stop_invalid() -> None:
    with pytest.raises(ValueError):
        variant_collection_should_stop(
            unique_count=0,
            generation_attempts=0,
            target_uniques=-1,
            max_generation_attempts=1,
        )
