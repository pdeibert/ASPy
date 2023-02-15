from typing import Optional, Union, Tuple, Iterable, Set, TYPE_CHECKING
from abc import ABC, abstractmethod
from functools import cached_property

import aspy
from aspy.program.expression import Expr
from aspy.program.substitution import Substitution
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.symbol_table import VARIABLE_RE, SYM_CONST_RE

if TYPE_CHECKING:
    from aspy.program.statements import Statement
    from aspy.program.query import Query


class Term(Expr, ABC):
    """Abstract base class for all terms."""
    @abstractmethod
    def precedes(self, other: "Term") -> bool:
        """Defines the total ordering operator defined for terms in ASP-Core-2."""
        pass

    def safety(self, rule: Optional[Union["Statement","Query"]]=None, global_vars: Optional[Set["Variable"]]=None) -> SafetyTriplet:
        return SafetyTriplet()


class TermTuple:
    """Represents a collection of terms."""
    def __init__(self, terms: Optional[Tuple[Term, ...]]=None) -> None:
        self.terms = terms if terms is not None else tuple()

    def __len__(self) -> int:
        return len(self.terms)

    def __eq__(self, other: "TermTuple") -> bool:
        if len(self) != len(other):
            return False

        for t1, t2 in zip(self, other):
            if t1 != t2:
                return False

        return True

    def __hash__(self) -> int:
        return hash(self.literals)

    def __iter__(self) -> Iterable[Term]:
        return iter(self.terms)

    def __add__(self, other: "TermTuple") -> "TermTuple":
        return TermTuple(self.terms + other.terms)

    @cached_property
    def ground(self) -> bool:
        return all(term.ground for term in self.terms)

    def substitute(self, subst: "Substitution") -> "TermTuple":
        # substitute terms recursively
        terms = (term.substitute(subst) for term in self)

        return TermTuple(terms)

    def vars(self, global_only: bool=False) -> Tuple[Set["Variable"], ...]:
        return tuple(term.vars(global_only) for term in self.terms)

    def safety(self, rule: Optional[Union["Statement","Query"]]=None, global_vars: Optional[Set["Variable"]]=None) -> Tuple["SafetyTriplet", ...]:
        return tuple(term.safety() for term in self.terms)


class Infimum(Term):
    """Least element in the total ordering for terms."""
    ground: bool=True

    def __str__(self) -> str:
        return "#inf"

    def __eq__(self, other) -> str:
        return isinstance(other, Infimum)

    def __hash__(self) -> int:
        return hash(("inf", ))

    def precedes(self, other: Term) -> bool:
        return True

    def vars(self, global_only: bool=False) -> Set["Variable"]:
        return set()

    def match(self, other: Expr) -> Set[Substitution]:
        """Tries to match the expression with another one."""
        if isinstance(other, Infimum):
            return set([Substitution()])
        else:
            return set()

    def substitute(self, subst: Substitution) -> "Infimum":
        return Infimum()


class Supremum(Term):
    """Greatest element in the total ordering for terms."""
    ground: bool=True

    def __str__(self) -> str:
        return "#sup"

    def __eq__(self, other) -> str:
        return isinstance(other, Supremum)

    def __hash__(self) -> int:
        return hash(("sup", ))

    def precedes(self, other: Term) -> bool:
        return False

    def vars(self, global_only: bool=False, bound_only: bool=False) -> Set["Variable"]:
        return set()

    def match(self, other: Expr) -> Set[Substitution]:
        """Tries to match the expression with another one."""
        if isinstance(other, Supremum):
            return set([Substitution()])
        else:
            return set()

    def substitute(self, subst: Substitution) -> "Supremum":
        return Supremum()


class Variable(Term):
    """Represents a variable."""
    ground: bool=False

    def __init__(self, val: str) -> None:

        # check if variable name is valid
        if aspy.debug() and not VARIABLE_RE.fullmatch(val):
            raise ValueError(f"Invalid value for {type(self)}: {val}")

        self.val = val

    def __str__(self) -> str:
        return self.val

    def __eq__(self, other) -> str:
        return isinstance(other, Variable) and other.val == self.val

    def __hash__(self) -> int:
        return hash(("var", self.val))

    def precedes(self, other: Term) -> bool:
        raise Exception("Total ordering is undefined for non-ground terms.")

    def vars(self, global_only: bool=False) -> Set["Variable"]:
        return {self}

    def safety(self, rule: Optional[Union["Statement","Query"]]=None, global_vars: Optional[Set["Variable"]]=None) -> SafetyTriplet:
        return SafetyTriplet({self})

    def simplify(self) -> "Number":
        """Used in arithmetical terms."""
        return Variable(self.val)

    def match(self, other: Expr) -> Set[Substitution]:
        """Tries to match the expression with another one."""
        return Substitution({self: other})

    def substitute(self, subst: Substitution) -> Term:
        return subst[self]


class AnonVariable(Variable):
    """Represents an anonymous variable."""
    def __init__(self, id: int) -> None:

        # check if id is valid
        if aspy.debug() and id < 0:
            raise ValueError(f"Invalid value for {type(self)}: {id}")

        self.val = f"_{id}"

    def __str__(self) -> str:
        return "_"

    def __eq__(self, other) -> str:
        return isinstance(other, AnonVariable) and other.val == self.val

    def __hash__(self) -> int:
        return hash(("var", self.val))

    def match(self, other: Expr) -> Set[Substitution]:
        """Tries to match the expression with another one."""
        return Substitution({self: other})


class Number(Term):
    """Represents a number."""
    ground: bool=True

    def __init__(self, val: int) -> None:
        self.val = val

    def __add__(self, other) -> "Number":
        return Number(self.val + other.val)

    def __sub__(self, other) -> "Number":
        return Number(self.val - other.val)

    def __mul__(self, other) -> "Number":
        return Number(self.val * other.val)

    def __floordiv__(self, other) -> "Number":
        return Number(self.val // other.val)

    def __neg__(self) -> "Number":
        return Number(-self.val)

    def __abs__(self) -> "Number":
        return Number(abs(self.val))

    def __str__(self) -> str:
        return str(self.val)

    def __eq__(self, other) -> str:
        return isinstance(other, Number) and other.val == self.val

    def __hash__(self) -> int:
        return hash((self.val, ))

    def precedes(self, other: Term) -> bool:
        if isinstance(other, Infimum):
            return False
        elif isinstance(other, Number):
            return self.val <= other.val
        else:
            return True

    def vars(self, global_only: bool=False, bound_only: bool=False) -> Set["Variable"]:
        return set()

    def simplify(self) -> "Number":
        """Used in arithmetical terms."""
        return Number(self.val)

    def match(self, other: Expr) -> Set[Substitution]:
        """Tries to match the expression with another one."""
        if isinstance(other, Number) and self.val == other.val:
            return set([Substitution()])
        else:
            return set()

    def substitute(self, subst: Substitution) -> "Number":
        return Number(self.val)


class SymbolicConstant(Term):
    """Represents a symbolic constant."""
    ground: bool=True

    def __init__(self, val: str) -> None:

        # check if symbolic constant name is valid
        if aspy.debug() and not SYM_CONST_RE.fullmatch(val): # TODO: alpha, eta, eps?
            raise ValueError(f"Invalid value for {type(self)}: {val}")

        self.val = val

    def __str__(self) -> str:
        return self.val

    def __str__(self) -> str:
        return str(self.val)

    def __eq__(self, other) -> str:
        return isinstance(other, SymbolicConstant) and other.val == self.val

    def __hash__(self) -> int:
        return hash(("const", self.val))

    def precedes(self, other: Term) -> bool:
        if isinstance(other, (Infimum, Number)):
            return False
        elif isinstance(other, SymbolicConstant):
            return self.val <= other.val
        else:
            return True

    def vars(self, global_only: bool=False, bound_only: bool=False) -> Set["Variable"]:
        return set()

    def match(self, other: Expr) -> Set[Substitution]:
        """Tries to match the expression with another one."""
        if isinstance(other, SymbolicConstant) and self.val == other.val:
            return set([Substitution()])
        else:
            return set()

    def substitute(self, subst: Substitution) -> "SymbolicConstant":
        return SymbolicConstant(self.val)


class String(Term):
    """Represents a string."""
    ground: bool=True

    def __init__(self, val: str) -> None:
        self.val = val

    def __str__(self) -> str:
        return '"' + self.val + '"'

    def __eq__(self, other) -> str:
        return isinstance(other, SymbolicConstant) and other.val == self.val

    def __hash__(self) -> int:
        return hash(("str", self.val))

    def precedes(self, other: Term) -> bool:
        if isinstance(other, (Infimum, Number, SymbolicConstant)):
            return False
        elif isinstance(other, String):
            return self.val <= other.val
        else:
            return True

    def vars(self, global_only: bool=False, bound_only: bool=False) -> Set["Variable"]:
        return set()

    def match(self, other: Expr) -> Set[Substitution]:
        """Tries to match the expression with another one."""
        if isinstance(other, String) and self.val == other.val:
            return set([Substitution()])
        else:
            return set()

    def substitute(self, subst: Substitution) -> "String":
        return String(self.val)