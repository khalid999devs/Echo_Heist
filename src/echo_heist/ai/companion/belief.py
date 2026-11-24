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
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, Position, StaticMap, Tile, tile_center
from echo_heist.core.perception.sensors import can_see, line_of_sight

GUARDS = frozenset({ActorKind.SENTINEL, ActorKind.TRACKER, ActorKind.INTERCEPTOR})
DANGER_TTL_TICKS = 90
BODY_MARGIN_TILES = 2
CONE_SLACK_DEGREES = 15
LEAD_TICKS = 45  # a guard seen walking within 1.5 s is expected further along
LEAD_TILES = 2
VELOCITY_TICKS = 6  # sightings this close together give a walking velocity


@dataclass(frozen=True, slots=True)
class Sighting:
    guard_id: str
    kind: ActorKind
    tile: Tile
    facing: Tile
    tick: int
    incapacitated: bool
    position: Position | None = None
    velocity: tuple[float, float] = (0.0, 0.0)  # tiles per tick, from consecutive sightings


@dataclass(slots=True)
class Beliefs:
    briefing: MissionBriefing
    sight_range_tiles: int
    half_angle_degrees: int
    sightings: dict[str, Sighting] = field(default_factory=dict)
    visible: frozenset[str] = frozenset()
    world_map: StaticMap | None = None
    cached: tuple[int, dict[Tile, int]] | None = None

    def update(self, observation: Observation) -> frozenset[str]:
        """Record current sightings; return guards that just came into sight.

        Every guard on screen is remembered with its walking velocity. Only those
        in line of sight within sight range count as in sight: a guard seen
        through a wall cannot see the Companion either.
        """
        seen: dict[str, EntityView] = {
            entity.actor_id: entity
            for entity in observation.visible_entities
            if entity.kind in GUARDS
        }
        own = observation.own_status
        eye = own.position or tile_center(own.tile)
        reach = (self.sight_range_tiles * UNIT) ** 2
        in_sight: set[str] = set()
        for guard_id, entity in seen.items():
            position = entity.position or tile_center(entity.tile)
            previous = self.sightings.get(guard_id)
            velocity = (0.0, 0.0)
            if previous is not None and previous.position is not None:
                elapsed = observation.tick - previous.tick
                if 0 < elapsed <= VELOCITY_TICKS:
                    velocity = (
                        (position[0] - previous.position[0]) / elapsed / UNIT,
                        (position[1] - previous.position[1]) / elapsed / UNIT,
                    )
            self.sightings[guard_id] = Sighting(
                guard_id,
                entity.kind,
                entity.tile,
                entity.facing,
                observation.tick,
                entity.disabled or entity.stunned,
                position,
                velocity,
            )
            close = (position[0] - eye[0]) ** 2 + (position[1] - eye[1]) ** 2 <= reach
            if close and line_of_sight(observation.map_static, eye, position):
                in_sight.add(guard_id)
        appeared = frozenset(in_sight) - self.visible
        self.visible = frozenset(in_sight)
        self.world_map = observation.map_static
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
        """Observed-risk weights 0..10 per tile from recent sightings' cones.

        A cone only covers tiles the guard could see past walls, and a guard seen
        recently also casts a weaker cone from a little further along its facing,
        where it is about to be.
        """
        if self.cached is not None and self.cached[0] == tick:
            return self.cached[1]
        weights: dict[Tile, int] = {}
        for sighting in self.sightings.values():
            age = tick - sighting.tick
            if age > DANGER_TTL_TICKS:
                continue
            weight = max(1, round(10 * (1 - age / DANGER_TTL_TICKS)))
            self._cone(weights, sighting, sighting.tile, weight)
            fx, fy = sighting.facing
            lead = (sighting.tile[0] + fx * LEAD_TILES, sighting.tile[1] + fy * LEAD_TILES)
            walkable = self.world_map is None or self.world_map.can_walk(lead)
            if age <= LEAD_TICKS and not sighting.incapacitated and walkable:
                self._cone(weights, sighting, lead, max(1, weight * 2 // 3))
        self.cached = (tick, weights)
        return weights

    def _cone(
        self, weights: dict[Tile, int], sighting: Sighting, origin: Tile, weight: int
    ) -> None:
        reach = self.sight_range_tiles
        threshold = cos(radians(min(89, self.half_angle_degrees + CONE_SLACK_DEGREES)))
        gx, gy = origin
        fx, fy = sighting.facing
        span = BODY_MARGIN_TILES if sighting.incapacitated else reach
        eye = tile_center(origin)
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
                tile = (x, y)
                if not (near or cone) or weights.get(tile, 0) >= weight:
                    continue
                if (
                    near
                    or self.world_map is None
                    or line_of_sight(self.world_map, eye, tile_center(tile))
                ):
                    weights[tile] = weight

    def watched_by(self, observation: Observation, tile: Tile) -> Sighting | None:
        """A visible active guard whose observed cone currently covers ``tile``.

        Uses the same cone and ray test as guard sensing, from the guard's seen
        position. For its own tile the Companion tests where it actually stands:
        a tile centre tucked behind cover can hide an exposed body at its edge.
        """
        own = observation.own_status
        point = own.position if tile == own.tile and own.position is not None else tile_center(tile)
        seen = {entity.actor_id: entity for entity in observation.visible_entities}
        for sighting in self.threats(observation):
            entity = seen[sighting.guard_id]
            origin = entity.position or tile_center(entity.tile)
            if origin == point or can_see(
                observation.map_static,
                origin,
                point,
                entity.facing,
                self.sight_range_tiles,
                self.half_angle_degrees,
            ):
                return sighting
        return None
