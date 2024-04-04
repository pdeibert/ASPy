import itertools
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Iterator, Optional, Self, Set, Union

from aspy.program.expression import Expr
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import AssignmentError, Substitution

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.query import Query
    from aspy.program.statements import Statement
    from aspy.program.terms import Variable
    from aspy.program.variable_table import VariableTable


@dataclass
class Literal(Expr, ABC):
    """Abstract base class for all literals.

    Declares some default as well as abstract methods for literals.
    All literals should inherit from this class or a subclass thereof.

    Attributes:
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not the literal is ground.
    """

    naf: bool = False

    @abstractmethod  # pragma: no cover
    def pos_occ(self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Set of `Literal` instances that occur positively in the literal.
        """
        pass

    @abstractmethod  # pragma: no cover
    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Set of `Literal` instances that occur negatively in the literal.
        """
        pass

    @abstractmethod  # pragma: no cover
    def match(self: Self, other: "Expr") -> Optional["Substitution"]:
        """Tries to match the predicate literal with an expression.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        pass

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the literal.

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Usually irrelevant for literals. Defaults to `None`.

        Returns:
            A (possibly empty) set of `Variable` instances.
        """
        return self.vars()

    def set_neg(self: Self, value: bool = True) -> None:
        """Setter for the `naf` attribute.

        Raises an error if not overridden.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.

        Raises:
            NotImplementedError: negation not defined as valid.
        """
        raise NotImplementedError(
            f"Setting negation for literal of type {type(self)} not defined."
        )

    def set_naf(self: Self, value: bool = True) -> None:
        """Setter for the `naf` attribute.

        Raises an error if not overridden.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.

        Raises:
            NotImplementedError: negation-as-failure not defined as valid.
        """
        raise NotImplementedError(
            f"Setting negation for literal of type {type(self)} not defined."
        )

    def __abs__(self: Self) -> "Literal":
        """TODO"""
        if self.naf:
            copy = deepcopy(self)
            copy.naf = False

            return copy

        return self


class LiteralCollection:
    """Represents an order-preserving unordered collection of literals.

    Attributes:
        literals: Tuple of `Literal` instances.
        ground: Boolean indicating whether or not all literals are ground.
    """

    def __init__(self: Self, *literals: Literal) -> None:
        """Initializes literal collection instance.

        Args:
            *literals: Sequence of `Literal` instances.
        """

        # initialize while removing duplicates and preserving order
        self.literals = tuple(dict.fromkeys(literals))

    def __str__(self: Self) -> str:
        """Returns the string representation for the literal collection.

        Returns:
            String consisting of the string representations of the literals,
            seperated by commas.
        """  # noqa
        return f"{','.join(str(literal) for literal in self.literals)}"

    def __len__(self: Self) -> int:
        return len(self.literals)

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the literal collection to a given object.

        Considered equal if the given object is also a `LiteralCollection` instance and contains
        the same terms in any order.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal collection is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, LiteralCollection)
            and len(self) == len(other)
            and frozenset(self.literals) == frozenset(other.literals)
        )

    def __hash__(self: Self) -> int:
        return hash(("literal collection", frozenset(self.literals)))

    def __iter__(self: Self) -> Iterator[Literal]:
        return iter(self.literals)

    def __add__(self: Self, other: "LiteralCollection") -> "LiteralCollection":
        return LiteralCollection(*self.literals, *other.literals)

    def __getitem__(self: Self, index: int) -> "Literal":
        return self.literals[index]

    def __lt__(self: Self, other: Union["LiteralCollection", Set["Literal"]]) -> bool:
        if isinstance(other, set):
            return set(self.literals) < other
        elif isinstance(other, LiteralCollection):
            return set(self.literals) < set(other.literals)

        return False

    def __gt__(self: Self, other: Union["LiteralCollection", Set["Literal"]]) -> bool:
        if isinstance(other, set):
            return set(self.literals) > other
        elif isinstance(other, LiteralCollection):
            return set(self.literals) > set(other.literals)

        return False

    def __le__(self: Self, other: Union["LiteralCollection", Set["Literal"]]) -> bool:
        if isinstance(other, set):
            return set(self.literals) <= other
        elif isinstance(other, LiteralCollection):
            return set(self.literals) <= set(other.literals)

        return False

    def __ge__(self: Self, other: Union["LiteralCollection", Set["Literal"]]) -> bool:
        if isinstance(other, set):
            return set(self.literals) >= other
        elif isinstance(other, LiteralCollection):
            return set(self.literals) >= set(other.literals)

        return False

    @cached_property
    def ground(self: Self) -> bool:
        return all(literal.ground for literal in self.literals)

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Union of the sets of `Literal` instances that occur positively in the literals.
        """  # noqa
        return LiteralCollection(
            *itertools.chain(*tuple(literal.pos_occ() for literal in self.literals))
        )

    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Union of the sets of `Literal` instances that occur negatively in the literals.
        """  # noqa
        return LiteralCollection(
            *itertools.chain(*tuple(literal.neg_occ() for literal in self.literals))
        )

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the literal collection.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of all literals.
        """  # noqa
        return set().union(*tuple(literal.vars() for literal in self.literals))

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the literal collection.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the global variables of all literals.
        """  # noqa
        return set().union(
            *tuple(literal.global_vars(statement) for literal in self.literals)
        )

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> "SafetyTriplet":
        """Returns the the safety characterizations for the literal collection.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for most literals. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance as the closure of the safety characterizations of all individual literals.
        """  # noqa
        return SafetyTriplet.closure(
            *tuple(literal.safety(statement) for literal in self.literals)
        )

    def without(self: Self, *literals: Literal) -> "LiteralCollection":
        """Returns a literal collection without any of the specified literals.

        Args:
            *literals: Sequence of `Literal` instances to be excluded.

        Returns:
            `LiteralCollection` instance excluding any of the specified literals.
        """
        return type(self)(
            *(literal for literal in self.literals if literal not in literals)
        )

    def substitute(self: Self, subst: "Substitution") -> "LiteralCollection":
        """Applies a substitution to the literal collection.

        Substitutes all literals recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `LiteralCollection` instance with (possibly substituted) literals.
        """
        if self.ground:
            return deepcopy(self)

        # substitute literals recursively
        literals = (literal.substitute(subst) for literal in self)

        return LiteralCollection(*literals)

    def match(self: Self, other: "Expr") -> Optional["Substitution"]:
        """Tries to match the literal collection with an expression.

        Can only be matched to a literal collection where all literals can be matched (in arbitrary order)
        without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if not (isinstance(other, LiteralCollection) and len(self) == len(other)):
            return None

        subst = Substitution()

        # create a set of the literals in the other tuple
        other_literals = set(other.literals)

        for literal1 in self.literals:
            for literal2 in other_literals:
                # try to match literal
                match = literal1.match(literal2)

                if match is not None:
                    try:
                        # update substitution
                        subst = subst + match
                        # remove matched literal from candidates
                        other_literals.remove(literal2)
                        break
                    except AssignmentError:
                        return None
            # if no match found for literal
            else:
                return None

        return subst

    def replace_arith(self: Self, var_table: "VariableTable") -> "LiteralCollection":
        """Replaces arithmetic terms appearing in the literal collection with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `LiteralCollection` instance.
        """  # noqa
        return LiteralCollection(
            *tuple(literal.replace_arith(var_table) for literal in self.literals)
        )
