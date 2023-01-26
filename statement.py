from typing import Tuple, Dict, Union, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

from expression import Expr
from term import Term
from atom import ClassicalAtom, Literal
from choice import Choice
from aggregate import AggregateLiteral
from tables import VariableTable


class Statement(Expr, ABC):
    """Abstract base class for all statements."""
    def __init__(self) -> None:
        # initialize variable table
        self.variables = VariableTable()

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def substitute(self, subst: Dict[str, Term]) -> "Statement":
        """substitutes the statement by replacing all variables with assigned terms."""
        pass

    def is_ground(self) -> bool:
        """Checks whether or not the statement contains any variables."""
        return not self.variables.variables

    def is_safe(self) -> bool:
        """Checks whether or not the statement is safe."""
        return all(self.variables.variables.values())

    def set_variable_table(self, variables: VariableTable) -> None:
        self.variables = variables


class Fact(Statement, ABC):
    """Abstract base class for all facts."""
    pass


@dataclass
class NormalFact(Fact):
    """Normal fact.

    Rule of form

        h :- .

    for a classical atom h. The symbol ':-' may be omitted.

    Semantically, any answer set must include h.
    """
    head: ClassicalAtom

    def __repr__(self) -> str:
        return f"NormalFact[{repr(self.head)}]"

    def __str__(self) -> str:
        return f"{str(self.head)}."

    def substitute(self, subst: Dict[str, Term]) -> "NormalFact":
        return NormalFact(self.head.substitute(subst))


@dataclass
class DisjunctiveFact(Fact):
    """Disjunctive fact.
    
    Rule of form

        h_1 | ... | h_m :- .

    for classical atoms h_1,...,h_m. The symbol ':-' may be omitted.

    Semantically, any answer set must include exactly one classical atom h_i.
    """
    head: Tuple[ClassicalAtom, ...]

    def __repr__(self) -> str:
        return f"DisjunctiveFact[{'| '.join([repr(atom) for atom in self.head])}]"

    def __str__(self) -> str:
        return ' | '.join([str(atom) for atom in self.head]) + '.'

    def substitute(self, subst: Dict[str, Term]) -> "DisjunctiveFact":
        return DisjunctiveFact(tuple([atom.substitute(subst) for atom in self.head]))


@dataclass
class ChoiceFact(Fact):
    """Choice fact.

    Rule of form

        u_1 R_1 { h_1,...,h_m } R_2 u_2 :- .

    for classical atoms h_1,...,h_m, terms u_1,u_2 and comparison operators R_1,R_2.
    The symbol ':-' may be omitted.

    TODO: R_1, R_2 may be omitted
    TODO: u_1,R_1 u_2,R_2 may be omitted.

    Semantically, any answer set may include any subset of {h_1,...,h_m} (including the empty set).
    """
    def __init__(self, head: Choice) -> None:
        self.head = head

    def __repr__(self) -> str:
        return f"ChoiceFact[{repr(self.head)}]"

    def __str__(self) -> str:
        return f"{{{','.join([str(literal) for literal in self.head.literals])}}}."

    def substitute(self, subst: Dict[str, Term]) -> "ChoiceFact":
        return ChoiceFact(self.head.substitute(subst))

    def transform(self) -> Tuple[Union[DisjunctiveFact, "Constraint"], ...]:
        """TODO"""
        raise Exception("Transformation of choice facts not supported yet.")


@dataclass
class NormalRule(Statement):
    """Normal rule.

    Rule of form:

        h :- b_1, ..., b_n .

    for a classical atom h and literals b_1,...,b_n.

    Semantically, any answer set that includes b_1,...,b_n must also include h.
    """
    head: ClassicalAtom
    body: Tuple[Literal, ...]

    def __repr__(self) -> str:
        return f"NormalRule[{repr(self.head)}]({', '.join([repr(literal) for literal in self.body])})"

    def __str__(self) -> str:
        return f"{str(self.head)} :- {', '.join([str(literal) for literal in self.body])}."

    def substitute(self, subst: Dict[str, Term]) -> "NormalRule":
        return NormalRule(self.head.substitute(subst), tuple([literal.substitute(subst) for literal in self.body]))


@dataclass
class DisjunctiveRule(Statement):
    """Disjunctive rule.
    
    Rule of form:

        h_1 | ... | h_m :- b_1,...,b_n .

    for classical atoms h_1,...,h_m and literals b_1,...,b_n.

    Semantically, any answer set that includes b_1,...,b_n must also include exactly one h_i.
    """
    head: Tuple[ClassicalAtom, ...]
    body: Tuple[Literal, ...]

    def __repr__(self) -> str:
        return f"DisjunctiveRule[{' | '.join([repr(atom) for atom in self.head])}]({', '.join([repr(literal) for literal in self.body])})"

    def __str__(self) -> str:
        return f"{' | '.join([repr(atom) for atom in self.head])} :- {', '.join([str(literal) for literal in self.body])}."

    def substitute(self, subst: Dict[str, Term]) -> "DisjunctiveRule":
        return DisjunctiveFact(tuple([atom.substitute(subst) for atom in self.head]), tuple([literal.substitute(subst) for literal in self.body]))


@dataclass
class ChoiceRule(Statement):
    """Choice rule.

    Rule of form:

        u_1 R_1 { h_1 ; ... ; h_m } R_2 u_2 :- b_1,...,b_n .

    for classical atoms h_1,...,h_m, literals b_1,...,b_n, terms u_1,u_2 and comparison operators R_1,R_2.

    Semantically, any answer set that includes b_1,...,b_n may also include any subset of {h_1,...,h_m} (including the empty set).
    """
    head: Choice
    body: Tuple[Literal, ...]

    def __repr__(self) -> str:
        return f"ChoiceRule[{repr(self.head)}]({', '.join([repr(literal) for literal in self.body])})"

    def __str__(self) -> str:
        return f"{str(self.head)} :- {', '.join([str(literal) for literal in self.body])}."

    def substitute(self, subst: Dict[str, Term]) -> "ChoiceFact":
        return ChoiceFact(self.head.substitute(subst), tuple([literal.substitute(subst) for literal in self.body]))

    def transform(self) -> Tuple[Union[DisjunctiveRule, "Constraint"], ...]:
        """TODO"""
        raise Exception("Transformation of choice rules not supported yet.")


# TODO: cardinality rules? not part of standard (syntactic sugar?)
# TODO: weight rules? not part of standard (syntactic sugar?)

@dataclass
class Constraint(Statement):
    """Constraint.

    Statement of form:

        :- b_1,...,b_n .

    for literals b_1,...,b_n.
    """
    body: Tuple[Literal, ...]

    def __repr__(self) -> str:
        return f"Constraint({', '.join([repr(literal) for literal in self.body])})"

    def __str__(self) -> str:
        return f":- {', '.join([str(literal) for literal in self.body])}."

    def substitute(self, subst: Dict[str, Term]) -> "Constraint":
        return Constraint(tuple([literal.substitute(subst) for literal in self.body]))

    def transform(self) -> Tuple[NormalRule]:
        """TODO"""
        raise Exception("Transformation of constraints not supported yet.")


@dataclass
class WeakConstraint(Statement):
    """Weak constraint.

    Statement of form:

        :~ b_1,...,b_n . [ w@l,t_1,...,t_m ]

    for literals b_1,...,b_n and terms w,l,t_1,...,t_m.
    '@ l' may be omitted if l=0.
    """
    body: Tuple[Literal, ...]
    weight: Term
    level: Term
    terms: Tuple[Term, ...]

    def __repr__(self) -> str:
        return f"WeakConstraint({', '.join([repr(literal) for literal in self.body])},{repr(self.weight)}@{repr(self.level)},{', '.join([repr(term) for term in self.terms])})"

    def __str__(self) -> str:
        return f":~ {', '.join([str(literal) for literal in self.body])}. [{str(self.weight)}@{str(self.level)}, {', '.join([str(term) for term in self.terms])}]"

    def substitute(self, subst: Dict[str, Term]) -> "WeakConstraint":
        return WeakConstraint(tuple([literal.substitute(subst) for literal in self.literal]), self.weight.substitute(subst), self.level.substitute(subst), tuple([term.substitute(subst) for term in self.body]))

    def transform(self) -> Tuple["WeakConstraint", ...]:
        """Handles any aggregates in the constraint body."""

        pos_aggr_ids = []
        neg_aggr_ids = []

        for i, term in enumerate(self.body):
            if isinstance(term, AggregateLiteral):
                if term.neg:
                    # TODO
                    pass
                else:
                    pass

                # TODO: check if aggregate is NOT
                # TODO: call transform on resulting weak constraints to handle additional aggregates!
                break
        
        raise Exception("Transformation of weak constraints is not supported yet.")


@dataclass
class OptimizeElement(Expr):
    """Optimization element for optimize statements.
    
    Expression of form:

        w @ l,t_1,...,t_m : b_1,...,b_n

    for terms w,l,t_1,...,t_m and literals b_1,...,b_n.
    '@ l' may be omitted if l=0.
    """
    weight: Term
    level: Term
    terms: Tuple[Term]
    literals: Tuple[Literal, ...]

    def __repr__(self) -> str:
        return f"OptimizeElement({repr(self.weight)}@{repr(self.level)}, {', '.join([repr(term) for term in self.terms])} : {', '.join([repr(literal) for literal in self.literals])})"

    def __str__(self) -> str:
        return f"{str(self.weight)}@{str(self.level)}, {', '.join([str(term) for term in self.terms])} : {', '.join([str(literal) for literal in self.literals])}"

    def substitute(self, subst: Dict[str, Term]) -> "OptimizeElement":
        return OptimizeElement(self.weight.substitute(subst), self.level.substitute(subst), tuple([term.substitute(subst) for term in self.terms]), tuple([literal.substitute(subst) for literal in self.literals]))


@dataclass
class OptimizeStatement(Statement, ABC):
    """Abstract base class for all optimize statement."""
    elements: Tuple[OptimizeElement, ...]
    minimize: bool

    def transform(self) -> Tuple[WeakConstraint, ...]:
        """Transforms the optimize statement into (possibly multiple) weak constraints."""
        # transform each optimize element into a weak constraint
        return tuple(
            WeakConstraint(
                element.literals,
                element.weight,
                element.level,
                element.terms
            )
            for element in self.elements
        )


class MinimizeStatement(OptimizeStatement):
    """Minimize statement.

    Statement of the form:

        #minimize{w_1@l_1,t_{11},...,t_{1m}:b_{11},...,b_{1n};...;w_k@l_k,t_{k1},...,t_{km}:b_{k1},...,b_{kn}}

    for literals b_{11},...,b_{1n},...,b_{k1},...,b_{kn} and terms w_1,...,w_k,l_1,...,l_k,t_{11},...,t_{1m},t_{k1},...,t_{km}.

    Can alternatively be written as multiple weak constraints:

        :~ b_{11},...,b_{1n}. [w_1@l_1,t_{11},...,t_{1m}]
        ...
        :~ b_{k1},...,b_{kn}. [w_k@l_1,t_{k1},...,t_{km}]
    """
    def __init__(self, elements: Tuple[OptimizeElement, ...]) -> None:
        super().__init__(elements, True)

    def __repr__(self) -> str:
        return f"Minimize({', '.join([repr(element) for element in self.elements])})"

    def __str__(self) -> str:
        return f"#minimize{{{' ; '.join([str(element) for element in self.elements])}}}"

    def substitute(self, subst: Dict[str, Term]) -> "MinimizeStatement":
        return OptimizeStatement(
            self.elements.substitute(subst)
        )


class MaximizeStatement(OptimizeStatement):
    """Maximize statement.

    Statement of the form:

        #maximize{w_1@l_1,t_{11},...,t_{1m}:b_{11},...,b_{1n};...;w_k@l_k,t_{k1},...,t_{km}:b_{k1},...,b_{kn}}

    for literals b_{11},...,b_{1n},...,b_{k1},...,b_{kn} and terms w_1,...,w_k,l_1,...,l_k,t_{11},...,t_{1m},t_{k1},...,t_{km}.

    Can alternatively be written as multiple weak constraints:

        :~ b_{11},...,b_{1n}. [-w_1@l_1,t_{11},...,t_{1m}]
        ...
        :~ b_{k1},...,b_{kn}. [-w_k@l_1,t_{k1},...,t_{km}]
    """
    def __init__(self, elements: Tuple[OptimizeElement, ...]) -> None:
        super().__init__(elements, False)

    def __repr__(self) -> str:
        return f"Maximize({', '.join([repr(element) for element in self.elements])})"

    def __str__(self) -> str:
        return f"#maximize{{{' ; '.join([str(element) for element in self.elements])}}}"

    def substitute(self, subst: Dict[str, Term]) -> "MaximizeStatement":
        return MaximizeStatement(
            self.elements.substitute(subst)
        )