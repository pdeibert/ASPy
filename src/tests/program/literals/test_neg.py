from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.literals import AggrCount, AggrLiteral, Equal, Guard, Neg, PredLiteral
from aspy.program.operators import RelOp
from aspy.program.terms import Number, Variable


class TestNaf:
    def test_naf(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # predicate literal
        literal = PredLiteral("p", Number(0), Variable("Y"))
        assert not literal.neg
        literal_ = Neg(PredLiteral("p", Number(0), Variable("Y")))
        assert literal_.neg
        assert literal.name == literal_.name and literal.terms == literal_.terms
        assert not Neg(PredLiteral("p", Number(0), Variable("Y")), False).neg
        assert Neg(PredLiteral("p", Number(0), Variable("Y")), True).neg

        # aggregate literal
        with pytest.raises(NotImplementedError):
            Neg(
                AggrLiteral(AggrCount(), tuple(), Guard(RelOp.LESS, Number(3), False)),
            )

        # builtin literal
        with pytest.raises(NotImplementedError):
            Neg(Equal(Number(0), Variable("Y")))
