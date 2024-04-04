from typing import Self

import aspy
from aspy.program.operators import AggrOp, ArithOp, RelOp


class TestSubstitution:
    def test_relop(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # string representation
        assert str(RelOp.EQUAL) == "="
        assert str(RelOp.UNEQUAL) == "!="
        assert str(RelOp.LESS) == "<"
        assert str(RelOp.GREATER) == ">"
        assert str(RelOp.LESS_OR_EQ) == "<="
        assert str(RelOp.GREATER_OR_EQ) == ">="

        # switching operand sides
        assert -RelOp.EQUAL == RelOp.EQUAL  # x  = y <=> y  = x
        assert -RelOp.UNEQUAL == RelOp.UNEQUAL  # x != y <-> y != x
        assert -RelOp.LESS == RelOp.GREATER  # x  < y <=> y  > x
        assert -RelOp.GREATER == RelOp.LESS  # x  > y <=> y  < x
        assert -RelOp.LESS_OR_EQ == RelOp.GREATER_OR_EQ  # x <= y <=> y >= x
        assert -RelOp.GREATER_OR_EQ == RelOp.LESS_OR_EQ  # x >= y <=> y <= x

        # equivalent negated operator
        assert ~RelOp.EQUAL == RelOp.UNEQUAL  # not x  = y <=> x != y
        assert ~RelOp.UNEQUAL == RelOp.EQUAL  # not x != y <=> x  = y
        assert ~RelOp.LESS == RelOp.GREATER_OR_EQ  # not x  < y <=> x >= y
        assert ~RelOp.GREATER == RelOp.LESS_OR_EQ  # not x  > y <=> x <= y
        assert ~RelOp.LESS_OR_EQ == RelOp.GREATER  # not x <= y <=> x  > y
        assert ~RelOp.GREATER_OR_EQ == RelOp.LESS  # not x >= y <=> x  < y

        # TODO: eval

    def test_arithop(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # string representation
        assert str(ArithOp.PLUS) == "+"
        assert str(ArithOp.MINUS) == "-"
        assert str(ArithOp.TIMES) == "*"
        assert str(ArithOp.DIV) == "/"

    def test_aggrop(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # string representation
        assert str(AggrOp.COUNT) == "#count"
        assert str(AggrOp.SUM) == "#sum"
        assert str(AggrOp.MAX) == "#max"
        assert str(AggrOp.MIN) == "#min"
