from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.literals import LiteralCollection, Naf, Neg, PredLiteral
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable, Minus, Number, String, Variable
from aspy.program.variable_table import VariableTable


class TestPredicate:
    def test_predicate(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # invalid initialization
        with pytest.raises(ValueError):
            PredLiteral("P")

        literal = PredLiteral("p", Number(0), String("x"))
        naf_literal = Naf(PredLiteral("p", Number(0), String("x")))
        var_literal = PredLiteral("p", Number(0), Variable("X"))

        # string representation
        assert str(literal) == 'p(0,"x")'
        assert str(Neg(PredLiteral("p", Number(0), String("x")))) == '-p(0,"x")'
        assert str(naf_literal) == 'not p(0,"x")'
        assert (
            str(Naf(Neg(PredLiteral("p", Number(0), String("x"))))) == 'not -p(0,"x")'
        )
        # equality
        assert literal == PredLiteral("p", Number(0), String("x"))
        # hashing
        assert hash(literal) == hash(PredLiteral("p", Number(0), String("x")))
        # arity
        assert literal.arity == 2
        # predicate tuple
        assert literal.pred() == ("p", 2)
        # ground
        assert literal.ground
        assert not var_literal.ground
        # variables
        assert literal.vars() == literal.global_vars() == set()
        assert var_literal.vars() == var_literal.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert literal.replace_arith(VariableTable()) == literal
        assert var_literal.replace_arith(VariableTable()) == var_literal
        assert PredLiteral("p", Number(0), Minus(Number(1))).replace_arith(
            VariableTable()
        ) == PredLiteral(
            "p", Number(0), Number(-1)
        )  # ground arithmetic term should not be replaced (only gets simplified)
        assert PredLiteral("p", Number(0), Minus(Variable("X"))).replace_arith(
            VariableTable()
        ) == PredLiteral(
            "p", Number(0), ArithVariable(0, Minus(Variable("X")))
        )  # non-ground arithmetic term should be replaced
        # positive/negative literal occurrences
        assert literal.pos_occ() == LiteralCollection(
            PredLiteral("p", Number(0), String("x"))
        )
        assert literal.neg_occ() == LiteralCollection()
        assert naf_literal.pos_occ() == LiteralCollection()
        assert naf_literal.neg_occ() == LiteralCollection(
            PredLiteral("p", Number(0), String("x"))
        )
        # safety characterization
        assert literal.safety() == SafetyTriplet()
        assert var_literal.safety() == SafetyTriplet({Variable("X")})

        # classical negation and negation-as-failure
        assert literal.naf == literal.neg == False  # noqa
        literal.set_neg(True)
        assert literal.neg == True  # noqa
        literal.set_naf(True)

        # substitute
        assert PredLiteral("p", Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == PredLiteral(
            "p", Number(1), Number(0)
        )  # NOTE: substitution is invalid
        # match
        assert PredLiteral("p", Variable("X"), String("f")).match(
            PredLiteral("p", Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            Naf(PredLiteral("p", Variable("X"), String("f"))).match(
                Naf(PredLiteral("p", Number(1), String("g")))
            )
            is None
        )  # ground terms don't match
        assert (
            Neg(PredLiteral("p", Variable("X"), Variable("X"))).match(
                Neg(PredLiteral("p", Number(1), String("f")))
            )
            is None
        )  # assignment conflict
