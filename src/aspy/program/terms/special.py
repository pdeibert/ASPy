from typing import TYPE_CHECKING, Any, Self

import aspy
from aspy.program.symbols import SpecialChar
from aspy.program.terms.term import Term

from .term import Variable

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.terms import ArithTerm


class ArithVariable(Variable):
    """Placeholder variable replacing a non-ground arithmetic term.

    Attributes:
        ground: Boolean indicating whether or not the term is ground (always `False`).
    """

    ground: bool = False

    def __init__(self: Self, id: int, orig_term: "ArithTerm") -> None:
        """Initializes the arithmetic variable instance.

        The variable identifier is initialized as `"\u03C4{id}"`.

        Args:
            id: Non-negative integer representing the id for the arithmetic variable.
                Should be unique within each statement or query.
            orig_term: `ArithTerm` instance that is replaced by the arithmetic variable.

        Raises:
            ValueError: Negative id specified for the variable. Only checked if `aspy.debug()` returns `True`.
        """  # noqa
        # check if id is valid
        if aspy.debug() and id < 0:
            raise ValueError(f"Invalid value for {type(self)}: {id}")

        self.val = f"{SpecialChar.TAU.value}{id}"
        self.id = id
        self.orig_term = orig_term

    def __str__(self: Self) -> str:
        """Returns the string representation for an arithmetic variable.

        Returns:
            String representing the value (i.e., identifier) of the arithmetic variable.
        """
        return self.val

    def __eq__(self: Self, other: "Any") -> str:
        """Compares the term to a given object.

        Considered equal if the given object is also a `ArithVariable` instance with same id (i.e., value)
        and original aritmetic term it replaces.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, ArithVariable)
            and other.val == self.val
            and self.orig_term == other.orig_term
        )

    def __hash__(self: Self) -> int:
        return hash(("arith var", self.val, self.orig_term))

    def precedes(self: Self, other: "Term") -> bool:
        """Checks precendence w.r.t. a given term.

        Undefined for variables (i.e., non-ground terms). Raises an exception.

        Args:
            other: `Term` instance.

        Raises:
            Exception: Total order is undefined for variables.
        """  # noqa
        raise Exception(
            "Total order is not defined for arithmetical (auxiliary) variables."
        )
