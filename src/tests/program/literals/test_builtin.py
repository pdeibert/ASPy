from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.literals import (
    Equal,
    Greater,
    GreaterEqual,
    Less,
    LessEqual,
    LiteralCollection,
    PredLiteral,
    Unequal,
)
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable, Minus, Number, String, Variable
from aspy.program.variable_table import VariableTable


class TestBuiltin:
    def test_equal(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_literal = Equal(Number(0), String("x"))
        var_literal = Equal(Number(0), Variable("X"))

        # string representation
        assert str(ground_literal) == '0="x"'
        # equality
        assert ground_literal == Equal(Number(0), String("x"))
        # hashing
        assert hash(ground_literal) == hash(Equal(Number(0), String("x")))
        # ground
        assert ground_literal.ground
        assert not var_literal.ground
        # variables
        assert ground_literal.vars() == ground_literal.global_vars() == set()
        assert var_literal.vars() == var_literal.global_vars() == {Variable("X")}
        # positive/negative literal occurrences
        assert (
            ground_literal.pos_occ() == ground_literal.neg_occ() == LiteralCollection()
        )
        # operands
        assert ground_literal.operands == (Number(0), String("x"))
        # safety characterization
        assert ground_literal.safety() == SafetyTriplet()
        safety = var_literal.safety()
        assert safety.safe == {Variable("X")}
        assert safety.unsafe == set()
        assert safety.rules == set()
        # replace arithmetic terms
        assert var_literal.replace_arith(VariableTable()) == Equal(
            Number(0), Variable("X")
        )
        assert Equal(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Equal(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        assert Equal(Number(0), Minus(Variable(("X")))).replace_arith(
            VariableTable()
        ) == Equal(Number(0), ArithVariable(0, Minus(Variable("X"))))
        # evaluation
        assert not Equal(Number(0), String("x")).eval()
        assert Equal(Number(0), Number(0)).eval()
        with pytest.raises(ValueError):
            Equal(Number(0), Variable("X")).eval()
        with pytest.raises(ValueError):
            Equal(Number(0), Minus(Variable("X"))).eval()

        # substitute
        assert Equal(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Equal(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        # match
        assert Equal(Variable("X"), String("f")).match(
            Equal(Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            Equal(Variable("X"), String("f")).match(Equal(Number(1), String("g")))
            is None
        )  # ground terms don't match
        assert (
            Equal(Variable("X"), String("f")).match(PredLiteral("p")) is None
        )  # different type
        assert (
            Equal(Variable("X"), Variable("X")).match(Equal(Number(1), String("f")))
            is None
        )  # assignment conflict

    def test_unequal(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_literal = Unequal(Number(0), String("x"))
        var_literal = Unequal(Number(0), Variable("X"))

        # string representation
        assert str(ground_literal) == '0!="x"'
        # equality
        assert ground_literal == Unequal(Number(0), String("x"))
        # hashing
        assert hash(ground_literal) == hash(Unequal(Number(0), String("x")))
        # ground
        assert ground_literal.ground
        assert not var_literal.ground
        # variables
        assert ground_literal.vars() == ground_literal.global_vars() == set()
        assert var_literal.vars() == var_literal.global_vars() == {Variable("X")}
        # positive/negative literal occurrences
        assert (
            ground_literal.pos_occ() == ground_literal.neg_occ() == LiteralCollection()
        )
        # operands
        assert ground_literal.operands == (Number(0), String("x"))
        # safety characterization
        assert ground_literal.safety() == SafetyTriplet()
        assert var_literal.safety() == SafetyTriplet(unsafe={Variable("X")})
        assert Unequal(Variable("Y"), Variable("X")).safety() == SafetyTriplet(
            unsafe={Variable("X"), Variable("Y")}
        )
        # replace arithmetic terms
        assert var_literal.replace_arith(VariableTable()) == Unequal(
            Number(0), Variable("X")
        )
        assert Unequal(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Unequal(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        assert Unequal(Number(0), Minus(Variable(("X")))).replace_arith(
            VariableTable()
        ) == Unequal(Number(0), ArithVariable(0, Minus(Variable("X"))))
        # evaluation
        assert Unequal(Number(0), String("x")).eval()
        assert not Unequal(Number(0), Number(0)).eval()
        with pytest.raises(ValueError):
            Unequal(Number(0), Variable("X")).eval()
        with pytest.raises(ValueError):
            Unequal(Number(0), Minus(Variable("X"))).eval()

        # substitute
        assert Unequal(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Unequal(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        # match
        assert Unequal(Variable("X"), String("f")).match(
            Unequal(Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            Unequal(Variable("X"), String("f")).match(Unequal(Number(1), String("g")))
            is None
        )  # ground terms don't match
        assert (
            Unequal(Variable("X"), String("f")).match(PredLiteral("p")) is None
        )  # different type
        assert (
            Unequal(Variable("X"), Variable("X")).match(Unequal(Number(1), String("f")))
            is None
        )  # assignment conflict

    def test_less(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_literal = Less(Number(0), String("x"))
        var_literal = Less(Number(0), Variable("X"))

        # string representation
        assert str(ground_literal) == '0<"x"'
        # equality
        assert ground_literal == Less(Number(0), String("x"))
        # hashing
        assert hash(ground_literal) == hash(Less(Number(0), String("x")))
        # ground
        assert ground_literal.ground
        assert not var_literal.ground
        # variables
        assert ground_literal.vars() == ground_literal.global_vars() == set()
        assert var_literal.vars() == var_literal.global_vars() == {Variable("X")}
        # positive/negative literal occurrences
        assert (
            ground_literal.pos_occ() == ground_literal.neg_occ() == LiteralCollection()
        )
        # operands
        assert ground_literal.operands == (Number(0), String("x"))
        # safety characterization
        assert ground_literal.safety() == SafetyTriplet()
        assert var_literal.safety() == SafetyTriplet(unsafe={Variable("X")})
        assert Less(Variable("Y"), Variable("X")).safety() == SafetyTriplet(
            unsafe={Variable("X"), Variable("Y")}
        )
        # replace arithmetic terms
        assert var_literal.replace_arith(VariableTable()) == Less(
            Number(0), Variable("X")
        )
        assert Less(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Less(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        assert Less(Number(0), Minus(Variable(("X")))).replace_arith(
            VariableTable()
        ) == Less(Number(0), ArithVariable(0, Minus(Variable("X"))))
        # evaluation
        assert Less(Number(0), String("x")).eval()
        assert Less(Number(0), Number(1)).eval()
        assert not Less(Number(0), Number(0)).eval()
        with pytest.raises(ValueError):
            Less(Number(0), Variable("X")).eval()
        with pytest.raises(ValueError):
            Less(Number(0), Minus(Variable("X"))).eval()

        # substitute
        assert Less(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Less(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        # match
        assert Less(Variable("X"), String("f")).match(
            Less(Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            Less(Variable("X"), String("f")).match(Less(Number(1), String("g"))) is None
        )  # ground terms don't match
        assert (
            Less(Variable("X"), String("f")).match(PredLiteral("p")) is None
        )  # different type
        assert (
            Less(Variable("X"), Variable("X")).match(Less(Number(1), String("f")))
            is None
        )  # assignment conflict

    def test_greater(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_literal = Greater(Number(0), String("x"))
        var_literal = Greater(Number(0), Variable("X"))

        # string representation
        assert str(ground_literal) == '0>"x"'
        # equality
        assert ground_literal == Greater(Number(0), String("x"))
        # hashing
        assert hash(ground_literal) == hash(Greater(Number(0), String("x")))
        # ground
        assert ground_literal.ground
        assert not var_literal.ground
        # variables
        assert ground_literal.vars() == ground_literal.global_vars() == set()
        assert var_literal.vars() == var_literal.global_vars() == {Variable("X")}
        # positive/negative literal occurrences
        assert (
            ground_literal.pos_occ() == ground_literal.neg_occ() == LiteralCollection()
        )
        # operands
        assert ground_literal.operands == (Number(0), String("x"))
        # safety characterization
        assert ground_literal.safety() == SafetyTriplet()
        assert var_literal.safety() == SafetyTriplet(unsafe={Variable("X")})
        assert Greater(Variable("Y"), Variable("X")).safety() == SafetyTriplet(
            unsafe={Variable("X"), Variable("Y")}
        )
        # replace arithmetic terms
        assert var_literal.replace_arith(VariableTable()) == Greater(
            Number(0), Variable("X")
        )
        assert Greater(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Greater(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        assert Greater(Number(0), Minus(Variable(("X")))).replace_arith(
            VariableTable()
        ) == Greater(Number(0), ArithVariable(0, Minus(Variable("X"))))
        # evaluation
        assert not Greater(Number(0), String("x")).eval()
        assert not Greater(Number(0), Number(1)).eval()
        assert not Greater(Number(0), Number(0)).eval()
        assert Greater(Number(0), Number(-1)).eval()
        with pytest.raises(ValueError):
            Greater(Number(0), Variable("X")).eval()
        with pytest.raises(ValueError):
            Greater(Number(0), Minus(Variable("X"))).eval()

        # substitute
        assert Greater(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Greater(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        # match
        assert Greater(Variable("X"), String("f")).match(
            Greater(Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            Greater(Variable("X"), String("f")).match(Greater(Number(1), String("g")))
            is None
        )  # ground terms don't match
        assert (
            Greater(Variable("X"), String("f")).match(PredLiteral("p")) is None
        )  # different type
        assert (
            Greater(Variable("X"), Variable("X")).match(Greater(Number(1), String("f")))
            is None
        )  # assignment conflict

    def test_less_equal(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_literal = LessEqual(Number(0), String("x"))
        var_literal = LessEqual(Number(0), Variable("X"))

        # string representation
        assert str(ground_literal) == '0<="x"'
        # equality
        assert ground_literal == LessEqual(Number(0), String("x"))
        # hashing
        assert hash(ground_literal) == hash(LessEqual(Number(0), String("x")))
        # ground
        assert ground_literal.ground
        assert not var_literal.ground
        # variables
        assert ground_literal.vars() == ground_literal.global_vars() == set()
        assert var_literal.vars() == var_literal.global_vars() == {Variable("X")}
        # positive/negative literals occurrences
        assert (
            ground_literal.pos_occ() == ground_literal.neg_occ() == LiteralCollection()
        )
        # operands
        assert ground_literal.operands == (Number(0), String("x"))
        # replace arithmetic terms
        assert var_literal.replace_arith(VariableTable()) == LessEqual(
            Number(0), Variable("X")
        )
        assert LessEqual(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == LessEqual(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        assert LessEqual(Number(0), Minus(Variable(("X")))).replace_arith(
            VariableTable()
        ) == LessEqual(Number(0), ArithVariable(0, Minus(Variable("X"))))
        # safety characterization
        assert ground_literal.safety() == SafetyTriplet()
        assert var_literal.safety() == SafetyTriplet(unsafe={Variable("X")})
        assert LessEqual(Variable("Y"), Variable("X")).safety() == SafetyTriplet(
            unsafe={Variable("X"), Variable("Y")}
        )
        # evaluation
        assert LessEqual(Number(0), String("x")).eval()
        assert LessEqual(Number(0), Number(1)).eval()
        assert LessEqual(Number(0), Number(0)).eval()
        assert not LessEqual(Number(0), Number(-1)).eval()
        with pytest.raises(ValueError):
            LessEqual(Number(0), Variable("X")).eval()
        with pytest.raises(ValueError):
            LessEqual(Number(0), Minus(Variable("X"))).eval()

        # substitute
        assert LessEqual(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == LessEqual(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        # match
        assert LessEqual(Variable("X"), String("f")).match(
            LessEqual(Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            LessEqual(Variable("X"), String("f")).match(
                LessEqual(Number(1), String("g"))
            )
            is None
        )  # ground terms don't match
        assert (
            LessEqual(Variable("X"), String("f")).match(PredLiteral("p")) is None
        )  # different type
        assert (
            LessEqual(Variable("X"), Variable("X")).match(
                LessEqual(Number(1), String("f"))
            )
            is None
        )  # assignment conflict

    def test_greater_equal(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_literal = GreaterEqual(Number(0), String("x"))
        var_literal = GreaterEqual(Number(0), Variable("X"))

        # string representation
        assert str(ground_literal) == '0>="x"'
        # equality
        assert ground_literal == GreaterEqual(Number(0), String("x"))
        # hashing
        assert hash(ground_literal) == hash(GreaterEqual(Number(0), String("x")))
        # ground
        assert ground_literal.ground
        assert not var_literal.ground
        # variables
        assert ground_literal.vars() == ground_literal.global_vars() == set()
        assert var_literal.vars() == var_literal.global_vars() == {Variable("X")}
        # positive/negative literal occurrences
        assert (
            ground_literal.pos_occ() == ground_literal.neg_occ() == LiteralCollection()
        )
        # operands
        assert ground_literal.operands == (Number(0), String("x"))
        # replace arithmetic variables
        assert var_literal.replace_arith(VariableTable()) == GreaterEqual(
            Number(0), Variable("X")
        )
        assert GreaterEqual(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == GreaterEqual(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        assert GreaterEqual(Number(0), Minus(Variable(("X")))).replace_arith(
            VariableTable()
        ) == GreaterEqual(Number(0), ArithVariable(0, Minus(Variable("X"))))
        # safety characterization
        assert ground_literal.safety() == SafetyTriplet()
        assert var_literal.safety() == SafetyTriplet(unsafe={Variable("X")})
        assert GreaterEqual(Variable("Y"), Variable("X")).safety() == SafetyTriplet(
            unsafe={Variable("X"), Variable("Y")}
        )
        # evaluation
        assert not GreaterEqual(Number(0), String("x")).eval()
        assert not GreaterEqual(Number(0), Number(1)).eval()
        assert GreaterEqual(Number(0), Number(0)).eval()
        with pytest.raises(ValueError):
            GreaterEqual(Number(0), Variable("X")).eval()
        with pytest.raises(ValueError):
            GreaterEqual(Number(0), Minus(Variable("X"))).eval()

        # substitute
        assert GreaterEqual(Variable("X"), Number(0)).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == GreaterEqual(
            Number(1), Number(0)
        )  # NOTE: substitution is invalid
        # match
        assert GreaterEqual(Variable("X"), String("f")).match(
            GreaterEqual(Number(1), String("f"))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            GreaterEqual(Variable("X"), String("f")).match(
                GreaterEqual(Number(1), String("g"))
            )
            is None
        )  # ground terms don't match
        assert (
            GreaterEqual(Variable("X"), String("f")).match(PredLiteral("p")) is None
        )  # different type
        assert (
            GreaterEqual(Variable("X"), Variable("X")).match(
                GreaterEqual(Number(1), String("f"))
            )
            is None
        )  # assignment conflict
