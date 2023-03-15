from copy import deepcopy
from typing import TYPE_CHECKING, Optional, Type, Union

import aspy
from aspy.program.literals import (
    AggrBaseLiteral,
    AggrElemLiteral,
    ChoiceBaseLiteral,
    ChoiceElemLiteral,
    LiteralCollection,
    PropBaseLiteral,
    PropElemLiteral,
)
from aspy.program.literals.builtin import op2rel
from aspy.program.substitution import Substitution
from aspy.program.terms import Number, TermTuple

from .normal import NormalRule

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.expression import Expr
    from aspy.program.literals import AggrElement, Guard
    from aspy.program.statements.choice import ChoiceElement
    from aspy.program.terms import Term
    from aspy.program.variable_table import VariableTable


class PropBaseRule(NormalRule):
    """TODO."""

    def __init__(
        self,
        atom: PropBaseLiteral,
        lguard: Optional["Guard"],
        rguard: Optional["Guard"],
        literals: "LiteralCollection",
    ) -> None:

        super().__init__(atom, *literals)
        self.guards = (lguard, rguard)

    @property
    def ref_id(self) -> int:
        return self.atom.ref_id

    @property
    def glob_vars(self) -> TermTuple:
        return self.atom.glob_vars

    @classmethod
    def from_scratch(
        cls,
        ref_id: int,
        glob_vars: TermTuple,
        lguard: Optional["Guard"],
        rguard: Optional["Guard"],
        base_value: "Term",
        non_aggr_literals: "LiteralCollection",
    ) -> "PropBaseRule":

        # check if global vars is tuple (important for FIXED order)
        if aspy.debug():
            if not isinstance(glob_vars, TermTuple):
                raise ValueError(
                    f"Argument 'global_vars' for {cls} must be of type {TermTuple}."
                )
            if (lguard is not None and lguard.right) or (
                rguard is not None and not rguard.right
            ):
                raise ValueError(
                    f"Left or right guard for {cls} must indicate the correct side."
                )

        # create head atom/literal
        atom = PropBaseLiteral(ref_id, glob_vars, deepcopy(glob_vars))
        # compute guard literals and combine them with non-aggregate literals
        lguard_literal = (
            op2rel[lguard.op](lguard.bound, base_value) if lguard is not None else None
        )
        rguard_literal = (
            op2rel[rguard.op](base_value, rguard.bound) if rguard is not None else None
        )
        guard_literals = LiteralCollection(
            *tuple(
                guard_literal
                for guard_literal in (lguard_literal, rguard_literal)
                if guard_literal is not None
            )
        )

        return PropBaseRule(atom, lguard, rguard, guard_literals + non_aggr_literals)

    def substitute(self, subst: "Substitution") -> "PropBaseRule":
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        return type(self)(
            self.atom.substitute(subst), *self.guards, self.literals.substitute(subst)
        )

    def replace_arith(self, var_table: "VariableTable") -> "PropBaseRule":
        return type(self)(
            self.atom.replace_arith(var_table),
            *self.guards,
            self.literals.replace_arith(var_table),
        )

    def gather_var_assignment(self) -> Substitution:
        """Get substitution of local and global variables from rules. Remaining variables will simply be mapped onto themselves."""  # noqa
        return self.atom.gather_var_assignment()


class PropElemRule(NormalRule):
    """TODO."""

    def __init__(
        self,
        atom: PropElemLiteral,
        element: Union["AggrElement", "ChoiceElement"],
        literals: "LiteralCollection",
    ) -> None:
        super().__init__(atom, *literals)
        self.element = element

    def __eq__(self, other: "Expr") -> bool:
        return (
            isinstance(other, type(self))
            and self.atom == other.atom
            and self.literals == other.literals
            and self.element == other.element
        )

    def __hash__(self) -> int:
        return hash(
            ("prop element rule", type(self), self.atom, self.literals, self.element)
        )

    @property
    def ref_id(self) -> int:
        return self.atom.ref_id

    @property
    def element_id(self) -> int:
        return self.atom.element_id

    @property
    def local_vars(self) -> int:
        return self.atom.local_vars

    @property
    def glob_vars(self) -> int:
        return self.atom.glob_vars

    @classmethod
    def from_scratch(
        cls,
        ref_id: int,
        element_id: int,
        glob_vars: TermTuple,
        element: "AggrElement",
        literals: "LiteralCollection",
    ) -> "PropElemRule":

        # compute local variables
        local_vars = TermTuple(
            *tuple(var for var in element.vars() if var not in glob_vars)
        )

        # create head atom/literal
        atom = PropElemLiteral(
            ref_id, element_id, local_vars, glob_vars, local_vars + glob_vars
        )
        # combine element literals with other literals
        literals = element.literals + literals

        return PropElemRule(atom, element, literals)

    def substitute(self, subst: "Substitution") -> "PropElemRule":
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        return type(self)(
            self.atom.substitute(subst), self.element, self.literals.substitute(subst)
        )

    def replace_arith(self, var_table: "VariableTable") -> "PropElemRule":
        return type(self)(
            self.atom.replace_arith(var_table),
            self.element,
            self.literals.replace_arith(var_table),
        )

    def gather_var_assignment(self) -> Substitution:
        """Get substitution of local and global variables from rules. Remaining variables will simply be mapped onto themselves."""  # noqa
        return self.atom.gather_var_assignment()


class AggrBaseRule(PropBaseRule):
    """TODO."""

    def __init__(
        self,
        atom: AggrBaseLiteral,
        lguard: Optional["Guard"],
        rguard: Optional["Guard"],
        literals: "LiteralCollection",
    ) -> None:

        super().__init__(atom, lguard, rguard, literals)

    @classmethod
    def from_scratch(
        cls,
        ref_id: int,
        glob_vars: TermTuple,
        lguard: Optional["Guard"],
        rguard: Optional["Guard"],
        base_value: "Term",
        non_aggr_literals: "LiteralCollection",
    ) -> "AggrBaseRule":

        # check if global vars is tuple (important for FIXED order)
        if aspy.debug():
            if not isinstance(glob_vars, TermTuple):
                raise ValueError(
                    f"Argument 'global_vars' for {cls} must be of type {TermTuple}."
                )
            if (lguard is not None and lguard.right) or (
                rguard is not None and not rguard.right
            ):
                raise ValueError(
                    f"Left or right guard for {cls} must indicate the correct side."
                )

        # create head atom/literal
        atom = AggrBaseLiteral(ref_id, glob_vars, deepcopy(glob_vars))
        # compute guard literals and combine them with non-aggregate literals
        lguard_literal = (
            op2rel[lguard.op](lguard.bound, base_value) if lguard is not None else None
        )
        rguard_literal = (
            op2rel[rguard.op](base_value, rguard.bound) if rguard is not None else None
        )
        guard_literals = LiteralCollection(
            *tuple(
                guard_literal
                for guard_literal in (lguard_literal, rguard_literal)
                if guard_literal is not None
            )
        )

        return AggrBaseRule(atom, lguard, rguard, guard_literals + non_aggr_literals)


class AggrElemRule(PropElemRule):
    """TODO."""

    def __init__(
        self,
        atom: AggrElemLiteral,
        element: "AggrElement",
        literals: "LiteralCollection",
    ) -> None:
        super().__init__(atom, element, literals)

    @classmethod
    def from_scratch(
        cls,
        ref_id: int,
        element_id: int,
        glob_vars: TermTuple,
        element: "AggrElement",
        non_aggr_literals: "LiteralCollection",
    ) -> "AggrElemRule":

        # compute local variables
        local_vars = TermTuple(
            *tuple(var for var in element.vars() if var not in glob_vars)
        )

        # create head atom/literal
        atom = AggrElemLiteral(
            ref_id, element_id, local_vars, glob_vars, local_vars + glob_vars
        )
        # combine element literals with non-aggregate literals
        literals = element.literals + non_aggr_literals

        return AggrElemRule(atom, element, literals)


class ChoiceBaseRule(PropBaseRule):
    """TODO."""

    def __init__(
        self,
        atom: ChoiceBaseLiteral,
        lguard: Optional["Guard"],
        rguard: Optional["Guard"],
        literals: "LiteralCollection",
    ) -> None:

        super().__init__(atom, lguard, rguard, literals)

    @classmethod
    def from_scratch(
        cls,
        ref_id: int,
        glob_vars: TermTuple,
        lguard: Optional["Guard"],
        rguard: Optional["Guard"],
        non_aggr_literals: "LiteralCollection",
    ) -> "ChoiceBaseRule":

        # check if global vars is tuple (important for FIXED order)
        if aspy.debug():
            if not isinstance(glob_vars, TermTuple):
                raise ValueError(
                    f"Argument 'global_vars' for {cls} must be of type {TermTuple}."
                )
            if (lguard is not None and lguard.right) or (
                rguard is not None and not rguard.right
            ):
                raise ValueError(
                    f"Left or right guard for {cls} must indicate the correct side."
                )

        # create head atom/literal
        atom = ChoiceBaseLiteral(ref_id, glob_vars, deepcopy(glob_vars))
        # compute guard literals and combine them with non-aggregate literals
        lguard_literal = (
            op2rel[lguard.op](lguard.bound, Number(0)) if lguard is not None else None
        )
        rguard_literal = (
            op2rel[rguard.op](Number(0), rguard.bound) if rguard is not None else None
        )
        guard_literals = LiteralCollection(
            *tuple(
                guard_literal
                for guard_literal in (lguard_literal, rguard_literal)
                if guard_literal is not None
            )
        )

        return ChoiceBaseRule(atom, lguard, rguard, guard_literals + non_aggr_literals)


class ChoiceElemRule(PropElemRule):
    """TODO."""

    def __init__(
        self,
        atom: ChoiceElemLiteral,
        element: "ChoiceElement",
        literals: "LiteralCollection",
    ) -> None:
        super().__init__(atom, element, literals)

    @classmethod
    def from_scratch(
        cls,
        ref_id: int,
        element_id: int,
        glob_vars: TermTuple,
        element: "ChoiceElement",
        non_aggr_literals: "LiteralCollection",
    ) -> "ChoiceElemRule":

        # compute local variables
        local_vars = TermTuple(
            *tuple(var for var in element.vars() if var not in glob_vars)
        )

        # create head atom/literal
        atom = ChoiceElemLiteral(
            ref_id, element_id, local_vars, glob_vars, local_vars + glob_vars
        )
        # combine element literals with non-aggregate literals
        literals = element.literals + non_aggr_literals

        return ChoiceElemRule(atom, element, literals)
