import itertools
from abc import ABC, abstractmethod
from functools import cached_property, reduce
from itertools import chain, combinations
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Iterator,
    Optional,
    Self,
    Set,
    Tuple,
    Type,
    Union,
)

from aspy.program.expression import Expr
from aspy.program.operators import AggrOp, RelOp
from aspy.program.safety_characterization import SafetyRule, SafetyTriplet
from aspy.program.terms import Infimum, Number, Supremum, TermTuple

from .guard import Guard
from .literal import Literal, LiteralCollection

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.query import Query
    from aspy.program.statements import Statement
    from aspy.program.substitution import Substitution
    from aspy.program.terms import Term, Variable
    from aspy.program.variable_table import VariableTable


def powerset(element_iterable: Iterable[Any]) -> Iterator[Tuple[Any, ...]]:
    """Computes the power set of an iterable.

    From https://docs.python.org/3/library/itertools.html#itertools.combinations.
    """
    elements = list(element_iterable)
    return chain.from_iterable(
        combinations(elements, n_elements) for n_elements in range(len(elements) + 1)
    )


class AggrElement(Expr):
    """Represents an aggregate element.

    Attributes:
        terms: `TermTuple` containing the terms of the element.
        head: same as `terms`.
        literals: `LiteralCollection` containing the literals (i.e., condition) of the element.
        body: same as `literals`
        ground: Boolean indicating whether or not all terms and literals are ground.
    """  # noqa

    def __init__(
        self: Self,
        terms: Optional[Union[Tuple["Term", ...], "TermTuple"]] = None,
        literals: Optional[Union[Tuple["Literal", ...], "LiteralCollection"]] = None,
    ) -> None:
        """Initializes the aggregate element instance.

        Args:
            terms: Optional `TermTuple` instance or tuple of `Term` instances.
                Defaults to None.
            literals: Optional `LiteralCollection` instance or tuple of `Literal` instances.
                Defaults to None.
        """  # noqa
        if literals is None:
            literals = LiteralCollection()
        if terms is None:
            terms = TermTuple()

        self.terms = terms if isinstance(terms, TermTuple) else TermTuple(*terms)
        self.literals = (
            literals
            if isinstance(literals, LiteralCollection)
            else LiteralCollection(*literals)
        )

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the element to a given object.

        Considered equal if the given object is also an `AggrElement` instance with same terms and literals.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the element is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, AggrElement)
            and self.terms == other.terms
            and self.literals == other.literals
        )

    def __hash__(self: Self) -> int:
        return hash(("aggr element", self.terms, self.literals))

    def __str__(self: Self) -> str:
        """Returns the string representation for the aggregate element.

        Returns:
            String representing the aggregate element.
            Represents literals and terms separated by commas, respectively and joined with a colon.
            If the element has no literals, the colon is omitted.
        """  # noqa
        return ",".join([str(term) for term in self.terms]) + (
            f":{','.join([str(literal) for literal in self.literals])}"
            if self.literals
            else ""
        )

    @property
    def head(self: Self) -> "TermTuple":
        return self.terms

    @property
    def body(self: Self) -> "LiteralCollection":
        return self.literals

    @cached_property
    def ground(self: Self) -> bool:
        return all(term.ground for term in self.terms) and all(
            literal.ground for literal in self.literals
        )

    def pos_occ(self: Self) -> LiteralCollection:
        """Positive literal occurrences.

        Returns:
            Union of the sets of `Literal` instances that occur positively in the literals.
        """  # noqa
        return self.literals.pos_occ()

    def neg_occ(self: Self) -> LiteralCollection:
        """Negative literal occurrences.

        Returns:
            Union of the sets of `Literal` instances that occur negatively in the literals.
        """  # noqa
        return self.literals.neg_occ()

    @property
    def weight(self: Self) -> int:
        """Returns the weight of the term tuple.

        Also see `TermTuple.weight`.

        Returns:
            Integer representing the value of the first term if it is a `Number` instance, and zero else.
        """  # noqa
        return self.terms.weight

    @property
    def pos_weight(self: Self) -> int:
        """Returns the positive weight of the term tuple.

        Also see `TermTuple.weight`.

        Returns:
            Integer representing the value of the first term if it is a positive `Number` instance, and zero else.
        """  # noqa
        return self.terms.pos_weight

    @property
    def neg_weight(self: Self) -> int:
        """Returns the negative weight of the term tuple.

        Also see `TermTuple.weight`.

        Returns:
            Integer representing the value of the first term if it is a negative `Number` instance, and zero else.
        """  # noqa
        return self.terms.neg_weight

    def satisfied(self: Self, literals: Set["Literal"]) -> bool:
        """Check whether or not the element is satisfied.

        Args:
            literals: Set of `Literal` instances interpreted as valid.

        Returns:
            Boolean indicating whether or not the element condition is part of the specified set of literals.
        """  # noqa
        # check if all condition literals are part of the specified set
        return all(literal in literals for literal in self.literals)

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the aggregate element.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the variables of all terms and literals.
        """  # noqa
        return self.head.vars().union(self.body.vars())

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the aggregate element.

        Returns:
            (Possibly empty) set of `Variable` instances as union of the global variables of all terms and literals.
        """  # noqa
        return self.head.global_vars().union(self.body.global_vars())

    def safety(self: Self, statement: Optional["Statement"] = None) -> SafetyTriplet:
        """Returns the the safety characterizations for the aggregate literal.

        Raises an exception, since safety characterization is undefined for aggregate elements
        without additional context.
        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` instance the term appears in.
                Irrelevant for aggregate elements. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance.

        Raises:
            ValueError: Safety characterization is undefined for aggregate elements
            without additional context.
        """  # noqa
        raise ValueError(
            "Safety characterization for aggregate elements is undefined without context."  # noqa
        )

    def substitute(self: Self, subst: "Substitution") -> "AggrElement":
        """Applies a substitution to the aggregate element.

        Substitutes all terms and literals recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `AggrElement` instance with (possibly substituted) terms and literals.
        """
        return AggrElement(
            self.terms.substitute(subst),
            self.literals.substitute(subst),
        )

    def match(self: Self, other: "Expr") -> Optional["Substitution"]:
        """Tries to match the aggregate element with an expression.

        Raises an exception, since matching for aggregate elements is undefined.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            Optional `Substitution` instance.
        """  # noqa
        raise Exception("Matching for aggregate elements is not defined.")

    def replace_arith(self: Self, var_table: "VariableTable") -> "AggrElement":
        """Replaces arithmetic terms appearing in the aggregate element with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `AggrElement` instance.
        """  # noqa
        return AggrElement(
            self.terms.replace_arith(var_table),
            self.literals.replace_arith(var_table),
        )

    def set_naf(self: Self, value: bool = True) -> None:
        """Setter for the `naf` attribute.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.
        """
        self.naf = value


class AggrFunc(ABC):
    """Abstract base class for all aggregate functions.

    Declares some default as well as abstract methods for aggregate functions.
    All aggregate function should inherit from this class or a subclass thereof.

    Attributes:
        base: `Term` instance representing the result of the aggregate operation
            for an empty set of aggregate elements.
    """

    @abstractmethod  # pragma: no cover
    def eval(self: Self, elements: Set["TermTuple"]) -> Number:
        """Evaluates the arithmetic function.

        Returns:
            `Number` instance representing the result of the aggregate operation.
        """  # noqa
        pass

    @property
    @abstractmethod  # pragma: no cover
    def base(self: Self) -> "Term":
        pass

    @abstractmethod  # pragma: no cover
    def propagate(
        self: Self,
        guards: Tuple[Optional[Guard], Optional[Guard]],
        elements: Set["AggrElement"],
        literals_I: Set["Literal"],
        literals_J: Set["Literal"],
    ) -> bool:
        """Aggregate propagation to approximate satisfiability.

        Approximates whether or not the aggregate function is satisfiable for
        given guards, aggregate elements and domains of literals.

        For details see Kaminski & Schaub (2022): "On the Foundations of Grounding in Answer Set Programming".

        Args:
            guards: Tuple of two optional `Guard` instances. The order is irrelevant.
            elements: Set of `AggregateElements` to be used.
            literals_I: domain of literals (`I` in the paper).
            literals_J: domain of literals (`J` in the paper).
        """  # noqa
        pass


class AggrCount(AggrFunc):
    """Represents a 'count' aggregate.

    Counts the number of unique tuples from elements that are satisfied.
    Zero for the empty set.

    Attributes:
        base: `Number(0)` instance representing the result of the aggregate operation
            for an empty set of aggregate elements.
    """

    base: Number = Number(0)

    def __str__(self: Self) -> str:
        """Returns the string representation for the aggregate function.

        Returns:
            String `"#count"`.
        """
        return "#count"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the aggregate function to a given object.

        Considered equal if the given object is also a `AggrCount` instance.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the function is considered equal to the given object.
        """  # noqa
        return isinstance(other, AggrCount)

    def __hash__(self: Self) -> int:
        return hash(("aggregate count"))

    @classmethod
    def eval(cls: Type["AggrCount"], tuples: Set["TermTuple"]) -> Number:
        """Evaluates the aggregate function.

        Args:
            tuples: Set of `TermTuple` instances.

        Returns:
            `Number` instance representing the number of unique tuples.
        """  # noqa
        return Number(len(tuples))

    def propagate(
        self: Self,
        guards: Tuple[Optional[Guard], Optional[Guard]],
        elements: Set["AggrElement"],
        literals_I: Set["Literal"],
        literals_J: Set["Literal"],
    ) -> bool:
        """Aggregate propagation to approximate satisfiability.

        Approximates whether or not the aggregate function is satisfiable for
        given guards, aggregate elements and domains of literals.
        Note: this procedure is not exact, but only an approximation.

        For details see Kaminski & Schaub (2022): "On the Foundations of Grounding in Answer Set Programming".
        The implementation here is partly based on `mu-gringo`: https://github.com/potassco/mu-gringo.

        Args:
            guards: Tuple of two optional `Guard` instances. The order is irrelevant.
            elements: Set of `AggregateElements` to be used.
            literals_I: domain of literals (`I` in the paper).
            literals_J: domain of literals (`J` in the paper).
        """  # noqa

        # cache holding intermediate results (to avoid recomputation)
        propagation_cache = dict()
        # elements that are satisfied by I and J, respectively (initialize to None)
        elements_I = None
        elements_J = None

        def get_I_elements() -> Set["AggrElement"]:
            nonlocal elements_I

            if elements_I is None:
                elements_I = {
                    element for element in elements if element.satisfied(literals_I)
                }
            return elements_I

        def get_J_elements() -> Set["AggrElement"]:
            nonlocal elements_J

            if elements_J is None:
                elements_J = {
                    element for element in elements if element.satisfied(literals_J)
                }
            return elements_J

        def get_propagation_result(
            op: RelOp, bound: "Term", domain: Set["AggrElement"]
        ) -> bool:
            nonlocal propagation_cache

            if (op, bound) not in propagation_cache:
                propagation_cache[(op, bound)] = op.eval(
                    self.eval({element.terms for element in domain}), bound
                )
            return propagation_cache[(op, bound)]

        # running boolean tracking the current result of the propagation
        res = True

        for guard in guards:
            if guard is None:
                continue
            if res is False:
                break

            op, bound, right = guard

            # move operator to right-hand side (for canonical processing)
            if not right:
                op = -op

            if op in {RelOp.GREATER, RelOp.GREATER_OR_EQ}:
                # check upper bound
                res &= get_propagation_result(op, bound, get_J_elements())
            elif op in {RelOp.LESS, RelOp.LESS_OR_EQ}:
                # check lower bound
                res &= get_propagation_result(op, bound, get_I_elements())
            elif op == RelOp.EQUAL:
                # check upper and lower bound
                res &= get_propagation_result(
                    RelOp.GREATER_OR_EQ, bound, get_J_elements()
                ) and get_propagation_result(RelOp.LESS_OR_EQ, bound, get_I_elements())
            elif op == RelOp.UNEQUAL:
                # check upper or lower bound as well as
                # whether or not J satisfies any elements that are not satisfied under I
                res &= get_propagation_result(
                    RelOp.GREATER, bound, get_J_elements()
                ) or get_propagation_result(RelOp.LESS, bound, get_I_elements())

        return res


class AggrSum(AggrFunc):
    """Represents a 'sum' aggregate.

    Sums up the first elements of unique tuples from elements that are satisfied,
    where the first element is a `Number`. Zero for the empty set.

    Attributes:
        base: `Number(0)` instance representing the result of the aggregate operation
            for an empty set of aggregate elements.
    """

    base: Number = Number(0)

    def __str__(self: Self) -> str:
        """Returns the string representation for the aggregate function.

        Returns:
            String `"#sum"`.
        """
        return "#sum"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the aggregate function to a given object.

        Considered equal if the given object is also a `AggrSum` instance.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the function is considered equal to the given object.
        """  # noqa
        return isinstance(other, AggrSum)

    def __hash__(self: Self) -> int:
        return hash(("aggregate sum"))

    @classmethod
    def eval(
        cls: Type["AggrSum"],
        tuples: Set["TermTuple"],
        positive: bool = True,
        negative: bool = True,
    ) -> Number:
        """Evaluates the aggregate function.

        Args:
            tuples: Set of `TermTuple` instances.
            positive: Boolean indicating whether or not to take positive values into account.
                Defaults to `True`.
            negative: Boolean indicating whether or not to take negative values into account.
                Defaults to `True`.

        Returns:
            `Number` instance representing the sum of all unique tuples with a number as first element.
        """  # noqa

        # empty tuple set
        if not tuples or (positive == negative == False):  # noqa (chaining is faster)
            return cls.base

        # non-empty set
        return Number(
            sum(
                (tup.pos_weight if positive else 0)
                + (tup.neg_weight if negative else 0)
                for tup in tuples
            )
        )

    def propagate(
        self: Self,
        guards: Tuple[Optional[Guard], Optional[Guard]],
        elements: Set["AggrElement"],
        literals_I: Set["Literal"],
        literals_J: Set["Literal"],
    ) -> bool:
        """Aggregate propagation to approximate satisfiability.

        Approximates whether or not the aggregate function is satisfiable for
        given guards, aggregate elements and domains of literals.
        Note: this procedure is not exact, but only an approximation.

        For details see Kaminski & Schaub (2022): "On the Foundations of Grounding in Answer Set Programming".
        The implementation here is partly based on `mu-gringo`: https://github.com/potassco/mu-gringo.

        Args:
            guards: Tuple of two optional `Guard` instances. The order is irrelevant.
            elements: Set of `AggregateElements` to be used.
            literals_I: domain of literals (`I` in the paper).
            literals_J: domain of literals (`J` in the paper).
        """  # noqa

        # cache holding intermediate results (to avoid recomputation)
        propagation_cache = dict()
        # elements that are satisfied by I and J, respectively (initialize to None)
        elements_I = None
        elements_J = None

        def get_I_elements() -> Set["AggrElement"]:
            nonlocal elements_I

            if elements_I is None:
                elements_I = {
                    element for element in elements if element.satisfied(literals_I)
                }
            return elements_I

        def get_J_elements() -> Set["AggrElement"]:
            nonlocal elements_J

            if elements_J is None:
                elements_J = {
                    element for element in elements if element.satisfied(literals_J)
                }
            return elements_J

        def get_propagation_result(
            op: RelOp,
            bound: "Term",
            adjust: int,
            domain: Set["AggrElement"],
            positive: bool = True,
            negative: bool = True,
        ) -> bool:
            nonlocal propagation_cache

            if (op, bound, adjust, positive, negative) not in propagation_cache:
                propagation_cache[(op, bound, adjust, positive, negative)] = op.eval(
                    Number(
                        self.eval(
                            {element.terms for element in domain}, positive, negative
                        ).val
                        + adjust
                    ),
                    bound,
                )
            return propagation_cache[(op, bound, adjust, positive, negative)]

        def propagate_subset(
            op,
            bound: "Term",
            elements_I: Set["AggrElement"],
            elements_J: Set["AggrElement"],
        ) -> bool:
            # compute baseline value
            J_terms = {element.terms for element in elements_J}
            baseline = self.eval(J_terms)
            # get all elements that would change the baseline valueself
            # (to reduce number of possible subsets to test)
            candidate_terms = {
                element.terms
                for element in elements_I
                if (element not in literals_J and element.weight != 0)
            } - J_terms

            # test all combinations of subsets of candidates
            return any(
                op.eval(bound, baseline + self.eval(X))
                for X in powerset(candidate_terms)
            )

        # running boolean tracking the current result of the propagation
        res = True

        for guard in guards:
            if guard is None:
                continue
            if res is False:
                break

            op, bound, right = guard

            # move operator to right-hand side (for canonical processing)
            if not right:
                op = -op

            if op in {RelOp.GREATER, RelOp.GREATER_OR_EQ}:
                res &= get_propagation_result(
                    op,
                    bound,
                    sum(min(element.weight, 0) for element in get_I_elements()),
                    get_J_elements(),
                    negative=False,
                )
            elif op in {RelOp.LESS, RelOp.LESS_OR_EQ}:
                res &= get_propagation_result(
                    op,
                    bound,
                    sum(max(element.weight, 0) for element in get_I_elements()),
                    get_J_elements(),
                    positive=False,
                )
            elif op == RelOp.EQUAL:
                # check upper and lower bound
                res &= (
                    get_propagation_result(
                        RelOp.GREATER_OR_EQ,
                        bound,
                        sum(min(element.weight, 0) for element in get_I_elements()),
                        get_J_elements(),
                        negative=False,
                    )
                    and get_propagation_result(
                        RelOp.LESS_OR_EQ,
                        bound,
                        sum(max(element.weight, 0) for element in get_I_elements()),
                        get_J_elements(),
                        positive=False,
                    )
                    and propagate_subset(
                        RelOp.EQUAL, bound, get_J_elements(), get_I_elements()
                    )
                )
            elif op == RelOp.UNEQUAL:
                # check upper or lower bound as well as
                # whether or not J satisfies any elements that are not satisfied under I
                res &= (
                    get_propagation_result(
                        RelOp.GREATER,
                        bound,
                        sum(min(element.weight, 0) for element in get_I_elements()),
                        get_J_elements(),
                        negative=False,
                    )
                    or get_propagation_result(
                        RelOp.LESS,
                        bound,
                        sum(max(element.weight, 0) for element in get_I_elements()),
                        get_J_elements(),
                        positive=False,
                    )
                    or not propagate_subset(
                        RelOp.EQUAL, bound, get_I_elements(), get_J_elements()
                    )
                )

        return res


class AggrMin(AggrFunc):
    """Represents a 'minimum' aggregate.

    Gathers the minimal first element of unique tuples from elements that are satisfied.
    `Supremum` for the empty set.

    Attributes:
        base: `Supremum` instance representing the result of the aggregate operation
            for an empty set of aggregate elements.
    """

    base: Supremum = Supremum()

    def __str__(self: Self) -> str:
        """Returns the string representation for the aggregate function.

        Returns:
            String `"#min"`.
        """
        return "#min"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the aggregate function to a given object.

        Considered equal if the given object is also a `AggrMin` instance.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the function is considered equal to the given object.
        """  # noqa
        return isinstance(other, AggrMin)

    def __hash__(self: Self) -> int:
        return hash(("aggregate min"))

    @classmethod
    def eval(cls: Type["AggrMin"], tuples: Set["TermTuple"]) -> "Term":
        """Evaluates the aggregate function.

        Args:
            tuples: Set of `TermTuple` instances.

        Returns:
            `Term` instance representing the minimal first element of all unique non-empty tuples.
            `Supremum` in case all tuples are empty or the set of tuples itself is empty.
        """  # noqa
        # return minimum first term across all non-empty elements
        # NOTE: includes 'Supremum' in case all elements are empty
        return reduce(
            lambda t1, t2: t2 if not t1.precedes(t2) else t1,
            (cls.base, *tuple(tup[0] for tup in tuples if tup)),
        )

    def propagate(
        self: Self,
        guards: Tuple[Optional[Guard], Optional[Guard]],
        elements: Set["AggrElement"],
        literals_I: Set["Literal"],
        literals_J: Set["Literal"],
    ) -> bool:
        """Aggregate propagation to approximate satisfiability.

        Approximates whether or not the aggregate function is satisfiable for
        given guards, aggregate elements and domains of literals.
        Note: this procedure is not exact, but only an approximation.

        For details see Kaminski & Schaub (2022): "On the Foundations of Grounding in Answer Set Programming".
        The implementation here is partly based on `mu-gringo`: https://github.com/potassco/mu-gringo.

        Args:
            guards: Tuple of two optional `Guard` instances. The order is irrelevant.
            elements: Set of `AggregateElements` to be used.
            literals_I: domain of literals (`I` in the paper).
            literals_J: domain of literals (`J` in the paper).
        """  # noqa

        # cache holding intermediate results (to avoid recomputation)
        propagation_cache = dict()
        # elements that are satisfied by I and J, respectively (initialize to None)
        elements_I = None
        elements_J = None

        def get_I_elements() -> Set["AggrElement"]:
            nonlocal elements_I

            if elements_I is None:
                elements_I = {
                    element for element in elements if element.satisfied(literals_I)
                }
            return elements_I

        def get_J_elements() -> Set["AggrElement"]:
            nonlocal elements_J

            if elements_J is None:
                elements_J = {
                    element for element in elements if element.satisfied(literals_J)
                }
            return elements_J

        def get_propagation_result(
            op: RelOp, bound: "Term", domain: Set["AggrElement"]
        ) -> bool:
            nonlocal propagation_cache

            if (op, bound) not in propagation_cache:
                propagation_cache[(op, bound)] = op.eval(
                    self.eval({element.terms for element in domain}), bound
                )
            return propagation_cache[(op, bound)]

        def propagate_subset(
            op,
            bound,
            elements_I: Set["AggrElement"],
            elements_J: Set["AggrElement"],
        ) -> bool:
            # compute baseline value
            baseline = self.eval({element.terms for element in elements_J})
            # get all elements that would change the baseline value
            # (to reduce number of possible subsets to test)
            candidates = {
                element
                for element in elements_I
                if (element.terms and not element.terms[0].precedes(baseline))
            }

            # test all combinations of subsets of candidates
            for X in powerset(candidates):
                value = self.eval({element.terms for element in X})

                if op.eval(
                    bound, (value if not baseline.precedes(value) else baseline)
                ):
                    return True

            return False

        # running boolean tracking the current result of the propagation
        res = True

        for guard in guards:
            if guard is None:
                continue
            if res is False:
                break

            op, bound, right = guard

            # move operator to right-hand side (for canonical processing)
            if not right:
                op = -op

            if op in {RelOp.LESS, RelOp.LESS_OR_EQ}:
                # check upper bound
                res &= get_propagation_result(op, bound, get_J_elements())
            elif op in {RelOp.GREATER, RelOp.GREATER_OR_EQ}:
                # check lower bound
                res &= get_propagation_result(op, bound, get_I_elements())
            elif op == RelOp.EQUAL:
                # check upper and lower bound
                res &= (
                    get_propagation_result(RelOp.GREATER_OR_EQ, bound, get_I_elements())
                    and get_propagation_result(
                        RelOp.LESS_OR_EQ, bound, get_J_elements()
                    )
                    and propagate_subset(
                        RelOp.EQUAL, bound, get_J_elements(), get_I_elements()
                    )
                )
            elif op == RelOp.UNEQUAL:
                # check upper or lower bound as well as
                # whether or not J satisfies any elements that are not satisfied under I
                res &= (
                    get_propagation_result(RelOp.GREATER, bound, get_I_elements())
                    or get_propagation_result(RelOp.LESS, bound, get_J_elements())
                    or not propagate_subset(
                        RelOp.EQUAL, bound, get_I_elements(), get_J_elements()
                    )
                )

        return res


class AggrMax(AggrFunc):
    """Represents a 'maximum' aggregate.

    Gathers the maximal first element of unique tuples from elements that are satisfied.
    `Infimum` for the empty set.

    Attributes:
        base: `Infimum` instance representing the result of the aggregate operation
            for an empty set of aggregate elements.
    """

    base: Infimum = Infimum()

    def __str__(self: Self) -> str:
        """Returns the string representation for the aggregate function.

        Returns:
            String `"#max"`.
        """
        return "#max"

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the aggregate function to a given object.

        Considered equal if the given object is also a `AggrMax` instance.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the function is considered equal to the given object.
        """  # noqa
        return isinstance(other, AggrMax)

    def __hash__(self: Self) -> int:
        return hash(("aggregate max"))

    @classmethod
    def eval(cls: Type["AggrMax"], tuples: Set["TermTuple"]) -> "Term":
        """Evaluates the aggregate function.

        Args:
            tuples: Set of `TermTuple` instances.

        Returns:
            `Term` instance representing the maximal first element of all unique non-empty tuples.
            `Infimum` in case all tuples are empty or the set of tuples itself is empty.
        """  # noqa
        # return maximum first term across all non-empty elements
        # NOTE: includes 'Infimum' in case all elements are empty
        return reduce(
            lambda t1, t2: t2 if not t2.precedes(t1) else t1,
            (cls.base, *tuple(tup[0] for tup in tuples if tup)),
        )

    def propagate(
        self: Self,
        guards: Tuple[Optional[Guard], Optional[Guard]],
        elements: Set["AggrElement"],
        literals_I: Set["Literal"],
        literals_J: Set["Literal"],
    ) -> bool:
        """Aggregate propagation to approximate satisfiability.

        Approximates whether or not the aggregate function is satisfiable for
        given guards, aggregate elements and domains of literals.
        Note: this procedure is not exact, but only an approximation.

        For details see Kaminski & Schaub (2022): "On the Foundations of Grounding in Answer Set Programming".
        The implementation here is partly based on `mu-gringo`: https://github.com/potassco/mu-gringo.

        Args:
            guards: Tuple of two optional `Guard` instances. The order is irrelevant.
            elements: Set of `AggregateElements` to be used.
            literals_I: domain of literals (`I` in the paper).
            literals_J: domain of literals (`J` in the paper).
        """  # noqa

        # cache holding intermediate results (to avoid recomputation)
        propagation_cache = dict()
        # elements that are satisfied by I and J, respectively (initialize to None)
        elements_I = None
        elements_J = None

        def get_I_elements() -> Set["AggrElement"]:
            nonlocal elements_I

            if elements_I is None:
                elements_I = {
                    element for element in elements if element.satisfied(literals_I)
                }
            return elements_I

        def get_J_elements() -> Set["AggrElement"]:
            nonlocal elements_J

            if elements_J is None:
                elements_J = {
                    element for element in elements if element.satisfied(literals_J)
                }
            return elements_J

        def get_propagation_result(
            op: RelOp, bound: "Term", domain: Set["AggrElement"]
        ) -> bool:
            nonlocal propagation_cache

            if (op, bound) not in propagation_cache:
                propagation_cache[(op, bound)] = op.eval(
                    self.eval({element.terms for element in domain}), bound
                )
            return propagation_cache[(op, bound)]

        def propagate_subset(
            op,
            bound,
            elements_I: Set["AggrElement"],
            elements_J: Set["AggrElement"],
        ) -> bool:
            # compute baseline value
            baseline = self.eval({element.terms for element in elements_J})
            # get all elements that would change the baseline value
            # (to reduce number of possible subsets to test)
            candidates = {
                element
                for element in elements_I
                if (element.terms and not element.terms[0].precedes(baseline))
            }

            # test all combinations of subsets of candidates
            for X in powerset(candidates):
                value = self.eval({element.terms for element in X})

                if op.eval(
                    bound, (value if not value.precedes(baseline) else baseline)
                ):
                    return True

            return False

        # running boolean tracking the current result of the propagation
        res = True

        for guard in guards:
            if guard is None:
                continue
            if res is False:
                break

            op, bound, right = guard

            # move operator to right-hand side (for canonical processing)
            if not right:
                op = -op

            if op in {RelOp.GREATER, RelOp.GREATER_OR_EQ}:
                # check upper bound
                res &= get_propagation_result(op, bound, get_J_elements())
            elif op in {RelOp.LESS, RelOp.LESS_OR_EQ}:
                # check lower bound
                res &= get_propagation_result(op, bound, get_I_elements())
            elif op == RelOp.EQUAL:
                # check upper and lower bound
                res &= (
                    get_propagation_result(RelOp.GREATER_OR_EQ, bound, get_J_elements())
                    and get_propagation_result(
                        RelOp.LESS_OR_EQ, bound, get_I_elements()
                    )
                    and propagate_subset(
                        RelOp.EQUAL, bound, get_J_elements(), get_I_elements()
                    )
                )
            elif op == RelOp.UNEQUAL:
                # check upper or lower bound as well as
                # whether or not J satisfies any elements that are not satisfied under I
                res &= (
                    get_propagation_result(RelOp.GREATER, bound, get_J_elements())
                    or get_propagation_result(RelOp.LESS, bound, get_I_elements())
                    or not propagate_subset(
                        RelOp.EQUAL, bound, get_I_elements(), get_J_elements()
                    )
                )

        return res


class AggrLiteral(Literal):
    """Represents an aggregate literal.

    Attributes:
        func: `AggrFunc` instance representing the aggregate function.
        elements: Tuple of `AggrElement` instances representing the set of aggregate elements.
        lguard: Optional left `Guard` instance.
        rguard: Optional right `Guard` instance.
        guards: Tuple of `lguard` and `rguard`.
        naf: Boolean indicating whether or not the aggregate literal is default-negated.
        ground: Boolean indicating whether or not the aggregate literal is ground.
            The literal is considered ground if all guards and elements are ground.
    """  # noqa

    def __init__(
        self: Self,
        func: AggrFunc,
        elements: Tuple[AggrElement, ...],
        guards: Union[Guard, Tuple[Guard, ...]],
        naf: bool = False,
    ) -> None:
        """Initializes the aggregate literal instance.

        Args:
            func: `AggrFunc` instance representing the aggregate function.
            elements: Tuple of `AggrElement` instances representing the set of aggregate elements.
            guards: single `Guard` instance or tuple of (maximum two) `Guard` instances.
                If two guards are specified, they are expected to represent opposite sides.
                The order of the guards is irrelevant.
            naf: Boolean indicating whether or not the aggregate literal is default-negated.
                Defaults to `False`.

        Raises:
            ValueError: Invalid number of guards or multiple guards for the same side.
        """  # noqa
        super().__init__(naf)

        # initialize left and right guard to 'None'
        self.lguard, self.rguard = None, None

        # single guard specified
        if isinstance(guards, Guard):
            # wrap in tuple
            guards = (guards,)
        # guard tuple specified
        elif isinstance(guards, Tuple) and len(guards) not in {1, 2}:
            raise ValueError("Aggregate requires at least one and at most two guards.")

        # process guards
        for guard in guards:
            if guard is None:
                continue

            if guard.right:
                if self.rguard is not None:
                    raise ValueError("Multiple right guards specified for aggregate.")
                self.rguard = guard
            else:
                if self.lguard is not None:
                    raise ValueError("Multiple left guards specified for aggregate.")
                self.lguard = guard

        self.func = func
        self.elements = elements

    def __str__(self) -> str:
        """Returns the string representation for the aggregate literal.

        Returns:
            String representing the aggregate literal.
            If the predicate literal is default-negated, the string is prefixed by `"not "`.
            The string then continuous with the string representation of the aggregate function,\
            followed by the string representations of the elements, separated by semicolons,
            and enclosed in curly braces.
            Guard representations precede or succeed the string if specified.
        """  # noqa
        elements_str = ";".join([str(element) for element in self.elements])
        lguard_str = f"{str(self.lguard)} " if self.lguard is not None else ""
        rguard_str = f" {str(self.rguard)}" if self.rguard is not None else ""

        return (
            "not " if self.naf else ""
        ) + f"{lguard_str}{str(self.func)}{{{elements_str}}}{rguard_str}"

    def __eq__(self, other: "Any") -> bool:
        """Compares the literal to a given object.

        Considered equal if the given object is also an `AggrLiteral` instance with same aggregate
        function, guards, set of elements and identical default-negation.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the literal is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, AggrLiteral)
            and self.func == other.func
            and set(self.elements) == set(other.elements)
            and self.guards == other.guards
        )

    def __hash__(self) -> int:
        return hash(("aggr literal", self.func, self.elements, self.guards))

    @cached_property
    def ground(self) -> bool:
        return (
            (self.lguard.bound.ground if self.lguard is not None else True)
            and (self.rguard.bound.ground if self.rguard is not None else True)
            and all(element.ground for element in self.elements)
        )

    def set_naf(self, value: bool = True) -> None:
        """Setter for the `naf` attribute.

        Args:
            value: Boolean value for the `naf` attribute. Defaults to `True`.
        """
        self.naf = value

    def pos_occ(self) -> LiteralCollection:
        """Positive literal occurrences.

        Returns:
            Set of `Literal` instances as the union of all positive
            literal occurrences in its elements.
        """
        return LiteralCollection(
            *itertools.chain(*tuple(element.pos_occ() for element in self.elements))
        )

    def neg_occ(self) -> LiteralCollection:
        """Negative literal occurrences.

        Returns:
            Set of `Literal` instances as the union of all negative
            literal occurrences in its elements.
        """
        return LiteralCollection(
            *itertools.chain(*tuple(element.neg_occ() for element in self.elements))
        )

    @property
    def guards(self) -> Tuple[Optional[Guard], Optional[Guard]]:
        return (self.lguard, self.rguard)

    def invars(self) -> Set["Variable"]:
        """Inner variables.

        Returns:
            Set of `Variable` instances that occurr inside any of the elements.
        """
        return set().union(*tuple(element.vars() for element in self.elements))

    def outvars(self) -> Set["Variable"]:
        """Outer variables.

        Returns:
            Set of `Variable` instances that occurr in any of the guards.
        """
        return set().union(
            *tuple(guard.bound.vars() for guard in self.guards if guard is not None)
        )

    def vars(self) -> Set["Variable"]:
        """Returns the variables associated with the aggregate literal.

        Union of the sets of inner and outer variables.

        Returns:
            (Possibly empty) set of `Variable` instances.
        """  # noqa
        return self.invars().union(self.outvars())

    def global_vars(self, statement: Optional["Statement"] = None) -> Set["Variable"]:
        """Returns the global variables associated with the aggregate literal.

        For aggregate literals the set of outer variables are considered global.

        Args:
            statement: Optional `Statement` instance the literal appears in.
                Irrelevant for aggregate literals. Defaults to `None`.

        Returns:
            A (possibly empty) set of `Variable` instances.
        """
        return self.outvars()

    def eval(self) -> bool:
        """Evaluates the aggregate literal.

        The aggregate must be ground for evaluation.

        Returns:
            Boolean indicating whether or not the guards hold for the aggregated value.

        Raises:
            ValueError: Non-ground aggregate.
        """  # noqa
        if not self.ground:
            raise ValueError("Cannot evaluate non-ground aggregate.")

        # evaluate aggregate function
        aggr_term = self.func.eval({element.terms for element in self.elements})

        # check guards
        return (
            self.lguard.op.eval(self.lguard.bound, aggr_term)
            if self.lguard is not None
            else True
        ) and (
            self.rguard.op.eval(aggr_term, self.rguard.bound)
            if self.rguard is not None
            else True
        )

    def safety(self, statement: Union["Statement", "Query"]) -> SafetyTriplet:
        """Returns the the safety characterizations for the built-in literal.

        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: `Statement` or `Query` instance the term appears in.

        Returns:
            `SafetyTriplet` instance as the closure of the safety characterizations of
            the aggregate w.r.t. to each guard.
            The safety characterization of the aggregate w.r.t. to a guard marks
            all global inner and all outer variables as unsafe.
            If the relation operator is `RelOp.EQUAL` the safety characterization
            is additionally normalized with safety rules for each safe variable
            in the guard as the depender and the set of global inner variables
            as dependees.
        """  # noqa
        # get global variables from rule
        global_vars = statement.global_vars()

        # set of global variables that appear inside the aggregate
        aggr_global_invars = self.invars().intersection(global_vars)
        aggr_global_vars = aggr_global_invars.union(self.outvars())

        guard_safeties = []

        for guard in self.guards:
            # guard not specified
            if guard is None:
                continue
            elif (
                str(guard.op) != "="
            ):  # TODO: cannot compare to enum directly due to circular imports
                guard_safeties.append(SafetyTriplet(unsafe=aggr_global_vars))
            else:
                # compute safety characterization w.r.t. left term guard
                guard_safeties.append(
                    SafetyTriplet(
                        unsafe=aggr_global_vars,
                        rules=set(
                            [
                                SafetyRule(var, aggr_global_invars)
                                for var in guard.safety().safe
                            ]
                        ),
                    ).normalize()
                )

        return SafetyTriplet.closure(*guard_safeties)

    def substitute(self, subst: "Substitution") -> "AggrLiteral":
        """Applies a substitution to the aggregate literal.

        Substitutes all guard terms and aggregate elements recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `AggrLiteral` instance with (possibly substituted) guards and elements.
        """
        # substitute guard terms recursively
        guards = tuple(
            guard.substitute(subst) if guard is not None else None
            for guard in self.guards
        )

        return AggrLiteral(
            self.func,
            tuple(element.substitute(subst) for element in self.elements),
            guards,
            naf=self.naf,
        )

    def match(self, other: "Expr") -> Set["Substitution"]:
        """Tries to match the aggregate element with an expression.

        Raises an exception, since direct matching for aggregate literals is undefined.
        During grounding, aggregate literals are rewritten and assembled after instantiation.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            Optional `Substitution` instance.
        """  # noqa
        raise Exception("Direct matching for aggregate literals not supported.")

    def replace_arith(self, var_table: "VariableTable") -> "AggrLiteral":
        """Replaces arithmetic terms appearing in the aggregate literal with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `AggrLiteral` instance.
        """  # noqa
        # replace guards
        guards = (
            None if guard is None else guard.replace_arith(var_table)
            for guard in self.guards
        )

        return AggrLiteral(
            self.func,
            tuple(element.replace_arith(var_table) for element in self.elements),
            guards,
            self.naf,
        )


# maps aggregate operators/functions to their corresponding AST constructs
op2aggr = {
    AggrOp.COUNT: AggrCount,
    AggrOp.SUM: AggrSum,
    AggrOp.MIN: AggrMin,
    AggrOp.MAX: AggrMax,
}
