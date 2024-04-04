from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Self, Set, Tuple

from aspy.program.expression import Expr
from aspy.program.literals import (
    AggrLiteral,
    AggrPlaceholder,
    Literal,
    LiteralCollection,
)
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.statements import AggrBaseRule, AggrElemRule
from aspy.program.terms import TermTuple
from aspy.program.variable_table import VariableTable

from .statement import Statement

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from aspy.program.substitution import Substitution
    from aspy.program.terms import Term, Variable


class WeightAtLevel(Expr):
    """Weight at level for weak constraints.

    Attributes:
        weight: `Term` instance.
        level: `Term` instance.
        terms: `TermTuple` instance.
        ground: Boolean indicating whether or not the term is ground.
    """

    def __init__(
        self: Self,
        weight: "Term",
        level: "Term",
        terms: Optional[Iterable["Term"]] = None,
    ) -> None:
        if terms is None:
            terms = tuple()

        self.weight = weight
        self.level = level
        self.terms = TermTuple(*terms) if not isinstance(terms, TermTuple) else terms

    def __str__(self: Self) -> str:
        """Returns the string representation for the weight at level.

        Returns:
            String representing the weight at level.
        """
        return f"{str(self.weight)}@{str(self.level)}, {str(self.terms)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the weight at level to a given object.

        Considered equal if the given object is also a `WeightAtLevel` instance
        with same weight, level and terms.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the weight at level is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, WeightAtLevel)
            and self.weight == other.weight
            and self.level == other.level
            and self.terms == other.terms
        )

    def __hash__(self: Self) -> int:
        return hash(("weight at level", self.weight, self.level, self.terms))

    @cached_property
    def ground(self: Self) -> bool:
        return (
            self.weight.ground
            and self.level.ground
            and all(term.ground for term in self.terms)
        )

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the weight at level.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of all terms.
        """  # noqa
        return set().union(
            self.weight.vars(),
            self.level.vars(),
            self.terms.vars(),
        )

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the expression.

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for this expression. Defaults to `None`.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the (global) variables of all terms.
        """  # noqa
        return set().union(
            self.weight.global_vars(),
            self.level.global_vars(),
            self.terms.global_vars(),
        )

    def safety(self: Self, statement: Optional["Statement"] = None) -> "SafetyTriplet":
        """Returns the safety characterization for the weight at level.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` instance the weight at level appears in.
                Irrelevant for weight at level. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance with the `Variable` instance marked as 'safe'.
        """  # noqa
        raise Exception(
            "Safety characterization for weight at level not supported yet."
        )

    def substitute(self: Self, subst: "Substitution") -> "WeightAtLevel":
        """Applies a substitution to the weight at level.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `WeightAtLevel` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        return WeightAtLevel(
            self.weight.substitute(subst),
            self.level.substitute(subst),
            self.terms.substitute(subst),
        )

    def replace_arith(self: Self, var_table: "VariableTable") -> "WeightAtLevel":
        """Replaces arithmetic terms appearing in the weight at level with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `WeightAtLevel` instance.
        """  # noqa
        return WeightAtLevel(
            self.weight.replace_arith(var_table),
            self.level.replace_arith(var_table),
            self.terms.replace_arith(var_table),
        )


class WeakConstraint(Statement):
    r"""Weak constraint.

    Statement of form:
        :~ :math:`b_1,\dots,b_n`. [:math:`w`@:math:`l`,:math:`t_1,\dots,t_m`]

    where:
        :math:`b_1,\dots,b_n` are literals with :math:`n\ge0`.
        :math:`w,l,t_1,\dots,t_m` are terms.

    Semantics: TODO.

    Attributes:
        literals: TODO
        weight_at_level: TODO
        head: TODO
        body: TODO
        var_table: `VariableTable` instance for the statement.
        safe: Boolean indicating whether or not the statement is considered safe.
        ground: Boolean indicating whether or not the statement is ground.
        deterministic: Boolean indicating whether or not the consequent of the rule is
            deterministic. Always `True` for weak constraints.
        contains_aggregates: Boolean indicating whether or not the statement contains
            aggregate expressions.
    """  # noqa

    deterministic: bool = True

    def __init__(
        self: Self,
        literals: Iterable["Literal"],
        weight_at_level: "WeightAtLevel",
    ) -> None:
        """Initializes the weak constraint instance.

        Args:
            literals: Iterable over `PredLiteral` instances.
            weight_at_level: `WeightAtLevel` instance.
        """
        super().__init__()

        self.literals = (
            LiteralCollection(*literals)
            if not isinstance(literals, LiteralCollection)
            else literals
        )
        self.weight_at_level = weight_at_level

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the statement to a given object.

        Considered equal if the given object is also a `WeakConstraint` instance with same literals
        and weight at level.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the statement is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, WeakConstraint)
            and self.literals == other.literals
            and self.weight_at_level == other.weight_at_level
        )

    def __hash__(self: Self) -> int:
        return hash(("weak constraint", self.literals, self.weight_at_level))

    def __str__(self: Self) -> str:
        """Returns the string representation for the statement.

        Returns:
            String representing the statement.
        """
        return f":~ {str(self.body)}. [{str(self.weight_at_level)}]"

    def __init_var_table(self: Self) -> None:
        # initialize variable table
        self.__var_table = VariableTable(
            self.literals.vars().union(self.weight_at_level.vars())
        )

        # mark global variables
        self.__var_table.update(
            {
                var: True
                for var in self.head.global_vars(self).union(
                    self.weight_at_level.global_vars()
                )
            }
        )

    @property
    def head(self: Self) -> LiteralCollection:
        return LiteralCollection()

    @property
    def body(self: Self) -> LiteralCollection:
        return self.literals

    @cached_property
    def safe(self: Self) -> bool:
        return self.body.safety(self) == SafetyTriplet(self.global_vars())

    @cached_property
    def ground(self: Self) -> bool:
        return self.weight_at_level.ground and all(
            literal.ground for literal in self.literals
        )

    @cached_property
    def contains_aggregates(self: Self) -> bool:
        return any(isinstance(literal, AggrLiteral) for literal in self.literals)

    def substitute(self: Self, subst: "Substitution") -> "WeakConstraint":
        """Applies a substitution to the statement.

        Substitutes all literals and terms in weight at level recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `WeakConstraint` instance with (possibly substituted) literals and
            weight at level.
        """
        if self.ground:
            return deepcopy(self)

        return WeakConstraint(
            self.literals.substitute(subst),
            self.weight_at_level.substitute(subst),
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
    ) -> "WeakConstraint":
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
            `WeakConstraint` instance representing the rewritten original statement
            without any aggregate expressions.
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
        alpha_rule = WeakConstraint(
            tuple(
                alpha_map[literal] if isinstance(literal, AggrLiteral) else literal
                for literal in self.body
            ),  # NOTE: restores original order of literals
            self.weight_at_level,
        )

        return alpha_rule

    def assemble_aggregates(
        self: Self, assembling_map: Dict["AggrPlaceholder", "AggrLiteral"]
    ) -> "WeakConstraint":
        """Reassembles rewritten aggregates expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `AggrPlaceholder` instances to
                `AggrLiteral` instances to be replaced with.

        Returns:
            `WeakConstraint` instance representing the reassembled original statement.
        """
        return WeakConstraint(
            tuple(
                literal if literal not in assembling_map else assembling_map[literal]
                for literal in self.body
            ),
            self.weight_at_level,
        )

    def replace_arith(self: Self, var_table: "VariableTable") -> "TermTuple":
        """Replaces arithmetic terms appearing in the statement with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `WeakConstraint` instance.
        """  # noqa
        return WeakConstraint(
            self.literals.replace_arith(var_table),
            self.weight_at_level.replace_arith(var_table),
        )
