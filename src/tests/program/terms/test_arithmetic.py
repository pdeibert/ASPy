from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import (
    Add,
    ArithVariable,
    Div,
    Minus,
    Mult,
    Number,
    Sub,
    Variable,
)
from aspy.program.variable_table import VariableTable


class TestArithmetic:
    def test_minus(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_term = Minus(Number(1))
        var_term = Minus(Variable("X"))

        # string representation
        assert str(ground_term) == "-1"
        assert (
            str(Minus(Add(Number(3), Variable("X")))) == "-(3+X)"
        )  # parentheses around nested term
        # equality
        assert ground_term == Minus(Number(1))
        # hashing
        assert hash(ground_term) == hash(Minus(Number(1)))
        # evaluation
        assert ground_term.eval() == -1
        with pytest.raises(Exception):
            var_term.eval()
        # total order for terms
        assert not ground_term.precedes(Number(-2))
        assert ground_term.precedes(Number(-1))
        with pytest.raises(Exception):
            var_term.precedes(Number(3))
        # ground
        assert ground_term.ground
        assert not var_term.ground
        # variables
        assert ground_term.vars() == ground_term.global_vars() == set()
        assert var_term.vars() == var_term.global_vars() == {Variable("X")}
        # safety charachterization
        assert ground_term.safety() == SafetyTriplet()
        assert var_term.safety() == SafetyTriplet(unsafe={Variable("X")})
        # simplify
        assert ground_term.simplify() == Number(-1)
        assert var_term.simplify() == var_term

        # substitute
        assert var_term.substitute(Substitution({Variable("X"): Number(1)})) == Number(
            -1
        )
        assert (
            ground_term.substitute(Substitution({Variable("X"): Number(1)}))
            == ground_term
        )
        # match
        with pytest.raises(ValueError):
            var_term.match(var_term)
        with pytest.raises(ValueError):
            Minus(Number(3)).match(var_term)
        assert Minus(Number(3)).match(Minus(Number(1))) is None
        assert Minus(Number(3)).match(Minus(Number(3))) == Substitution()

        assert Minus(Number(1)).simplify() == Number(-1)
        # double negation
        assert Minus(Minus(Variable("X"))).simplify() == Variable("X")

    def test_add(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_term = Add(Number(1), Number(2))
        var_term = Add(Number(1), Variable("X"))

        # string representation
        assert str(ground_term) == "1+2"
        assert (
            str(Add(Number(1), Add(Number(2), Number(3)))) == "1+(2+3)"
        )  # parentheses around nested term
        # equality
        assert ground_term, Add(Number(1) == Number(2))
        # hashing
        assert hash(ground_term) == hash(Add(Number(1), Number(2)))
        # evaluation
        assert ground_term.eval() == 3
        with pytest.raises(Exception):
            var_term.eval()
        # total order for terms
        assert not ground_term.precedes(Number(2))
        assert ground_term.precedes(Number(3))
        with pytest.raises(Exception):
            var_term.precedes(Number(3))
        # ground
        assert ground_term.ground
        assert not var_term.ground
        # variables
        assert ground_term.vars() == ground_term.global_vars() == set()
        assert var_term.vars() == var_term.global_vars() == {Variable("X")}
        # replace arithmetic variable
        assert (
            ground_term.replace_arith(VariableTable())
            == ground_term.simplify()
            == Number(3)
        )
        assert var_term.replace_arith(VariableTable()) == ArithVariable(0, var_term)
        # safety characterization
        assert ground_term.safety() == SafetyTriplet()
        assert var_term.safety() == SafetyTriplet(unsafe={Variable("X")})
        # simplify
        assert ground_term.simplify() == Number(3)
        assert var_term.simplify() == var_term

        # substitute
        assert Add(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1)})
        ) == Number(1)
        assert (
            ground_term.substitute(Substitution({Variable("X"): Number(1)}))
            == ground_term
        )
        # match
        with pytest.raises(ValueError):
            Add(Variable("X"), Number(2)).match(Number(3))
        with pytest.raises(ValueError):
            Add(Number(1), Number(2)).match(Minus(Variable("X")))
        assert Add(Number(1), Number(2)).match(Add(Number(3), Number(1))) is None
        assert (
            Add(Number(1), Number(2)).match(Add(Number(3), Number(0))) == Substitution()
        )

        # addition of numbers
        assert Add(Number(1), Number(2)).simplify() == Number(3)
        # right operand zero
        assert Add(Variable("X"), Number(0)).simplify() == Variable("X")
        # left operand zero
        assert Add(Number(0), Variable("X")).simplify() == Variable("X")

    def test_sub(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_term = Sub(Number(1), Number(2))
        var_term = Sub(Number(1), Variable("X"))

        # string representation
        assert str(ground_term) == "1-2"
        assert (
            str(Sub(Number(1), Sub(Number(3), Number(2)))) == "1-(3-2)"
        )  # parentheses around nested term
        # equality
        assert ground_term == Sub(Number(1), Number(2))
        # hashing
        assert hash(ground_term) == hash(Sub(Number(1), Number(2)))
        # evaluation
        assert ground_term.eval() == -1
        with pytest.raises(Exception):
            var_term.eval()
        # total order for terms
        assert not ground_term.precedes(Number(-2))
        with pytest.raises(Exception):
            var_term.precedes(Number(-1))
        # ground
        assert ground_term.ground
        assert not var_term.ground
        # variables
        assert ground_term.vars() == ground_term.global_vars() == set()
        assert var_term.vars() == var_term.global_vars() == {Variable("X")}
        # replace arithmetic variable
        assert (
            ground_term.replace_arith(VariableTable())
            == ground_term.simplify()
            == Number(-1)
        )
        assert var_term.replace_arith(VariableTable()) == ArithVariable(0, var_term)
        # safety characterization
        assert ground_term.safety() == SafetyTriplet()
        assert var_term.safety() == SafetyTriplet(unsafe={Variable("X")})
        # simplify
        assert ground_term.simplify() == Number(-1)
        assert var_term.simplify() == var_term

        # substitute
        assert Sub(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1)})
        ) == Number(1)
        assert (
            ground_term.substitute(Substitution({Variable("X"): Number(1)}))
            == ground_term
        )
        # match
        with pytest.raises(ValueError):
            Sub(Variable("X"), Number(2)).match(Number(1))
        with pytest.raises(ValueError):
            Sub(Number(3), Number(2)).match(Minus(Variable("X")))
        assert Sub(Number(3), Number(2)).match(Sub(Number(3), Number(1))) is None
        assert (
            Sub(Number(3), Number(2)).match(Sub(Number(3), Number(2))) == Substitution()
        )

        # subtraction of numbers
        assert Sub(Number(1), Number(2)).simplify() == Number(-1)
        # right operand zero
        assert Sub(Variable("X"), Number(0)).simplify() == Variable("X")
        # left operand zero
        assert Sub(Number(0), Variable("X")).simplify() == Minus(Variable("X"))

    def test_mult(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_term = Mult(Number(3), Number(2))
        var_term = Mult(Number(3), Variable("X"))

        # string representation
        assert str(ground_term) == "3*2"
        assert (
            str(Mult(Number(3), Mult(Number(2), Number(1)))) == "3*(2*1)"
        )  # parentheses around nested term
        # equality
        assert ground_term == Mult(Number(3), Number(2))
        # hashing
        assert hash(ground_term) == hash(Mult(Number(3), Number(2)))
        # evaluation
        assert ground_term.eval() == 6
        with pytest.raises(Exception):
            var_term.eval()
        # total order for terms
        assert not ground_term.precedes(Number(5))
        assert ground_term.precedes(Number(6))
        with pytest.raises(Exception):
            var_term.precedes(Number(3))
        # ground
        assert ground_term.ground
        assert not var_term.ground
        # variables
        assert ground_term.vars() == ground_term.global_vars() == set()
        assert var_term.vars() == var_term.global_vars() == {Variable("X")}
        # replace arithmetic variable
        assert (
            ground_term.replace_arith(VariableTable())
            == ground_term.simplify()
            == Number(6)
        )
        assert var_term.replace_arith(VariableTable()) == ArithVariable(0, var_term)
        # safety characterization
        assert var_term.safety() == SafetyTriplet()
        assert ground_term.safety() == SafetyTriplet(unsafe={Variable("X")})
        # simplify
        assert ground_term.simplify() == Number(6)
        assert var_term.simplify() == var_term

        # substitute
        assert Mult(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1)})
        ) == Number(0)
        assert (
            ground_term.substitute(Substitution({Variable("X"): Number(1)}))
            == ground_term
        )
        # match
        with pytest.raises(ValueError):
            Mult(Variable("X"), Number(2)).match(Number(6))
        with pytest.raises(ValueError):
            Mult(Number(3), Number(2)).match(Minus(Variable("X")))
        assert Mult(Number(3), Number(2)).match(Mult(Number(3), Number(1))) is None
        assert (
            Mult(Number(3), Number(2)).match(Mult(Number(2), Number(3)))
            == Substitution()
        )

        # multiplication of numbers
        assert Mult(Number(2), Number(3)).simplify() == Number(6)
        # right operand zero
        assert Mult(Number(10), Number(0)).simplify() == Number(0)
        assert Mult(Variable("X"), Number(0)).simplify() == Mult(
            Variable("X"), Number(0)
        )
        # left operand zero
        assert Mult(Number(0), Number(10)).simplify() == Number(0)
        assert Mult(Number(0), Variable("X")).simplify() == Mult(
            Number(0), Variable("X")
        )
        # right operand one
        assert Mult(Variable("X"), Number(1)).simplify() == Variable("X")
        # left operand one
        assert Mult(Number(1), Variable("X")).simplify() == Variable("X")
        # right operand negative one
        assert Mult(Variable("X"), Number(-1)).simplify() == Minus(Variable("X"))
        assert Mult(Minus(Variable("X")), Number(-1)).simplify() == Variable("X")
        # left operand negative one
        assert Mult(Number(-1), Variable("X")).simplify() == Minus(Variable("X"))
        assert Mult(Number(-1), Minus(Variable("X"))).simplify() == Variable("X")

    def test_div(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_term = Div(Number(1), Number(2))
        var_term = Div(Number(1), Variable("X"))

        # string representation
        assert str(ground_term) == "1/2"
        assert (
            str(Div(Number(3), Div(Number(2), Number(1)))) == "3/(2/1)"
        )  # parentheses around nested term
        # equality
        assert ground_term == Div(Number(1), Number(2))
        # hashing
        assert hash(ground_term) == hash(Div(Number(1), Number(2)))
        # evaluation
        assert ground_term.eval() == 0
        with pytest.raises(Exception):
            var_term.eval()
        # total order for terms
        assert not ground_term.precedes(Number(-1))
        assert ground_term.precedes(Number(0))
        with pytest.raises(Exception):
            var_term.precedes(Number(0))
        # ground
        assert ground_term.ground
        assert not var_term.ground
        # variables
        assert ground_term.vars() == ground_term.global_vars() == set()
        assert var_term.vars() == var_term.global_vars() == {Variable("X")}
        # replace arithmetic variable
        assert (
            ground_term.replace_arith(VariableTable())
            == ground_term.simplify()
            == Number(0)
        )
        assert var_term.replace_arith(VariableTable()) == ArithVariable(0, var_term)
        # safety characterization
        assert ground_term.safety() == SafetyTriplet()
        assert var_term.safety() == SafetyTriplet(unsafe={Variable("X")})
        # simplify
        assert ground_term.simplify() == Number(0)
        assert var_term.simplify() == var_term

        # substitute
        assert Div(Variable("X"), Number(1)).substitute(
            Substitution({Variable("X"): Number(2)})
        ) == Number(2)
        assert (
            ground_term.substitute(Substitution({Variable("X"): Number(1)}))
            == ground_term
        )
        # match
        with pytest.raises(ValueError):
            Div(Variable("X"), Number(2)).match(Number(3))
        with pytest.raises(ValueError):
            Div(Number(1), Number(2)).match(Minus(Variable("X")))
        assert Div(Number(1), Number(2)).match(Div(Number(1), Number(1))) is None
        assert (
            Div(Number(1), Number(2)).match(Div(Number(0), Number(3))) == Substitution()
        )

        # division of (valid) numbers
        assert Div(Number(3), Number(2)).simplify() == Number(1)  # integer division
        assert Div(Number(3), Number(-2)).simplify() == Number(-2)  # integer division
        # right operand zero
        with pytest.raises(ArithmeticError):
            Div(Variable("X"), Number(0)).simplify()
        with pytest.raises(ArithmeticError):
            Div(Number(1), Number(0)).simplify()
        # left operand zero
        assert Div(Number(0), Number(10)).simplify() == Number(0)
        assert Div(Number(0), Variable("X")).simplify() == Div(Number(0), Variable("X"))
        # right operand one
        assert Div(Variable("X"), Number(1)).simplify() == Variable("X")
        # right operand negative one
        assert Div(Variable("X"), Number(-1)).simplify() == Minus(Variable("X"))
        assert Div(Minus(Variable("X")), Number(-1)).simplify() == Variable("X")
