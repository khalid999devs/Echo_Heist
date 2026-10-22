"""Scripted keyboard input for native QA footage; never the Companion controller."""

from dataclasses import dataclass, field, replace

import pygame

from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import Position, Tile, tile_center

ARRIVE = UNIT // 8


@dataclass
class HumanDriver:
    rules: GameRules
    use_tools: bool = False
    sprint: bool = True
    held: set[int] = field(default_factory=set)
    previous_position: Position | None = None

    def _bodies(self, observation: Observation) -> frozenset[Tile]:
        return frozenset(
            actor.tile for actor in observation.visible_entities if actor.disabled or actor.stunned
        ) - {observation.own_status.tile}

    def arrived(self, observation: Observation, goal: Tile) -> bool:
        position = observation.own_status.position
        assert position is not None
        body_in_way = self.use_tools and (
            goal in self._bodies(observation)
            or (observation.own_status.tile == goal and not self._clear_center(observation, goal))
        )
        return (
            body_in_way
            or max(abs(a - b) for a, b in zip(position, tile_center(goal), strict=True)) <= ARRIVE
        )

    def _clear_center(self, observation: Observation, tile: Tile) -> bool:
        center = tile_center(tile)
        return all(
            actor.position is None
            or not (actor.disabled or actor.stunned)
            or sum((a - b) ** 2 for a, b in zip(center, actor.position, strict=True))
            >= (2 * self.rules.actor_radius_units) ** 2
            for actor in observation.visible_entities
        )

    def _changes(self, desired: set[int]) -> list[pygame.event.Event]:
        events = [
            pygame.event.Event(pygame.KEYUP, key=code) for code in sorted(self.held - desired)
        ]
        events.extend(
            pygame.event.Event(pygame.KEYDOWN, key=code) for code in sorted(desired - self.held)
        )
        self.held = desired
        return events

    def release(self) -> list[pygame.event.Event]:
        return self._changes(set())

    def events(self, observation: Observation, goal: Tile) -> list[pygame.event.Event]:
        if observation.own_status.stair_ticks_remaining:
            return self._changes(set())
        position = observation.own_status.position
        assert position is not None
        if any(
            link.tile == observation.own_status.tile and link.destination == goal
            for link in observation.map_static.stairs
        ):
            return self._changes({pygame.K_e} if pygame.K_e not in self.held else set())
        target = tile_center(goal)
        bodies = self._bodies(observation)
        if self.use_tools and bodies:
            route_map = replace(
                observation.map_static, blocked_tiles=observation.map_static.blocked_tiles | bodies
            )
            path = bfs(route_map, observation.own_status.tile, goal).path
            if len(path) > 1:
                target = tile_center(path[1])
                center = tile_center(observation.own_status.tile)
                # Center the perpendicular axis before taking a detour around a body.
                # Otherwise a diagonal corner cut can collide with its physical radius.
                if not self._clear_center(observation, observation.own_status.tile):
                    pass  # A body can overhang its tile; move out before recentering.
                elif path[1][0] != observation.own_status.tile[0]:
                    if abs(center[1] - position[1]) > ARRIVE:
                        target = (position[0], center[1])
                elif abs(center[0] - position[0]) > ARRIVE:
                    target = (center[0], position[1])
        dx, dy = target[0] - position[0], target[1] - position[1]
        direction = (
            pygame.K_d
            if dx > ARRIVE
            else pygame.K_a
            if dx < -ARRIVE
            else pygame.K_s
            if dy > ARRIVE
            else pygame.K_w
            if dy < -ARRIVE
            else None
        )
        if self.previous_position == position:
            # Feedback from actual movement: align the other axis when a corner
            # prevents the preferred step. This never bypasses collision.
            if direction in (pygame.K_a, pygame.K_d) and abs(dy) > ARRIVE:
                direction = pygame.K_s if dy > 0 else pygame.K_w
            elif direction in (pygame.K_w, pygame.K_s) and abs(dx) > ARRIVE:
                direction = pygame.K_d if dx > 0 else pygame.K_a
        self.previous_position = position
        desired = {direction} if direction is not None else set()
        if direction is not None and self.sprint:
            desired.add(pygame.K_LSHIFT)
        if (
            self.use_tools
            and observation.own_status.inventory.emp_charges
            and pygame.K_f not in self.held
        ):
            # Conserve charges until contact is imminent; firing at every
            # distant patrol wastes the escape tools before the return route.
            radius = self.rules.capture_range_units + UNIT // 8
            if any(
                actor.position is not None
                and not actor.disabled
                and not actor.stunned
                and sum((a - b) ** 2 for a, b in zip(actor.position, position, strict=True))
                <= radius**2
                for actor in observation.visible_entities
            ):
                desired.add(pygame.K_f)
        elif self.use_tools and pygame.K_SPACE not in self.held:
            if any(
                actor.position is not None
                and not actor.disabled
                and not actor.stunned
                and sum((a - b) ** 2 for a, b in zip(actor.position, position, strict=True))
                <= self.rules.melee_range_units**2
                for actor in observation.visible_entities
            ):
                desired.add(pygame.K_SPACE)
        return self._changes(desired)
