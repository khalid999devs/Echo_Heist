"""Authored interactive props and their versioned rules (P05-SR2).

These are static, immutable inputs to Simulation. The mutable per-run state
lives only in Simulation (``core/environment``); presentation receives the
separate read-only ``EnvironmentView``.
"""

from dataclasses import dataclass, fields
from typing import Self

from echo_heist.core.contracts.environment.presentation import PropKind
from echo_heist.core.contracts.world import Tile, immutable_tile


@dataclass(frozen=True, slots=True)
class EnvironmentRules:
    """Balance defaults from blueprint p. 7; radii are acoustic tiles."""

    schema_version: int = 1
    door_cycle_ticks: int = 12
    door_noise_radius_tiles: int = 2
    glass_noise_radius_tiles: int = 6
    canister_noise_radius_tiles: int = 4
    canister_step_ticks: int = 5
    canister_roll_tiles: int = 4
    locker_cycle_ticks: int = 9
    cue_ttl_ticks: int = 60

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or not 0 < value <= 10_000:
                raise ValueError(
                    f"Environment rule {field.name} must be a bounded positive integer"
                )
        if self.schema_version != 1:
            raise ValueError("Unsupported environment rules schema")

    @classmethod
    def from_payload(cls, payload: object) -> Self:
        names = {field.name for field in fields(cls)}
        if not isinstance(payload, dict) or set(payload) != names:
            raise ValueError("Environment rules must contain exactly the supported fields")
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class PropSpec:
    """One authored prop with a stable ID.

    ``tiles`` are the physical tiles a door/glass pane controls (a door may
    span a two-tile corridor); a canister or locker uses exactly one tile.
    ``horizontal`` means the leaf/pane runs along x (the passage is crossed
    moving vertically).
    """

    object_id: str
    kind: PropKind
    tiles: tuple[Tile, ...]
    horizontal: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "tiles", tuple(immutable_tile(tile) for tile in self.tiles))
        if not self.object_id or not isinstance(self.kind, PropKind) or not self.tiles:
            raise ValueError("A prop needs a stable ID, supported kind and at least one tile")
        if len(set(self.tiles)) != len(self.tiles):
            raise ValueError("Prop tiles must be distinct")
        if self.kind in (PropKind.CANISTER, PropKind.LOCKER) and len(self.tiles) != 1:
            raise ValueError("Canisters and lockers occupy exactly one tile")
        if len(self.tiles) > 1:
            xs = sorted(tile[0] for tile in self.tiles)
            ys = sorted(tile[1] for tile in self.tiles)
            run = (len(set(ys)) == 1 and xs == list(range(xs[0], xs[0] + len(xs)))) or (
                len(set(xs)) == 1 and ys == list(range(ys[0], ys[0] + len(ys)))
            )
            if not run or self.horizontal != (len(set(ys)) == 1):
                raise ValueError("A wide door/pane must be one straight run along its leaf")

    @property
    def tile(self) -> Tile:
        return self.tiles[0]


@dataclass(frozen=True, slots=True)
class EnvironmentSpec:
    props: tuple[PropSpec, ...] = ()
    rules: EnvironmentRules = EnvironmentRules()

    def __post_init__(self) -> None:
        props = tuple(sorted(self.props, key=lambda prop: prop.object_id))
        object.__setattr__(self, "props", props)
        if len({prop.object_id for prop in props}) != len(props):
            raise ValueError("Environment prop IDs must be unique")
        tiles = [tile for prop in props for tile in prop.tiles]
        if len(set(tiles)) != len(tiles):
            raise ValueError("Two props cannot share a tile")
