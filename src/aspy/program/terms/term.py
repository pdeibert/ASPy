from abc import ABC, abstractmethod
from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Iterable, Optional, Self, Set, Tuple, Union

import aspy
from aspy.program.expression import Expr
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import AssignmentError, Substitution
from aspy.program.symbols import SYM_CONST_RE, VARIABLE_RE

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.query import Query
    from aspy.program.statements import Statement
    from aspy.program.variable_table import VariableTable


class Term(Expr, ABC):
    """Abstract base class for all terms.

    Declares some default as well as abstract methods for terms.
    All terms should inherit from this class or a subclass thereof.
    """

    @abstractmethod  # pragma: no cover
    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term to a given object.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        pass

    @abstractmethod  # pragma: no cover
    def precedes(self: Self, other: "Term") -> bool:
        """Checks precendence of w.r.t. a given term.

        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Args:
            other: `Term` instance.

        Returns:
            Boolean value indicating whether or not the term precedes the given term.
        """  # noqa
        pass

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the term.

        Returns:
            Empty set of `Variable` instances.
        """
        return set()

    def global_vars(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the term.

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Usually irrelevant for terms. Defaults to `None`.

        Returns:
            A (possibly empty) set of `Variable` instances.
        """
        return self.vars()

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> SafetyTriplet:
        """Returns the safety characterization for the term.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Usually irrelevant for terms. Defaults to `None`.

        Returns:
            Empty `SafetyTriplet` instance.
        """  # noqa
        return SafetyTriplet()

    def replace_arith(self: Self, var_table: "VariableTable") -> "Term":
        """Replaces arithmetic terms appearing in the term with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `Term` instance.
        """
        return deepcopy(self)

    def substitute(self: Self, subst: Substitution) -> "Term":
        """Applies a substitution to the term.

        Replaces all variables with their substitution terms.

        Args:
            subst: `Substitution` instance.

        Returns:
            (Possibly substituted) `Term` instance.
        """
        return deepcopy(self)

    def match(self: Self, other: "Expr") -> Optional[Substitution]:
        """Tries to match the expression with another one.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching, if the expression can be matched (may be empty).
            `None` if the expression cannot be matched.
        """  # noqa
        # empty substitution
        return Substitution() if self == other else None


class Infimum(Term):
    """Least element in the total ordering for terms.

    Attributes:
        ground: Boolean indicating whether or not the term is ground (always `True`).
    """

    ground: bool = True

    def __str__(self: Self) -> str:
        """Returns the string representation for an infimum.

        Returns:
            String `"#inf"`.
        """
        return "#inf"

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Infimum` instance.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return isinstance(other, Infimum)

    def __hash__(self: Self) -> int:
        return hash(("inf",))

    def precedes(self: Self, other: Term) -> bool:
        """Checks precendence of w.r.t. a given term.

        As the least element in the total ordering for terms, `Infimum` precedes any term.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Args:
            other: `Term` instance.

        Returns:
            Boolean value (always `True`).
        """  # noqa
        return True


class Supremum(Term):
    """Greatest element in the total ordering for terms.

    Attributes:
        ground: Boolean indicating whether or not the term is ground (always `True`).
    """

    ground: bool = True

    def __str__(self: Self) -> str:
        """Returns the string representation for a supremum.

        Returns:
            String `"#sup"`.
        """
        return "#sup"

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Supremum` instance.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return isinstance(other, Supremum)

    def __hash__(self: Self) -> int:
        return hash(("sup",))

    def precedes(self: Self, other: Term) -> bool:
        """Checks precendence of w.r.t. a given term.

        As the greatest element in the total ordering for terms, `Supremum` precedes only itself.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Args:
            other: `Term` instance.

        Returns:
            Boolean value indicating whether or not the term precedes the given term.
        """  # noqa
        return True if isinstance(other, Supremum) else False


class Variable(Term):
    """Represents a variable.

    Attributes:
        val: String representing the identifier for the variable.
        ground: Boolean indicating whether or not the term is ground (always `False`).
    """

    ground: bool = False

    def __init__(self: Self, val: str) -> None:
        """Initializes the variable instance.

        Args:
            val: String representing the identifier for the variable.
                Valid identifiers start with an upper-case latin letter, followed by zero or more alphanumerics and underscores.

        Raises:
            ValueError: Invalid value specified for the variable. Only checked if `aspy.debug()` returns `True`.
        """  # noqa
        # check if variable name is valid
        if aspy.debug() and not (isinstance(val, str) and VARIABLE_RE.fullmatch(val)):
            raise ValueError(f"Invalid value for {type(self)}: {val}")

        self.val = val

    def __str__(self: Self) -> str:
        """Returns the string representation for a variable.

        Returns:
            String representing the value (i.e., identifier) of the variable.
        """
        return self.val

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Variable` instance with same value.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return isinstance(other, Variable) and other.val == self.val

    def __hash__(self: Self) -> int:
        return hash(("var", self.val))

    def precedes(self: Self, other: Term) -> bool:
        """Checks precendence w.r.t. a given term.

        Undefined for variables (i.e., non-ground terms). Raises an exception.

        Args:
            other: `Term` instance.

        Raises:
            Exception: Total order is undefined for variables.
        """  # noqa
        raise Exception("Total ordering is undefined for non-ground terms.")

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the term.

        Returns:
            Singleton set containing the `Variable` instance itself.
        """
        return {self}

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> SafetyTriplet:
        """Returns the safety characterization for a variable.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for variables. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance with the `Variable` instance marked as 'safe'.
        """  # noqa
        return SafetyTriplet({self})

    def simplify(self: Self) -> "Variable":
        """Simplifies the variable as part of an arithmetic term.

        Used in arithmetic terms. Returns a copy of itself, as variables cannot be simplified.

        Returns:
            Copy of the `Variable` instance.
        """  # noqa
        return Variable(self.val)

    def match(self: Self, other: "Expr") -> Optional[Substitution]:
        """Tries to match the expression with another one.

        Variables can be matched to any expression.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty).
        """  # noqa
        return Substitution({self: other}) if not self == other else Substitution()

    def substitute(self: Self, subst: Substitution) -> Term:
        """Applies a substitution to the term.

        Replaces the variable with its substitution term.

        Args:
            subst: `Substitution` instance.

        Returns:
            (Possibly substituted) `Term` instance.
        """
        return subst[self]


class AnonVariable(Variable):
    """Represents an anonymous variable.

    Attributes:
        val: String representing the identifier for the anonymous variable.
        id: Integer representing the id for the anonymous variable.
        ground: Boolean indicating whether or not the term is ground (always `False`).
    """

    def __init__(self: Self, id: int) -> None:
        """Initializes the anonymous variable instance.

        The variable identifier is initialized as `"_{id}"`.

        Args:
            id: Non-negative integer representing the id for the anonymous variable.
                Should be unique within each statement or query.

        Raises:
            ValueError: Negative id specified for the variable. Only checked if `aspy.debug()` returns `True`.
        """  # noqa
        # check if id is valid
        if aspy.debug() and id < 0:
            raise ValueError(f"Invalid value for {type(self)}: {id}")

        self.val = f"_{id}"
        self.id = id

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `AnonVariable` instance with same id (i.e., value).

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, AnonVariable)
            and other.val == self.val
            and other.id == self.id
        )

    def __hash__(self: Self) -> int:
        return hash(("anon var", self.val))

    def simplify(self: Self) -> "AnonVariable":
        """Simplifies the variable as part of an arithmetic term.

        Used in arithmetic terms. Returns a copy of itself, as variables cannot be simplified.

        Returns:
            Copy of the `AnonVariable` instance.
        """  # noqa
        return AnonVariable(self.id)


class Number(Term):
    """Represents a number.

    Attributes:
        val: Integer representing the value of the number.
        ground: Boolean indicating whether or not the term is ground (always `True`).
    """

    ground: bool = True

    def __init__(self: Self, val: int) -> None:
        """Initializes the number instance.

        Args:
            val: Integer representing the value of the number.
        """
        self.val = val

    def __add__(self: Self, other: "Number") -> "Number":
        """Returns a number representing the sum of this and a given number.

        Args:
            other: `Number` instance to be added.

        Returns:
            `Number` instance representing the sum of this and the given number.
        """
        return Number(self.val + other.val)

    def __sub__(self: Self, other: "Number") -> "Number":
        """Returns a number representing the difference of this and a given number.

        Args:
            other: `Number` instance to be subtracted.

        Returns:
            `Number` instance representing the difference of this and the given number.
        """
        return Number(self.val - other.val)

    def __mul__(self: Self, other: "Number") -> "Number":
        """Returns a number representing the product of this and a given number.

        Args:
            other: `Number` instance to be multiplied by.

        Returns:
            `Number` instance representing the product of this and the given number.
        """
        return Number(self.val * other.val)

    def __floordiv__(self: Self, other: "Number") -> "Number":
        """Returns a number representing the integer division of this and a given number.

        Args:
            other: `Number` instance to be divided by.

        Returns:
            `Number` instance representing the integer division of this and the given number.
        """  # noqa
        return Number(self.val // other.val)

    def __neg__(self: Self) -> "Number":
        """Returns the negation of the number.

        Returns:
            `Number` instance representing the negation of the number.
        """  # noqa
        return Number(-self.val)

    def __abs__(self: Self) -> "Number":
        """Returns the absolute number.

        Returns:
            `Number` instance representing the absolute number.
        """  # noqa
        return Number(abs(self.val))

    def __str__(self: Self) -> str:
        """Returns the string representation for a number.

        Returns:
            String representing the integer value of the number.
        """
        return str(self.val)

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Number` instance with same integer value.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return isinstance(other, Number) and other.val == self.val

    def __hash__(self: Self) -> int:
        return hash(("num", self.val))

    def precedes(self: Self, other: Term) -> bool:
        """Checks precendence of w.r.t. a given term.

        A number is preceded by `Infimum` and all `Number` instances with smaller or equal integer value.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Args:
            other: `Term` instance.

        Raises:
            ValueError: Comparison with non-ground arithmetic term or variable.

        Returns:
            Boolean value indicating whether or not the term precedes the given term.
        """  # noqa
        if not other.ground:
            raise ValueError(
                (
                    "Cannot compare total ordering with non-ground"
                    " arithmetic terms or variables"
                )
            )

        if isinstance(other, Infimum):
            return False
        elif isinstance(other, Number):
            return self.val <= other.val
        else:
            return True

    def simplify(self: Self) -> "Number":
        """Simplifies the variable as part of an arithmetic term.

        Used in arithmetic terms. Returns a copy of itself, as numbers cannot be further simplified.

        Returns:
            Copy of the `Number` instance.
        """  # noqa
        return Number(self.val)

    def eval(self: Self) -> int:
        """Evaluates the number.

        Returns:
            Integer value of the number.
        """
        return self.val


class SymbolicConstant(Term):
    """Represents a symbolic constant.

    Attributes:
        val: String representing the identifier for the symbolic constant.
        ground: Boolean indicating whether or not the term is ground (always `True`).
    """

    ground: bool = True

    def __init__(self: Self, val: str) -> None:
        """Initializes the symbolic constant instance.

        Args:
            val: String representing the identifier for the symbolic constant.
                Valid identifiers start with a lower-case latin letter, followed by zero or more alphanumerics and underscores.
                Instead of a single lower-case latin letter, identifiers may also start with '\u03b1', '\u03C7', '\u03b5\u03b1',
                '\u03b5\u03C7', '\u03b7\u03b1', or '\u03b7\u03C7', but are reserved for internal use.

        Raises:
            ValueError: Invalid value specified for the symbolic constant. Only checked if `aspy.debug()` returns `True`.
        """  # noqa
        # check if symbolic constant name is valid
        if aspy.debug() and not SYM_CONST_RE.fullmatch(val):  # TODO: alpha, eta, eps?
            raise ValueError(f"Invalid value for {type(self)}: {val}")

        self.val = val

    def __str__(self: Self) -> str:
        """Returns the string representation for a symbolic constant.

        Returns:
            String representing the identifier of the symbolic constant.
        """
        return self.val

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `SymbolicConstant` instance with same identifier value.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return isinstance(other, SymbolicConstant) and other.val == self.val

    def __hash__(self: Self) -> int:
        return hash(("symbolic const", self.val))

    def precedes(self: Self, other: Term) -> bool:
        """Checks precendence of w.r.t. a given term.

        A symbolic constant is preceded by `Infimum`, `Number` instances,
        and all `SymbolicConstant` instances with lexicographically smaller or equal identifier values.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Args:
            other: `Term` instance.

        Raises:
            ValueError: Comparison with non-ground arithmetic term or variable.

        Returns:
            Boolean value indicating whether or not the term precedes the given term.
        """  # noqa
        if not other.ground:
            raise ValueError(
                (
                    "Cannot compare total ordering with non-ground"
                    " arithmetic terms or variables"
                )
            )

        if isinstance(other, (Infimum, Number)):
            return False
        elif isinstance(other, SymbolicConstant):
            return self.val <= other.val
        else:
            return True


class String(Term):
    """Represents a string.

    Attributes:
        val: String representing the string value.
        ground: Boolean indicating whether or not the term is ground (always `True`).
    """

    ground: bool = True

    def __init__(self: Self, val: str) -> None:
        """Initializes the string instance.

        Args:
            val: String representing the string value.
        """
        self.val = val

    def __str__(self: Self) -> str:
        """Returns the string representation for a string.

        Returns:
            String representing the string value enclosed in double quotes.
        """
        return f'"{self.val}"'

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term to a given object.

        Considered equal if the given object is also a `String` instance with same value.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return isinstance(other, String) and other.val == self.val

    def __hash__(self: Self) -> int:
        return hash(("str", self.val))

    def precedes(self: Self, other: Term) -> bool:
        """Checks precendence of w.r.t. a given term.

        A string is preceded by all (ground) terms except `Supremum` and all `String` instances with lexicographically greater identifier values.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Args:
            other: `Term` instance.

        Raises:
            ValueError: Comparison with non-ground arithmetic term or variable.

        Returns:
            Boolean value indicating whether or not the term precedes the given term.
        """  # noqa
        if not other.ground:
            raise ValueError(
                (
                    "Cannot compare total ordering with non-ground"
                    " arithmetic terms or variables"
                )
            )

        if isinstance(other, (Infimum, Number, SymbolicConstant)):
            return False
        elif isinstance(other, String):
            return self.val <= other.val
        else:
            return True


class TermTuple:
    """Represents an ordered collection of terms.

    Attributes:
        terms: Tuple of `Term` instances.
        ground: Boolean indicating whether or not all terms are ground.
    """

    def __init__(self: Self, *terms: Term) -> None:
        """Initializes the term tuple instance.

        Args:
            *terms: sequence of terms.
        """
        self.terms = terms

    def __len__(self: Self) -> int:
        return len(self.terms)

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term tuple to another given term tuple.

        Considered equal if the given object is also a `TermTuple` instance and contains
        the same terms in the exact same order.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term tuple is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, TermTuple)
            and len(self) == len(other)
            and all(t1 == t2 for t1, t2 in zip(self, other))
        )

    def __hash__(self: Self) -> int:
        return hash(("term tuple", *self.terms))

    def __str__(self: Self) -> str:
        """TODO"""
        return ",".join(tuple(str(term) for term in self.terms))

    def __iter__(self: Self) -> Iterable[Term]:
        return iter(self.terms)

    def __add__(self: Self, other: "TermTuple") -> "TermTuple":
        """Concatenates another given term tuple.

        Args:
            other: `TermTuple` instance to be concatenated.

        Returns:
            `TermTuple` instance representing the concatenated term tuples.
        """
        return TermTuple(*self.terms, *other.terms)

    def __getitem__(self: Self, index: int) -> "Term":
        return self.terms[index]

    @cached_property
    def ground(self: Self) -> bool:
        return all(term.ground for term in self.terms)

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the term tuple.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of all terms.
        """  # noqa
        return set().union(*tuple(term.vars() for term in self.terms))

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the term tuple.

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Usually irrelevant for terms. Defaults to `None`.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the (global) variables of all terms.
        """  # noqa
        return self.vars()

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> Tuple["SafetyTriplet", ...]:
        """Returns the safety characterizations for all individual terms.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for terms. Defaults to `None`.

        Returns:
            Tuple of `SafetyTriplet` instances corresponding to the individual terms.
        """  # noqa
        return tuple(term.safety(statement) for term in self.terms)

    def replace_arith(self: Self, var_table: "VariableTable") -> "TermTuple":
        """Replaces arithmetic terms appearing in the term tuple with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `TermTuple` instance.
        """  # noqa
        return TermTuple(*tuple(term.replace_arith(var_table) for term in self.terms))

    @cached_property
    def weight(self: Self) -> int:
        """Returns the weight of the term tuple.

        Returns:
            Integer representing the value of the first term if it is a `Number` instance, and zero else.
        """  # noqa
        if len(self.terms) > 0 and isinstance(self.terms[0], Number):
            return self.terms[0].val

        return 0

    @cached_property
    def pos_weight(self: Self) -> int:
        """Returns the positive weight of the term tuple.

        Returns:
            Integer representing the value of the first term if it is a positive `Number` instance, and zero else.
        """  # noqa
        if len(self.terms) > 0 and isinstance(self.terms[0], Number):
            return max(self.terms[0].val, 0)

        return 0

    @cached_property
    def neg_weight(self: Self) -> int:
        """Returns the negative weight of the term tuple.

        Returns:
            Integer representing the value of the first term if it is a negative `Number` instance, and zero else.
        """  # noqa"
        if len(self.terms) > 0 and isinstance(self.terms[0], Number):
            return min(self.terms[0].val, 0)

        return 0

    def match(self: Self, other: "Expr") -> Optional[Substitution]:
        """Tries to match the term tuple with an expression.

        Can only be matched to a term tuple where each corresponding term can be matched
        without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if not (isinstance(other, TermTuple) and len(self) == len(other)):
            return None

        subst = Substitution()

        for term1, term2 in zip(self.terms, other.terms):
            match = term1.match(term2)

            if match is None:
                return None

            try:
                subst = subst + match
            except AssignmentError:
                return None

        return subst

    def substitute(self: Self, subst: "Substitution") -> "TermTuple":
        """Applies a substitution to the term tuple.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `TermTuple` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        terms = (term.substitute(subst) for term in self)

        return TermTuple(*terms)
