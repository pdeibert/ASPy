from copy import deepcopy
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Self, Set, Union

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.operators import RelOp
    from aspy.program.query import Query
    from aspy.program.safety_characterization import SafetyTriplet
    from aspy.program.statements import Statement
    from aspy.program.substitution import Substitution
    from aspy.program.terms import Term, Variable
    from aspy.program.variable_table import VariableTable


class Guard(NamedTuple):
    """Guard for aggregates.

    Attributes:
        op: `RelOp` representing the relational operator.
        bound: `Term` instance representing the bound.
        right: Boolean indicating whether or not this is a right-hand side guard.
        ground: Boolean indicating whether or not the bound term is ground.
    """

    op: "RelOp"
    bound: "Term"
    right: bool

    def __str__(self: Self) -> str:
        """Returns the string representation for the guard.

        Returns:
            String representing the guard.
            If the guard is a right-hand side guard, consists of the string representation of
            the operator followed by the string representation of the bound.
            Else, the bound string representation precedes the operator string representation.
        """  # noqa
        if self.right:
            return f"{str(self.op)} {str(self.bound)}"
        else:
            return f"{str(self.bound)} {str(self.op)}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the guard to a given object.

        Considered equal if the given object is also a `Guard` instance with same bound
        and relational operator if moved to the same side.

        Example:
            Guard(>=, 3, True) == Guard(<=, 3, False)

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the term is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Guard)
            and self.bound == other.bound
            and (
                (self.right == other.right and self.op == other.op)
                or (self.right != other.right and self.op == -other.op)
            )
        )

    def __hash__(self: Self) -> int:
        return hash(("guard", self.op, self.bound, self.right))

    def to_left(self: Self) -> "Guard":
        """Moves guard to the left-hand side.

        Returns:
            Equivalent `Guard` instance for the left-hand side.
        """
        if self.right:
            return Guard(-self.op, self.bound, False)
        return deepcopy(self)

    def to_right(self: Self) -> "Guard":
        """Moves guard to the right-hand side.

        Returns:
            Equivalent `Guard` instance for the right-hand side.
        """
        if not self.right:
            return Guard(-self.op, self.bound, True)
        return deepcopy(self)

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the guard.

        Returns:
            (Possibly empty) set of `Variable` instances as the variables of the bound.
        """  # noqa
        return self.bound.vars()

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the guard.

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Usually irrelevant for literals. Defaults to `None`.

        Returns:
            (Possibly empty) set of `Variable` instances as the global variables of the bound.
        """  # noqa
        return self.bound.global_vars(statement)

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> "SafetyTriplet":
        """Returns the the safety characterizations for the guard.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Irrelevant for guards. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance as the safety characterization of the bound term.
        """  # noqa
        return self.bound.safety(statement)

    @property
    def ground(self: Self) -> bool:
        return self.bound.ground

    def substitute(self: Self, subst: "Substitution") -> "Guard":
        """Applies a substitution to the guard.

        Substitutes the bound term recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `Guard` instance with (possibly substituted) bound term.
        """
        return Guard(self.op, self.bound.substitute(subst), self.right)

    def replace_arith(self: Self, var_table: "VariableTable") -> "Guard":
        """Replaces arithmetic terms appearing in the guard bound with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `Guard` instance.
        """  # noqa
        return Guard(self.op, self.bound.replace_arith(var_table), self.right)
