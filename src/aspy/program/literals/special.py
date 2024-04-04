from abc import ABC
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Self

from aspy.program.literals import LiteralCollection, PredLiteral
from aspy.program.substitution import Substitution
from aspy.program.symbols import SpecialChar
from aspy.program.terms import TermTuple

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.variable_table import VariableTable


# TODO: even necessary ???
class AuxLiteral(PredLiteral, ABC):
    """Abstract base class for auxiliary predicate literals."""

    def __init__(self, name: str, *args, **kwargs) -> None:
        """Initializes the auxiliary literal instance.

        Args:
            name: String representing the predicate identifier.
                Does not need to adhere to standard identifier limitations, but should
                make sense when printed.
        """
        super().__init__("f", *args, **kwargs)
        self.name = name  # TODO: better way to avoid regex check in 'PredLiteral'?


class PropPlaceholder(AuxLiteral):
    """Placeholder literal for propagation.

    Replaces an expression that needs to be propagated.

    Args:
        prefix: String appended as a prefix for the predicate identifier.
        ref_id: Non-negative integer representing a reference id for this placeholder.
        glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self,
        prefix: str,
        ref_id: int,
        glob_vars: TermTuple,
        terms: TermTuple,
        naf: bool = False,
    ) -> None:
        """Initializes the propagation placeholder literal instance.

        Args:
            prefix: String appended as a prefix for the predicate identifier.
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of global variables does not match number of specified terms.
        """  # noqa
        if len(glob_vars) != len(terms):
            raise ValueError(
                f"Number of global variables for {type(self)} does not match number of specified terms."  # noqa
            )

        super().__init__(f"{prefix}{ref_id}", *terms, naf=naf)
        self.prefix = prefix
        self.ref_id = ref_id
        self.glob_vars = glob_vars

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the literal to a given object.

        Considered equal if the given object is also a `PropPlaceholder` instance with same
        prefix, reference id, set of global variables and identical assignment of terms to these
        global variables.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, type(self))
            and self.prefix == other.prefix
            and self.ref_id == other.ref_id
            and set(self.glob_vars) == set(other.glob_vars)
            and {v: t for v, t in zip(self.glob_vars, self.terms)}
            == {v: t for v, t in zip(other.glob_vars, other.terms)}
        )

    def __hash__(self: Self) -> int:
        return hash(
            (
                "prop placeholder",
                self.prefix,
                self.ref_id,
                frozenset((v, t) for v, t in zip(self.glob_vars, self.terms)),
            )
        )

    def set_neg(self: Self, value: bool = True) -> None:
        """Setter for the `neg` attribute.

        Raises an exception as placeholder literals cannot be classically negated.

        Args:
            value: Boolean value for the `neg` attribute. Defaults to `True`.
        """
        raise Exception(
            f"Classical negation cannot be set for literal of type {type(self)}."  # noqa
        )

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Empty set if placeholder literal is default-negated.
            Else a singleton set with a copy is returned.
        """
        if self.naf:
            return LiteralCollection()

        return LiteralCollection(
            type(self)(
                prefix=self.prefix,
                ref_id=self.ref_id,
                glob_vars=self.glob_vars,
                terms=self.terms,
            )
        )

    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Empty set if placeholder literal is not default-negated.
            Else a singleton set with a non-default-negated copy is returned.
        """
        if not self.naf:
            return LiteralCollection()

        # NOTE: naf flag gets dropped
        return LiteralCollection(
            type(self)(
                prefix=self.prefix,
                ref_id=self.ref_id,
                glob_vars=self.glob_vars,
                terms=self.terms,
            )
        )

    def substitute(self: Self, subst: "Substitution") -> "PropPlaceholder":
        """Applies a substitution to the literal.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `PropPlaceholder` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        return type(self)(
            prefix=self.prefix,
            ref_id=self.ref_id,
            glob_vars=self.glob_vars,
            terms=TermTuple(*tuple(term.substitute(subst) for term in self.terms)),
            naf=self.naf,
        )

    def replace_arith(self: Self, var_table: "VariableTable") -> "PropPlaceholder":
        """Replaces arithmetic terms appearing in the literal with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `PropPlaceholder` instance.
        """  # noqa
        return type(self)(
            prefix=self.prefix,
            ref_id=self.ref_id,
            glob_vars=self.glob_vars,
            terms=self.terms,
            naf=self.naf,
        )

    def gather_var_assignment(self: Self) -> Substitution:
        """Get assignment of global variables from current terms.

        Returns:
            `Substitution` instance.
        """
        return Substitution(
            {
                var: term
                for (var, term) in zip(self.glob_vars, self.terms)
                if var != term
            }
        )


class PropBaseLiteral(AuxLiteral):
    """Auxiliary literal for propagation representing an empty propagatable expression.

    Predicate that represents whether or not a corresponding propagated expression is
    satisfiable without any elements.

    Args:
        prefix: String appended as a prefix for the predicate identifier.
        ref_id: Non-negative integer representing a reference id for this placeholder.
        glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False`).
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self, prefix: str, ref_id: int, glob_vars: TermTuple, terms: TermTuple
    ) -> None:
        """Initializes the literal instance representing an empty propagatable expression.

        Args:
            prefix: String appended as a prefix for the predicate identifier.
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of global variables does not match number of specified terms.
        """  # noqa

        if len(glob_vars) != len(terms):
            raise ValueError(
                f"Number of global variables for {type(self)} does not match number of specified terms."  # noqa
            )

        super().__init__(f"{SpecialChar.EPS.value}{prefix}{ref_id}", *terms)
        self.prefix = prefix
        self.ref_id = ref_id
        # store tuple to have a fixed reference order for variables
        self.glob_vars = glob_vars

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the literal to a given object.

        Considered equal if the given object is also a `PropBaseLiteral` instance with same
        prefix, reference id, set of global variables and identical assignment of terms to these
        global variables.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, type(self))
            and self.prefix == other.prefix
            and self.ref_id == other.ref_id
            and set(self.glob_vars) == set(other.glob_vars)
            and {v: t for v, t in zip(self.glob_vars, self.terms)}
            == {v: t for v, t in zip(other.glob_vars, other.terms)}
        )

    def __hash__(self: Self) -> int:
        return hash(
            (
                "prop base literal",
                self.prefix,
                self.ref_id,
                frozenset((v, t) for v, t in zip(self.glob_vars, self.terms)),
            )
        )

    def set_naf(self: Self, value: bool = True) -> None:
        """Setter for the `neg` attribute.

        Raises an exception as propagation literals cannot be default-negated.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.
        """
        raise Exception(
            f"Negation as failure cannot be set for literal of type {type(self)}."  # noqa
        )

    def set_neg(self: Self, value: bool = True) -> None:
        """Setter for the `neg` attribute.

        Raises an exception as propagation literals cannot be classically negated.

        Args:
            value: Boolean value for the `neg` attribute. Defaults to `True`.
        """
        raise Exception(
            f"Classical negation cannot be set for literal of type {type(self)}."  # noqa
        )

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Singleton set with a copy (literal is always positive).
        """
        return LiteralCollection(
            type(self)(
                prefix=self.prefix,
                ref_id=self.ref_id,
                glob_vars=self.glob_vars,
                terms=self.terms,
            )
        )

    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Empty set (literal is never default-negated).
        """
        return LiteralCollection()

    def substitute(self: Self, subst: "Substitution") -> "PropBaseLiteral":
        """Applies a substitution to the literal.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `PropBaseLiteral` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        return type(self)(
            prefix=self.prefix,
            ref_id=self.ref_id,
            glob_vars=self.glob_vars,
            terms=TermTuple(*tuple((term.substitute(subst) for term in self.terms))),
        )

    def replace_arith(self: Self, var_table: "VariableTable") -> "PropBaseLiteral":
        """Replaces arithmetic terms appearing in the literal with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `PropBaseLiteral` instance.
        """  # noqa
        return type(self)(
            prefix=self.prefix,
            ref_id=self.ref_id,
            glob_vars=self.glob_vars,
            terms=self.terms,
        )

    def gather_var_assignment(self: Self) -> Substitution:
        """Get assignment of global variables from current terms.

        Returns:
            `Substitution` instance.
        """
        return Substitution(
            {
                var: term
                for (var, term) in zip(self.glob_vars, self.terms)
                if var != term
            }
        )


class PropElemLiteral(AuxLiteral):
    """Auxiliary literal for propagation representing an element of a propagatable expression.

    Predicate that represents whether or not a corresponding propagated expression is
    satisfiable.

    Args:
        prefix: String appended as a prefix for the predicate identifier.
        ref_id: Non-negative integer representing a reference id for this placeholder.
        element_id: Non-negative integer representing the element id for the corresponding replaced
        aggregate or choice expression.
        glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self,
        prefix: str,
        ref_id: int,
        element_id: int,
        local_vars: "TermTuple",
        glob_vars: "TermTuple",
        terms: "TermTuple",
    ) -> None:
        """Initializes the literal instance representing an element of a propagatable expression.

        Args:
            prefix: String appended as a prefix for the predicate identifier.
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of total (local & global) variables does not match number of specified terms.
        """  # noqa
        if len(glob_vars) + len(local_vars) != len(terms):
            raise ValueError(
                f"Number of global/local variables for {type(self)} does not match number of specified terms."  # noqa
            )

        super().__init__(
            f"{SpecialChar.ETA.value}{prefix}{ref_id}_{element_id}",
            *terms,
        )
        self.prefix = prefix
        self.ref_id = ref_id
        self.element_id = element_id
        # store tuples to have a fixed reference order for variables
        self.local_vars = local_vars
        self.glob_vars = glob_vars

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the literal to a given object.

        Considered equal if the given object is also a `PropElemLiteral` instance with same
        prefix, reference and element ids, sets of local and global variables and identical assignment
        of terms to these variables.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, type(self))
            and self.prefix == other.prefix
            and self.ref_id == other.ref_id
            and self.element_id == other.element_id
            and set(self.glob_vars) == set(other.glob_vars)
            and set(self.local_vars) == set(other.local_vars)
            and {v: t for v, t in zip(self.local_vars + self.glob_vars, self.terms)}
            == {v: t for v, t in zip(other.local_vars + other.glob_vars, other.terms)}
        )

    def __hash__(self: Self) -> int:
        return hash(
            (
                "prop element literal",
                self.prefix,
                self.ref_id,
                self.element_id,
                frozenset(
                    (v, t)
                    for v, t in zip(self.local_vars, self.terms[: len(self.local_vars)])
                ),
                frozenset(
                    (v, t)
                    for v, t in zip(self.glob_vars, self.terms[len(self.local_vars) :])
                ),
            )
        )

    def set_naf(self: Self, value: bool = True) -> None:
        """Setter for the `neg` attribute.

        Raises an exception as propagation literals cannot be default-negated.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.
        """
        raise Exception(
            f"Negation as failure cannot be set for literal of type {type(self)}."  # noqa
        )

    def set_neg(self: Self, value: bool = True) -> None:
        """Setter for the `neg` attribute.

        Raises an exception as propagation literals cannot be default-negated.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.
        """
        raise Exception(
            f"Classical negation cannot be set for literal of type {type(self)}."  # noqa
        )

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Singleton set with a copy (literal is always positive).
        """
        return LiteralCollection(
            type(self)(
                prefix=self.prefix,
                ref_id=self.ref_id,
                element_id=self.element_id,
                local_vars=self.local_vars,
                glob_vars=self.glob_vars,
                terms=self.terms,
            )
        )

    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Empty set (literal is never default-negated).
        """
        return LiteralCollection()

    def substitute(self: Self, subst: "Substitution") -> "PropElemLiteral":
        """Applies a substitution to the literal.

        Substitutes all terms recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `PropElemLiteral` instance with (possibly substituted) terms.
        """
        if self.ground:
            return deepcopy(self)

        # substitute terms recursively
        return type(self)(
            prefix=self.prefix,
            ref_id=self.ref_id,
            element_id=self.element_id,
            local_vars=self.local_vars,
            glob_vars=self.glob_vars,
            terms=TermTuple(*tuple(term.substitute(subst) for term in self.terms)),
        )

    def replace_arith(self: Self, var_table: "VariableTable") -> "PropElemLiteral":
        """Replaces arithmetic terms appearing in the literal with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `PropElemLiteral` instance.
        """  # noqa
        return type(self)(
            prefix=self.prefix,
            ref_id=self.ref_id,
            element_id=self.element_id,
            local_vars=self.local_vars,
            glob_vars=self.glob_vars,
            terms=self.terms,
        )

    def gather_var_assignment(self: Self) -> Substitution:
        """Get assignment of variables from current terms.

        Returns:
            `Substitution` instance.
        """
        return Substitution(
            {
                var: term
                for (var, term) in zip(self.local_vars + self.glob_vars, self.terms)
                if var != term
            }
        )


class AggrPlaceholder(PropPlaceholder):
    """Placeholder literal for aggregate expression during propagation.

    Replaces an aggregate expression that needs to be propagated.

    Args:
        ref_id: Non-negative integer representing a reference id for this placeholder.
        glob_vars: Set of global `Variable` instances appearing inside the replaced aggregate expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self,
        ref_id: int,
        glob_vars: TermTuple,
        terms: TermTuple,
        naf: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """Initializes the aggregate placeholder instance.

        Args:
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced aggregate expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of global variables does not match number of specified terms.
        """  # noqa
        super().__init__(SpecialChar.ALPHA.value, ref_id, glob_vars, terms, naf=naf)


class AggrBaseLiteral(PropBaseLiteral):
    """Auxiliary literal for propagation representing an empty aggregate expression.

    Predicate that represents whether or not a corresponding propagated aggregate expression is
    satisfiable without any elements.

    Args:
        ref_id: Non-negative integer representing a reference id for this placeholder.
        glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False`).
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self, ref_id: int, glob_vars: TermTuple, terms: TermTuple, *args, **kwargs
    ) -> None:
        """Initializes the literal instance representing an empty propagated aggregate expression.

        Args:
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced aggregate expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of global variables does not match number of specified terms.
        """  # noqa
        super().__init__(SpecialChar.ALPHA.value, ref_id, glob_vars, terms)


class AggrElemLiteral(PropElemLiteral):
    """Auxiliary literal for propagation representing an element of an aggregate expression.

    Predicate that represents whether or not a corresponding propagated aggregate expression is
    satisfiable.

    Args:
        ref_id: Non-negative integer representing a reference id for this placeholder.
        element_id: Non-negative integer representing the element id for the corresponding replaced
        aggregate or choice expression.
        glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self,
        ref_id: int,
        element_id: int,
        local_vars: "TermTuple",
        glob_vars: "TermTuple",
        terms: "TermTuple",
        *args,
        **kwargs,
    ) -> None:
        """Initializes the literal instance representing an element of an aggregate expression.

        Args:
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced aggregate expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of total (local & global) variables does not match number of specified terms.
        """  # noqa
        super().__init__(
            SpecialChar.ALPHA.value, ref_id, element_id, local_vars, glob_vars, terms
        )


class ChoicePlaceholder(PropPlaceholder):
    """Placeholder literal for choice expressions during propagation.

    Replaces a choice expression that needs to be propagated.

    Args:
        ref_id: Non-negative integer representing a reference id for this placeholder.
        glob_vars: Set of global `Variable` instances appearing inside the replaced choice expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self,
        ref_id: int,
        glob_vars: TermTuple,
        terms: TermTuple,
        naf: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """Initializes the propagation placeholder literal instance.

        Args:
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced choice expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of global variables does not match number of specified terms.
        """  # noqa
        super().__init__(SpecialChar.CHI.value, ref_id, glob_vars, terms, naf=naf)

    def set_naf(self: Self, value: bool = True) -> None:
        """Setter for the `neg` attribute.

        Raises an exception as placeholder literals for choice expressions cannot be default-negated.

        Args:
            value: Boolean value for the `neg` attribute. Defaults to `True`.
        """  # noqa
        raise Exception(
            f"Negation-as-failure cannot be set for literal of type {ChoicePlaceholder}."  # noqa
        )


class ChoiceBaseLiteral(PropBaseLiteral):
    """Auxiliary literal for propagation representing an empty choice expression.

    Predicate that represents whether or not a corresponding propagated choice expression is
    satisfiable without any elements.

    Args:
        ref_id: Non-negative integer representing a reference id for this placeholder.
        glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated
            (always `False`).
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self, ref_id: int, glob_vars: TermTuple, terms: TermTuple, *args, **kwargs
    ) -> None:
        """Initializes the literal instance representing an empty propagated choice expression.

        Args:
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced choice expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of global variables does not match number of specified terms.
        """  # noqa
        super().__init__(SpecialChar.CHI.value, ref_id, glob_vars, terms)


class ChoiceElemLiteral(PropElemLiteral):
    """Auxiliary literal for propagation representing an element of a choice expression.

    Predicate that represents whether or not a corresponding propagated choice expression is
    satisfiable.

    Args:
        ref_id: Non-negative integer representing a reference id for this placeholder.
        element_id: Non-negative integer representing the element id for the corresponding replaced
        aggregate or choice expression.
        glob_vars: Set of global `Variable` instances appearing inside the replaced propogation expression.
        terms: Set of `Term` instances, that are the assignments for `glob_vars`.
        naf: Boolean indicating whether or not the literal is default-negated.
        ground: Boolean indicating whether or not the literal is ground.
    """  # noqa

    def __init__(
        self: Self,
        ref_id: int,
        element_id: int,
        local_vars: "TermTuple",
        glob_vars: "TermTuple",
        terms: "TermTuple",
        *args,
        **kwargs,
    ) -> None:
        """Initializes the literal instance representing an element of a choice expression.

        Args:
            ref_id: Non-negative integer representing a reference id for this placeholder.
            glob_vars: Set of global `Variable` instances appearing inside the replaced choice expression.
            terms: Set of `Term` instances, that are the assignments for `glob_vars`.
            naf: Boolean indicating whether or not the literal is default-negated.

        Raises:
            ValueError: Number of total (local & global) variables does not match number of specified terms.
        """  # noqa
        super().__init__(
            SpecialChar.CHI.value, ref_id, element_id, local_vars, glob_vars, terms
        )
