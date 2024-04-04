from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, Self, Set, Union

import aspy
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.symbols import SYM_CONST_RE

from .term import Infimum, Number, String, SymbolicConstant, Term, TermTuple

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.expression import Expr
    from aspy.program.query import Query
    from aspy.program.statements import Statement
    from aspy.program.terms import Variable
    from aspy.program.variable_table import VariableTable


class Functional(Term):
    """Represents a functional term.

    Attributes:
        symbol: String representing the identifier for the functional term.
        terms: `TermTuple` instance containing the terms of the functional term.
        ground: Boolean indicating whether or not all terms are ground.
        arity: Integer representing the arity of the functional term (equal to the number of terms).
    """  # noqa

    def __init__(self: Self, symbol: str, *terms: Term) -> None:
        """Initializes the functional term instance.

        Args:
            symbol: String representing the identifier for the functional term.
                Valid identifiers start with a lower-case latin letter, followed by zero or more alphanumerics and underscores.
                Instead of a single lower-case latin letter, identifiers may also start with '\u03b1', '\u03C7', '\u03b5\u03b1',
                '\u03b5\u03C7', '\u03b7\u03b1', or '\u03b7\u03C7', but are reserved for internal use.
            *terms: Sequence of `Term` instances.

        Raises:
            ValueError: Invalid value specified for the symbolic constant. Only checked if `aspy.debug()` returns `True`.
        """  # noqa
        # check if functor name is valid
        if aspy.debug() and not SYM_CONST_RE.fullmatch(symbol):
            raise ValueError(f"Invalid value for {type(self)}: {symbol}")

        self.symbol = symbol
        self.terms = TermTuple(*terms)

    def __str__(self: Self) -> str:
        """Returns the string representation for a functional term.

        Returns:
            String representing the functional term.
            Starts with the symbol/identifier, followed by the string representations of the terms,
            seperated by commas and enclosed by parentheses.
            If the functional term has no terms, the parentheses are omitted.
        """  # noqa
        return self.symbol + (f"({','.join([str(term) for term in self.terms])})")

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Functional` instance with same symbol/identifier value
        as well as equal terms.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Functional)
            and other.symbol == self.symbol
            and other.terms == self.terms
        )

    def __hash__(self: Self) -> int:
        return hash(("functional", self.symbol, self.terms))

    @property
    def arity(self: Self) -> int:
        return len(self.terms)

    @cached_property
    def ground(self: Self) -> bool:
        return self.terms.ground

    def precedes(self: Self, other: Term) -> bool:
        if isinstance(other, (Infimum, Number, SymbolicConstant, String)):
            return False
        elif isinstance(other, Functional):
            if self.arity == other.arity:
                if self.symbol == other.symbol:
                    for self_term, other_term in zip(self.terms, other.terms):
                        # other_term < self_term
                        if other_term.precedes(self_term) and not self_term.precedes(
                            other_term
                        ):
                            return False
                elif self.symbol > other.symbol:
                    return False

        return True

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the functional term.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of all terms.
        """  # noqa
        return self.terms.vars()

    def safety(
        self: Self, statenment: Optional[Union["Statement", "Query"]] = None
    ) -> SafetyTriplet:
        """Returns the the safety characterizations for the functional term.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for terms. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance as the closure of the safety characterizations of all individual terms.
        """  # noqa
        return SafetyTriplet.closure(*self.terms.safety())

    def replace_arith(self: Self, var_table: "VariableTable") -> "Functional":
        """Replaces arithmetic terms appearing in the functional term with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `Functional` instance.
        """  # noqa
        return Functional(self.symbol, *self.terms.replace_arith(var_table))

    def match(self: Self, other: "Expr") -> Optional[Substitution]:
        """Tries to match the term tuple with an expression.

        Can only be matched to a functional term with same identifier where each
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if not (
            isinstance(other, Functional)
            and self.symbol == other.symbol
            and self.arity == other.arity
        ):
            return None

        return self.terms.match(other.terms)

    def substitute(self: Self, subst: Substitution) -> "Functional":
        """Applies a substitution to the functional term.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `Functional` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        terms = (term.substitute(subst) for term in self.terms)

        return Functional(self.symbol, *terms)
