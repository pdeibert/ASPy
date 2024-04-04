from typing import TYPE_CHECKING, Any, Dict, Optional, Self, Set, Union

from .expression import Expr
from .literals import LiteralCollection, PredLiteral

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.terms import Term, Variable

    from .safety_characterization import SafetyTriplet
    from .statements import Statement


class Query(Expr):
    """Query."""

    def __init__(self: Self, atom: "PredLiteral") -> None:
        self.atom = atom

    def __str__(self: Self) -> str:
        return f"{str(self.atom)} ?"

    def __eq__(self: Self, other: "Any") -> bool:
        return isinstance(other, Query) and self.atom == other.atom

    def __hash__(self: Self) -> int:
        return hash(("query", self.atom))

    @property
    def head(self: Self) -> LiteralCollection:
        return LiteralCollection(self.atom)

    @property
    def body(self: Self) -> LiteralCollection:
        return LiteralCollection()

    @property
    def ground(self: Self) -> bool:
        return self.atom.ground

    def vars(self: Self) -> Set["Variable"]:
        return self.atom.vars()

    def global_vars(self: Self) -> Set["Variable"]:
        return self.atom.global_vars()

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> "SafetyTriplet":
        return self.atom.safety(self)

    def substitute(self: Self, subst: Dict[str, "Term"]) -> "Query":  # type: ignore
        return Query(self.atom.substitute(subst))
