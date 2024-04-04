from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Self, Set, Type

if TYPE_CHECKING:  # pragma: no cover
    from .terms import Variable


@dataclass
class SafetyRule:
    """Safety rule for safety characterization.

    For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

    Attributes:
        depender: `Variable` instance representing the depender.
        dependees: Set of `Variable` instances representing the dependees.
    """  # noqa

    depender: "Variable"
    dependees: Set["Variable"]

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the safety rule to a given object.

        Considered equal if the given object is also a `SafetyRule` instance with same
        depender and dependees.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the safety rule is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, SafetyRule)
            and self.depender == other.depender
            and self.dependees == other.dependees
        )

    def __str__(self: Self) -> str:
        return (
            f"{str(self.depender)} <- {','.join(tuple(str(v) for v in self.dependees))}"
        )

    def __hash__(self: Self) -> int:
        return hash(("safety rule", self.depender, frozenset(self.dependees)))


class SafetyTriplet:
    """Safety characterization.

    For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

    Attributes:
        safe: Set of `Variable` instances considered safe.
        unsafe: Set of `Variable` instances considered unsafe.
        rules: Set of `SafetyRule` instances.
    """  # noqa

    def __init__(
        self: Self,
        safe: Optional[Set["Variable"]] = None,
        unsafe: Optional[Set["Variable"]] = None,
        rules: Optional[Set[SafetyRule]] = None,
    ) -> None:
        """Initializes the safety triplet instance.

        Args:
            safe: Set of `Variable` instances considered safe. Defaults to None.
            unsafe: Set of `Variable` instances considered unsafe. Defaults to None.
            rules: Optional set of `SafetyRule` instances. Defaults to None.
        """
        self.safe = safe if safe is not None else set()
        self.unsafe = unsafe if unsafe is not None else set()
        self.rules = rules if rules is not None else set()

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the safety characterization to a given object.

        Considered equal if the given object is also a `SafetyTriplet` instance with same
        set of safe and unsafe variables as well as rules.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the safety triplet is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, SafetyTriplet)
            and self.safe == other.safe
            and self.unsafe == self.unsafe
            and self.rules == other.rules
        )

    def normalize(self: Self) -> "SafetyTriplet":
        """Normalizes the safety characterization.

        Implements Algorithm 1 in Bicheler (2015):
        "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Returns:
            Normalized `SafetyTriplet` instance.
        """  # noqa

        # create copy of current safety characterization
        safe = self.safe.copy()
        unsafe = self.safe.copy()
        rules = self.rules.copy()

        # remove rules whose depender depends on itself
        rules = {rule for rule in self.rules if rule.depender not in rule.dependees}

        prev_safe = set()
        prev_unsafe = set()
        prev_rules = set()

        # until there is no more change
        while rules != prev_rules or safe != prev_safe or unsafe != prev_unsafe:
            prev_safe = safe.copy()
            prev_unsafe = unsafe.copy()
            prev_rules = rules.copy()

            rules.clear()

            for rule in prev_rules:
                if not (rule.depender in rule.dependees or rule.depender in safe):
                    # remove safe variables from dependees and check if it becomes empty
                    if not (updated_dependees := rule.dependees - safe):
                        # drop rule and add depender to safe variables
                        safe.add(rule.depender)
                    else:
                        # updated rule
                        rules.add(SafetyRule(rule.depender, updated_dependees))

        for rule in rules:
            # mark rule variables as unsafe
            unsafe.add(rule.depender)
            unsafe.update(rule.dependees)

        # remove safe variables from set of unsafe ones
        unsafe = unsafe - safe

        return SafetyTriplet(safe, unsafe, rules)

    @classmethod
    def closure(
        cls: Type["SafetyTriplet"], *safeties: "SafetyTriplet"
    ) -> "SafetyTriplet":
        """Computes the closure for specified safety characterizations.

        Args:
            *safeties: Sequence of `SafetyTriplet` instances.

        Returns:
            `SafetyTriplet` instance representing the closure of the specified
            safety characterizations.
        """
        safe = set()
        unsafe = set()
        rules = set()

        # combine all safeties
        for safety in safeties:
            safe = safe.union(safety.safe)
            unsafe = unsafe.union(safety.unsafe)
            rules = rules.union(safety.rules)

        # return normalized combined safety
        return SafetyTriplet(safe, unsafe, rules).normalize()
