"""Bounded open-loop Monte Carlo Tree Search with UCT (all four stages).

Each iteration samples one plausible world from the caller's belief model
(determinization), then:

1. **Selection** descends fully expanded nodes by UCT
   ``mean + c * sqrt(ln(parent visits) / child visits)``;
2. **Expansion** adds one untried action that is legal in the sampled state;
3. **Rollout** plays the model's seeded randomized default policy over legal
   actions to the depth limit using its approximate transition model;
4. **Backpropagation** adds the normalized reward to every node on the path.

The budget is a fixed iteration count, never wall-clock time, and all ties break
by the model's stable action order, so a seed reproduces the same search.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from math import log, sqrt
from random import Random
from typing import Protocol


class TacticalModel[S, A](Protocol):
    def sample(self, rng: Random) -> S: ...
    def actions(self, state: S) -> Sequence[A]: ...
    def step(self, state: S, action: A, rng: Random) -> S: ...
    def terminal(self, state: S) -> bool: ...
    def reward(self, state: S) -> float: ...  # normalized to [0, 1]
    def playout(self, state: S, legal: Sequence[A], rng: Random) -> A: ...


@dataclass(slots=True)
class _Node[A]:
    action: A | None
    depth: int
    children: dict[A, "_Node[A]"] = field(default_factory=dict)
    visits: int = 0
    total: float = 0.0


@dataclass(frozen=True, slots=True)
class ActionStats[A]:
    action: A
    visits: int
    mean_reward: float | None


@dataclass(frozen=True, slots=True)
class StageCounts:
    selections: int
    expansions: int
    rollout_steps: int
    backpropagations: int


@dataclass(frozen=True, slots=True)
class MctsResult[A]:
    best: A | None
    simulations: int
    alternatives: tuple[ActionStats[A], ...]
    stages: StageCounts
    root_legal: tuple[A, ...]


def uct(child_total: float, child_visits: int, parent_visits: int, exploration: float) -> float:
    return child_total / child_visits + exploration * sqrt(log(parent_visits) / child_visits)


def search[S, A](
    model: TacticalModel[S, A],
    *,
    iterations: int,
    max_depth: int,
    rng: Random,
    exploration: float = 0.25,
) -> MctsResult[A]:
    if iterations <= 0 or max_depth <= 0:
        raise ValueError("MCTS needs a positive iteration budget and depth")
    root: _Node[A] = _Node(None, 0)
    selections = expansions = rollouts = backups = 0
    root_legal = tuple(model.actions(model.sample(Random(0))))
    for _ in range(iterations):
        state = model.sample(rng)
        node, path = root, [root]
        # 1. Selection over children whose actions are legal in this sample.
        while not model.terminal(state) and node.depth < max_depth:
            legal = tuple(model.actions(state))
            untried = [action for action in legal if action not in node.children]
            if untried or not legal:
                break
            parent = node
            node = max(
                (parent.children[action] for action in legal),
                key=lambda child: uct(child.total, child.visits, parent.visits, exploration),
            )
            assert node.action is not None
            state = model.step(state, node.action, rng)
            path.append(node)
            selections += 1
        # 2. Expansion of exactly one untried legal action.
        if not model.terminal(state) and node.depth < max_depth:
            untried = [a for a in model.actions(state) if a not in node.children]
            if untried:
                action = untried[0]
                child: _Node[A] = _Node(action, node.depth + 1)
                node.children[action] = child
                state = model.step(state, action, rng)
                node = child
                path.append(node)
                expansions += 1
        # 3. Rollout with the seeded randomized default policy to the depth limit.
        depth = node.depth
        while not model.terminal(state) and depth < max_depth:
            legal = tuple(model.actions(state))
            if not legal:
                break
            state = model.step(state, model.playout(state, legal, rng), rng)
            depth += 1
            rollouts += 1
        # 4. Backpropagation of the normalized reward.
        value = min(1.0, max(0.0, model.reward(state)))
        for visited in path:
            visited.visits += 1
            visited.total += value
        backups += 1
    stats = tuple(
        ActionStats(
            action,
            root.children[action].visits if action in root.children else 0,
            root.children[action].total / root.children[action].visits
            if action in root.children and root.children[action].visits
            else None,
        )
        for action in root_legal
    )
    visited_stats = [item for item in stats if item.visits]
    best = (
        max(
            visited_stats,
            key=lambda item: (item.visits, item.mean_reward or 0.0, -root_legal.index(item.action)),
        ).action
        if visited_stats
        else None
    )
    return MctsResult(
        best, iterations, stats, StageCounts(selections, expansions, rollouts, backups), root_legal
    )
