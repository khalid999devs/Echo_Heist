"""Foresight: where each guard the Companion has seen will be looking soon.

The Companion learns every guard's beat from its own sightings, the way a
player does by watching. A patrolling guard pauses at the corners of its route
and, while it pauses, already faces the way it will leave, so one look at a
pause teaches that turn. The Companion also learns how fast each guard walks
and how long its pauses last.

A calm guard is walked forward along what is known of its beat, once with the
shortest and once with the longest pauses seen, so every moment ahead holds
the band of places it may be in, each with the way it faces there. Past the
last turn it has shown, a guard keeps walking straight. At a wall it may turn
any way. A guard that is checking, identifying, pursuing or searching looks
every way around the place it is heading for. Exposure of a tile uses the
guards' own sight range and wall test, with a little slack on the cone. Only
the Companion's own observations feed any of this.
"""

from dataclasses import dataclass, field
from math import ceil, cos, hypot, radians

from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, MissionPhase, StaticMap, Tile, tile_center
from echo_heist.core.perception.sensors import line_of_sight

STEP_TICKS = 6  # one planning step; walking a tile takes two
HORIZON_STEPS = 35  # seven seconds ahead
HEARING_TILES = 3.5  # a sprint this close to a guard is heard
MEMORY_TICKS = 90  # an alerted guard, or one without a known beat, fades after three seconds
BEAT_MEMORY_TICKS = 240  # a guard on a known beat is followed for eight seconds
PAUSE_PRIOR = (10, 40)  # pause range assumed before any pause has been timed
SAMPLE_TILES = 0.5
STILL = 0.004  # tiles per tick: slower than this is standing
SLACK_DEGREES = 5
EYE_GRID = UNIT // 8  # guard eyes are rounded to an eighth of a tile for ray caching
EDGE = UNIT * 3 // 10
SPOTS = ((0, 0), (-EDGE, -EDGE), (EDGE, -EDGE), (-EDGE, EDGE), (EDGE, EDGE))
FORKS = 1  # unknown junctions followed per prediction
BRANCH_TILES = 3  # a side opening this deep is a corridor a guard may turn into
BODY_TILES = 1.6  # this close a guard hears footsteps and turns
SPEED_PRIOR = {
    ActorKind.SENTINEL: 0.06,
    ActorKind.TRACKER: 0.067,
    ActorKind.INTERCEPTOR: 0.093,
}
CALM = frozenset({"PATROL", "RETURN"})
HUNT_MEMORY_TICKS = 300  # a hunting guard is routed around for ten seconds
POST_MEMORY_TICKS = 2700  # a posted guard until its post is seen empty
POSTED_TICKS = 45  # standing this long is holding a post, not pausing at a corner
DETOUR = (12, 12, 8, 4)  # route cost by distance from such a guard
GUARDS = frozenset(SPEED_PRIOR)
NEVER = 10**9

# One possible guard pose: x and y in position units, then the facing. A
# facing of (0, 0) means the guard may look any way.
type Pose = tuple[float, float, float, float]
type Item = tuple[float, float, Pose]  # a pose and the window of ticks it may hold


@dataclass(slots=True)
class Track:
    """What the Companion has learned about one guard."""

    kind: ActorKind
    turns: dict[tuple[Tile, Tile], Tile] = field(default_factory=dict)
    passes: set[tuple[Tile, Tile]] = field(default_factory=set)  # walked straight through
    speed: float = 0.0  # tiles per tick while walking calmly
    pause_min: int = NEVER  # pauses timed before the lockdown
    pause_max: int = 0
    rush_min: int = NEVER  # pauses timed during the lockdown
    rush_max: int = 0
    position: tuple[int, int] = (0, 0)
    velocity: tuple[float, float] = (0.0, 0.0)
    tile: Tile = (0, 0)
    facing: Tile = (0, 0)
    heading: Tile = (0, 0)  # last walking direction, along one axis
    heading_seen: bool = False  # that direction was watched, not assumed
    entry_heading: Tile = (0, 0)  # how it walked into its current tile
    paused_here: bool = True  # it stood still on its current tile (or may have)
    alert: str = ""
    tick: int = -NEVER
    still_since: int = -1  # tick a pause began, or -1 while walking
    still_known: bool = False  # the start of that pause was watched
    out_of_action: bool = False
    gone: bool = False  # its last place has since been seen empty

    def pauses(self, lockdown: bool) -> tuple[int, int]:
        low, high = (self.pause_min, self.pause_max) if self.pause_max else PAUSE_PRIOR
        if lockdown:
            # Lockdown halves every pause until some have been timed during it.
            return (self.rush_min, self.rush_max) if self.rush_max else (low // 2, high // 2)
        return low, high


def _axis(dx: float, dy: float) -> Tile:
    if abs(dx) >= abs(dy):
        return ((dx > 0) - (dx < 0), 0)
    return (0, (dy > 0) - (dy < 0))


@dataclass(slots=True)
class Foresight:
    sight_range_tiles: int
    half_angle_degrees: int
    tracks: dict[str, Track] = field(default_factory=dict)
    tick: int = -1
    world_map: StaticMap | None = None
    lockdown: bool = False
    steps: list[list[Pose]] = field(default_factory=list)
    cache: dict[tuple[Tile, int], bool] = field(default_factory=dict)
    rays: dict[tuple[int, int, Tile], bool] = field(default_factory=dict)
    branches: dict[tuple[Tile, Tile], bool] = field(default_factory=dict)
    eye: tuple[int, int] | None = None
    views: dict[Tile, bool] = field(default_factory=dict)
    revision: int = -1

    # ------------------------------------------------------------- learning
    def observe(self, observation: Observation) -> None:
        """Learn from the guards in view this tick (call once per tick)."""
        tick = observation.tick
        if observation.geometry_revision != self.revision:
            self.rays.clear()
            self.branches.clear()
            self.revision = observation.geometry_revision
        self.world_map = observation.map_static
        self.lockdown = observation.phase == MissionPhase.LOCKDOWN
        own = observation.own_status
        self.eye = own.position or tile_center(own.tile)
        for entity in observation.visible_entities:
            if entity.kind not in GUARDS:
                continue
            track = self.tracks.setdefault(entity.actor_id, Track(entity.kind))
            position = entity.position or tile_center(entity.tile)
            calm = entity.alert == "PATROL"
            if track.tick == tick - 1:
                dx = (position[0] - track.position[0]) / UNIT
                dy = (position[1] - track.position[1]) / UNIT
                moved = hypot(dx, dy)
                track.velocity = (dx, dy)
                if moved > STILL:
                    heading = _axis(dx, dy)
                    if entity.tile != track.tile:
                        if calm and not track.paused_here and track.entry_heading == heading:
                            track.passes.add((track.tile, heading))
                        track.entry_heading, track.paused_here = heading, False
                    if calm:
                        track.speed = moved if not track.speed else 0.8 * track.speed + 0.2 * moved
                        if track.still_since >= 0 and track.still_known:
                            paused = tick - track.still_since
                            if self.lockdown:
                                track.rush_min = min(track.rush_min, paused)
                                track.rush_max = max(track.rush_max, paused)
                            else:
                                track.pause_min = min(track.pause_min, paused)
                                track.pause_max = max(track.pause_max, paused)
                    track.still_since, track.heading, track.heading_seen = -1, heading, True
                else:
                    track.paused_here = True
                    if track.still_since < 0:
                        # A pause first noticed right after a gap began unseen.
                        track.still_since, track.still_known = tick, track.heading_seen
                    if calm and track.heading_seen and sum(map(abs, entity.facing)) == 1:
                        # A pausing guard already faces the way it will leave.
                        track.turns[(entity.tile, track.heading)] = entity.facing
            else:
                # First look after a gap: assume it walks the way it faces.
                track.velocity = (0.0, 0.0)
                track.heading = entity.facing if sum(map(abs, entity.facing)) == 1 else (0, 0)
                track.heading_seen, track.still_since, track.still_known = False, -1, False
                track.entry_heading, track.paused_here = (0, 0), True
            track.position, track.tile, track.facing = position, entity.tile, entity.facing
            track.alert, track.tick = entity.alert, tick
            track.out_of_action = entity.disabled or entity.stunned
            track.gone = False
        for track in self.tracks.values():
            if track.tick != tick and not track.gone:
                x, y = tile_center(track.tile)
                track.gone = self._sees_spot(x, y)

    # ----------------------------------------------------------- prediction
    def refresh(self, tick: int) -> None:
        """Predict every remembered guard's poses for the steps ahead."""
        if tick == self.tick:
            return
        self.tick = tick
        self.cache.clear()
        self.views.clear()
        self.steps = [[] for _ in range(HORIZON_STEPS + 2)]
        for track in self.tracks.values():
            age = tick - track.tick
            if track.out_of_action and age <= 1:
                continue
            if track.alert in CALM:
                if age <= (BEAT_MEMORY_TICKS if track.turns else MEMORY_TICKS):
                    self._beat(track, age)
            elif age <= MEMORY_TICKS:
                self._alerted(track, age)

    def blockers(self, tick: int) -> tuple[Tile, ...]:
        """Where guards were last seen hunting, or holding a post nobody has seen
        them leave."""
        found = []
        for track in self.tracks.values():
            if track.out_of_action or track.gone:
                continue
            posted = track.still_since >= 0 and track.tick - track.still_since >= POSTED_TICKS
            memory = POST_MEMORY_TICKS if posted else HUNT_MEMORY_TICKS
            if tick - track.tick <= memory and (posted or track.alert not in CALM):
                found.append(track.tile)
        return tuple(sorted(found))

    def detour(self, tick: int) -> dict[Tile, int]:
        """Extra route cost around hunting and posted guards."""
        assert self.world_map is not None
        extra: dict[Tile, int] = {}
        for x, y in self.blockers(tick):
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    tile = (x + dx, y + dy)
                    if self.world_map.can_walk(tile):
                        price = DETOUR[max(abs(dx), abs(dy))]
                        extra[tile] = max(extra.get(tile, 0), price)
        return extra

    def exposed(self, tile: Tile, step: int) -> bool:
        """May a guard see ``tile`` about ``step`` walking steps from now?"""
        step = max(0, min(step, HORIZON_STEPS + 1))
        key = (tile, step)
        known = self.cache.get(key)
        if known is None:
            known = self.cache[key] = any(self._sees(pose, tile) for pose in self.steps[step])
        return known

    def clear_for(self, tile: Tile, start: int, steps: int) -> bool:
        return not any(self.exposed(tile, step) for step in range(start, start + steps + 1))

    def guards_near(self, tile: Tile, tiles: float, step: int = 0) -> bool:
        """Is any predicted guard pose within ``tiles`` of ``tile`` at ``step``?"""
        cx, cy = tile_center(tile)
        reach = tiles * UNIT
        return any(
            hypot(pose[0] - cx, pose[1] - cy) <= reach
            for pose in self.steps[max(0, min(step, HORIZON_STEPS + 1))]
        )

    def loud(self, tile: Tile, step: int) -> bool:
        """Would a sprint onto ``tile`` at ``step`` be heard by a guard?"""
        return self.guards_near(tile, HEARING_TILES, step)

    def _add(self, low: float, high: float, pose: Pose) -> None:
        first = max(0, ceil((low - STEP_TICKS) / STEP_TICKS))
        last = min(HORIZON_STEPS + 1, int((high + STEP_TICKS) // STEP_TICKS))
        for step in range(first, last + 1):
            self.steps[step].append(pose)

    def _beat(self, track: Track, age: int) -> None:
        """Walk a calm guard along its learned beat, early and late."""
        speed = track.speed or SPEED_PRIOR[track.kind]
        if self.lockdown:
            speed = max(speed, SPEED_PRIOR[track.kind] * 1.2)
        shortest, longest = track.pauses(self.lockdown)
        x, y = float(track.position[0]), float(track.position[1])
        tile, heading = track.tile, track.heading
        low = high = float(-age)
        start: list[Item] = []
        if track.still_since >= 0:
            waited = track.tick - track.still_since if track.still_known else 0
            rest_low = max(0, shortest - waited)
            rest_high = max(rest_low, longest - waited)
            facing = track.facing
            if track.alert != "PATROL" or sum(map(abs, facing)) != 1:
                heading = (0, 0)
            else:
                start.append((low, high + rest_high, (x, y, float(facing[0]), float(facing[1]))))
                low, high, heading = low + rest_low, high + rest_high, facing
                x, y = map(float, tile_center(tile))
        if heading == (0, 0):
            start.append((low, high + longest, (x, y, 0.0, 0.0)))
            items = start + self._leave(track, (x, y), tile, None, (low, high), speed, FORKS, age)
        else:
            items = self._follow(
                track, (x, y), tile, heading, (low, high), speed, FORKS, age, start
            )
        for item in items:
            self._add(*item)

    def _follow(
        self,
        track: Track,
        point: tuple[float, float],
        tile: Tile,
        heading: Tile,
        window: tuple[float, float],
        speed: float,
        forks: int,
        age: int,
        start: list[Item] | None = None,
    ) -> list[Item]:
        """Walk the beat from ``point``. At a junction it was never seen to pass,
        and at a wall where its turn is unknown, also follow the ways it might
        take. A branch whose present position the Companion can see empty is
        dropped together with the branches that would only start later."""
        world_map = self.world_map
        assert world_map is not None
        shortest, longest = track.pauses(self.lockdown)
        (x, y), (low, high) = point, window
        horizon = (HORIZON_STEPS + 1) * STEP_TICKS
        mine: list[Item] = list(start or ())
        kids: list[tuple[float, list[Item]]] = []
        turned = False
        while low <= horizon:
            cx, cy = tile_center(tile)
            if (cx - x) * heading[0] + (cy - y) * heading[1] <= 0:
                # Past the middle of this tile: walk on into the next one.
                ahead = (tile[0] + heading[0], tile[1] + heading[1])
                if not world_map.can_walk(ahead):
                    # A turn it has not shown: it looks around, then goes some way.
                    mine.append((low, high + longest, (x, y, 0.0, 0.0)))
                    if forks:
                        kids.append(
                            (
                                low + shortest,
                                self._leave(
                                    track, (x, y), tile, heading, (low, high), speed, forks - 1, age
                                ),
                            )
                        )
                    break
                tile = ahead
                cx, cy = tile_center(tile)
            span = hypot(cx - x, cy - y) / UNIT
            parts = max(1, ceil(span / SAMPLE_TILES))
            for part in range(1, parts + 1):
                low += span / parts / speed
                high += span / parts / speed
                spot = (x + (cx - x) * part / parts, y + (cy - y) * part / parts)
                mine.append((low, high, (*spot, float(heading[0]), float(heading[1]))))
            x, y = float(cx), float(cy)
            turn = track.turns.get((tile, heading))
            if turn is not None and not turned:
                mine.append((low, high + longest, (x, y, float(turn[0]), float(turn[1]))))
                low, high, heading = low + shortest, high + longest, turn
                x, y = x - turn[0], y - turn[1]  # just behind the centre, facing out
                turned = True
                continue
            if forks and not turned and (tile, heading) not in track.passes:
                for side in ((heading[1], heading[0]), (-heading[1], -heading[0])):
                    if self._branch(tile, side):
                        mine.append((low, high + longest, (x, y, float(side[0]), float(side[1]))))
                        later = (low + shortest, high + longest)
                        kids.append(
                            (
                                later[0],
                                self._follow(
                                    track,
                                    (x - side[0], y - side[1]),
                                    tile,
                                    side,
                                    later,
                                    speed,
                                    forks - 1,
                                    age,
                                ),
                            )
                        )
            x, y = x + heading[0], y + heading[1]  # leave the centre behind
            turned = False
        alive = not self._ruled_out(mine, age)
        items = mine if alive else []
        for begins, branch in kids:
            if alive or begins <= 0:
                items.extend(branch)
        return items

    def _leave(
        self,
        track: Track,
        point: tuple[float, float],
        tile: Tile,
        heading: Tile | None,
        window: tuple[float, float],
        speed: float,
        forks: int,
        age: int,
    ) -> list[Item]:
        """After an unknown pause, it may walk off any open way but straight on."""
        world_map = self.world_map
        assert world_map is not None
        shortest, longest = track.pauses(self.lockdown)
        later = (window[0] + shortest, window[1] + longest)
        items: list[Item] = []
        for way in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            if way == heading or not world_map.can_walk((tile[0] + way[0], tile[1] + way[1])):
                continue
            start = (point[0] - way[0], point[1] - way[1])
            items.extend(self._follow(track, start, tile, way, later, speed, forks, age))
        return items

    def _ruled_out(self, items: list[Item], age: int) -> bool:
        """The Companion sees every place this branch puts the guard right now."""
        if age <= 0:
            return False
        now = [pose for low, high, pose in items if low - STEP_TICKS <= 0 <= high + STEP_TICKS]
        return bool(now) and all(self._in_view(pose[0], pose[1]) for pose in now)

    def _sees_spot(self, x: int, y: int) -> bool:
        """Does the Companion have a clear look at this point right now?"""
        assert self.world_map is not None and self.eye is not None
        if hypot(x - self.eye[0], y - self.eye[1]) > self.sight_range_tiles * UNIT:
            return False
        return line_of_sight(self.world_map, self.eye, (x, y))

    def _in_view(self, x: float, y: float) -> bool:
        if self.eye is None:
            return False
        if hypot(x - self.eye[0], y - self.eye[1]) > self.sight_range_tiles * UNIT:
            return False
        tile = (int(x // UNIT), int(y // UNIT))
        known = self.views.get(tile)
        if known is None:
            assert self.world_map is not None
            known = self.views[tile] = line_of_sight(self.world_map, self.eye, (int(x), int(y)))
        return known

    def _branch(self, tile: Tile, side: Tile) -> bool:
        """A real side corridor, not just the far half of a wide one."""
        key = (tile, side)
        known = self.branches.get(key)
        if known is None:
            assert self.world_map is not None
            known = self.branches[key] = all(
                self.world_map.can_walk((tile[0] + side[0] * n, tile[1] + side[1] * n))
                for n in range(1, BRANCH_TILES + 1)
            )
        return known

    def _alerted(self, track: Track, age: int) -> None:
        """An alerted guard keeps its course and may look any way."""
        world_map = self.world_map
        assert world_map is not None
        vx, vy = track.velocity
        x, y = float(track.position[0]), float(track.position[1])
        walked = 0
        poses: list[Pose] = []
        for step in range(HORIZON_STEPS + 2):
            ticks = age + step * STEP_TICKS
            while walked < ticks and (vx or vy):
                nx, ny = x + vx * UNIT, y + vy * UNIT
                if not world_map.can_walk((int(nx // UNIT), int(ny // UNIT))):
                    vx = vy = 0.0
                    break
                x, y, walked = nx, ny, walked + 1
            poses.append((x, y, 0.0, 0.0))
        if age > 0 and self._in_view(poses[0][0], poses[0][1]):
            return  # it is not where it was heading: the Companion can see that spot
        for step, pose in enumerate(poses):
            self.steps[step].append(pose)

    def _sees(self, pose: Pose, tile: Tile) -> bool:
        gx, gy, fx, fy = pose
        tx, ty = tile_center(tile)
        dx, dy = (tx - gx) / UNIT, (ty - gy) / UNIT
        length = hypot(dx, dy)
        if length <= BODY_TILES:
            return True
        if length > self.sight_range_tiles + 0.5:
            return False
        if fx or fy:
            limit = cos(radians(min(89, self.half_angle_degrees + SLACK_DEGREES)))
            if dx * fx + dy * fy < limit * length * hypot(fx, fy):
                return False
        key = (round(gx / EYE_GRID), round(gy / EYE_GRID), tile)
        clear = self.rays.get(key)
        if clear is None:
            assert self.world_map is not None
            eye = (key[0] * EYE_GRID, key[1] * EYE_GRID)
            # A body may stand anywhere on its tile: any clear ray to it counts.
            clear = self.rays[key] = any(
                line_of_sight(self.world_map, eye, (tx + ox, ty + oy)) for ox, oy in SPOTS
            )
        return clear
