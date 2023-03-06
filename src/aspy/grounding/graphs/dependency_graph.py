from typing import Tuple, Set, TYPE_CHECKING

if TYPE_CHECKING: # pragma: no cover
    from aspy.program.statements import Statement


class DependencyGraph():
    def __init__(self, rules: Tuple["Statement", ...]) -> None:
        self.nodes = rules

        self.pos_edges = set()
        self.neg_edges = set()

        for dependee in rules:

            head_predicates = set(literal.pred() for literal in dependee.head)

            for depender in rules:

                # skip self
                if depender is dependee:
                    continue

                pos_body_predicates = set([literal.pred() for literal in depender.body.pos_occ()])
                neg_body_predicates = set([literal.pred() for literal in depender.body.neg_occ()])

                # positive dependency
                if head_predicates.intersection(pos_body_predicates):
                    self.pos_edges.add( (depender, dependee) )

                # negative dependency
                if head_predicates.intersection(neg_body_predicates):
                    self.neg_edges.add( (depender, dependee) )

    @property
    def edges(self) -> Set[Tuple["Statement", "Statement"]]:
        return self.pos_edges.union(self.neg_edges)