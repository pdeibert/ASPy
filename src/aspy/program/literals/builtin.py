from abc import ABC, abstractmethod
from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, Self, Set, Tuple, Union

from aspy.program.operators import RelOp
from aspy.program.safety_characterization import SafetyRule, SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithTerm, Number, TermTuple

from .literal import Literal, LiteralCollection

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.expression import Expr
    from aspy.program.query import Query
    from aspy.program.statements import Statement
    from aspy.program.terms import Term, Variable
    from aspy.program.variable_table import VariableTable


class BuiltinLiteral(Literal, ABC):
    """Abstract base class for all built-in literals.

    Declares some default as well as abstract methods for built-in literal.
    All built-in literals should inherit from this class or a subclass thereof.

    Attributes:
        operands: Tuple consisting of the left and right operands.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False` for built-in literals).
        ground: Boolean indicating whether or not the literal is ground.
    """

    def __init__(self: Self, loperand: "Term", roperand: "Term") -> None:
        """Initializes built-in literal instance.

        Args:
            loperand: `Term` instance representing the left operand
            roperand: `Term` instance representing the right operand.
        """
        # built-in literals are always positive
        super().__init__(naf=False)

        self.loperand = loperand
        self.roperand = roperand

    @cached_property
    def ground(self: Self) -> bool:
        return self.loperand.ground and self.roperand.ground

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Empty set (built-in literals are considered neither positive nor negative).
        """
        return LiteralCollection()

    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Empty set (built-in literals are considered neither positive nor negative).
        """
        return LiteralCollection()

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the built-in literal.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of both operands.
        """  # noqa
        return self.loperand.vars().union(self.roperand.vars())

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> SafetyTriplet:
        """Returns the the safety characterizations for the built-in literal.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance with all variables marked as unsafe.
        """  # noqa
        return SafetyTriplet(unsafe=self.vars())

    @property
    def operands(self: Self) -> Tuple["Term", "Term"]:
        return (self.loperand, self.roperand)

    @abstractmethod  # pragma: no cover
    def eval(self: Self) -> bool:
        """Evaluates the built-in literal.

        Returns:
            Boolean indicating whether or not the relational comparison holds.
        """  # noqa
        pass

    def replace_arith(self: Self, var_table: "VariableTable") -> "BuiltinLiteral":
        """Replaces arithmetic terms appearing in the operand(s).

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `BuiltinLiteral` instance.
        """
        return type(self)(
            self.loperand.replace_arith(var_table),
            self.roperand.replace_arith(var_table),
        )

    def substitute(self: Self, subst: Substitution) -> "Equal":
        """Applies a substitution to the built-in literals.

        Substitutes all operands recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `BuiltinLiteral` instance with (possibly substituted) operands.
        """
        if self.ground:
            return deepcopy(self)

        # substitute operands recursively
        operands = (operand.substitute(subst) for operand in self.operands)

        return type(self)(*operands)


class Equal(BuiltinLiteral):
    """Represents an equality comparison between terms.

    Attributes:
        operands: Tuple consisting of the left and right operands.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False` for built-in literals).
        ground: Boolean indicating whether or not the literal is ground.
    """

    def __str__(self: Self) -> str:
        """Returns the string representation for the built-in literal.

        Returns:
            String consisting of the string representations of the operands joined
            with the string representation of ther relational operator.
        """
        return f"{str(self.loperand)}={str(self.roperand)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the built-in literal to a given object.

        Considered equal if the given object is also an `Equal` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Equal)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("equal", self.loperand, self.roperand))

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> SafetyTriplet:
        """Returns the the safety characterizations for the built-in literal.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
            Irrelevant for built-in literals. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance as the normalization of the safety characterization with
            all variables marked as unsafe and safety rules for each variable as the depender
            and the set of variables from the opposing operand as dependees.
        """  # noqa
        # overrides inherited safety method

        # get variables
        lvars = self.loperand.vars()
        rvars = self.roperand.vars()

        lsafety = self.loperand.safety()
        rsafety = self.roperand.safety()

        rules = {SafetyRule(var, lvars.copy()) for var in rsafety.safe}.union(
            {SafetyRule(var, rvars.copy()) for var in lsafety.safe}
        )

        return SafetyTriplet(unsafe=lvars.union(rvars), rules=rules).normalize()

    def eval(self: Self) -> bool:
        """Evaluates the built-in literal w.r.t. the total ordering for terms.

        Requires both operands to be ground.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Returns:
            Boolean indicating whether or not the relational comparison holds.

        Raises:
            ValueError: Non-ground operands.
        """  # noqa
        if not (self.loperand.ground and self.roperand.ground):
            raise ValueError("Cannot evaluate built-in literal with non-ground terms")

        loperand = (
            Number(self.loperand.eval())
            if isinstance(self.loperand, ArithTerm)
            else self.loperand
        )
        roperand = (
            Number(self.roperand.eval())
            if isinstance(self.roperand, ArithTerm)
            else self.roperand
        )

        return loperand.precedes(roperand) and roperand.precedes(loperand)

    def match(self: Self, other: "Expr") -> Optional[Substitution]:
        """Tries to match the built-in literal with an expression.

        Can only be matched to an `Equal` instance with equal operands.
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if isinstance(other, Equal):
            return TermTuple(*self.operands).match(TermTuple(*other.operands))

        return None


class Unequal(BuiltinLiteral):
    """Represents an unequality comparison between terms.

    Attributes:
        operands: Tuple consisting of the left and right operands.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False` for built-in literals).
        ground: Boolean indicating whether or not the literal is ground.
    """

    def __str__(self: Self) -> str:
        """Returns the string representation for the built-in literal.

        Returns:
            String consisting of the string representations of the operands joined
            with the string representation of ther relational operator.
        """
        return f"{str(self.loperand)}!={str(self.roperand)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the built-in literal to a given object.

        Considered equal if the given object is also an `Unequal` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Unequal)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("unequal", self.loperand, self.roperand))

    def eval(self: Self) -> bool:
        """Evaluates the built-in literal w.r.t. the total ordering for terms.

        Requires both operands to be ground.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Returns:
            Boolean indicating whether or not the relational comparison holds.

        Raises:
            ValueError: Non-ground operands.
        """  # noqa
        if not (self.loperand.ground and self.roperand.ground):
            raise ValueError("Cannot evaluate built-in literal with non-ground terms")

        loperand = (
            Number(self.loperand.eval())
            if isinstance(self.loperand, ArithTerm)
            else self.loperand
        )
        roperand = (
            Number(self.roperand.eval())
            if isinstance(self.roperand, ArithTerm)
            else self.roperand
        )

        return not (loperand.precedes(roperand) and roperand.precedes(loperand))

    def match(self: Self, other: "Expr") -> Set[Substitution]:
        """Tries to match the built-in literal with an expression.

        Can only be matched to an `Equal` instance with equal operands.
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if isinstance(other, Unequal):
            return TermTuple(*self.operands).match(TermTuple(*other.operands))

        return None


class Less(BuiltinLiteral):
    """Represents a less-than comparison between terms.

    Attributes:
        operands: Tuple consisting of the left and right operands.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False` for built-in literals).
        ground: Boolean indicating whether or not the literal is ground.
    """

    def __str__(self: Self) -> str:
        """Returns the string representation for the built-in literal.

        Returns:
            String consisting of the string representations of the operands joined
            with the string representation of ther relational operator.
        """
        return f"{str(self.loperand)}<{str(self.roperand)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the built-in literal to a given object.

        Considered equal if the given object is also an `Less` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Less)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("less", self.loperand, self.roperand))

    def eval(self: Self) -> bool:
        """Evaluates the built-in literal w.r.t. the total ordering for terms.

        Requires both operands to be ground.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Returns:
            Boolean indicating whether or not the relational comparison holds.

        Raises:
            ValueError: Non-ground operands.
        """  # noqa
        if not (self.loperand.ground and self.roperand.ground):
            raise ValueError("Cannot evaluate built-in literal with non-ground terms")

        loperand = (
            Number(self.loperand.eval())
            if isinstance(self.loperand, ArithTerm)
            else self.loperand
        )
        roperand = (
            Number(self.roperand.eval())
            if isinstance(self.roperand, ArithTerm)
            else self.roperand
        )

        return loperand.precedes(roperand) and not roperand.precedes(loperand)

    def match(self: Self, other: "Expr") -> Set[Substitution]:
        """Tries to match the built-in literal with an expression.

        Can only be matched to an `Equal` instance with equal operands.
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if isinstance(other, Less):
            return TermTuple(*self.operands).match(TermTuple(*other.operands))

        return None


class Greater(BuiltinLiteral):
    """Represents a greater-than comparison between terms.

    Attributes:
        operands: Tuple consisting of the left and right operands.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False` for built-in literals).
        ground: Boolean indicating whether or not the literal is ground.
    """

    def __str__(self: Self) -> str:
        """Returns the string representation for the built-in literal.

        Returns:
            String consisting of the string representations of the operands joined
            with the string representation of ther relational operator.
        """
        return f"{str(self.loperand)}>{str(self.roperand)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the built-in literal to a given object.

        Considered equal if the given object is also an `Greater` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Greater)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("greater", self.loperand, self.roperand))

    def eval(self: Self) -> bool:
        """Evaluates the built-in literal w.r.t. the total ordering for terms.

        Requires both operands to be ground.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Returns:
            Boolean indicating whether or not the relational comparison holds.

        Raises:
            ValueError: Non-ground operands.
        """  # noqa
        if not (self.loperand.ground and self.roperand.ground):
            raise ValueError("Cannot evaluate built-in literal with non-ground terms")

        loperand = (
            Number(self.loperand.eval())
            if isinstance(self.loperand, ArithTerm)
            else self.loperand
        )
        roperand = (
            Number(self.roperand.eval())
            if isinstance(self.roperand, ArithTerm)
            else self.roperand
        )

        return not loperand.precedes(roperand) and roperand.precedes(loperand)

    def match(self: Self, other: "Expr") -> Set[Substitution]:
        """Tries to match the built-in literal with an expression.

        Can only be matched to an `Equal` instance with equal operands.
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if isinstance(other, Greater):
            return TermTuple(*self.operands).match(TermTuple(*other.operands))

        return None


class LessEqual(BuiltinLiteral):
    """Represents a less-than-or-equal-to comparison between terms.

    Attributes:
        operands: Tuple consisting of the left and right operands.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False` for built-in literals).
        ground: Boolean indicating whether or not the literal is ground.
    """

    def __str__(self: Self) -> str:
        """Returns the string representation for the built-in literal.

        Returns:
            String consisting of the string representations of the operands joined
            with the string representation of ther relational operator.
        """
        return f"{str(self.loperand)}<={str(self.roperand)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the built-in literal to a given object.

        Considered equal if the given object is also an `LessEqual` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, LessEqual)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("less equal", self.loperand, self.roperand))

    def eval(self: Self) -> bool:
        """Evaluates the built-in literal w.r.t. the total ordering for terms.

        Requires both operands to be ground.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Returns:
            Boolean indicating whether or not the relational comparison holds.

        Raises:
            ValueError: Non-ground operands.
        """  # noqa
        if not (self.loperand.ground and self.roperand.ground):
            raise ValueError("Cannot evaluate built-in literal with non-ground terms")

        loperand = (
            Number(self.loperand.eval())
            if isinstance(self.loperand, ArithTerm)
            else self.loperand
        )
        roperand = (
            Number(self.roperand.eval())
            if isinstance(self.roperand, ArithTerm)
            else self.roperand
        )

        return loperand.precedes(roperand)

    def match(self: Self, other: "Expr") -> Set[Substitution]:
        """Tries to match the built-in literal with an expression.

        Can only be matched to an `Equal` instance with equal operands.
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if isinstance(other, LessEqual):
            return TermTuple(*self.operands).match(TermTuple(*other.operands))

        return None


class GreaterEqual(BuiltinLiteral):
    """Represents a greater-than-or-equal-to comparison between terms.

    Attributes:
        operands: Tuple consisting of the left and right operands.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False` for built-in literals).
        ground: Boolean indicating whether or not the literal is ground.
    """

    def __str__(self: Self) -> str:
        """Returns the string representation for the built-in literal.

        Returns:
            String consisting of the string representations of the operands joined
            with the string representation of ther relational operator.
        """
        return f"{str(self.loperand)}>={str(self.roperand)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the built-in literal to a given object.

        Considered equal if the given object is also an `GreaterEqual` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, GreaterEqual)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("greater equal", self.loperand, self.roperand))

    def eval(self: Self) -> bool:
        """Evaluates the built-in literal w.r.t. the total ordering for terms.

        Requires both operands to be ground.
        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Returns:
            Boolean indicating whether or not the relational comparison holds.

        Raises:
            ValueError: Non-ground operands.
        """  # noqa
        if not (self.loperand.ground and self.roperand.ground):
            raise ValueError("Cannot evaluate built-in literal with non-ground terms")

        loperand = (
            Number(self.loperand.eval())
            if isinstance(self.loperand, ArithTerm)
            else self.loperand
        )
        roperand = (
            Number(self.roperand.eval())
            if isinstance(self.roperand, ArithTerm)
            else self.roperand
        )

        return roperand.precedes(loperand)

    def match(self: Self, other: "Expr") -> Set[Substitution]:
        """Tries to match the built-in literal with an expression.

        Can only be matched to an `Equal` instance with equal operands.
        corresponding term can be matched without any assignment conflicts.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if isinstance(other, GreaterEqual):
            return TermTuple(*self.operands).match(TermTuple(*other.operands))

        return None


# maps relational operators to their corresponding AST constructs
op2rel = {
    RelOp.EQUAL: Equal,
    RelOp.UNEQUAL: Unequal,
    RelOp.LESS: Less,
    RelOp.GREATER: Greater,
    RelOp.LESS_OR_EQ: LessEqual,
    RelOp.GREATER_OR_EQ: GreaterEqual,
}
