from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Set, Tuple

from aspy.program.literals import AggrLiteral, LiteralCollection
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.terms import TermTuple

from .statement import Statement

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import AggrPlaceholder, Literal
    from aspy.program.statements import AggrBaseRule, AggrElemRule
    from aspy.program.substitution import Substitution
    from aspy.program.variable_table import VariableTable


class Constraint(Statement):
    """Constraint.

    Statement of form:

        :- b_1,...,b_n .

    for literals b_1,...,b_n.
    """

    deterministic: bool = True

    def __init__(self, *literals: "Literal", **kwargs) -> None:
        super().__init__(**kwargs)

        self.literals = LiteralCollection(*literals)

    def __eq__(self, other: "Any") -> bool:
        return isinstance(other, Constraint) and set(self.literals) == set(
            other.literals
        )

    def __hash__(self) -> int:
        return hash(("constraint", frozenset(self.literals)))

    def __str__(self) -> str:
        return f":- {', '.join([str(literal) for literal in self.body])}."

    @property
    def head(self) -> LiteralCollection:
        return LiteralCollection()

    @property
    def body(self) -> LiteralCollection:
        return self.literals

    @cached_property
    def safe(self) -> bool:
        global_vars = self.global_vars()
        body_safety = self.body.safety(self)

        return body_safety == SafetyTriplet(global_vars)

    @cached_property
    def ground(self) -> bool:
        return all(literal.ground for literal in self.literals)

    @cached_property
    def contains_aggregates(self) -> bool:
        return any(isinstance(literal, AggrLiteral) for literal in self.literals)

    def substitute(self, subst: "Substitution") -> "Constraint":
        if self.ground:
            return deepcopy(self)

        return Constraint(*self.literals.substitute(subst))

    def rewrite_aggregates(
        self,
        aggr_counter: int,
        aggr_map: Dict[
            int,
            Tuple[
                "AggrLiteral",
                "AggrPlaceholder",
                "AggrBaseRule",
                Set["AggrElemRule"],
            ],
        ],
    ) -> "Constraint":

        # global variables
        glob_vars = self.global_vars(self)

        # group literals
        non_aggr_literals = []
        aggr_literals = []

        for literal in self.body:
            (
                aggr_literals if isinstance(literal, AggrLiteral) else non_aggr_literals
            ).append(literal)

        # mapping from original literals to alpha literals
        alpha_map = dict()

        # local import due to circular import
        from .rewrite import rewrite_aggregate

        for literal in aggr_literals:
            # rewrite aggregate literal
            alpha_literal, eps_rule, eta_rules = rewrite_aggregate(
                literal, aggr_counter, glob_vars, non_aggr_literals
            )

            # map original aggregate literal to new alpha literal
            alpha_map[literal] = alpha_literal

            # store aggregate information
            aggr_map[aggr_counter] = (literal, alpha_literal, eps_rule, eta_rules)

            # increase aggregate counter
            aggr_counter += 1

        # replace original rule with modified one
        alpha_rule = Constraint(
            *tuple(
                alpha_map[literal] if isinstance(literal, AggrLiteral) else literal
                for literal in self.body
            ),  # NOTE: restores original order of literals
        )

        return alpha_rule

    def assemble_aggregates(
        self, assembling_map: Dict["AggrPlaceholder", "AggrLiteral"]
    ) -> "Constraint":
        return Constraint(
            *tuple(
                literal if literal not in assembling_map else assembling_map[literal]
                for literal in self.body
            ),
        )

    def replace_arith(self, var_table: "VariableTable") -> "TermTuple":
        """Replaces arithmetic terms appearing in the term tuple with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `TermTuple` instance.
        """  # noqa
        return Constraint(*self.literals.replace_arith(var_table))
