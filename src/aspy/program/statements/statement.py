from abc import ABC, abstractmethod
from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Optional, Self, Set, Tuple

from aspy.program.expression import Expr
from aspy.program.literals import AggrLiteral
from aspy.program.variable_table import VariableTable

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import (
        AggrPlaceholder,
        ChoicePlaceholder,
        LiteralCollection,
    )
    from aspy.program.safety_characterization import SafetyTriplet
    from aspy.program.terms import Variable

    from .choice import Choice
    from .special import AggrBaseRule, AggrElemRule, ChoiceBaseRule, ChoiceElemRule


class Statement(Expr, ABC):
    """Abstract base class for all statements.

    Declares some default as well as abstract methods for statements.
    All statements should inherit from this class or a subclass thereof.

    Attributes:
        head: TODO
        body: TODO
        var_table: `VariableTable` instance for the statement.
        safe: Boolean indicating whether or not the statement is considered safe.
        ground: Boolean indicating whether or not the statement is ground.
        deterministic: Boolean indicating whehter or not the consequent of the statement
            is deterministic.
        contains_aggregates: Boolean indicating whether or not the statement contains
            aggregate expressions.
    """

    __slots__ = "deterministic"

    def __init__(
        self: Self, var_table: Optional["VariableTable"] = None, *args, **kwargs
    ) -> None:
        """Initializes the statement instance.

        Should always be called to allow passing of variable table.

        Args:
            var_table: Optional `VariableTable` instance corresponding to the statement.
                Defaults to None.
        """
        self.__var_table = var_table

    @abstractmethod  # pragma: no cover
    def __str__(self: Self) -> str:
        """Returns the string representation of the statement.

        Returns:
            String representation of the statement.
        """
        pass

    @property
    @abstractmethod  # pragma: no cover
    def head(self: Self) -> Any:
        # TODO: necessary to require for all statements?
        pass

    @property
    @abstractmethod  # pragma: no cover
    def body(self: Self) -> Any:
        # TODO: necessary to require for all statements?
        pass

    @property
    @abstractmethod  # pragma: no cover
    def safe(self: Self) -> bool:
        pass

    @property
    @abstractmethod  # pragma: no cover
    def ground(self: Self) -> bool:
        pass

    @cached_property
    def contains_aggregates(self: Self) -> bool:
        return any(isinstance(literal, AggrLiteral) for literal in self.body)

    @property
    def var_table(self: Self) -> "VariableTable":
        """Variable table of the statement.

        Initializes variable table from scratch if necessary.

        Returns:
            `VariableTable` instance.
        """
        if self.__var_table is None:
            self.__init_var_table()

        return self.__var_table

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the statement.

        Returns:
            Set of `Variable` instances.
        """
        return self.var_table.vars()

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the statement.

        Returns:
            Set of `Variable` instances.
        """
        return self.var_table.global_vars()

    def safety(self: Self, statment: Optional["Statement"] = None) -> "SafetyTriplet":
        """Returns the safety characterization for the statement.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for statements. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance.
        """  # noqa
        raise NotImplementedError()

    def __init_var_table(self: Self) -> None:
        """Initializes the variable table from scratch."""
        # initialize variable table
        self.__var_table = VariableTable(self.head.vars().union(self.body.vars()))

        # mark global variables
        self.__var_table.update(
            {
                var: True
                for var in self.head.global_vars(self).union(
                    self.body.global_vars(self)
                )
            }
        )

    @abstractmethod  # pragma: no cover
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
    ) -> "Statement":
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
            `Statement` instance representing the rewritten original statement without
            any aggregate expressions.
        """
        pass

    @abstractmethod  # pragma: no cover
    def assemble_aggregates(
        self: Self, assembling_map: Dict["AggrPlaceholder", "AggrLiteral"]
    ) -> "Statement":
        """Reassembles rewritten aggregates expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `AggrPlaceholder` instances to
                `AggrLiteral` instances to be replaced with.

        Returns:
            `Statement` instance representing the reassembled original statement.
        """
        pass

    def rewrite_choices(
        self: Self,
        choice_counter: int,
        choice_map: Dict[
            int,
            Tuple[
                "Choice",
                "ChoicePlaceholder",
                "ChoiceBaseRule",
                Set["ChoiceElemRule"],
            ],
        ],
    ) -> "Statement":
        """Rewrites choice expressions inside the statement.

        Args:
            choice_counter: Integer representing the current count of rewritten choice
                expressions in the Program. Used as unique ids for placeholder literals.
            aggr_map: Dictionary mapping integer choice ids to tuples consisting of
                the original `Choice` instance replaced, the `ChoicePlaceholder`
                instance replacing it in the original statement, a `ChoiceBaseRule`
                instance and a set of `ChoiceElemRule` instances representing rules for
                propagation. Pre-existing content in the dictionary is irrelevant for
                the method, the dictionary is simply updated in-place.

        Returns:
            `Statement` instance representing the rewritten original statement without
            any choice expressions.
        """
        return deepcopy(self)

    def assemble_choices(
        self: Self,
        assembling_map: Dict["ChoicePlaceholder", "Choice"],
    ) -> "Statement":
        """Reassembles rewritten choice expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `ChoicePlaceholder` instances to
                `Choice` instances to be replaced with.

        Returns:
            `Statement` instance representing the reassembled original statement.
        """
        return deepcopy(self)

    def consequents(self: Self) -> "LiteralCollection":
        """Returns the consequents of the statement.

        Returns:
            `LiteralCollection` instance.
        """
        return self.head

    def antecedents(self: Self) -> "LiteralCollection":
        """Returns the antecedents of the statement.

        Returns:
            `LiteralCollection` instance.
        """
        return self.body

    def pos_occ(self: Self) -> "LiteralCollection":
        """TODO"""
        return self.head.pos_occ() + self.body.pos_occ()

    def neg_occ(self: Self) -> "LiteralCollection":
        """TODO"""
        return self.head.neg_occ() + self.body.neg_occ()

    @property
    def is_fact(self: Self) -> bool:
        return False
