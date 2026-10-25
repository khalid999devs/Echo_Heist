"""MCTS stages, legality, determinism and the Companion's policy-weighted reward."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from random import Random

from echo_heist.ai.companion import tactics
from echo_heist.ai.companion.briefing import policy_weights
from echo_heist.ai.planning.mcts import search
from echo_heist.core.contracts.autonomy.policy import (
    Emergency,
    GuardReaction,
    Navigation,
    PolicySelection,
    Risk,
)

GHOST = PolicySelection(Navigation.SAFEST, GuardReaction.HIDE, Emergency.ESCAPE, Risk.CAUTIOUS)
RUSH = PolicySelection(
    Navigation.SHORTEST, GuardReaction.CONSIDER_ECHO, Emergency.MELEE_IF_ADJACENT, Risk.BOLD
)


@dataclass(frozen=True)
class Toy:
    depth: int
    total: float
    sampled: int


class ToyModel:
    """GOOD pays more than SAFE on average; LOCKED is never legal."""

    def __init__(self) -> None:
        self.samples = 0

    def sample(self, rng: Random) -> Toy:
        self.samples += 1
        return Toy(0, 0.0, rng.randrange(3))

    def actions(self, state: Toy) -> Sequence[str]:
        return () if state.depth >= 3 else ("SAFE", "GOOD")

    def step(self, state: Toy, action: str, rng: Random) -> Toy:
        assert action != "LOCKED"
        gain = 0.3 if action == "SAFE" else (0.6 if rng.random() < 0.8 else 0.0)
        return Toy(state.depth + 1, state.total + gain, state.sampled)

    def terminal(self, state: Toy) -> bool:
        return state.depth >= 3

    def reward(self, state: Toy) -> float:
        return state.total / 1.8

    def playout(self, state: Toy, legal: Sequence[str], rng: Random) -> str:
        return legal[rng.randrange(len(legal))]


def test_all_four_stages_run_and_backpropagate_every_iteration() -> None:
    model = ToyModel()
    result = search(model, iterations=64, max_depth=3, rng=Random(5))
    stats = {item.action: item for item in result.alternatives}
    assert result.simulations == 64 and set(stats) == {"SAFE", "GOOD"}
    assert sum(item.visits for item in result.alternatives) == 64
    assert result.stages.backpropagations == 64 and result.stages.expansions >= 2
    assert result.stages.selections > 0 and result.stages.rollout_steps > 0
    assert result.best == "GOOD" and stats["GOOD"].visits > stats["SAFE"].visits
    assert model.samples == 65  # a fresh belief sample per iteration (+ root legality)
    # One iteration: one expansion, one backed-up reward on exactly one root child.
    single = search(ToyModel(), iterations=1, max_depth=3, rng=Random(5))
    assert [item.visits for item in single.alternatives] == [1, 0]
    assert single.alternatives[1].mean_reward is None  # unvisited is unknown, not zero


def test_fixed_seed_repeats_and_illegal_actions_never_appear() -> None:
    first = search(ToyModel(), iterations=64, max_depth=3, rng=Random(9))
    second = search(ToyModel(), iterations=64, max_depth=3, rng=Random(9))
    assert first == second
    assert "LOCKED" not in first.root_legal


def test_workshop_weights_shift_the_time_versus_risk_reward() -> None:
    """Navigation/Risk blocks rescale the blueprint reward: fast-but-seen against
    slow-and-clean ranks differently for Rush and Ghost."""
    root = tactics.TacticalState(
        0, 0, False, 3, 1, 0.0, 0.0, 0, False, False, (), 0, False, "entry"
    )
    fast_seen = replace(root, advanced=2, seconds=8.0, detections=0.45, survival=0.92)
    slow_clean = replace(root, advanced=2, seconds=40.0)

    def score(policy: PolicySelection, state: tactics.TacticalState) -> float:
        model = tactics.CompanionModel(
            None,  # type: ignore[arg-type]  # raw() needs only weights/root/legs
            policy_weights(policy),
            root,
            (),
            (),
            {},
            {},
            frozenset(),
            False,
            False,
            False,
            False,
            False,
            {},
            False,
        )
        return model.raw(state)

    assert score(RUSH, fast_seen) > score(RUSH, slow_clean)
    assert score(GHOST, slow_clean) > score(GHOST, fast_seen)
    assert policy_weights(GHOST).risk_weight > policy_weights(RUSH).risk_weight == 0
