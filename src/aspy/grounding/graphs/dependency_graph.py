from typing import TYPE_CHECKING, Self, Set, Tuple

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.statements import Statement


class DependencyGraph:
    def __init__(self: Self, rules: Tuple["Statement", ...]) -> None:
        self.nodes = rules

        self.pos_edges = set()
        self.neg_edges = set()

        for dependee in rules:
            head_predicates = set(literal.pred() for literal in dependee.consequents())

            for depender in rules:
                # skip self
                if depender is dependee:
                    continue

                body_predicates = depender.antecedents()

                pos_body_predicates = set(
                    [literal.pred() for literal in body_predicates.pos_occ()]
                )
                neg_body_predicates = set(
                    [literal.pred() for literal in body_predicates.neg_occ()]
                )

                # positive dependency
                if head_predicates.intersection(pos_body_predicates):
                    self.pos_edges.add((depender, dependee))

                # negative dependency
                if head_predicates.intersection(neg_body_predicates):
                    self.neg_edges.add((depender, dependee))

    @property
    def edges(self: Self) -> Set[Tuple["Statement", "Statement"]]:
        return self.pos_edges.union(self.neg_edges)
