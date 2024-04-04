from abc import ABC, abstractmethod
from copy import deepcopy
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, Self, Set, Tuple, Union

from aspy.program.operators import ArithOp
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.symbols import SpecialChar

from .special import ArithVariable
from .term import Number, Term, Variable

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.expression import Expr
    from aspy.program.query import Query
    from aspy.program.statements import Statement
    from aspy.program.variable_table import VariableTable


class ArithTerm(Term, ABC):
    """Abstract base class for all arithmetic terms.

    Declares some default as well as abstract methods for terms. All terms should inherit from this class or a subclass thereof.

    Attributes:
        ground: Boolean indicating whether or not all operands are ground.
        operands: Tuple consisting of the left and right operands.
    """  # noqa

    def precedes(self: Self, other: Term) -> bool:
        """Checks precendence of w.r.t. a given term.

        To compute precedence, the arithmetic term is evaluated first.
        The arithmetic term must therefore be ground.

        For details see https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03c.pdf.

        Args:
            other: `Term` instance.

        Returns:
            Boolean value indicating whether or not the term precedes the given term.

        Raises:
            ValueError: Arithmetic term is not ground.
        """  # noqa
        if not self.ground:
            raise ValueError(
                "Total order is not defined for non-ground arithmetic terms."
            )

        return Number(self.eval()).precedes(other)

    @abstractmethod  # pragma: no cover
    def simplify(self: Self) -> Union["ArithTerm", "Number", "Variable"]:
        """Simplifies the arithmetic term.

        Returns:
            `ArithTerm`, `Number` or `Variable` instance.
        """  # noqa
        pass

    @abstractmethod  # pragma: no cover
    def eval(self) -> int:
        """Evaluates the arithmetic term.

        Returns:
            Integer value representing the result of the arithmetic operation.
        """  # noqa
        pass

    @property
    def operands(self: Self) -> Tuple[Term, Term]:
        return (self.loperand, self.roperand)

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the arithmetic term.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of all operands.
        """  # noqa
        return set().union(*tuple(operand.vars() for operand in self.operands))

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> SafetyTriplet:
        """Returns the the safety characterizations for the arithmetic term.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for terms. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance with all variables marked as unsafe.
        """  # noqa
        return SafetyTriplet(
            unsafe=set().union(*tuple(operand.vars() for operand in self.operands))
        )

    def replace_arith(
        self: Self, var_table: "VariableTable"
    ) -> Union["ArithTerm", ArithVariable, "Number", "Variable"]:
        """Replaces arithmetic terms appearing in the operand(s).

        Note: arithmetic terms are not replaced in-place.
        Also, all arithmetic terms are simplified in the process.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `ArithVariable` instance if the term is not ground.
            A `ArithTerm`, `Number`, or "Variable" instance as the simplification of the term, otherwise.
        """  # noqa
        # replace ground arithmetic term with its value
        if self.ground:
            return self.simplify()

        # replace non-ground arithmetic term with a new special variable
        return var_table.create(SpecialChar.TAU.value, orig_term=self, register=False)

    def match(self: Self, other: "Expr") -> Optional["Substitution"]:
        """Tries to match the term tuple with an expression.

        Can only be matched with a ground arithmetic term or a number.
        For matching, ground arithmetic terms are simplified first.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            A substitution necessary for matching (may be empty) or `None` if cannot be matched.
        """  # noqa
        if not (self.ground and other.ground):
            raise ValueError("Cannot match non-groun arithmetic terms directly.")

        if isinstance(other, ArithTerm):
            # returns a 'Number' instance since 'other' is ground
            other = other.simplify()

        if not self.simplify() == other:
            return None

        return Substitution()

    def substitute(self: Self, subst: "Substitution") -> "ArithTerm":
        """Applies a substitution to the term term tuple.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `TermTuple` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        # substitute operands recursively
        operands = (operand.substitute(subst) for operand in self.operands)

        return type(self)(*operands).simplify()


class Minus(ArithTerm):
    """Represents a negation of an arithmetic term.

    Attributes:
        ground: Boolean indicating whether or not the operand is ground.
        operand: `ArithTerm` instance representing the operand.
        operands: Tuple consisting of the (single) operand.
    """

    def __init__(self: Self, operand: Union[ArithTerm, Number, "Variable"]) -> None:
        """Initializes the arithmetic term.

        Args:
            operand: `ArithTerm`, `Number`, or `Variable` instance.
        """  # noqa
        self.operand = operand

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Minus` instance with same operand.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return isinstance(other, Minus) and self.operand == other.operand

    def __hash__(self: Self) -> int:
        return hash(("minus", self.operand))

    def __str__(self: Self) -> str:
        """Returns the string representation for the arithmetic term.

        Returns:
            String representation of the operand prefixed with a '-'.
            If the operand is a `ArithTerm` instance, the operand string is additionally enclosed in parentheses.
        """  # noqa
        operand_str = (
            f"({str(self.operand)})"
            if isinstance(self.operand, ArithTerm)
            else str(self.operand)
        )

        return f"-{operand_str}"

    @cached_property
    def ground(self: Self) -> bool:
        return self.operand.ground

    @property
    def operands(self: Self) -> Tuple[Term]:
        return (self.operand,)

    def eval(self: Self) -> int:
        """Evaluates the arithmetic term.

        Operands must be ground to perform evaluation.

        Returns:
            Integer value representing the negation of the operand value.

        Raises:
            ValueError: Operand is not ground.
        """  # noqa
        if not self.ground:
            raise ValueError("Cannot evaluate non-ground arithmetic term.")

        return -self.operand.eval()

    def simplify(self: Self) -> Union["ArithTerm", "Number", "Variable"]:
        """Simplifies the arithmetic term.

        First the operand is simplified.
        If the (simplified) operand is a `Number`, simplifies to a new `Number` instance with negative value.
        If the (simplified) operand is a `Minus`, simplifies the operand of the operand itself (double negation).
        Else a `Minus` instance with (simplified) operand is returned (cannot be further simplified).

        Returns:
            `ArithTerm`, `Number` or `Variable` instance.
        """  # noqa
        # simplify operand
        operand = self.operand.simplify()

        # simplified operand is a number
        if isinstance(operand, Number):
            return Number(-operand.val)
        # two negatives cancel each other out
        elif isinstance(operand, Minus):
            return operand.operand
        else:
            return Minus(operand)


class Add(ArithTerm):
    """Represents an addition of arithmetic terms.

    Attributes:
        ground: Boolean indicating whether or not all operands are ground.
        loperand: `ArithTerm` instance representing the left operand.
        roperand: `ArithTerm` instance representing the right operand.
        operands: Tuple consisting of the left and right operands.
    """

    def __init__(
        self: Self,
        loperand: Union[ArithTerm, Number, "Variable"],
        roperand: Union[ArithTerm, Number, "Variable"],
    ) -> None:
        """Initializes the arithmetic term.

        Args:
            loperand: `ArithTerm`, `Number`, or `Variable` instance.
            roperand: `ArithTerm`, `Number`, or `Variable` instance.
        """  # noqa
        self.loperand = loperand
        self.roperand = roperand

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term to a given object.

        Considered equal if the given object is also an `Add` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Add)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("add", self.loperand, self.roperand))

    def __str__(self: Self) -> str:
        """Returns the string representation for the arithmetic term.

        Returns:
            String representations of the operands joined with '+'.
            If an operand is a `ArithTerm` instance, its string is additionally enclosed in parentheses.
        """  # noqa
        loperand_str = (
            f"({str(self.loperand)})"
            if isinstance(self.loperand, ArithTerm)
            else str(self.loperand)
        )
        roperand_str = (
            f"({str(self.roperand)})"
            if isinstance(self.roperand, ArithTerm)
            else str(self.roperand)
        )

        return f"{loperand_str}+{roperand_str}"

    @cached_property
    def ground(self: Self) -> bool:
        return self.loperand.ground and self.roperand.ground

    def eval(self: Self) -> int:
        """Evaluates the arithmetic term.

        Operands must be ground to perform evaluation.

        Returns:
            Integer value representing the sum of the operand values.

        Raises:
            ValueError: Operands are not ground.
        """  # noqa
        if not self.ground:
            raise ValueError("Cannot evaluate non-ground arithmetic term.")

        return self.loperand.eval() + self.roperand.eval()

    def simplify(self: Self) -> Union[ArithTerm, "Number", "Variable"]:
        """Simplifies the arithmetic term.

        First the operands are simplified.
        If both (simplified) operands are `Number` instances, simplifies to a new `Number` instance representing the sum of both numbers.
        If some (simplified) operand is a `Number` equal to zero, simplifies to the other (simplified) operand.
        Else an `Add` instance with (simplified) operands is returned (cannot be further simplified).

        Returns:
            `ArithTerm`, `Number` or `Variable` instance.
        """  # noqa

        # simplify operands
        loperand = self.loperand.simplify()
        roperand = self.roperand.simplify()

        # if both operands can be simplified to numbers, add them
        if isinstance(loperand, Number) and isinstance(roperand, Number):
            return Number(loperand.val + roperand.val)
        # only left operand is a number
        elif isinstance(loperand, Number):
            # left operand does not add anything
            if loperand.val == 0:
                return roperand
        # only right operand is a number
        elif isinstance(roperand, Number):
            # right operand does not add anything
            if roperand.val == 0:
                return loperand

        # else return an instance of a simplified addition
        return Add(loperand, roperand)


class Sub(ArithTerm):
    """Represents a subtraction of arithmetic terms.

    Attributes:
        ground: Boolean indicating whether or not all operands are ground.
        loperand: `ArithTerm` instance representing the left operand.
        roperand: `ArithTerm` instance representing the right operand.
        operands: Tuple consisting of the left and right operands.
    """

    def __init__(
        self: Self,
        loperand: Union[ArithTerm, Number, "Variable"],
        roperand: Union[ArithTerm, Number, "Variable"],
    ) -> None:
        """Initializes the arithmetic term.

        Args:
            loperand: `ArithTerm`, `Number`, or `Variable` instance.
            roperand: `ArithTerm`, `Number`, or `Variable` instance.
        """  # noqa
        self.loperand = loperand
        self.roperand = roperand

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Sub` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Sub)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("sub", self.loperand, self.roperand))

    def __str__(self: Self) -> str:
        """Returns the string representation for the arithmetic term.

        Returns:
            String representations of the operands joined with '-'.
            If an operand is a `ArithTerm` instance, its string is additionally enclosed in parentheses.
        """  # noqa
        loperand_str = (
            f"({str(self.loperand)})"
            if isinstance(self.loperand, ArithTerm)
            else str(self.loperand)
        )
        roperand_str = (
            f"({str(self.roperand)})"
            if isinstance(self.roperand, ArithTerm)
            else str(self.roperand)
        )

        return f"{loperand_str}-{roperand_str}"

    @cached_property
    def ground(self: Self) -> bool:
        return self.loperand.ground and self.roperand.ground

    def eval(self: Self) -> int:
        """Evaluates the arithmetic term.

        Operands must be ground to perform evaluation.

        Returns:
            Integer value representing the difference of the operand values.

        Raises:
            ValueError: Operands are not ground.
        """  # noqa
        if not self.ground:
            raise ValueError("Cannot evaluate non-ground arithmetic term.")

        return self.loperand.eval() - self.roperand.eval()

    def simplify(self: Self) -> Union["ArithTerm", Number, "Variable"]:
        """Simplifies the arithmetic term.

        First the operands are simplified.
        If both (simplified) operands are `Number` instances, simplifies to a new `Number` instance representing the difference of both numbers.
        If the left (simplified) operand is a `Number` equal to zero, simplifies to a `Minus` instance with the right (simplified) operand as operand.
        If the right (simplified) operand is a `Number` equal to zero, simplifies to the right (simplified) operand.
        Else a `Sub` instance with (simplified) operands is returned (cannot be further simplified).

        Returns:
            `ArithTerm`, `Number` or `Variable` instance.
        """  # noqa
        # simplify operands
        loperand = self.loperand.simplify()
        roperand = self.roperand.simplify()

        # if both operands can be simplified to numbers, subtract them
        if isinstance(loperand, Number) and isinstance(roperand, Number):
            return Number(loperand.val - roperand.val)
        # only left operand is a number
        elif isinstance(loperand, Number):
            # left operand does not add anything
            if loperand.val == 0:
                # NOTE: return the negative of the right operand
                return Minus(roperand)
        # only right operand is a number
        elif isinstance(roperand, Number):
            # right operand does not add anything
            if roperand.val == 0:
                return loperand

        # else return an instance of a simplified subtraction
        return Sub(loperand, roperand)


class Mult(ArithTerm):
    """Represents a multiplication of arithmetic terms.

    Attributes:
        ground: Boolean indicating whether or not all operands are ground.
        loperand: `ArithTerm` instance representing the left operand.
        roperand: `ArithTerm` instance representing the right operand.
        operands: Tuple consisting of the left and right operands.
    """

    def __init__(
        self: Self,
        loperand: Union[ArithTerm, Number, "Variable"],
        roperand: Union[ArithTerm, Number, "Variable"],
    ) -> None:
        """Initializes the arithmetic term.

        Args:
            loperand: `ArithTerm`, `Number`, or `Variable` instance.
            roperand: `ArithTerm`, `Number`, or `Variable` instance.
        """  # noqa
        self.loperand = loperand
        self.roperand = roperand

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Mult` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Mult)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("mult", self.loperand, self.roperand))

    def __str__(self: Self) -> str:
        """Returns the string representation for the arithmetic term.

        Returns:
            String representations of the operands joined with '*'.
            If an operand is a `ArithTerm` instance, its string is additionally enclosed in parentheses.
        """  # noqa
        loperand_str = (
            f"({str(self.loperand)})"
            if isinstance(self.loperand, ArithTerm)
            else str(self.loperand)
        )
        roperand_str = (
            f"({str(self.roperand)})"
            if isinstance(self.roperand, ArithTerm)
            else str(self.roperand)
        )

        return f"{loperand_str}*{roperand_str}"

    @cached_property
    def ground(self: Self) -> bool:
        return self.loperand.ground and self.roperand.ground

    def eval(self: Self) -> int:
        """Evaluates the arithmetic term.

        Operands must be ground to perform evaluation.

        Returns:
            Integer value representing the difference of the operand values.

        Raises:
            ValueError: Operands are not ground.
        """  # noqa
        if not self.ground:
            raise ValueError("Cannot evaluate non-ground arithmetic term.")

        return self.loperand.eval() * self.roperand.eval()

    def simplify(self: Self) -> Union[ArithTerm, "Number", "Variable"]:
        """Simplifies the arithmetic term.

        First the operands are simplified.
        If both (simplified) operands are `Number` instances, simplifies to a new `Number` instance representing the product of both numbers.
        If the left (simplified) operand is a `Number` equal to one, simplifies to the right (simplified) operand.
        If the left (simplified) operand is a `Number` equal to minus one, simplifies to a `Minus` instance with the right (simplified) operand as operand
        (the `Minus` instance is simplified again if the (simplified) operand is already a `Minus` instance).
        If the right (simplified) operand is a `Number` equal to one, simplifies to the left (simplified) operand.
        If the right (simplified) operand is a `Number` equal to minus one, simplifies to a `Minus` instance with the left (simplified) operand as operand.
        Else a `Mult` instance with (simplified) operands is returned (cannot be further simplified).

        Note: multiplications with zero are not simplified wherever possible, since variables may get dropped (might affect groundings).

        Returns:
            `ArithTerm`, `Number` or `Variable` instance.
        """  # noqa
        # simplify operands
        loperand = self.loperand.simplify()
        roperand = self.roperand.simplify()

        # if both operands can be simplified to numbers, multiply them
        if isinstance(loperand, Number) and isinstance(roperand, Number):
            return Number(loperand.val * roperand.val)
        # only left operand is a number
        elif isinstance(loperand, Number):
            # identity multiplication
            if loperand.val == 1:
                return roperand
            # negation
            elif loperand.val == -1:
                # check if left operand is already a 'Minus' instance (cancel out)
                if isinstance(roperand, Minus):
                    return roperand.operand

                return Minus(roperand)
        # only right operand is a number
        elif isinstance(roperand, Number):
            # identity multiplication
            if roperand.val == 1:
                return loperand
            # negation
            elif roperand.val == -1:
                # check if right operand is already a 'Minus' instance (cancel out)
                if isinstance(loperand, Minus):
                    return loperand.operand

                return Minus(loperand)

        # else return an instance of a simplified multiplication
        return Mult(loperand, roperand)


class Div(ArithTerm):
    """Represents an integer division of arithmetic terms.

    Attributes:
        ground: Boolean indicating whether or not all operands are ground.
        loperand: `ArithTerm` instance representing the left operand.
        roperand: `ArithTerm` instance representing the right operand.
        operands: Tuple consisting of the left and right operands.
    """

    def __init__(
        self: Self,
        loperand: Union[ArithTerm, Number, "Variable"],
        roperand: Union[ArithTerm, Number, "Variable"],
    ) -> None:
        """Initializes the arithmetic term.

        Args:
            loperand: `ArithTerm`, `Number`, or `Variable` instance.
            roperand: `ArithTerm`, `Number`, or `Variable` instance.
        """  # noqa
        self.loperand = loperand
        self.roperand = roperand

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the term to a given object.

        Considered equal if the given object is also a `Div` instance with same operands.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Div)
            and self.loperand == other.loperand
            and self.roperand == other.roperand
        )

    def __hash__(self: Self) -> int:
        return hash(("div", self.loperand, self.roperand))

    def __str__(self: Self) -> str:
        """Returns the string representation for the arithmetic term.

        Returns:
            String representations of the operands joined with '/'.
            If an operand is a `ArithTerm` instance, its string is additionally enclosed in parentheses.
        """  # noqa
        loperand_str = (
            f"({str(self.loperand)})"
            if isinstance(self.loperand, ArithTerm)
            else str(self.loperand)
        )
        roperand_str = (
            f"({str(self.roperand)})"
            if isinstance(self.roperand, ArithTerm)
            else str(self.roperand)
        )

        return f"{loperand_str}/{roperand_str}"

    @cached_property
    def ground(self: Self) -> bool:
        return self.loperand.ground and self.roperand.ground

    def eval(self: Self) -> int:
        """Evaluates the arithmetic term.

        Operands must be ground to perform evaluation.

        Returns:
            Integer value representing the integer devision of the operand values.

        Raises:
            ValueError: Operands are not ground.
        """  # noqa
        if not self.ground:
            raise Exception("Cannot evaluate non-ground arithmetic term.")

        # NOTE: ASP-Core-2 requires integer division
        return self.loperand.eval() // self.roperand.eval()

    def simplify(self: Self) -> Union[ArithTerm, "Number", "Variable"]:
        """Simplifies the arithmetic term.

        First the operands are simplified.
        If both (simplified) operands are `Number` instances, simplifies to a new `Number` instance representing the integer division of both numbers.
        If the right (simplified) operand is a `Number` equal to one, simplifies to the left (simplified) operand.
        If the right (simplified) operand is a `Number` equal to minus one, simplifies to a `Minus` instance with the left (simplified) operand as operand
        (the `Minus` instance is simplified again if the (simplified) operand is already a `Minus` instance).
        Else a `Div` instance with (simplified) operands is returned (cannot be further simplified).

        Returns:
            `ArithTerm`, `Number` or `Variable` instance.

        Raises:
            ArithmeticError: Division by zero.
        """  # noqa
        # simplify operands
        loperand = self.loperand.simplify()
        roperand = self.roperand.simplify()

        # if both operands can be simplified to numbers, divide them
        if isinstance(loperand, Number) and isinstance(roperand, Number):
            if roperand.val == 0:
                raise ArithmeticError(
                    "Division by zero detected while simplifying arithmetical term."
                )

            # NOTE: integer division
            return Number(loperand.val // roperand.val)
        # only right operand is a number
        elif isinstance(roperand, Number):
            # division by zero
            if roperand.val == 0:
                raise ArithmeticError(
                    "Division by zero detected while simplifying arithmetical term."
                )
            elif roperand.val == 1:
                return loperand
            elif roperand.val == -1:
                # check if right operand is already a 'Minus' instance (cancel out)
                if isinstance(loperand, Minus):
                    return loperand.operand

                return Minus(loperand)

        # else return an instance of a simplified division
        return Div(loperand, roperand)


# maps arithmetic operators to their corresponding AST constructs
op2arith = {
    ArithOp.PLUS: Add,
    ArithOp.MINUS: Sub,
    ArithOp.TIMES: Mult,
    ArithOp.DIV: Div,
}
