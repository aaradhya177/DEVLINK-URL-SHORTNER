import re
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.shared.id_generator import (
    BASE62_ALPHABET,
    SnowflakeGenerator,
    decode_base62,
    encode_base62,
)


def test_base62_round_trip_known_values() -> None:
    """Base62 encoding should be reversible for boundary-ish values."""
    values = [0, 1, 61, 62, 63, 3843, 2**63 - 1]

    for value in values:
        assert decode_base62(encode_base62(value)) == value


def test_base62_rejects_invalid_input() -> None:
    """Invalid Base62 values should fail loudly."""
    with pytest.raises(ValueError):
        encode_base62(-1)
    with pytest.raises(ValueError):
        decode_base62("")
    with pytest.raises(ValueError):
        decode_base62("not_base62!")


def test_generated_short_code_format_and_uniqueness() -> None:
    """Snowflake IDs should produce unique URL-safe Base62 codes."""
    generator = SnowflakeGenerator(worker_id=7)
    codes = {generator.generate_short_code() for _ in range(1_000)}

    assert len(codes) == 1_000
    assert all(re.fullmatch(f"[{BASE62_ALPHABET}]+", code) for code in codes)


def test_generator_is_thread_safe() -> None:
    """Concurrent generation should not duplicate IDs."""
    generator = SnowflakeGenerator(worker_id=2)

    with ThreadPoolExecutor(max_workers=8) as executor:
        ids = list(executor.map(lambda _: generator.generate(), range(2_000)))

    assert len(ids) == len(set(ids))


def test_generator_rejects_invalid_worker_id() -> None:
    """Worker IDs must fit in the configured bit allocation."""
    with pytest.raises(ValueError):
        SnowflakeGenerator(worker_id=-1)
    with pytest.raises(ValueError):
        SnowflakeGenerator(worker_id=SnowflakeGenerator.max_worker_id + 1)
