import os
import threading
import time


BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def encode_base62(value: int) -> str:
    """Encode a non-negative integer as a compact Base62 string."""
    if value < 0:
        raise ValueError("Base62 encoding requires a non-negative integer.")
    if value == 0:
        return BASE62_ALPHABET[0]

    base = len(BASE62_ALPHABET)
    encoded = ""
    while value:
        value, remainder = divmod(value, base)
        encoded = BASE62_ALPHABET[remainder] + encoded
    return encoded


def decode_base62(value: str) -> int:
    """Decode a Base62 string produced by encode_base62 into an integer."""
    if not value:
        raise ValueError("Base62 value cannot be empty.")

    decoded = 0
    base = len(BASE62_ALPHABET)
    for char in value:
        try:
            digit = BASE62_ALPHABET.index(char)
        except ValueError as exc:
            raise ValueError(f"Invalid Base62 character: {char}") from exc
        decoded = decoded * base + digit
    return decoded


class SnowflakeGenerator:
    """Generate sortable 64-bit IDs.

    Bit layout, from most significant to least significant:

    - 41 bits: milliseconds elapsed since custom epoch.
    - 10 bits: worker ID, allowing 1,024 independently assigned workers.
    - 12 bits: per-worker sequence number within the same millisecond.

    Worker ID is read from DEVLINK_WORKER_ID by default. In production this
    should be assigned by deployment coordination, or later by a shared
    allocator such as ZooKeeper/Kafka-compatible coordination infrastructure.
    """

    timestamp_bits = 41
    worker_id_bits = 10
    sequence_bits = 12
    max_worker_id = (1 << worker_id_bits) - 1
    max_sequence = (1 << sequence_bits) - 1
    worker_id_shift = sequence_bits
    timestamp_shift = sequence_bits + worker_id_bits
    custom_epoch_ms = 1_767_225_600_000

    def __init__(self, worker_id: int | None = None) -> None:
        """Create a generator for one process-local worker."""
        resolved_worker_id = (
            int(os.getenv("DEVLINK_WORKER_ID", "1"))
            if worker_id is None
            else worker_id
        )
        if resolved_worker_id < 0 or resolved_worker_id > self.max_worker_id:
            raise ValueError(
                f"worker_id must be between 0 and {self.max_worker_id}."
            )

        self.worker_id = resolved_worker_id
        self._lock = threading.Lock()
        self._last_timestamp_ms = -1
        self._sequence = 0

    def generate(self) -> int:
        """Return a unique, roughly time-sortable 64-bit integer ID."""
        with self._lock:
            timestamp_ms = self._current_timestamp_ms()
            if timestamp_ms < self._last_timestamp_ms:
                raise RuntimeError("System clock moved backwards.")

            if timestamp_ms == self._last_timestamp_ms:
                self._sequence = (self._sequence + 1) & self.max_sequence
                if self._sequence == 0:
                    timestamp_ms = self._wait_for_next_millisecond(timestamp_ms)
            else:
                self._sequence = 0

            self._last_timestamp_ms = timestamp_ms
            elapsed_ms = timestamp_ms - self.custom_epoch_ms
            if elapsed_ms < 0:
                raise RuntimeError("Current time is before the custom epoch.")

            return (
                (elapsed_ms << self.timestamp_shift)
                | (self.worker_id << self.worker_id_shift)
                | self._sequence
            )

    def generate_short_code(self) -> str:
        """Generate a Snowflake ID and return its Base62 short-code form."""
        return encode_base62(self.generate())

    def _current_timestamp_ms(self) -> int:
        """Return the current Unix timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _wait_for_next_millisecond(self, timestamp_ms: int) -> int:
        """Block until the system clock advances beyond timestamp_ms."""
        next_timestamp_ms = self._current_timestamp_ms()
        while next_timestamp_ms <= timestamp_ms:
            next_timestamp_ms = self._current_timestamp_ms()
        return next_timestamp_ms


default_generator = SnowflakeGenerator()
