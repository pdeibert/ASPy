from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, Self, Set, Tuple, Union

import aspy
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.symbols import SYM_CONST_RE
from aspy.program.terms import Functional, TermTuple

from .literal import Literal, LiteralCollection

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.expression import Expr
    from aspy.program.query import Query
    from aspy.program.statements import Statement
    from aspy.program.terms import Term, Variable
    from aspy.program.variable_table import VariableTable


class PredLiteral(Literal):
    """Predicate Literal.

    Attributes:
        name: String representing the identifier of the predicate.
        terms: `TermTuple` instance containing the terms of ther predicate literal.
        neg: Boolean indicating whether or not the literal is classically negated.
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not all terms are ground.
        arity: Integer representing the arity of the functional term (equal to the number of terms).
    """  # noqa

    def __init__(
        self,
        name: str,
        *terms: "Term",
        neg: bool = False,
        naf: bool = False,
    ) -> None:
        """Initializes predicate literal instance.

        Args:
            name: String representing the identifier of the predicate.
                Valid identifiers start with a lower-case latin letter, followed by zero or more alphanumerics and underscores.
                Instead of a single lower-case latin letter, identifiers may also start with '\u03b1', '\u03C7', '\u03b5\u03b1',
                '\u03b5\u03C7', '\u03b7\u03b1', or '\u03b7\u03C7', but are reserved for internal use.
            *terms: Sequence of `Term` instances.
            neg: Boolean indicating whether or not the literal is classically negated. Defaults to False.
            naf: Boolean indicating whether or not the literal is default-negated. Defaults to False.

        Raises:
            ValueError: Invalid name/identifier. Only checked if `aspy.debug()` returns `True`.
        """  # noqa
        super().__init__(naf)

        # check if predicate name is valid
        if aspy.debug() and not SYM_CONST_RE.fullmatch(name):
            raise ValueError(f"Invalid value for {type(self)}: {name}")

        self.name = name
        self.neg = neg
        self.terms = TermTuple(*terms)

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the literal to a given object.

        Considered equal if the given object is also a `PredLiteral` instance with same name/identifier value
        as well as equal terms.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, PredLiteral)
            and self.name == other.name
            and self.terms == other.terms
            and self.neg == other.neg
            and self.naf == other.naf
        )

    def __hash__(self: Self) -> int:
        return hash(("predicate literal", self.naf, self.neg, self.name, *self.terms))

    def __str__(self: Self) -> str:
        """Returns the string representation for the predicate literal.

        Returns:
            String representing the predicate literal.
            If the predicate literal is default-negated, the string is prefixed by `"not "`.
            If the predicate literal is classically-negated, the string is followed by `'-'`.
            The string then continuous with the name/identifier, followed by the string representations of the terms,
            seperated by commas and enclosed by parentheses.
            If the predicate literal has no terms, the parentheses are omitted.
        """  # noqa
        terms_str = (
            f"({','.join([str(term) for term in self.terms])})" if self.terms else ""
        )
        return f"{('not ' if self.naf else '')}{('-' if self.neg else '')}{self.name}{terms_str}"  # noqa

    @property
    def arity(self: Self) -> int:
        return len(self.terms)

    @cached_property
    def ground(self: Self) -> bool:
        return all(term.ground for term in self.terms)

    def set_neg(self: Self, value: bool = True) -> None:
        """Setter for the `neg` attribute.

        Args:
            value: Boolean value for the `neg` attribute. Defaults to `True`.
        """
        self.neg = value

    def set_naf(self: Self, value: bool = True) -> None:
        """Setter for the `naf` attribute.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.
        """
        self.naf = value

    def pred(self: Self) -> Tuple[str, int]:
        """Predicate signature of the predicate literal.

        Returns:
            Tuple of a string and an integer, representing the identifier and arity
            of the predicate literal, respectively.
        """
        return (self.name, self.arity)

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Empty set if predicate literal is default-negated.
            Else a singleton set with a copy is returned.
        """
        if self.naf:
            return LiteralCollection()

        return LiteralCollection(
            PredLiteral(self.name, *self.terms.terms, neg=self.neg)
        )

    def neg_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Empty set if predicate literal is not default-negated.
            Else a singleton set with a non-default-negated copy is returned.
        """
        if not self.naf:
            return LiteralCollection()

        # NOTE: naf flag gets dropped
        return LiteralCollection(
            PredLiteral(self.name, *self.terms.terms, neg=self.neg)
        )

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the predicate literal.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of all terms.
        """  # noqa
        return set().union(self.terms.vars())

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> Tuple[SafetyTriplet, ...]:
        """Returns the the safety characterizations for the predicate literal.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for predicate literals. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance.
            If the predicate literal is default-negated, all variables are marked as unsafe.
            Else the closure of the safety characterizations of all individual terms is returned.
        """  # noqa
        return (
            SafetyTriplet.closure(*self.terms.safety())
            if not self.naf
            else SafetyTriplet(unsafe=self.vars())
        )

    def match(self: Self, other: "Expr") -> Optional[Substitution]:
        """Tries to match the predicate literal with an expression.

        Can only be matched to a predicate literal with same identifier where each
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if (
            isinstance(other, PredLiteral)
            and self.name == other.name
            and self.arity == other.arity
            and self.neg == other.neg
        ):
            return self.terms.match(other.terms)

        return None

    def substitute(self: Self, subst: Substitution) -> "PredLiteral":
        """Applies a substitution to the predicate literal.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `PredicateLiteral` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        return PredLiteral(
            self.name,
            *tuple((term.substitute(subst) for term in self.terms)),
            neg=self.neg,
            naf=self.naf,
        )

    def replace_arith(self: Self, var_table: "VariableTable") -> "PredLiteral":
        """Replaces arithmetic terms appearing in the predicate literal with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `PredLiteral` instance.
        """  # noqa
        return PredLiteral(
            self.name, *self.terms.replace_arith(var_table), neg=self.neg, naf=self.naf
        )

    def as_term(self: Self) -> Functional:
        """TODO"""
        return Functional(self.name, *self.terms)
