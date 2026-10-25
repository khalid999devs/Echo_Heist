"""Immediate-danger utility overrides: break a grab, conserve scarce gadgets.

These run every tick before the strategic plan and only consider guards the
Companion currently sees. Scarce tools are reserved for real capture threats:
EMP when trapped or grabbed, melee only against an adjacent guard that is not
already stunned or still inside its post-stun immunity window.
"""

from dataclasses import dataclass

from echo_heist.ai.companion.belief import Sighting
from echo_heist.core.contracts.autonomy.policy import Emergency
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.world import ActorKind, Position, tile_center

GUARDS = frozenset({ActorKind.SENTINEL, ActorKind.TRACKER, ActorKind.INTERCEPTOR})


@dataclass(frozen=True, slots=True)
class Override:
    kind: str  # EMP, MELEE, ESCAPE or REACT
    reason: str
    target_id: str | None = None
    away_from: Position | None = None


def _distance2(first: Position, second: Position) -> int:
    return (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2


def active_guards(observation: Observation) -> tuple[EntityView, ...]:
    return tuple(
        entity
        for entity in observation.visible_entities
        if entity.kind in GUARDS and not entity.disabled and not entity.stunned
    )


def emergency(
    observation: Observation,
    rules: GameRules,
    choice: Emergency,
    melee_ready_at: dict[str, int],
    watched: Sighting | None,
) -> Override | None:
    own = observation.own_status
    position = own.position or tile_center(own.tile)
    guards = sorted(
        (
            (
                _distance2(position, entity.position or tile_center(entity.tile)),
                entity.actor_id,
                entity,
            )
            for entity in active_guards(observation)
        ),
        key=lambda item: (item[0], item[1]),
    )
    emp = own.inventory.emp_charges > 0
    if own.capture_ticks_remaining is not None:
        # A grab is felt even when the grabbing guard is out of view (e.g. in cover).
        remaining = own.capture_ticks_remaining
        nearest = guards[0] if guards else None
        can_melee = (
            nearest is not None
            and nearest[0] <= rules.melee_range_units**2
            and (observation.tick >= melee_ready_at.get(nearest[1], 0))
        )
        if can_melee and nearest and choice == Emergency.MELEE_IF_ADJACENT:
            return Override("MELEE", "Grabbed: melee the adjacent guard", nearest[1])
        if emp and (choice != Emergency.ESCAPE or remaining <= 4):
            return Override("EMP", f"Grabbed ({remaining} ticks left): EMP breaks it")
        if can_melee and nearest:
            return Override("MELEE", "Grabbed: melee to break free", nearest[1])
        away = (nearest[2].position or tile_center(nearest[2].tile)) if nearest else None
        return Override("ESCAPE", "Grabbed: pull out of reach", away_from=away)
    if not guards:
        return None
    nearest_d2, nearest_id, nearest_view = guards[0]
    nearest_position = nearest_view.position or tile_center(nearest_view.tile)
    can_melee = nearest_d2 <= rules.melee_range_units**2 and observation.tick >= melee_ready_at.get(
        nearest_id, 0
    )
    in_emp = nearest_d2 <= (rules.emp_radius_units * 8 // 10) ** 2
    close = nearest_d2 <= (rules.capture_range_units * 3 // 2) ** 2
    if close and watched is not None:
        if choice == Emergency.MELEE_IF_ADJACENT and can_melee:
            return Override("MELEE", "Adjacent guard is about to grab", nearest_id)
        if choice == Emergency.EMP_IF_TRAPPED and emp and in_emp:
            return Override("EMP", "Trapped within grab range: EMP")
        if can_melee and choice != Emergency.ESCAPE:
            return Override("MELEE", "No EMP left: melee the adjacent guard", nearest_id)
        return Override(
            "ESCAPE", "Guard within grab range: escape first", away_from=nearest_position
        )
    if watched is not None:
        return Override("REACT", f"In {watched.guard_id}'s sight cone: break line of sight")
    return None
