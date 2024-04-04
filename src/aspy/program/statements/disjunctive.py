from copy import deepcopy
from functools import cached_property
from itertools import combinations
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    Set,
    Tuple,
    Union,
)

import aspy
from aspy.program.literals import (
    AggrLiteral,
    AggrPlaceholder,
    LiteralCollection,
    PredLiteral,
)
from aspy.program.safety_characterization import SafetyTriplet

from .normal import NormalRule
from .statement import Statement

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import Literal
    from aspy.program.statements import AggrBaseRule, AggrElemRule
    from aspy.program.substitution import Substitution


class DisjunctiveRule(Statement):
    r"""Disjunctive rule.

    Statement of form:
        :math:`h_1 | \dots | h_m` :- :math:`b_1,\dots,b_n`.

    where:
        :math:`h_1|\dots|h_m` are classical atoms (non-default-negated predicate literals)
            with :math:`m>1`.
        :math:`b_1,\dots,b_n` are literals with :math:`n\ge0`.

    for :math:`n=0` the rule is called a fact.

    Semantically, any answer set that includes :math:`b_1,\dots,b_n` must also choose precisely
    one :math:`h\in\{h_1,\dots,h_m}`.

    Attributes:
        atoms: TODO
        literals: TODO
        head: TODO
        body: TODO
        var_table: `VariableTable` instance for the statement.
        safe: Boolean indicating whether or not the statement is considered safe.
        ground: Boolean indicating whether or not the statement is ground.
        deterministic: Boolean indicating whether or not the consequent of the rule is
            deterministic. Always `False` for disjunctive rules.
        contains_aggregates: Boolean indicating whether or not the statement contains
            aggregate expressions.
    """  # noqa

    deterministic: bool = False

    def __init__(
        self: Self,
        head: Iterable["Literal"],
        body: Optional[Iterable["Literal"]] = None,
        **kwargs,
    ) -> None:
        """Initializes the disjunctive rule instance.

        Args:
            head: Iterable over `PredLiteral` instances.
            body: Optional iterable over `Literal` instances.
                Defaults to None.
        """
        super().__init__(**kwargs)

        if body is None:
            body = tuple()

        if len(head) < 2:
            raise ValueError(
                (
                    f"Head for {type(self)} requires at least two literals."
                    " Use {NormalRule} instead."
                )
            )

        if aspy.debug() and not all(
            isinstance(atom, PredLiteral) and not atom.naf for atom in head
        ):
            raise ValueError(
                (
                    f"Head literals for {type(self)} must all be"
                    " positive literals of type {PredLiteral}."
                )
            )

        self.atoms = (
            head if isinstance(head, LiteralCollection) else LiteralCollection(*head)
        )
        self.literals = (
            body if isinstance(body, LiteralCollection) else LiteralCollection(*body)
        )

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the statement to a given object.

        Considered equal if the given object is also a `DisjunctiveRule` instance with same atoms
        and literals.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the statement is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, DisjunctiveRule)
            and set(self.atoms) == set(other.atoms)
            and set(self.literals) == set(other.literals)
        )

    def __hash__(self: Self) -> int:
        return hash(("disjunctive rule", self.atoms, self.literals))

    def __str__(self: Self) -> str:
        """Returns the string representation for the statement.

        Returns:
            String representing the statement.
        """
        return f"{' | '.join([str(atom) for atom in self.head])}{f' :- {str(self.body)}' if self.body else ''}."  # noqa

    @property
    def head(self: Self) -> LiteralCollection:
        return self.atoms

    @property
    def body(self: Self) -> LiteralCollection:
        return self.literals

    @cached_property
    def safe(self: Self) -> bool:
        return self.body.safety(self) == SafetyTriplet(self.global_vars())

    @cached_property
    def ground(self: Self) -> bool:
        return self.head.ground and self.body.ground

    def substitute(
        self: Self, subst: "Substitution"
    ) -> Union["DisjunctiveRule", "NormalRule"]:
        """Applies a substitution to the statement.

        Substitutes all atoms and literals recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `DisjunctiveRule` or `NormalRule` instance with (possibly substituted)
            atoms and literals. `NormalRule` is returned if the substitution results
            in a single unique head atom.
        """
        if self.ground:
            return deepcopy(self)

        subst_head = self.head.substitute(subst)

        if len(set(subst_head)) == 1:
            return NormalRule(*subst_head, self.literals.substitute(subst))

        return DisjunctiveRule(subst_head, self.literals.substitute(subst))

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
    ) -> "DisjunctiveRule":
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
            `DisjunctiveRule` instance representing the rewritten original statement
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
        alpha_rule = DisjunctiveRule(
            deepcopy(self.atoms),
            tuple(
                alpha_map[literal] if isinstance(literal, AggrLiteral) else literal
                for literal in self.body
            ),  # NOTE: restores original order of literals
        )

        return alpha_rule

    def assemble_aggregates(
        self: Self, assembling_map: Dict["AggrPlaceholder", "AggrLiteral"]
    ) -> "DisjunctiveRule":
        """Reassembles rewritten aggregates expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `AggrPlaceholder` instances to
                `AggrLiteral` instances to be replaced with.

        Returns:
            `DisjunctiveRule` instance representing the reassembled original statement.
        """
        return DisjunctiveRule(
            deepcopy(self.atoms),
            tuple(
                literal if literal not in assembling_map else assembling_map[literal]
                for literal in self.body
            ),
        )

    def replace_arith(self: Self) -> "DisjunctiveRule":
        """Replaces arithmetic terms appearing in the statement with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `DisjunctiveRule` instance.
        """  # noqa
        return DisjunctiveRule(
            self.head.replace_arith(self.var_table),
            self.body.replace_arith(self.var_table),
        )

    @cached_property
    def is_fact(self: Self) -> bool:
        return not bool(len(self.body))

    def powerset(
        self: Self,
    ) -> List[Tuple[int, ...]]:
        """TODO"""

        n_out = len(self.head)

        # return all possible combinations with n >= 1
        return sum(
            [list(combinations(range(n_out), r=n)) for n in range(1, n_out + 1)],
            [],
        )
