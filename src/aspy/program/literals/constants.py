from typing import Any, Dict, Set

from aspy.program.expression import Expr
from aspy.program.terms import Term

from .literal import Literal, LiteralCollection

# TODO: must also include changes to grounder (or at least throw error))


class TrueConstant(Literal):
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, TrueConstant)

    def __hash__(self) -> int:
        return hash(("#true"))

    def __str__(self) -> str:
        return "#true"

    def match(self, *args, **kwargs) -> None:  # TODO: signature!!!
        raise NotImplementedError("Matching not defined for special '#true' constant.")

    def pos_occ(self, *args, **kwargs) -> LiteralCollection:  # TODO: signature!!!
        return LiteralCollection(self)

    def neg_occ(self, *args, **kwargs) -> LiteralCollection:  # TODO: signature!!!
        return LiteralCollection()

    def safety(self, *args, **kwargs) -> None:  # TODO: signature!!!
        raise NotImplementedError(
            "Safety characterization not defined for special '#true' constant."
        )

    def vars(self, *args, **kwargs) -> Set:  # TODO: signature!!!
        return set()

    def substitute(self, subst: Dict[str, Term]) -> Expr:
        return self  # TODO: correct?


class FalseConstant(Literal):
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, FalseConstant)

    def __hash__(self) -> int:
        return hash(("#false"))

    def __str__(self) -> str:
        return "#false"

    def match(self, *args, **kwargs) -> None:  # TODO: signature!!!
        raise NotImplementedError("Matching not defined for special '#false' constant.")

    def pos_occ(self, *args, **kwargs) -> LiteralCollection:  # TODO: signature!!!
        return LiteralCollection(self)

    def neg_occ(self, *args, **kwargs) -> LiteralCollection:  # TODO: signature!!!
        return LiteralCollection()

    def safety(self, *args, **kwargs) -> None:  # TODO: signature!!!
        raise NotImplementedError(
            "Safety characterization not defined for special '#false' constant."
        )

    def vars(self, *args, **kwargs) -> Set:  # TODO: signature!!!
        return set()

    def substitute(self, subst: Dict[str, Term]) -> Expr:
        return self  # TODO: correct?
