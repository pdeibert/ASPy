from typing import Self

import aspy
from aspy.program.literals import Guard
from aspy.program.operators import RelOp
from aspy.program.terms import ArithVariable, Minus, Number, Variable
from aspy.program.variable_table import VariableTable


class TestGuard:
    def test_guard(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        rguard = Guard(RelOp.GREATER, Number(3), True)
        lguard = Guard(RelOp.LESS, Number(3), False)

        var_guard = Guard(RelOp.EQUAL, Minus(Variable("X")), True)

        # string representation
        assert str(rguard) == "> 3"
        assert str(lguard) == "3 <"
        # equality
        assert rguard == Guard(RelOp.GREATER, Number(3), True)
        assert lguard == Guard(RelOp.LESS, Number(3), False)
        # hashing
        assert hash(rguard) == hash(Guard(RelOp.GREATER, Number(3), True))
        assert hash(lguard) == hash(Guard(RelOp.LESS, Number(3), False))
        # to left
        assert lguard.to_left() == lguard
        assert rguard.to_left() == lguard
        # to right
        assert rguard.to_right() == rguard
        assert lguard.to_right() == rguard
        # ground
        assert rguard.ground == lguard.ground == True  # noqa
        assert not var_guard.ground
        # variables
        assert var_guard.vars() == var_guard.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert var_guard.replace_arith(VariableTable()) == Guard(
            RelOp.EQUAL, ArithVariable(0, Minus(Variable("X"))), True
        )
        # TODO: substitute (see aggregate tests)
        # TODO: match (see aggregate tests)
        # TODO: safety characterization (see aggregate tests)
