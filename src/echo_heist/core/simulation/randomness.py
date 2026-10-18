"""Stable independent RNG namespaces; never use Python's randomized hash()."""

from hashlib import sha256
from random import Random


def seeded_rng(seed: int, namespace: str) -> Random:
    material = f"{seed}:{namespace}".encode()
    return Random(int.from_bytes(sha256(material).digest(), "big"))
