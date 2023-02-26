from typing import Optional, Tuple, Set, Union, TYPE_CHECKING
from functools import cached_property
from copy import deepcopy

from aspy.program.expression import Expr
from aspy.program.literals import LiteralTuple
from aspy.program.safety_characterization import SafetyTriplet

from .statement import Fact, Rule

if TYPE_CHECKING:
    from aspy.program.substitution import Substitution
    from aspy.program.terms import Term, Variable
    from aspy.program.literals import PredicateLiteral, Guard
    from aspy.program.operators import RelOp

    from .statement import Statement


class ChoiceElement(Expr):
    """Choice element."""
    def __init__(self, atom: "PredicateLiteral", literals: Optional["LiteralTuple"]=None) -> None:
        if literals is None:
            literals = LiteralTuple()

        # TODO: debug tests for literals types

        self.atom = atom
        self.literals = literals

    def __str__(self) -> str:
        return f"{str(self.atom)}:{','.join([str(literal) for literal in self.literals])}"

    @property
    def head(self) -> LiteralTuple:
        return LiteralTuple([self.atom])

    @property
    def body(self) -> LiteralTuple:
        return self.literals

    @cached_property
    def ground(self) -> bool:
        return self.atom.ground and all(literal.ground for literal in self.literals)

    def vars(self, global_only: bool=False) -> Set["Variable"]:
        # TODO: global
        if global_only:
            raise Exception()

        return set().union(literal.vars() for literal in self.literals)

    def safety(self, rule: Optional["Statement"], global_vars: Optional[Set["Variable"]]=None) -> "SafetyTriplet":
        raise Exception()

    def substitute(self, subst: "Substitution") -> "ChoiceElement":
        raise Exception("Substitution for choice elements not supported yet.")

    def match(self, other: Expr) -> Set["Substitution"]:
        raise Exception("Matching for choice elements not supported yet.")


class Choice(Expr):
    """Choice."""
    def __init__(self, elements: Optional[Tuple[ChoiceElement]]=None, guards: Optional[Union["Guard", Tuple["Guard", ...]]]=None):
        if guards is None:
            guards = tuple()

        # initialize left and right guard to 'None'
        self.lguard, self.rguard = None, None

        # single guard specified
        if isinstance(guards, Guard):
            # wrap in tuple
            guards = (guards, )
        # no guards specified
        elif guards is None:
            # TODO: set default guards
            raise Exception()
        # guard tuple specified
        elif isinstance(guards, Tuple) and len(guards) > 2:
            raise ValueError("Choice expression requires at least one and at most two guards to be specified.")
        else:
            raise ValueError(f"Invalid specification of aggregate guards: {guards}.")

        # process guards
        for guard in guards:
            if guard.right:
                if self.rguard is not None:
                    raise ValueError("Multiple right guards specified for choice expression.")
                self.rguard = guard
            else:
                if self.lguard is not None:
                    raise ValueError("Multiple right guards specified for choice expression.")
                self.lguard = guard

        if elements is None:
            elements = tuple()

        self.elements = elements

    def __str__(self) -> str:
        return (f"{str(self.lguard.bound)} {str(self.lguard.op)}" if self.lguard else "") + f"{{{';'.join([str(literal) for literal in self.elements])}}}" + (f"{str(self.rguard.op)} {str(self.rguard.bound)}" if self.lguard else "")

    @cached_property
    def ground(self) -> bool:
        return all(element.ground for element in self.elements)

    def guards(self) -> Tuple[Union["Guard", None], Union["Guard", None]]:
        return (self.lguard, self.rguard)

    def vars(self, global_only: bool=False) -> Set["Variable"]:
        # TODO: global
        if global_only:
            raise Exception()

        return set().union(guard.bound.vars() for guard in self.guards() if guard is not None)

    def substitute(self, subst: "Substitution") -> "Choice":
        if self.ground:
            return deepcopy(self)

        # substitute elements recursively
        elements = (element.substitute(subst) for element in self.elements)
    
        # substitute guard terms recursively
        guards = tuple(guard.substitute(subst) if guard is not None else None for guard in self.guards)

        return Choice(elements, guards)

    def match(self, other: Expr) -> Set["Substitution"]:
        raise Exception("Matching for choice expressions not supported yet.")


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
    def __init__(self, head: Choice, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.choice = head

    def __str__(self) -> str:
        return f"{{{','.join([str(literal) for literal in self.head.elements])}}}."

    def body(self) -> LiteralTuple:
        return LiteralTuple()

    def safety(self, rule: Optional["Statement"], global_vars: Optional[Set["Variable"]]=None) -> "SafetyTriplet":
        raise Exception()

    @cached_property
    def safe(self) -> bool:
        return len(self.vars()) > 0

    @cached_property
    def ground(self) -> bool:
        return self.head.ground

    def safety(self, rule: Optional["Statement"], global_vars: Optional[Set["Variable"]]=None) -> "SafetyTriplet":
        raise Exception("Safety characterization for choice facts not supported yet.")

    def substitute(self, subst: "Substitution") -> "ChoiceFact":
        if self.ground:
            return deepcopy(self)

        return ChoiceFact(self.head.substitute(subst))

    def match(self, other: Expr) -> Set["Substitution"]:
        raise Exception("Matching for choice facts not supported yet.")


class ChoiceRule(Rule):
    """Choice rule.

    Rule of form:

        u_1 R_1 { h_1 ; ... ; h_m } R_2 u_2 :- b_1,...,b_n .

    for classical atoms h_1,...,h_m, literals b_1,...,b_n, terms u_1,u_2 and comparison operators R_1,R_2.

    Semantically, any answer set that includes b_1,...,b_n may also include any subset of {h_1,...,h_m} (including the empty set).
    """
    def __init__(self, head: Choice, body: LiteralTuple, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.choice = head
        self.literals = body

    def __str__(self) -> str:
        return f"{str(self.head)} :- {', '.join([str(literal) for literal in self.body])}."

    @property
    def head(self) -> Choice:
        # TODO: correct?
        return self.choice

    @property
    def body(self) -> LiteralTuple:
        return self.literals

    @cached_property
    def safe(self) -> bool:
        global_vars = self.vars(global_only=True)
        body_safety = SafetyTriplet.closure(self.body.safety(global_vars=global_vars))

        return body_safety == SafetyTriplet(global_vars)

    @cached_property
    def ground(self) -> bool:
        return self.head.ground and self.body.ground

    def safety(self, rule: Optional["Statement"], global_vars: Optional[Set["Variable"]]=None) -> "SafetyTriplet":
        raise Exception("Safety characterization for choice rules not supported yet.")

    def substitute(self, subst: "Substitution") -> "ChoiceRule":
        if self.ground:
            return deepcopy(self)

        return ChoiceRule(self.head.substitute(subst), self.body.substitute(subst))

    def match(self, other: Expr) -> Set["Substitution"]:
        raise Exception("Matching for choice rules not supported yet.")