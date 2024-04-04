from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Self, Set, Tuple, Union

from aspy.program.literals import (
    AggrLiteral,
    AggrPlaceholder,
    LiteralCollection,
    PredLiteral,
)
from aspy.program.safety_characterization import SafetyTriplet

from .constraint import Constraint
from .statement import Statement

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import Literal
    from aspy.program.literals.special import ChoicePlaceholder
    from aspy.program.substitution import Substitution

    from .choice import Choice, ChoiceRule
    from .special import AggrBaseRule, AggrElemRule


class NormalRule(Statement):
    r"""Normal rule.

    Statement of form:
        :math:`h` :- :math:`b_1,\dots,b_n`.

    where:
        :math:`h` is a classical atom (non-default-negated predicate literal).
        :math:`b_1,\dots,b_n` are literals with :math:`n\ge0`.

    for :math:`n=0` the rule is called a fact.

    Semantically, any answer set that includes :math:`b_1,\dots,b_n` must also include :math:`h`.

    Attributes:
        atom: TODO
        literals: TODO
        head: TODO
        body: TODO
        var_table: `VariableTable` instance for the statement.
        safe: Boolean indicating whether or not the statement is considered safe.
        ground: Boolean indicating whether or not the statement is ground.
        deterministic: Boolean indicating whether or not the consequent of the rule is
            deterministic. Always `True` for normal rules.
        contains_aggregates: Boolean indicating whether or not the statement contains
            aggregate expressions.
    """  # noqa

    deterministic: bool = True

    def __init__(
        self: Self,
        atom: "PredLiteral",
        body: Optional[Iterable["Literal"]] = None,
        **kwargs,
    ) -> None:
        """Initializes the normal rule instance.

        Args:
            atom: `PredLiteral` instance.
            body: Optional iterable over `Literal` instances.
                Defaults to None.
        """
        super().__init__(**kwargs)

        if body is None:
            body = LiteralCollection()

        self.atom = atom
        self.literals = (
            LiteralCollection(*body)
            if not isinstance(body, LiteralCollection)
            else body
        )

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the statement to a given object.

        Considered equal if the given object is also a `NormalRule` instance with same atom
        and literals.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the statement is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, NormalRule)
            and self.atom == other.atom
            and self.literals == other.literals
        )

    def __hash__(self: Self) -> int:
        return hash(("normal rule", self.atom, self.literals))

    def __str__(self: Self) -> str:
        """Returns the string representation for the statement.

        Returns:
            String representing the statement.
        """
        return f"{str(self.atom)}{f' :- {str(self.body)}' if self.body else ''}."

    @property
    def head(self: Self) -> LiteralCollection:
        return LiteralCollection(self.atom)

    @property
    def body(self: Self) -> LiteralCollection:
        return self.literals

    @cached_property
    def safe(self: Self) -> bool:
        return self.body.safety(self) == SafetyTriplet(self.global_vars())

    @cached_property
    def ground(self: Self) -> bool:
        return self.atom.ground and self.literals.ground

    def substitute(self: Self, subst: "Substitution") -> "NormalRule":
        """Applies a substitution to the statement.

        Substitutes the atom and all literals recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `NormalRule` instance with (possibly substituted) atom and literals.
        """
        if self.ground:
            return deepcopy(self)

        return NormalRule(self.atom.substitute(subst), self.literals.substitute(subst))

    def replace_arith(self: Self) -> "NormalRule":
        """Replaces arithmetic terms appearing in the statement with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `NormalRule` instance.
        """  # noqa
        return NormalRule(
            self.atom.replace_arith(self.var_table),
            self.literals.replace_arith(self.var_table),
        )

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
    ) -> "NormalRule":
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
            `NormalRule` instance representing the rewritten original statement without
            any aggregate expressions.
        """

        # global variables
        glob_vars = self.global_vars()

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
        alpha_rule = NormalRule(
            self.atom,
            tuple(
                alpha_map[literal] if isinstance(literal, AggrLiteral) else literal
                for literal in self.body
            ),  # NOTE: restores original order of literals
        )

        return alpha_rule

    def assemble_aggregates(
        self: Self, assembling_map: Dict["AggrPlaceholder", "AggrLiteral"]
    ) -> "NormalRule":
        """Reassembles rewritten aggregates expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `AggrPlaceholder` instances to
                `AggrLiteral` instances to be replaced with.

        Returns:
            `NormalRule` instance representing the reassembled original statement.
        """
        return NormalRule(
            self.atom,
            tuple(
                literal if literal not in assembling_map else assembling_map[literal]
                for literal in self.body
            ),
        )

    def assemble_choices(
        self: Self,
        assembling_map: Dict["ChoicePlaceholder", "Choice"],
    ) -> Union["NormalRule", "ChoiceRule"]:
        """Reassembles rewritten choice expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `ChoicePlaceholder` instances to
                `Choice` instances to be replaced with.

        Returns:
            `NormalRule` or `ChoiceRule` instance representing the reassembled original
            statement.
        """
        # local import to avoid circular imports
        from aspy.program.literals.special import ChoicePlaceholder

        from .choice import ChoiceRule

        # choice rule
        if isinstance(self.atom, ChoicePlaceholder):
            # satisfiable (instantiate choice rule)
            if self.atom in assembling_map:
                return ChoiceRule(assembling_map[self.atom], self.body)
            # unsatisfiable (instantiate constraint)
            else:
                return Constraint(*self.body)

        # non-choice rule (nothing to be done here)
        return deepcopy(self)

    @cached_property
    def is_fact(self: Self) -> bool:
        return not bool(len(self.body))
