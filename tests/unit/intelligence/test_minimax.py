"""Alpha-beta agrees with plain minimax and prunes; Interceptor search over real gates."""

from random import Random

from echo_heist.ai.guards.interceptor import InterceptProblem, build_tree, route_hypotheses
from echo_heist.ai.navigation.grid import distances_from
from echo_heist.ai.planning.minimax import GameTree, alphabeta, minimax
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.security import build_security_registry

type Path = tuple[int, ...]


def random_tree(seed: int, depth: int) -> GameTree[Path, int]:
    """A fixed tree: every width/value is a pure function of seed and path."""

    def moves(path: Path, maximizing: bool) -> tuple[int, ...]:
        if len(path) >= depth:
            return ()
        return tuple(range(Random(f"{seed}:w:{path}").randint(1, 4)))

    def evaluate(path: Path) -> float:
        # Coarse values create many exact ties, exercising the shared tie rule.
        return float(Random(f"{seed}:v:{path}").randint(0, 6))

    return GameTree(moves, lambda path, move, _: (*path, move), evaluate)


def test_alpha_beta_matches_unpruned_minimax_on_many_seeded_trees() -> None:
    pruned_somewhere = False
    for seed in range(200):
        depth = 2 + seed % 3
        plain = minimax(random_tree(seed, depth), (), depth, seed % 2 == 0)
        fast = alphabeta(random_tree(seed, depth), (), depth, seed % 2 == 0)
        assert (fast.value, fast.move) == (plain.value, plain.move)
        assert fast.evaluated <= plain.evaluated and plain.pruned == 0
        pruned_somewhere |= fast.pruned > 0 and fast.evaluated < plain.evaluated
    assert pruned_somewhere


def test_constructed_tree_prunes_a_dominated_branch() -> None:
    values = {(0, 0): 3.0, (0, 1): 5.0, (1, 0): 2.0, (1, 1): 9.0, (1, 2): 8.0}
    tree: GameTree[Path, int] = GameTree(
        lambda path, _: (
            () if len(path) == 2 else ((0, 1) if not path else (0, 1, 2)[: 2 + path[0]])
        ),
        lambda path, move, _: (*path, move),
        lambda path: values[path],
    )
    plain, fast = minimax(tree, (), 2, True), alphabeta(tree, (), 2, True)
    # MAX root over MIN children: min(3,5)=3 beats min(2,...) after seeing 2.
    assert plain.value == fast.value == 3.0 and plain.move == fast.move == 0
    assert (plain.evaluated, fast.evaluated, fast.pruned) == (5, 3, 2)


def test_interceptor_tree_uses_real_gates_and_travel_time(rules: GameRules) -> None:
    level = load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))
    registry = build_security_registry(level, rules)
    graph, director = registry.graph, registry.director
    assert graph is not None and director is not None
    world_map = level.static_map
    hypotheses = route_hypotheses(
        graph, graph.core_tile, graph.exit_tile, distances_from(world_map, graph.core_tile)
    )
    assert 2 <= len(hypotheses) <= 3
    assert {hypothesis.nodes[0] for hypothesis in hypotheses} == {
        "choke-research-core",
        "choke-security-core",
    }
    posts = ("choke-research-core", "choke-security-core")

    def solve(guard_tile: tuple[int, int]) -> str:
        own = distances_from(world_map, guard_tile)
        problem = InterceptProblem(
            hypotheses,
            posts,
            tuple((post, own[graph.node(post).tile]) for post in posts),
            graph,
            0,
            director.guard_ticks_per_tile,
            director.intruder_ticks_per_tile,
        )
        tree = build_tree(problem, 3)
        plain, fast = (
            minimax(tree, (None, None, None), 3, False),
            alphabeta(tree, (None, None, None), 3, False),
        )
        assert (plain.value, plain.move) == (fast.value, fast.move)
        assert fast.evaluated < plain.evaluated and fast.pruned > 0
        assert isinstance(fast.move, str)
        return fast.move

    # Where the Interceptor stands changes which gate it can reach in time.
    assert solve((50, 29)) == "choke-research-core"
    assert solve((50, 13)) == "choke-security-core"
