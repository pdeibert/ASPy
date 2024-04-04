from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional, Self, Set, Union

if TYPE_CHECKING:  # pragma: no cover
    from .query import Query
    from .safety_characterization import SafetyTriplet
    from .statements import Statement
    from .terms import Term, Variable


class Expr(ABC):
    """Abstract base class for all expressions.

    Declares some default as well as abstract methods for expressions.
    All expressions should inherit from this class or a subclass thereof.
    """

    __slots__ = "ground"

    @abstractmethod  # pragma: no cover
    def vars(self: Self) -> Set["Variable"]:  # type: ignore
        """Returns the variables associated with the expression.

        Returns:
            Set of `Variable` instances.
        """
        pass

    @abstractmethod  # pragma: no cover
    def global_vars(self: Self, statement: Optional["Statement"] = None) -> Set["Variable"]:  # type: ignore # noqa
        """Returns the global variables associated with the expression.

        Returns:
            Set of `Variable` instances.
        """
        pass

    @abstractmethod  # pragma: no cover
    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> "SafetyTriplet":
        """Returns the safety characterization for the expression.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` or `Query` instance the term appears in.
                Usually irrelevant for expressions. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance.
        """  # noqa
        pass

    @abstractmethod  # pragma: no cover
    def substitute(self: Self, subst: Dict[str, "Term"]) -> "Expr":  # type: ignore
        """Applies a substitution to the expression.

        Replaces all variables with their substitution terms.

        Args:
            subst: `Substitution` instance.

        Returns:
            (Possibly substituted) `Expr` instance.
        """
        pass
