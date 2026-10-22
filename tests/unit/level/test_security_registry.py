"""Typed guard registry over the packaged map: roles, validation and stable revision."""

from dataclasses import replace

import pytest

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.security.model import GuardRole
from echo_heist.core.contracts.world import ActorKind
from echo_heist.infrastructure.resources import load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import GuardPost, LevelData, PatrolRoute
from echo_heist.level.security import SecurityRegistryError, build_security_registry


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


def test_packaged_posts_get_real_roles_and_a_stable_revision(
    level: LevelData, rules: GameRules
) -> None:
    registry = build_security_registry(level, rules)
    roles = {value.guard_id: value.role for value in registry.assignments}
    assert roles == {
        "guard-core": GuardRole.POST,
        "guard-research": GuardRole.TRACKER,
        "guard-security": GuardRole.SENTINEL,
        "guard-service": GuardRole.SENTINEL,
    }
    core = registry.assignment("guard-core")
    assert core.zone_id == "core-chamber"
    assert core.chokepoint_ids == ("choke-research-core", "choke-security-core")
    assert all(value.patrol.points[0] != value.patrol.points[-1] for value in registry.assignments)
    spec = registry.spec(load_sensor_rules())
    assert {patrol.actor_id for patrol in spec.patrols} == set(roles)
    assert build_security_registry(level, rules).revision == registry.revision


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("missing", "missing route"),
        ("shared", "shares route"),
        ("offset", "first waypoint"),
        ("wall", "does not fit"),
    ],
)
def test_invalid_assignments_are_reported(
    level: LevelData, rules: GameRules, change: str, message: str
) -> None:
    posts = list(level.guards)
    routes = list(level.routes)
    tracker = next(index for index, post in enumerate(posts) if post.kind == ActorKind.TRACKER)
    post = posts[tracker]
    if change == "missing":
        posts[tracker] = replace(post, route_id="route-nowhere")
    elif change == "shared":
        posts.append(GuardPost("guard-extra", ActorKind.SENTINEL, post.tile, post.route_id))
    elif change == "offset":
        posts[tracker] = replace(post, tile=(post.tile[0] - 1, post.tile[1]))
    else:
        index = next(i for i, route in enumerate(routes) if route.route_id == post.route_id)
        wall = next(iter(sorted(level.static_map.hard_blocked)))
        routes[index] = PatrolRoute(post.route_id, (*routes[index].points, wall))
    with pytest.raises(SecurityRegistryError) as error:
        build_security_registry(replace(level, guards=tuple(posts), routes=tuple(routes)), rules)
    assert any(message in problem for problem in error.value.problems)
