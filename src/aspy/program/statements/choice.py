import itertools
from copy import deepcopy
from functools import cached_property
from itertools import chain, combinations
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Self,
    Set,
    Tuple,
    Type,
    Union,
)

from aspy.program.expression import Expr
from aspy.program.literals import (
    AggrLiteral,
    ChoicePlaceholder,
    Guard,
    LiteralCollection,
)
from aspy.program.literals.builtin import GreaterEqual, op2rel
from aspy.program.operators import RelOp
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.terms import Infimum, Number

from .normal import NormalRule
from .special import ChoiceBaseRule, ChoiceElemRule
from .statement import Statement

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import AggrPlaceholder, Literal, PredLiteral
    from aspy.program.query import Query
    from aspy.program.substitution import Substitution
    from aspy.program.terms import Term, Variable
    from aspy.program.variable_table import VariableTable

    from .special import AggrBaseRule, AggrElemRule


def powerset(element_iterable: Iterable[Any]) -> Iterator[Tuple[Any, ...]]:
    """From https://docs.python.org/3/library/itertools.html#itertools.combinations recipes."""  # noqa
    elements = list(element_iterable)
    return chain.from_iterable(
        combinations(elements, n_elements) for n_elements in range(len(elements) + 1)
    )


class ChoiceElement(Expr):
    """Choice element for choice expressions.

    Attributes:
        atom: TODO
        literals: TODO
        head: TODO
        body: TODO
        ground: Boolean indicating whether or not the element is ground.
    """

    def __init__(
        self: Self,
        atom: "PredLiteral",
        literals: Optional[Iterable["Literal"]] = None,
    ) -> None:
        """Initializes the choice element instance.

        Args:
            atom: `PredLiteral` instance.
            literals: Iterable over `Literal` instances.
        """
        if literals is None:
            literals = LiteralCollection()

        self.atom = atom
        self.literals = (
            literals
            if isinstance(literals, LiteralCollection)
            else LiteralCollection(*literals)
        )

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the element to a given object.

        Considered equal if the given object is also a `ChoiceElement` instance with same atom and literals.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the element is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, ChoiceElement)
            and self.atom == other.atom
            and self.literals == other.literals
        )

    def __hash__(self: Self) -> int:
        return hash(("choice element", self.atom, self.literals))

    def __str__(self: Self) -> str:
        """Returns the string representation for the choice element.

        Returns:
            String representing the choice element.
            Joins the atom and the literals (separated by commas) with a colon
            If the element has no literals, the colon is omitted.
        """  # noqa
        return str(self.atom) + (
            f":{','.join([str(literal) for literal in self.literals])}"
            if self.literals
            else ""
        )

    @property
    def head(self: Self) -> LiteralCollection:
        return LiteralCollection(self.atom)

    @property
    def body(self: Self) -> LiteralCollection:
        return self.literals

    @cached_property
    def ground(self: Self) -> bool:
        return self.atom.ground and self.literals.ground

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Set of `Literal` instances that occur positively in the element.
        """
        return self.atom.pos_occ() + self.literals.pos_occ()

    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Set of `Literal` instances that occur negatively in the element.
        """
        return self.atom.neg_occ() + self.literals.neg_occ()

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the element.

        Returns:
            A (possibly empty) set of `Variable` instances.
        """
        return self.atom.vars().union(self.literals.vars())

    def global_vars(
        self: Self, statement: Optional["Statement"] = None
    ) -> Set["Variable"]:
        """Returns the global variables associated with the literal.

        Args:
            statement: Optional `Statement` instance the element appears in.
                Usually irrelevant for choice elements. Defaults to `None`.

        Returns:
            A (possibly empty) set of `Variable` instances.
        """
        return self.vars()

    def safety(self: Self, statement: Optional["Statement"] = None) -> SafetyTriplet:
        """Returns the the safety characterizations for the choice literal.

        Raises an exception, since safety characterization is undefined for choice elements
        without additional context.
        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` instance the term appears in.
                Irrelevant for choice elements. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance.

        Raises:
            ValueError: Safety characterization is undefined for choice elements
            without additional context.
        """  # noqa
        raise ValueError(
            "Safety characterization for choice elements is undefined without context."  # noqa
        )

    def substitute(self: Self, subst: "Substitution") -> "ChoiceElement":
        """Applies a substitution to the choice element.

        Substitutes all literals recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `ChoiceElement` instance with (possibly substituted) literals.
        """
        return ChoiceElement(
            self.atom.substitute(subst),
            self.literals.substitute(subst),
        )

    def match(self: Self, other: "Expr") -> Set["Substitution"]:
        """Tries to match the choice element with an expression.

        Raises an exception, since matching for choice elements is undefined.

        Args:
            other: `Expr` instance to be matched to.

        Returns:
            Optional `Substitution` instance.
        """  # noqa
        raise Exception("Matching for choice elements is not defined.")

    def replace_arith(self: Self, var_table: "VariableTable") -> "ChoiceElement":
        """Replaces arithmetic terms appearing in the element with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `ChoiceElement` instance.
        """  # noqa
        return ChoiceElement(
            self.atom.replace_arith(var_table),
            self.literals.replace_arith(var_table),
        )

    def satisfied(self: Self, literals: Set["Literal"]) -> bool:
        """Check whether or not the element is satisfied.

        Args:
            literals: Set of `Literal` instances interpreted as valid.

        Returns:
            Boolean indicating whether or not the element condition is part of the specified set of literals.
        """  # noqa
        # check if all condition literals are part of the specified set
        return all(literal in literals for literal in self.literals)


class Choice(Expr):
    """Choice expression.

    Attributes:
        elements: Tuple of `ChoiceElement` instances representing the set of choice elements.
        lguard: Optional left `Guard` instance.
        rguard: Optional right `Guard` instance.
        guards: Tuple of `lguard` and `rguard`.
        ground: Boolean indicating whether or not the choice expression is ground.
            The expression is considered ground if all guards and elements are ground.
    """  # noqa

    def __init__(
        self: Self,
        elements: Tuple[ChoiceElement],
        guards: Optional[Union["Guard", Tuple["Guard", ...]]] = None,
    ):
        """Initializes the choice expression instance.

        Args:
            elements: Tuple of `ChoiceElement` instances representing the set of choice elements.
            guards: Optional single `Guard` instance or tuple of (maximum two) `Guard` instances.
                If two guards are specified, they are expected to represent opposite sides.
                The order of the guards is irrelevant. Defaults to None.

        Raises:
            ValueError: Invalid number of guards or multiple guards for the same side.
        """  # noqa
        # initialize left and right guard to 'None'
        self.lguard, self.rguard = None, None

        if guards is None:
            guards = tuple()

        # single guard specified
        if isinstance(guards, Guard):
            # wrap in tuple
            guards = (guards,)
        # guard tuple specified
        elif isinstance(guards, Tuple) and len(guards) > 2:
            raise ValueError("Choice expression allows at most two guards.")

        # process guards
        for guard in guards:
            if guard is None:
                continue

            if guard.right:
                if self.rguard is not None:
                    raise ValueError(
                        "Multiple right guards specified for choice expression."
                    )
                self.rguard = guard
            else:
                if self.lguard is not None:
                    raise ValueError(
                        "Multiple left guards specified for choice expression."
                    )
                self.lguard = guard

        self.elements = elements

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the choice expression to a given object.

        Considered equal if the given object is also a `Choice` instance with same
        elements and guards.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the choice expression is considered equal
            to the given object.
        """
        return (
            isinstance(other, Choice)
            and set(self.elements) == set(other.elements)
            and self.guards == other.guards
        )

    def __hash__(self: Self) -> int:
        return hash(("choice", frozenset(self.elements), self.guards))

    def __str__(self: Self) -> str:
        """Returns the string representation for the choice expression.

        Returns:
            String representing the choice expression.
            Contains the string representations of the elements, separated by semicolons,
            Guard representations precede or succeed the string if specified.
        """  # noqa
        elements_str = ";".join([str(literal) for literal in self.elements])
        lguard_str = f"{str(self.lguard)} " if self.lguard is not None else ""
        rguard_str = f" {str(self.rguard)}" if self.rguard is not None else ""

        return f"{lguard_str}{{{elements_str}}}{rguard_str}"

    def __iter__(self: Self) -> Iterator[ChoiceElement]:
        return iter(self.elements)

    def __len__(self: Self) -> int:
        return len(self.head)

    @property
    def head(self: Self) -> LiteralCollection:
        return LiteralCollection(*tuple(element.atom for element in self.elements))

    @property
    def body(self: Self) -> LiteralCollection:
        return LiteralCollection(
            *chain(*tuple(element.literals for element in self.elements))
        )

    @cached_property
    def ground(self: Self) -> bool:
        return all(element.ground for element in self.elements)

    @property
    def guards(self: Self) -> Tuple[Union["Guard", None], Union["Guard", None]]:
        return (self.lguard, self.rguard)

    def invars(self: Self) -> Set["Variable"]:
        """Inner variables.

        Returns:
            Set of `Variable` instances that occurr inside any of the elements.
        """
        return set().union(*tuple(element.vars() for element in self.elements))

    def outvars(self: Self) -> Set["Variable"]:
        """Outer variables.

        Returns:
            Set of `Variable` instances that occurr in any of the guards.
        """
        return set().union(
            *tuple(guard.bound.vars() for guard in self.guards if guard is not None)
        )

    def vars(self: Self) -> Set["Variable"]:
        """Returns the variables associated with the choice expressions.

        Union of the sets of inner and outer variables.

        Returns:
            (Possibly empty) set of `Variable` instances.
        """  # noqa
        return self.invars().union(self.outvars())

    def global_vars(self: Self, statement: "Statement") -> Set["Variable"]:
        """Returns the global variables associated with the choice expression.

        For choice exressions the set of inner and outer variables that are global
        in the body of the specified statement are considered global.

        Args:
            statement: Optional `Statement` instance the choice expression appears in.

        Returns:
            A (possibly empty) set of `Variable` instances.
        """
        glob_body_vars = statement.body.global_vars()

        return self.outvars().union(self.invars().intersection(glob_body_vars))

    def pos_occ(self: Self) -> "LiteralCollection":
        """Positive literal occurrences.

        Returns:
            Union of the sets of `Literal` instances that occur positively in the elements.
        """  # noqa
        return LiteralCollection(
            *itertools.chain(*tuple(element.pos_occ() for element in self.elements))
        )

    def neg_occ(self: Self) -> "LiteralCollection":
        """Negative literal occurrences.

        Returns:
            Union of the sets of `Literal` instances that occur negatively in the elements.
        """  # noqa
        return LiteralCollection(
            *itertools.chain(*tuple(element.neg_occ() for element in self.elements))
        )

    @classmethod
    def eval(
        cls: Type["Choice"],
        atoms: Set["PredLiteral"],
        guards: Tuple[Optional[Guard], Optional[Guard]],
    ) -> bool:
        """Evaluates a choice aggregate.

        Args:
            atoms: Set of `PredLiteral` instances.
            guards: Tuple of optional left and right `Guard` instances.
                The order is irrelevant.

        Returns:
            Boolean indicating whether or not the specified guards are satisfiable
            for a choice expression with given atoms.
        """  # noqa
        if not all(atom.ground for atom in atoms):
            raise ValueError("Cannot evaluate non-ground choice expression.")

        n_atoms = Number(len(atoms))

        res = True

        for guard in guards:
            if guard is None:
                continue

            op, bound, right = guard

            # move operator to right-hand side (for canonical processing)
            if not right:
                op = -op

            if op in {RelOp.GREATER, RelOp.GREATER_OR_EQ}:
                # make sure there are enough elements to potentially satisfy bound
                res &= op.eval(n_atoms, bound)
            elif op in {RelOp.EQUAL}:
                # make sure there are enough elements to potentially satisfy bound
                # and that bound is not negative (i.e., unsatisfiable)
                res &= (bound.val >= 0) and GreaterEqual(n_atoms, bound).eval()
            elif op in {RelOp.UNEQUAL}:
                # only edge case '!= 0', but no elements (i.e., unsatisfiable)
                res &= (bound.val != 0) or n_atoms.val > 0
            else:
                # make sure that upper bound can be satisfied
                res &= op.eval(Number(0), bound)

        return res

    def propagate(
        self: Self,
        guards: Tuple[Optional[Guard], Optional[Guard]],
        elements: Set["ChoiceElement"],
        literals_I: Set["Literal"],
        literals_J: Set["Literal"],
    ) -> bool:
        """Choice propagation to approximate satisfiability.

        Approximates whether or not the choice expression is satisfiable for
        given guards, choice elements and domains of literals.
        Note: this procedure is not exact, but only an approximation.

        For details see Kaminski & Schaub (2022): "On the Foundations of Grounding in Answer Set Programming".
        The implementation here is partly based on the aggregate propagation in
        `mu-gringo`: https://github.com/potassco/mu-gringo.

        Args:
            guards: Tuple of two optional `Guard` instances. The order is irrelevant.
            elements: Set of `ChoiceElements` to be used.
            literals_I: domain of literals (`I` in the paper).
            literals_J: domain of literals (`J` in the paper).
        """  # noqa

        # cache holding intermediate results (to avoid recomputation)
        propagation_cache = dict()
        # elements that are satisfied by I and J, respectively (initialize to None)
        elements_I = None
        elements_J = None

        def get_I_elements() -> Set["ChoiceElement"]:
            nonlocal elements_I

            if elements_I is None:
                elements_I = {
                    element for element in elements if element.satisfied(literals_I)
                }
            return elements_I

        def get_J_elements() -> Set["ChoiceElement"]:
            nonlocal elements_J

            if elements_J is None:
                elements_J = {
                    element for element in elements if element.satisfied(literals_J)
                }
            return elements_J

        def get_propagation_result(
            op: RelOp, bound: "Term", domain: Set["ChoiceElement"]
        ) -> bool:
            nonlocal propagation_cache

            if (op, bound) not in propagation_cache:
                propagation_cache[(op, bound)] = op2rel[op](
                    Number(len({element.atom for element in domain})), bound
                ).eval()
            return propagation_cache[(op, bound)]

        def propagate_subset(
            op,
            bound,
            elements_I: Set["ChoiceElement"],
            elements_J: Set["ChoiceElement"],
        ) -> bool:
            # test all combinations of subsets of candidates
            # TODO: may be complete overkill (hence, inefficient!)
            for X in powerset(
                {element.atom for element in elements_I.union(elements_J)}
            ):
                if op.eval(bound, Number(len(X))):
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
                res &= get_propagation_result(op, bound, set())
            elif op == RelOp.EQUAL:
                # check upper bound (TODO: suffices?)
                res &= get_propagation_result(
                    RelOp.GREATER_OR_EQ, bound, get_J_elements()
                )
            elif op == RelOp.UNEQUAL:
                # check if any subset of elements satisfies bound
                res &= propagate_subset(op, bound, get_I_elements(), get_J_elements())

        return res

    def safety(self: Self, statement: Optional["Statement"] = None) -> SafetyTriplet:
        """Returns the the safety characterizations for the choice expression.

        Raises an exception, since safety characterization is undefined for choice expressions.
        For details see Bicheler (2015): "Optimizing Non-Ground Answer Set Programs via Rule Decomposition".

        Args:
            statement: Optional `Statement` instance the term appears in.
                Irrelevant for aggregate elements. Defaults to `None`.

        Returns:
            `SafetyTriplet` instance.

        Raises:
            ValueError: Safety characterization is undefined for choice expressions.
        """  # noqa
        raise Exception("Safety characterization not defined for choice expressions.")

    def substitute(self: Self, subst: "Substitution") -> "Choice":
        """Applies a substitution to the choice expression.

        Substitutes all guards and elements recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `Choice` instance with (possibly substituted) guards and elements.
        """
        if self.ground:
            return deepcopy(self)

        # substitute elements recursively
        elements = (element.substitute(subst) for element in self.elements)

        # substitute guard terms recursively
        guards = tuple(
            guard.substitute(subst) if guard is not None else None
            for guard in self.guards
        )

        return Choice(elements, guards)

    def replace_arith(self: Self, var_table: "VariableTable") -> "Choice":
        """Replaces arithmetic terms appearing in the choice expression with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `Choice` instance.
        """  # noqa
        # replace guards
        guards = (
            None if guard is None else guard.replace_arith(var_table)
            for guard in self.guards
        )

        return Choice(
            tuple(element.replace_arith(var_table) for element in self.elements),
            guards,
        )

    def range(self: Self) -> Iterator[int]:
        """TODO"""

        # empty set is smallest possible choice
        lb = 0
        # maximum unique atoms available
        ub = len(self.head)

        # list of invalid numbers of atoms to choose
        exclude = set()

        for guard in self.guards:
            if guard is None:
                continue
            elif guard.right:
                # transform to left guard for convenience
                guard = guard.to_left()

            # evaluate bound
            if isinstance(guard.bound, Infimum):
                # bound is smaller than all integers
                bound = -float("inf")
            elif not isinstance(guard.bound, Number):
                # bound is larger than all integers
                bound = float("inf")
            else:
                # bound is an integer
                bound = guard.bound.eval()

            # process bounds
            if guard.op == RelOp.EQUAL:
                if bound in exclude or lb > bound or ub < bound:
                    # choice cannot be satisfied (no valid choices)
                    return tuple()

                # set both lower & upper bound
                lb = bound
                ub = bound
            elif guard.op == RelOp.UNEQUAL:
                exclude.add(bound)
            elif guard.op == RelOp.LESS:
                lb = max(lb, bound - 1) if bound != float("inf") else tuple()
            elif guard.op == RelOp.GREATER:
                ub = min(ub, bound - 1) if bound != -float("inf") else tuple()
            elif guard.op == RelOp.LESS_OR_EQ:
                lb = max(lb, bound) if bound != float("inf") else tuple()
            elif guard.op == RelOp.GREATER_OR_EQ:
                ub = min(ub, bound) if bound != -float("inf") else tuple()

        return (r for r in range(lb, ub + 1) if r not in exclude)


class ChoiceRule(Statement):
    r"""Choice rule.

    Statement of form:
        :math:`t_1` :math:`\prec_1` {:math:`e_1`;:math:`\dots`;:math:`e_m`} :math:`\prec_2` :math:`t_2` :- :math:`b_1,\dots,b_n` or
        :math:`t_1` :math:`\prec_1` {:math:`e_1`;:math:`\dots`;:math:`e_m`} :- :math:`b_1,\dots,b_n` or
        {:math:`e_1`;:math:`\dots`;:math:`e_m`} :math:`\prec_2` :math:`t_2` :- :math:`b_1,\dots,b_n` or
        {:math:`e_1`;:math:`\dots`;:math:`e_m`} :- :math:`b_1,\dots,b_n`.

    where:
        :math:`e_1,\dots,e_m` are choice elements with :math:`m\ge0`.
            Each element is of form :math:`h_i`::math:`c_{i1},\dots,c_{ik_i}`
            with atom :math:`h_i`, literals :math:`c_{i1},\dots,c_{ik_i}` (called condition),
            :math:`i\in\{1,\dots,m\}` and :math:`k_i\ge0`.
        :math:`b_1,\dots,b_n` are literals with :math:`n\ge0`.
        :math:`t_1,t_2` are bound terms with corresponding relational operators :math:`\prec_1,\prec_2`.

    Semantically, any answer set that includes :math:`b_1,\dots,b_n` may include any bound-satisfying subset
    of atoms :math:`h_i,i=1,...,m` whose corresponding elements are satisfied. An element is satisfied
    if its condition :math:`c_{i1},\dots,c_{ik_i}` is part of the answer set.
    If no bounds are specified, any subset is valid.

    Attributes:
        choice: TODO
        literals: TODO
        head: TODO
        body: TODO
        var_table: `VariableTable` instance for the statement.
        safe: Boolean indicating whether or not the statement is considered safe.
        ground: Boolean indicating whether or not the statement is ground.
        deterministic: Boolean indicating whether or not the consequent of the rule is
            deterministic. Always `False` for choice rules.
        contains_aggregates: Boolean indicating whether or not the statement contains
            aggregate expressions.
    """  # noqa

    def __init__(
        self: Self,
        head: Choice,
        body: Optional[Iterable["Literal"]] = None,
        *args,
        **kwargs,
    ) -> None:
        """Initializes the choice rule instance.

        Args:
            head: `Choice` instance.
            body: Optional iterable over `Literal` instances.
                Defaults to None.
        """
        super().__init__(*args, **kwargs)

        if body is None:
            body = tuple()

        # TODO: correctly infer determinism after propagation/grounding?
        self.deterministic: bool = False

        self.choice = head
        self.literals = (
            body if isinstance(body, LiteralCollection) else LiteralCollection(*body)
        )

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the statement to a given object.

        Considered equal if the given object is also a `ChoiceRule` instance with same choice and
        literals.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the statement is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, ChoiceRule)
            and self.head == other.head
            and self.literals == other.literals
        )

    def __hash__(self: Self) -> int:
        return hash(("choice rule", self.head, self.literals))

    def __str__(self: Self) -> str:
        """Returns the string representation for the statement.

        Returns:
            String representing the statement.
        """
        return f"{str(self.head)}{f' :- {str(self.body)}' if self.body else ''}."

    @property
    def head(self: Self) -> Choice:
        return self.choice

    @property
    def body(self: Self) -> LiteralCollection:
        return self.literals

    @cached_property
    def safe(self: Self) -> bool:
        outside_glob_vars = self.body.global_vars().union(self.choice.outvars())

        for element in self.choice:
            global_vars = outside_glob_vars.union(element.head.global_vars())

            if LiteralCollection(*self.body, *element.body).safety(
                self
            ) != SafetyTriplet(global_vars):
                return False

        return True

    @cached_property
    def ground(self: Self) -> bool:
        return self.head.ground and self.body.ground

    def consequents(self: Self) -> "LiteralCollection":
        """Returns the consequents of the statement.

        Returns:
            `LiteralCollection` instance.
        """
        return self.choice.head

    def antecedents(self: Self) -> "LiteralCollection":
        """Returns the antecedents of the statement.

        Returns:
            `LiteralCollection` instance.
        """
        return LiteralCollection(*self.literals, *self.choice.body)

    def safety(
        self: Self, statement: Optional[Union["Statement", "Query"]] = None
    ) -> "SafetyTriplet":
        raise Exception("Safety characterization for choice rules not supported yet.")

    def substitute(self: Self, subst: "Substitution") -> "ChoiceRule":
        """Applies a substitution to the statement.

        Substitutes the choice and all literals recursively.

        Args:
            subst: `Substitution` instance.

        Returns:
            `ChoiceRule` instance with (possibly substituted) choice and literals.
        """
        if self.ground:
            return deepcopy(self)

        return ChoiceRule(self.head.substitute(subst), self.body.substitute(subst))

    def replace_arith(self: Self) -> "ChoiceRule":
        """Replaces arithmetic terms appearing in the statement with arithmetic variables.

        Note: arithmetic terms are not replaced in-place.

        Args:
            var_table: `VariableTable` instance.

        Returns:
            `ChoiceRule` instance.
        """  # noqa
        return ChoiceRule(
            self.head.replace_arith(self.var_table),
            self.body.replace_arith(self.var_table),
        )

    def rewrite_aggregates(
        self: Self,
        aggr_counter: int,
        aggr_map: Dict[
            int,
            Tuple[
                "AggrLiteral",
                "AggrPlaceholder",
                "AggrBaseRule",
                Set["AggrElemRule"],
            ],
        ],
    ) -> "ChoiceRule":
        """Rewrites aggregates expressions inside the statement.

        Args:
            aggr_counter: Integer representing the current count of rewritten aggregates
                in the Program. Used as unique ids for placeholder literals.
            aggr_map: Dictionary mapping integer aggregate ids to tuples consisting of
                the original `AggrLiteral` instance replaced, the `AggrPlaceholder`
                instance replacing it in the original statement, an `AggrBaseRule`
                instance and a set of `AggrElemRule` instances representing rules for
                propagation. Pre-existing content in the dictionary is irrelevant for
                the method, the dictionary is simply updated in-place.

        Returns:
            `ChoiceRule` instance representing the rewritten original statement without
            any aggregate expressions.
        """

        # global variables
        glob_vars = self.global_vars()

        # group literals
        non_aggr_literals = []
        aggr_literals = []

        for literal in self.body:
            (
                aggr_literals if isinstance(literal, AggrLiteral) else non_aggr_literals
            ).append(literal)

        # mapping from original literals to alpha literals
        alpha_map = dict()

        # local import due to circular import
        from .rewrite import rewrite_aggregate

        for literal in aggr_literals:
            # rewrite aggregate literal
            alpha_literal, eps_rule, eta_rules = rewrite_aggregate(
                literal, aggr_counter, glob_vars, non_aggr_literals
            )

            # map original aggregate literal to new alpha literal
            alpha_map[literal] = alpha_literal

            # store aggregate information
            aggr_map[aggr_counter] = (literal, alpha_literal, eps_rule, eta_rules)

            # increase aggregate counter
            aggr_counter += 1

        # replace original rule with modified one
        alpha_rule = ChoiceRule(
            self.choice,
            tuple(
                alpha_map[literal] if isinstance(literal, AggrLiteral) else literal
                for literal in self.body
            ),  # NOTE: restores original order of literals
        )

        return alpha_rule

    def assemble_aggregates(
        self: Self, assembling_map: Dict["AggrPlaceholder", "AggrLiteral"]
    ) -> "ChoiceRule":
        """Reassembles rewritten aggregates expressions inside the statement.

        Args:
            assembling_map: Dictionary mapping `AggrPlaceholder` instances to
                `AggrLiteral` instances to be replaced with.

        Returns:
            `ChoiceRule` instance representing the reassembled original statement.
        """
        return ChoiceRule(
            self.choice,
            *tuple(
                literal if literal not in assembling_map else assembling_map[literal]
                for literal in self.body
            ),
        )

    def rewrite_choices(
        self: Self,
        choice_counter: int,
        choice_map: Dict[
            int,
            Tuple[
                "Choice",
                "ChoicePlaceholder",
                "ChoiceBaseRule",
                Set["ChoiceElemRule"],
            ],
        ],
    ) -> "NormalRule":
        """Rewrites choice expressions inside the statement.

        Args:
            choice_counter: Integer representing the current count of rewritten choice
                expressions in the Program. Used as unique ids for placeholder literals.
            aggr_map: Dictionary mapping integer choice ids to tuples consisting of
                the original `Choice` instance replaced, the `ChoicePlaceholder`
                instance replacing it in the original statement, a `ChoiceBaseRule`
                instance and a set of `ChoiceElemRule` instances representing rules for
                propagation. Pre-existing content in the dictionary is irrelevant for
                the method, the dictionary is simply updated in-place.

        Returns:
            `NormalRule` instance representing the rewritten original statement without
            any choice expressions.
        """

        # global variables
        glob_vars = self.global_vars()  # TODO: correct ???

        # local import due to circular import
        from .rewrite import rewrite_choice

        chi_literal, eps_rule, eta_rules = rewrite_choice(
            self.choice, choice_counter, glob_vars, self.literals
        )

        # store choice information
        choice_map[choice_counter] = (self.choice, chi_literal, eps_rule, eta_rules)

        # replace original rule with modified one
        chi_rule = NormalRule(chi_literal, self.literals)

        return chi_rule

    @cached_property
    def is_fact(self: Self) -> bool:
        return bool(self.literals)

    def powerset(
        self: Self,
    ) -> List[Tuple[int, ...]]:
        """TODO"""

        n_out = len(self.choice)

        # return all possible combinations with ub >= n >= lb, n not excluded
        return sum(
            [list(combinations(range(n_out), r=n)) for n in self.choice.range()],
            [],
        )
