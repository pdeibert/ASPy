from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Self, Set, Tuple

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
    r"""Constraint.

    Statement of form:
        :- :math:`b_1,\dots,b_n`.

    where:
        :math:`b_1,\dots,b_n` are literals with :math:`n\ge0`.

    Semantically, no answer set may include :math:`b_1,\dots,b_n`.

    Attributes:
        literals: TODO
        head: TODO
        body: TODO
        var_table: `VariableTable` instance for the statement.
        safe: Boolean indicating whether or not the statement is considered safe.
        ground: Boolean indicating whether or not the statement is ground.
        deterministic: Boolean indicating whether or not the consequent of the rule is
            deterministic. Always `True` for constraints.
        contains_aggregates: Boolean indicating whether or not the statement contains
            aggregate expressions.
    """  # noqa

    deterministic: bool = True

    def __init__(self: Self, *literals: "Literal", **kwargs) -> None:
        """Initializes the constraint instance.

        Args:
            *literals: Sequence of `PredLiteral` instances.
        """
        super().__init__(**kwargs)

        self.literals = LiteralCollection(*literals)

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the statement to a given object.

        Considered equal if the given object is also a `Constraint` instance with same literals.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the statement is considered equal to the given object.
        """  # noqa
        return isinstance(other, Constraint) and set(self.literals) == set(
            other.literals
        )

    def __hash__(self: Self) -> int:
        return hash(("constraint", frozenset(self.literals)))

    def __str__(self: Self) -> str:
        """Returns the string representation for the statement.

        Returns:
            String representing the statement.
        """
        return f":- {', '.join([str(literal) for literal in self.body])}."

    @property
    def head(self: Self) -> LiteralCollection:
        return LiteralCollection()

    @property
    def body(self: Self) -> LiteralCollection:
        return self.literals

    @cached_property
    def safe(self: Self) -> bool:
        global_vars = self.global_vars()
        body_safety = self.body.safety(self)

        return body_safety == SafetyTriplet(global_vars)

    @cached_property
    def ground(self: Self) -> bool:
        return all(literal.ground for literal in self.literals)

    @cached_property
    def contains_aggregates(self: Self) -> bool:
        return any(isinstance(literal, AggrLiteral) for literal in self.literals)

    def substitute(self: Self, subst: "Substitution") -> "Constraint":
        """Applies a substitution to the statement.

        Substitutes all literals recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `Constraint` instance with (possibly substituted) literals.
        """
        if self.ground:
            return deepcopy(self)

        return Constraint(*self.literals.substitute(subst))

    def rewrite_aggregates(
        self: Self,
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
        """Rewrites aggregates expressions inside the statement.

        Args:
            aggr_counter: Integer representing the current count of rewritten aggregates
                in the Program. Used as unique ids for placeholder literals.
            aggr_map: Dictionary mapping integer aggregate ids to tuples consisting of
                the original `AggrLiteral` instance replaced, the `AggrPlaceholder`
                instance replacing it in the original statement, an `AggrBaseRule`
                instance and a set of `AggrElemRule` instances representing rules for
                propagation. Pre-existing content in the dictionary is irrelevant for
                the method, the dictionary is simply updated in-place.

        Returns:
            `Constraint` instance representing the rewritten original statement without
            any aggregate expressions.
        """
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
        self: Self, assembling_map: Dict["AggrPlaceholder", "AggrLiteral"]
    ) -> "Constraint":
        """Reassembles rewritten aggregates expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `AggrPlaceholder` instances to
                `AggrLiteral` instances to be replaced with.

        Returns:
            `Constraint` instance representing the reassembled original statement.
        """
        return Constraint(
            *tuple(
                literal if literal not in assembling_map else assembling_map[literal]
                for literal in self.body
            ),
        )

    def replace_arith(self: Self, var_table: "VariableTable") -> "TermTuple":
        """Replaces arithmetic terms appearing in the statement with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `Constraint` instance.
        """  # noqa
        return Constraint(*self.literals.replace_arith(var_table))
