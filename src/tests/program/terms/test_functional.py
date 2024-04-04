from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import (
    ArithVariable,
    Functional,
    Infimum,
    Minus,
    Number,
    String,
    Supremum,
    Variable,
)
from aspy.program.variable_table import VariableTable


class TestFunctional:
    def test_functional(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # invalid initialization
        with pytest.raises(ValueError):
            Functional("F")
        # valid initialization
        ground_term = Functional("f", Number(1), String("x"))
        var_term = Functional("f", Variable("X"))
        # string representation
        assert str(ground_term) == 'f(1,"x")'
        # equality
        assert ground_term == Functional("f", Number(1), String("x"))
        # hashing
        assert hash(ground_term) == hash(Functional("f", Number(1), String("x")))
        # arity
        assert ground_term.arity == 2
        # total order for terms
        assert not ground_term.precedes(Infimum())
        assert not ground_term.precedes(Functional("e", Number(1), String("x")))
        assert not ground_term.precedes(Functional("f", Number(0), String("x")))
        assert not ground_term.precedes(Functional("f", Number(0), String("y")))
        assert ground_term.precedes(Functional("f", Number(1), String("x")))
        assert ground_term.precedes(Functional("g", Infimum(), Infimum()))
        assert ground_term.precedes(Functional("f", Number(1), String("x"), Number(2)))
        assert ground_term.precedes(Supremum())
        # ground
        assert ground_term.ground
        assert not var_term.ground
        # variables
        assert ground_term.vars() == ground_term.global_vars() == set()
        assert var_term.vars() == var_term.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert Functional("f", Minus(Variable("X")), String("x")).replace_arith(
            VariableTable()
        ) == Functional("f", ArithVariable(0, Minus(Variable("X"))), String("x"))
        # safety characterizatin
        assert ground_term.safety() == SafetyTriplet()
        assert var_term.safety() == SafetyTriplet({Variable("X")})

        # substitute
        assert Functional("f", String("f"), Variable("X")).substitute(
            Substitution({String("f"): Number(0), Variable("X"): Number(1)})
        ) == Functional(
            "f", String("f"), Number(1)
        )  # NOTE: substitution is invalid
        assert (
            ground_term.substitute(
                Substitution({String("f"): Number(0), Variable("X"): Number(1)})
            )
            == ground_term
        )
        # match
        assert Functional("f", Variable("X"), String("f")).match(
            Functional("f", Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            Functional("f", Variable("X"), String("f")).match(
                Functional("f", Number(1), String("g"))
            )
            is None
        )  # ground terms don't match
        assert (
            Functional("f", Variable("X"), Variable("X")).match(
                Functional("f", Number(1), String("f"), Number(2))
            )
            is None
        )  # different arity
        assert (
            Functional("f", Variable("X"), Variable("X")).match(
                Functional("g", Variable("X"), Variable("X"))
            )
            is None
        )  # different symbol
        assert (
            Functional("f", Variable("X"), Variable("X")).match(
                Functional("f", Number(1), String("f"))
            )
            is None
        )  # assignment conflict
