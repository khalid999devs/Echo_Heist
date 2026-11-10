"""Limited persistent NEXUS countermeasures between attempts (pure rules).

After each attempt NEXUS adds only the evidence it legitimately observed
(witnessed Echo decoys, confirmed contacts per sector, groups drawn off when the
Core fell) and selects **at most one** protocol for the next attempt. The
protocol is announced through ``ProtocolState`` before deployment and applied
unchanged for that whole attempt. A reset clears every adaptation input.
"""

from dataclasses import dataclass, field

from echo_heist.core.contracts.autonomy.model import LearnedProtocol, ProtocolState
from echo_heist.core.contracts.security.director import ActiveProtocol, NexusEvidence, ProtocolId

SCHEMA_VERSION = 1
THRESHOLD = 2  # repeated evidence before NEXUS adapts
LABELS = {
    ProtocolId.VERIFY_ECHO: "Verify Echo",
    ProtocolId.REINFORCE_ROUTE: "Reinforce Route",
    ProtocolId.SPREAD_FORMATION: "Spread Formation",
}


@dataclass(frozen=True, slots=True)
class ProtocolMemory:
    """Everything persisted; a reset returns every field except revision/enabled to zero."""

    revision: int = 0
    enabled: bool = True
    attempts: int = 0
    totals: NexusEvidence = field(default_factory=NexusEvidence)
    active: ActiveProtocol | None = None
    rationale: str = ""
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))
        if min(self.revision, self.attempts) < 0 or type(self.enabled) is not bool:
            raise ValueError("Invalid NEXUS memory counters")
        if self.active is not None and not (self.enabled and self.rationale):
            raise ValueError("An active protocol needs enabled memory and its rationale")

    @property
    def has_inputs(self) -> bool:
        return bool(self.attempts or self.active or self.totals != NexusEvidence())


def _merge(first: NexusEvidence, second: NexusEvidence) -> NexusEvidence:
    contacts = dict(first.contacts)
    for sector, count in second.contacts:
        contacts[sector] = contacts.get(sector, 0) + count
    return NexusEvidence(
        first.echo_witnessed + second.echo_witnessed,
        tuple(contacts.items()),
        first.bypassed_groups + second.bypassed_groups,
    )


def select(
    totals: NexusEvidence, reinforceable: frozenset[str]
) -> tuple[ActiveProtocol | None, str, tuple[str, ...]]:
    """The single strongest evidence-backed protocol, or none below threshold.

    Ties keep a fixed order: REINFORCE_ROUTE, VERIFY_ECHO, SPREAD_FORMATION.
    """
    sectors = sorted(
        ((count, sector) for sector, count in totals.contacts if sector in reinforceable),
        key=lambda item: (-item[0], item[1]),
    )
    options: list[tuple[float, int, ActiveProtocol, str, tuple[str, ...]]] = []
    if sectors and sectors[0][0] >= THRESHOLD:
        count, sector = sectors[0]
        options.append(
            (
                count / THRESHOLD,
                0,
                ActiveProtocol(ProtocolId.REINFORCE_ROUTE, sector),
                f"Repeated confirmed contacts on the {sector} route",
                (f"{count} confirmed contacts in {sector}",),
            )
        )
    if totals.echo_witnessed >= THRESHOLD:
        options.append(
            (
                totals.echo_witnessed / THRESHOLD,
                1,
                ActiveProtocol(ProtocolId.VERIFY_ECHO),
                "Multiple witnessed Echo distractions",
                (f"{totals.echo_witnessed} Echo decoys seen by guards",),
            )
        )
    if totals.bypassed_groups >= 1:
        options.append(
            (
                totals.bypassed_groups,
                2,
                ActiveProtocol(ProtocolId.SPREAD_FORMATION),
                "Grouped guards were drawn away while the Core was taken",
                (f"{totals.bypassed_groups} attempts bypassed a grouped response",),
            )
        )
    if not options:
        return None, "", ()
    _, _, protocol, reason, evidence = min(options, key=lambda item: (-item[0], item[1]))
    return protocol, reason, evidence


def record_attempt(
    memory: ProtocolMemory, observed: NexusEvidence, reinforceable: frozenset[str]
) -> ProtocolMemory:
    """Add one finished attempt's legitimate evidence and choose the next protocol."""
    if not memory.enabled:
        return memory
    totals = _merge(memory.totals, observed)
    protocol, reason, evidence = select(totals, reinforceable)
    return ProtocolMemory(
        memory.revision + 1, True, memory.attempts + 1, totals, protocol, reason, evidence
    )


def reset(memory: ProtocolMemory) -> ProtocolMemory:
    return ProtocolMemory(memory.revision + 1, memory.enabled)


def state(memory: ProtocolMemory) -> ProtocolState:
    active = (
        LearnedProtocol(
            memory.active.protocol_id.value
            + (f":{memory.active.sector}" if memory.active.sector else ""),
            LABELS[memory.active.protocol_id]
            + (f" / {memory.active.sector}" if memory.active.sector else ""),
            memory.rationale,
            memory.evidence,
        )
        if memory.active is not None
        else None
    )
    return ProtocolState(memory.revision, memory.enabled, active, memory.has_inputs)
