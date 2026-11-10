"""Versioned NEXUS memory file: atomic writes, corrupt-file quarantine, future refusal."""

import json
from pathlib import Path
from time import time_ns

from echo_heist.ai.director.protocols import SCHEMA_VERSION, ProtocolMemory
from echo_heist.core.contracts.security.director import ActiveProtocol, NexusEvidence, ProtocolId
from echo_heist.infrastructure.persistence.atomic import atomic_write_json

FILE_NAME = "nexus-memory.json"


class FutureProtocolVersion(ValueError):
    """A newer build wrote this memory; it is never silently overwritten."""


def encode(memory: ProtocolMemory) -> dict[str, object]:
    return {
        "schema": SCHEMA_VERSION,
        "revision": memory.revision,
        "enabled": memory.enabled,
        "attempts": memory.attempts,
        "totals": {
            "echo_witnessed": memory.totals.echo_witnessed,
            "contacts": {sector: count for sector, count in memory.totals.contacts},
            "bypassed_groups": memory.totals.bypassed_groups,
        },
        "active": None
        if memory.active is None
        else {"protocol": memory.active.protocol_id.value, "sector": memory.active.sector},
        "rationale": memory.rationale,
        "evidence": list(memory.evidence),
    }


def _count(value: object) -> int:
    if type(value) is not int or not 0 <= value <= 1_000_000:
        raise ValueError("NEXUS memory counts must be bounded integers")
    return value


def decode(payload: object) -> ProtocolMemory:
    if not isinstance(payload, dict):
        raise ValueError("NEXUS memory must be a JSON object")
    schema = payload.get("schema")
    if type(schema) is int and schema > SCHEMA_VERSION:
        raise FutureProtocolVersion(f"NEXUS memory schema {schema} is newer than this build")
    if schema != SCHEMA_VERSION:
        raise ValueError("Unsupported NEXUS memory schema")
    totals = payload.get("totals")
    if not isinstance(totals, dict) or not isinstance(totals.get("contacts"), dict):
        raise ValueError("NEXUS memory evidence is malformed")
    contacts = tuple((str(sector), _count(count)) for sector, count in totals["contacts"].items())
    active = payload.get("active")
    protocol = None
    if active is not None:
        if not isinstance(active, dict):
            raise ValueError("NEXUS protocol is malformed")
        protocol = ActiveProtocol(
            ProtocolId(str(active.get("protocol"))), str(active.get("sector", ""))
        )
    evidence = payload.get("evidence", [])
    enabled = payload.get("enabled")
    if not isinstance(evidence, list) or type(enabled) is not bool:
        raise ValueError("NEXUS memory fields are malformed")
    return ProtocolMemory(
        _count(payload.get("revision")),
        enabled,
        _count(payload.get("attempts")),
        NexusEvidence(
            _count(totals.get("echo_witnessed")), contacts, _count(totals.get("bypassed_groups"))
        ),
        protocol,
        str(payload.get("rationale", "")),
        tuple(str(item) for item in evidence),
    )


class ProtocolStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.notice = ""

    def load(self) -> ProtocolMemory:
        """Missing -> baseline. Corrupt -> quarantined copy plus baseline. Future -> raise."""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ProtocolMemory()
        try:
            return decode(json.loads(text))
        except FutureProtocolVersion:
            raise
        except (ValueError, TypeError, KeyError) as error:
            quarantine = self.path.with_name(f"{self.path.stem}.corrupt-{time_ns()}.json")
            self.path.replace(quarantine)
            self.notice = f"NEXUS memory was unreadable ({error}); kept as {quarantine.name}"
            return ProtocolMemory()

    def save(self, memory: ProtocolMemory) -> None:
        atomic_write_json(self.path, encode(memory))
