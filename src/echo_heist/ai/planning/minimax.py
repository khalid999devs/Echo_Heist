"""Depth-limited minimax and alpha-beta over the same callable game tree.

Both searches share one move ordering and one strict ``>``/``<`` tie rule (the
first best move in order wins), so for any tree they return the same value and
the same move. Alpha-beta additionally reports how many sibling branches it
skipped after a cutoff; plain minimax never prunes.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import inf


@dataclass(frozen=True, slots=True)
class SearchResult[M]:
    value: float
    move: M | None
    evaluated: int  # leaf evaluations actually computed
    pruned: int  # child branches never visited because of a cutoff


@dataclass(slots=True)
class _Counter:
    evaluated: int = 0
    pruned: int = 0


class GameTree[S, M]:
    """Callable description: ``moves(state, maximizing)``, ``child`` and ``evaluate``."""

    def __init__(
        self,
        moves: Callable[[S, bool], Sequence[M]],
        child: Callable[[S, M, bool], S],
        evaluate: Callable[[S], float],
    ) -> None:
        self.moves, self.child, self.evaluate = moves, child, evaluate


def minimax[S, M](tree: GameTree[S, M], state: S, depth: int, maximizing: bool) -> SearchResult[M]:
    counter = _Counter()

    def search(node: S, remaining: int, maximize: bool) -> tuple[float, M | None]:
        moves = tree.moves(node, maximize) if remaining > 0 else ()
        if not moves:
            counter.evaluated += 1
            return tree.evaluate(node), None
        best_value, best_move = (-inf if maximize else inf), None
        for move in moves:
            value, _ = search(tree.child(node, move, maximize), remaining - 1, not maximize)
            if (value > best_value) if maximize else (value < best_value):
                best_value, best_move = value, move
        return best_value, best_move

    value, move = search(state, depth, maximizing)
    return SearchResult(value, move, counter.evaluated, 0)


def alphabeta[S, M](
    tree: GameTree[S, M], state: S, depth: int, maximizing: bool
) -> SearchResult[M]:
    counter = _Counter()

    def search(
        node: S, remaining: int, maximize: bool, alpha: float, beta: float
    ) -> tuple[float, M | None]:
        moves = tree.moves(node, maximize) if remaining > 0 else ()
        if not moves:
            counter.evaluated += 1
            return tree.evaluate(node), None
        best_value, best_move = (-inf if maximize else inf), None
        for index, move in enumerate(moves):
            value, _ = search(
                tree.child(node, move, maximize), remaining - 1, not maximize, alpha, beta
            )
            if maximize:
                if value > best_value:
                    best_value, best_move = value, move
                alpha = max(alpha, best_value)
            else:
                if value < best_value:
                    best_value, best_move = value, move
                beta = min(beta, best_value)
            # Strict cutoff keeps equal-valued siblings, so the first-best tie rule
            # (and therefore the chosen move) matches plain minimax exactly.
            if alpha > beta:
                counter.pruned += len(moves) - index - 1
                break
        return best_value, best_move

    value, move = search(state, depth, maximizing, -inf, inf)
    return SearchResult(value, move, counter.evaluated, counter.pruned)
