from copy import deepcopy
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, Optional, Self, Type

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.terms import Term, Variable


class AssignmentError(Exception):
    """Error representing an assignment conflict between substitions."""

    def __init__(self: Self, subst_1: "Substitution", subst_2: "Substitution") -> None:
        """Initializes the assignment error instance.

        Automatically formats the error message based on the specified substitutions.

        Args:
            subst_1: First `Substitution` instance.
            subst_2: Second `Substitution` instance.
        """
        super().__init__(
            f"Substitution {subst_1} is inconsistent with substitution {subst_2}."
        )


class Substitution(dict):
    """Substitution mapping variables to terms replacing those variables."""

    def __init__(
        self: Self, subst_dict: Optional[Dict["Variable", "Term"]] = None
    ) -> None:
        """Initializes the substitution instance.

        Args:
            subst_dict: Optional dictionary mapping `Variable` instances to
                `Term` instances. Defaults to `None`.
        """
        if subst_dict is not None:
            self.update(subst_dict)

    def __getitem__(self: Self, var: "Variable") -> "Term":
        """Getter for variables in the substitution.

        For variables that are not part of the substitution, the variable is implicitely
        mapped onto itself.

        Returns:
            `Term` instance representing the target of the substitution.
            Note: a copy is returned instead of the original object.
        """
        # map variables to themselves if no substitution specified
        return deepcopy(dict.__getitem__(self, var)) if var in self else deepcopy(var)

    def __str__(self: Self) -> str:
        """Returns the string representation for the substitution.

        Returns:
            String representing the substituion, containing the mappings,
            separated by commas.
            Each mapping consists of the variable identifier and its target term,
            separated by a colon.
        """
        assignments_str = ",".join(
            [f"{str(var)}:{str(target)}" for var, target in self.items()]
        )

        return f"{{{assignments_str}}}"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the substitution to a given object.

        Considered equal if the given object is also a `Substitution` instance with the
        same variable mappings. If a variable in one substitution is not part of the other,
        it must be mapped to itself.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the substitution is considered equal to the given object.
        """  # noqa
        return isinstance(other, Substitution) and super(Substitution, self).__eq__(
            other
        )

    def __hash__(self: Self) -> int:
        return hash(("substitution", frozenset(self.items())))

    def __add__(self: Self, other: "Substitution") -> "Substitution":
        """Combines the substitution with another one.

        Args:
            other: `Substitution` instance to be combined with.

        Returns:
            `Substitution` instance representing the union of both substitutions.

        Raises:
            AssignmentError: Assignment conflict between both substitutions.
        """
        subst = dict(self.items())

        for var, target in other.items():
            if var in subst:
                if not target == subst[var]:
                    raise AssignmentError(self, other)
            else:
                subst[var] = target

        return Substitution(subst)

    def compose(self: Self, other: "Substitution") -> "Substitution":
        """Composes substitution with another one.

        Specified substitution is applied to the current substitution.

        Args:
            other: `Substitution` instance to be composed with.

        Returns:
            `Substitution` instance representing the composition of both substitutions.
        """

        # apply other substitution to substituted values
        subst = {var: target.substitute(other) for (var, target) in self.items()}
        # add substitution of variables that are not in the original substitution
        # (i.e., originally mapped onto themselves)
        subst.update(
            {var: target for (var, target) in other.items() if var not in subst}
        )

        return Substitution(subst)

    @classmethod
    def composition(
        cls: Type["Substitution"], *substitutions: "Substitution"
    ) -> "Substitution":
        """Composes substitution with another one.

        Specified substitutions are applied to the current substitution in order.

        Args:
            *substitutions: `Substitution` instances to be composed with.

        Returns:
            `Substitution` instance representing the composition of all substitutions.
        """
        return reduce(lambda s1, s2: s1.compose(s2), substitutions)

    def is_identity(self: Self) -> bool:
        """Checks if the substitution is an identity substitution.

        Returns:
            Boolean indicating whether or not the substitution is an identity substitution.
        """  # noqa
        return all(var == target for (var, target) in self.items())
