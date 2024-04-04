from enum import Enum
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.terms import Term


class RelOp(Enum):
    """Relational operators."""

    EQUAL = "="
    UNEQUAL = "!="
    LESS = "<"
    GREATER = ">"
    LESS_OR_EQ = "<="
    GREATER_OR_EQ = ">="

    def __str__(self: Self) -> str:
        """String representation of the relational operator.

        Returns:
            String representing the relational operator.
        """
        return self._value_

    def __neg__(self: Self) -> "RelOp":
        """Inverts the comparison operator for switched operands.

        Returns:
            `RelOp` instance.
        """
        if self == RelOp.EQUAL or self == RelOp.UNEQUAL:
            return self
        elif self == RelOp.LESS:
            return RelOp.GREATER
        elif self == RelOp.GREATER:
            return RelOp.LESS
        elif self == RelOp.LESS_OR_EQ:
            return RelOp.GREATER_OR_EQ
        else:
            return RelOp.LESS_OR_EQ

    def __invert__(self: Self) -> "RelOp":
        """Returns the equivalent operator after negation.

        Returns:
            `RelOp` instance.
        """
        if self == RelOp.EQUAL:
            return RelOp.UNEQUAL
        elif self == RelOp.UNEQUAL:
            return RelOp.EQUAL
        elif self == RelOp.LESS:
            return RelOp.GREATER_OR_EQ
        elif self == RelOp.GREATER:
            return RelOp.LESS_OR_EQ
        elif self == RelOp.LESS_OR_EQ:
            return RelOp.GREATER
        else:
            return RelOp.LESS

    def eval(self: Self, loperand: "Term", roperand: "Term") -> bool:
        """Evaluates the relational operator for given operands.

        Args:
            loperand: `Term` instance representing the left operand.
            roperand: `Term` instance representing the right operand.

        Returns:
            Boolean indicating whether or not the relational operation holds
            for the given operands.
        """
        if self == RelOp.EQUAL:
            return loperand.precedes(roperand) and roperand.precedes(loperand)
        elif self == RelOp.UNEQUAL:
            return not (loperand.precedes(roperand) and roperand.precedes(loperand))
        elif self == RelOp.LESS:
            return loperand.precedes(roperand) and not roperand.precedes(loperand)
        elif self == RelOp.GREATER:
            return not loperand.precedes(roperand) and roperand.precedes(loperand)
        elif self == RelOp.LESS_OR_EQ:
            return loperand.precedes(roperand)
        else:
            return roperand.precedes(loperand)


class ArithOp(Enum):
    """Arithmetic operators."""

    PLUS = "+"
    MINUS = "-"
    TIMES = "*"
    DIV = "/"

    def __str__(self: Self) -> str:
        """String representation of the arithmetic operator.

        Returns:
            String representing the arithmetic operator.
        """
        return self._value_


class AggrOp(Enum):
    """Aggregate operators."""

    COUNT = "#count"
    SUM = "#sum"
    MAX = "#max"
    MIN = "#min"

    def __str__(self: Self) -> str:
        """String representation of the aggregate operator.

        Returns:
            String representing the aggregate operator.
        """
        return self._value_
