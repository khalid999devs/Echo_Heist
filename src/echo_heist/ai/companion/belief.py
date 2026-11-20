"""Companion working memory built only from its own filtered observations.

A sighting is what the Companion actually saw (tile, facing, tick). Old
sightings become hypotheses with declining confidence; a never-seen guard is
believed to be near its briefed home sector. Danger tiles are observed sight
cones (and a small body margin) with decaying weight, never hidden truth.
"""

from dataclasses import dataclass, field
from math import cos, radians

from echo_heist.ai.companion.briefing import GuardBrief, MissionBriefing
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.world import ActorKind, Tile, tile_center
from echo_heist.core.perception.sensors import line_of_sight

GUARDS = frozenset({ActorKind.SENTINEL, ActorKind.TRACKER, ActorKind.INTERCEPTOR})
DANGER_TTL_TICKS = 90
BODY_MARGIN_TILES = 2
CONE_SLACK_DEGREES = 15


@dataclass(frozen=True, slots=True)
class Sighting:
    guard_id: str
    kind: ActorKind
    tile: Tile
    facing: Tile
    tick: int
    incapacitated: bool


@dataclass(slots=True)
class Beliefs:
    briefing: MissionBriefing
    sight_range_tiles: int
    half_angle_degrees: int
    sightings: dict[str, Sighting] = field(default_factory=dict)
    visible: frozenset[str] = frozenset()

    def update(self, observation: Observation) -> frozenset[str]:
        """Record current sightings; return guards that just came into view."""
        seen: dict[str, EntityView] = {
            entity.actor_id: entity
            for entity in observation.visible_entities
            if entity.kind in GUARDS
        }
        for guard_id, entity in seen.items():
            self.sightings[guard_id] = Sighting(
                guard_id,
                entity.kind,
                entity.tile,
                entity.facing,
                observation.tick,
                entity.disabled or entity.stunned,
            )
        appeared = frozenset(seen) - self.visible
        self.visible = frozenset(seen)
        return appeared

    def threats(self, observation: Observation) -> tuple[Sighting, ...]:
        """Currently visible, active guards (this tick's observation only)."""
        return tuple(
            sighting
            for guard_id, sighting in sorted(self.sightings.items())
            if guard_id in self.visible
            and sighting.tick == observation.tick
            and not sighting.incapacitated
        )

    def prior(self, brief: GuardBrief) -> dict[str, float]:
        """Briefing-only prior: mostly the home sector, a little in its neighbours."""
        graph = self.briefing.graph
        neighbors = sorted(
            {zone for node in graph.nodes if brief.home_zone in node.zones for zone in node.zones}
            - {brief.home_zone}
        )
        belief = {brief.home_zone: 0.75}
        for zone in neighbors:
            belief[zone] = belief.get(zone, 0.0) + 0.25 / max(1, len(neighbors))
        return belief

    def zone_belief(self, brief: GuardBrief, tick: int) -> dict[str, float]:
        """Probability per zone: recent sighting decays toward the briefed home sector."""
        graph = self.briefing.graph
        sighting = self.sightings.get(brief.guard_id)
        if sighting is None:
            return self.prior(brief)
        seen_zone = graph.zone_of(sighting.tile) or brief.home_zone
        confidence = max(0.25, 1.0 - (tick - sighting.tick) / 450)
        belief = {seen_zone: confidence}
        belief[brief.home_zone] = belief.get(brief.home_zone, 0.0) + 1.0 - confidence
        return belief

    def danger(self, tick: int) -> dict[Tile, int]:
        """Observed-risk weights 0..10 per tile from recent sightings' cones."""
        weights: dict[Tile, int] = {}
        reach = self.sight_range_tiles
        threshold = cos(radians(min(89, self.half_angle_degrees + CONE_SLACK_DEGREES)))
        for sighting in self.sightings.values():
            age = tick - sighting.tick
            if age > DANGER_TTL_TICKS:
                continue
            weight = max(1, round(10 * (1 - age / DANGER_TTL_TICKS)))
            gx, gy = sighting.tile
            fx, fy = sighting.facing
            span = BODY_MARGIN_TILES if sighting.incapacitated else reach
            for x in range(gx - span, gx + span + 1):
                for y in range(gy - span, gy + span + 1):
                    dx, dy = x - gx, y - gy
                    near = abs(dx) + abs(dy) <= BODY_MARGIN_TILES
                    length = (dx * dx + dy * dy) ** 0.5
                    cone = (
                        not sighting.incapacitated
                        and 0 < length <= reach
                        and (dx * fx + dy * fy)
                        >= threshold * length * max(1.0, (fx * fx + fy * fy) ** 0.5)
                    )
                    if near or cone:
                        tile = (x, y)
                        weights[tile] = max(weights.get(tile, 0), weight)
        return weights

    def watched_by(self, observation: Observation, tile: Tile) -> Sighting | None:
        """A visible active guard whose observed cone currently covers ``tile``."""
        threshold = cos(radians(self.half_angle_degrees))
        for sighting in self.threats(observation):
            dx, dy = tile[0] - sighting.tile[0], tile[1] - sighting.tile[1]
            length = (dx * dx + dy * dy) ** 0.5
            fx, fy = sighting.facing
            inside = length == 0 or (
                length <= self.sight_range_tiles
                and dx * fx + dy * fy >= threshold * length * max(1.0, (fx * fx + fy * fy) ** 0.5)
            )
            if inside and line_of_sight(
                observation.map_static, tile_center(sighting.tile), tile_center(tile)
            ):
                return sighting
        return None
