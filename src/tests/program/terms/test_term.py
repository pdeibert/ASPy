from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import (
    AnonVariable,
    ArithVariable,
    Infimum,
    Minus,
    Number,
    String,
    Supremum,
    SymbolicConstant,
    TermTuple,
    Variable,
)
from aspy.program.variable_table import VariableTable


class TestTerm:
    def test_infimum(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        term = Infimum()
        # string representation
        assert str(term) == "#inf"
        # equality
        assert term == Infimum()
        # hashing
        assert hash(term) == hash(Infimum())
        # total order for terms
        assert term.precedes(Number(0))
        # ground
        assert term.ground
        # variables
        assert term.vars() == term.global_vars() == set()
        # replace arithmetic terms
        assert term.replace_arith(VariableTable()) == term
        # safety characterization
        assert term.safety() == SafetyTriplet()

        # substitute
        assert (
            Infimum().substitute(Substitution({Infimum(): Supremum()})) == Infimum()
        )  # NOTE: substitution is invalid
        # match
        assert Infimum().match(Supremum()) is None
        assert Infimum().match(Infimum()) == Substitution()

    def test_supremum(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        term = Supremum()
        # string representation
        assert str(term) == "#sup"
        # equality
        assert term == Supremum()
        # hashing
        assert hash(term) == hash(Supremum())
        # total order for terms
        assert term.precedes(Supremum())
        # ground
        assert term.ground
        # variables
        assert term.vars() == term.global_vars() == set()
        # replace arithmetic terms
        assert term.replace_arith(VariableTable()) == term
        # safety characterization
        assert term.safety() == SafetyTriplet()

        # substitute
        assert (
            Supremum().substitute(Substitution({Supremum(): Infimum()})) == Supremum()
        )  # NOTE: substitution is invalid
        # match
        assert Supremum().match(Infimum()) is None
        assert Supremum().match(Supremum()) == Substitution()

    def test_variable(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # invalid initialization
        with pytest.raises(ValueError):
            Variable("x")
        # valid initialization
        term = Variable("X")
        # string representation
        assert str(term) == "X"
        # equality
        assert term == Variable("X")
        # hashing
        assert hash(term) == hash(Variable("X"))
        # total order for terms
        with pytest.raises(Exception):
            term.precedes(term)
        # ground
        assert not term.ground
        # variables
        assert term.vars() == term.global_vars() == {term}
        # replace arithmetic terms
        assert term.replace_arith(VariableTable()) == term
        # safety characterization
        assert term.safety() == SafetyTriplet({term})
        # simplify
        assert term.simplify() == term

        # substitute
        assert Variable("X").substitute(
            Substitution({Variable("Y"): Number(0)})
        ) == Variable("X")
        assert Variable("X").substitute(
            Substitution({Variable("X"): Number(0)})
        ) == Number(0)
        # match
        assert Variable("X").match(Variable("X")) == Substitution()
        assert Variable("X").match(Number(1)) == Substitution(
            {Variable("X"): Number(1)}
        )

    def test_anon_variable(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # invalid initialization
        with pytest.raises(ValueError):
            AnonVariable(-1)
        # valid initialization
        term = AnonVariable(0)
        # string representation
        assert str(term) == "_0"
        # equality
        assert term == AnonVariable(0)
        # hashing
        assert hash(term) == hash(AnonVariable(0))
        # total order for terms
        with pytest.raises(Exception):
            term.precedes(term)
        # ground
        assert not term.ground
        # variables
        assert term.vars() == term.global_vars() == {term}
        # replace arithmetic terms
        assert term.replace_arith(VariableTable()) == term
        # safety characterization
        assert term.safety() == SafetyTriplet({term})
        # simplify
        assert term.simplify() == term

        # substitute
        assert AnonVariable(0).substitute(
            Substitution({AnonVariable(1): Number(0)})
        ) == AnonVariable(0)
        assert AnonVariable(0).substitute(
            Substitution({AnonVariable(0): Number(0)})
        ) == Number(0)
        # match
        assert AnonVariable(0).match(AnonVariable(0)) == Substitution()
        assert AnonVariable(0).match(Number(1)) == Substitution(
            {AnonVariable(0): Number(1)}
        )

    def test_number(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        term = Number(5)
        # string representation
        assert str(term) == "5"
        # equality
        assert term == Number(5)
        # hashing
        assert hash(term) == hash(Number(5))
        # evaluation
        assert term.eval() == 5
        # total order for terms
        assert not term.precedes(Number(4))
        assert term.precedes(Number(5))
        with pytest.raises(ValueError):
            term.precedes(Variable("X"))
        # ground
        assert term.ground
        # variables
        assert term.vars() == term.global_vars() == set()
        # negation
        assert -term == Number(-5)
        # absolute value
        assert abs(term) == abs(Number(-5)) == Number(5)
        # replace arithmetic terms
        assert term.replace_arith(VariableTable()) == term
        # safety characterization
        assert term.safety() == SafetyTriplet()
        # simplify
        assert term.simplify() == term

        # operators
        assert (term + Number(2)) == Number(7)
        assert (term - Number(2)) == Number(3)
        assert (term * Number(2)) == Number(10)
        assert (term // Number(2)) == Number(2)

        # substitute
        assert Number(0).substitute(Substitution({Number(0): Number(1)})) == Number(
            0
        )  # NOTE: substitution is invalid
        # match
        assert Number(0).match(Number(1)) is None
        assert Number(0).match(Number(0)) == Substitution()

    def test_symbolic_constant(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # invalid initialization
        with pytest.raises(ValueError):
            SymbolicConstant("1")
        with pytest.raises(ValueError):
            SymbolicConstant("Z")

        term = SymbolicConstant("b")
        # string representation
        assert str(term) == "b"
        # equality
        assert term == SymbolicConstant("b")
        # hashing
        assert hash(term) == hash(SymbolicConstant("b"))
        # total order for terms
        assert not term.precedes(Infimum())
        assert not term.precedes(SymbolicConstant("a"))
        assert term.precedes(SymbolicConstant("b"))
        assert term.precedes(Supremum())
        with pytest.raises(ValueError):
            term.precedes(Variable("X"))
        # ground
        assert term.ground
        # variables
        assert term.vars() == term.global_vars() == set()
        # replace arithmetic terms
        assert term.replace_arith(VariableTable()) == term
        # safety characterization
        assert term.safety() == SafetyTriplet()

        # substitute
        assert SymbolicConstant("f").substitute(
            Substitution({SymbolicConstant("f"): Number(0)})
        ) == SymbolicConstant(
            "f"
        )  # NOTE: substitution is invalid
        # match
        assert SymbolicConstant("a").match(SymbolicConstant("b")) is None
        assert SymbolicConstant("a").match(SymbolicConstant("a")) == Substitution()

    def test_string(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        term = String("!?$#b")
        # string representation
        assert str(term) == '"!?$#b"'
        # equality
        assert term == String("!?$#b")
        # hashing
        assert hash(term) == hash(String("!?$#b"))
        # total order for terms
        assert not term.precedes(Infimum())
        assert not term.precedes(String("!?$#a"))
        assert term.precedes(String("!?$#b"))
        assert term.precedes(Supremum())

        with pytest.raises(ValueError):
            term.precedes(Variable("X"))
        # ground
        assert term.ground
        # variables
        assert term.vars() == term.global_vars() == set()
        # replace arithmetic terms
        assert term.replace_arith(VariableTable()) == term
        # safety characterization
        assert term.safety() == SafetyTriplet()

        # substitute
        assert String("f").substitute(Substitution({String("f"): Number(0)})) == String(
            "f"
        )  # NOTE: substitution is invalid
        # match
        assert String("a").match(String("b")) is None
        assert String("a").match(String("a")) == Substitution()

    def test_term_tuple(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        terms = TermTuple(Number(0), Variable("X"))
        # length
        assert len(terms) == 2
        # equality
        assert terms[0] == Number(0)
        assert terms[1] == Variable("X")
        assert terms == TermTuple(Number(0), Variable("X"))
        # hashing
        assert hash(terms) == hash(TermTuple(Number(0), Variable("X")))
        # ground
        assert not terms.ground
        # variables
        assert terms.vars() == terms.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert TermTuple(Number(0), Minus(Variable("X"))).replace_arith(
            VariableTable()
        ) == TermTuple(Number(0), ArithVariable(0, Minus(Variable("X"))))
        # safety characterization
        assert terms.safety() == (terms[0].safety(), terms[1].safety())

        # substitute
        assert TermTuple(String("f"), Variable("X")).substitute(
            Substitution({String("f"): Number(0), Variable("X"): Number(1)})
        ) == TermTuple(
            String("f"), Number(1)
        )  # NOTE: substitution is invalid
        # match
        assert TermTuple(Variable("X"), String("f")).match(
            TermTuple(Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            TermTuple(Variable("X"), String("f")).match(
                TermTuple(Number(1), String("g"))
            )
            is None
        )  # ground terms don't match
        assert (
            TermTuple(Variable("X"), Variable("X"), String("f")).match(
                TermTuple(Number(1), String("f"))
            )
            is None
        )  # wrong length
        assert (
            TermTuple(Variable("X"), Variable("X")).match(
                TermTuple(Number(1), String("f"))
            )
            is None
        )  # assignment conflict

        # combining terms
        assert terms + TermTuple(String("")) == TermTuple(
            Number(0), Variable("X"), String("")
        )
        # (positive/negative) weight
        assert TermTuple(Number(-3)).weight == -3
        assert TermTuple(Number(3)).weight == 3
        assert TermTuple(String("f")).weight == 0
        assert TermTuple(Number(-3)).pos_weight == 0
        assert TermTuple(Number(3)).pos_weight == 3
        assert TermTuple(String("f")).pos_weight == 0
        assert TermTuple(Number(-3)).neg_weight == -3
        assert TermTuple(Number(33)).neg_weight == 0
        assert TermTuple(String("f")).neg_weight == 0
