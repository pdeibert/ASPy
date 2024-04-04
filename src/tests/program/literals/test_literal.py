from typing import Self

import aspy
from aspy.program.literals import LiteralCollection, PredLiteral
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable, Minus, Number, String, Variable
from aspy.program.variable_table import VariableTable


class TestLiteral:
    def test_literal_collection(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        literals = LiteralCollection(
            PredLiteral("p", Number(0), Variable("X")),
            PredLiteral("q", Minus(Variable("Y"))),
        )
        # length
        assert len(literals) == 2
        # string representation
        assert str(literals) == "p(0,X),q(-Y)"
        # equality
        assert literals[0] == PredLiteral("p", Number(0), Variable("X"))
        assert literals[1] == PredLiteral("q", Minus(Variable("Y")))
        assert literals == LiteralCollection(
            PredLiteral("p", Number(0), Variable("X")),
            PredLiteral("q", Minus(Variable("Y"))),
        )
        # hashing
        assert hash(literals) == hash(
            LiteralCollection(
                PredLiteral("p", Number(0), Variable("X")),
                PredLiteral("q", Minus(Variable("Y"))),
            )
        )
        # ground
        assert not literals.ground
        # variables
        assert (
            literals.vars() == literals.global_vars() == {Variable("X"), Variable("Y")}
        )
        # replace arithmetic terms
        assert literals.replace_arith(VariableTable()) == LiteralCollection(
            PredLiteral("p", Number(0), Variable("X")),
            PredLiteral("q", ArithVariable(0, Minus(Variable("Y")))),
        )
        assert literals.safety() == SafetyTriplet.closure(
            literals[0].safety(), literals[1].safety()
        )
        # safety characterization
        assert literals.safety() == SafetyTriplet.closure(
            literals[0].safety(), literals[1].safety()
        )

        # substitute
        assert LiteralCollection(
            PredLiteral("p", String("f"), Variable("X"))
        ).substitute(
            Substitution({String("f"): Number(0), Variable("X"): Number(1)})
        ) == LiteralCollection(
            PredLiteral("p", String("f"), Number(1))
        )  # NOTE: substitution is invalid
        # match
        assert LiteralCollection(
            PredLiteral("p", Variable("X"), String("f")),
            PredLiteral("q", Variable("X")),
        ).match(
            LiteralCollection(
                PredLiteral("p", Number(1), String("f")),
                PredLiteral("q", Number(1)),
            )
        ) == Substitution(
            {Variable("X"): Number(1)}
        )
        assert (
            LiteralCollection(
                PredLiteral("p", Variable("X"), String("f")),
                PredLiteral("q", Variable("X")),
            ).match(
                LiteralCollection(
                    PredLiteral("p", Number(1), String("g")),
                    PredLiteral("q", Number(1)),
                )
            )
            is None
        )  # ground terms don't match
        assert (
            LiteralCollection(
                PredLiteral("p", Variable("X"), String("f")),
                PredLiteral("q", Variable("X")),
            ).match(PredLiteral("p"))
            is None
        )  # wrong type
        assert (
            LiteralCollection(
                PredLiteral("p", Variable("X"), String("f")),
                PredLiteral("q", Variable("X")),
            ).match(
                LiteralCollection(
                    PredLiteral("p", Number(1), String("f")),
                    PredLiteral("q", Number(0)),
                )
            )
            is None
        )  # assignment conflict
        assert (
            LiteralCollection(
                PredLiteral("p", Number(0), String("f")),
                PredLiteral("q", Number(1)),
                PredLiteral("u", Number(0)),
            ).match(
                LiteralCollection(
                    PredLiteral("p", Number(0), String("f")),
                    PredLiteral("u", Number(0)),
                    PredLiteral("q", Number(1)),
                )
            )
            == Substitution()
        )  # different order of literals

        # combining literal collections
        assert literals + LiteralCollection(PredLiteral("u")) == LiteralCollection(
            PredLiteral("p", Number(0), Variable("X")),
            PredLiteral("q", Minus(Variable("Y"))),
            PredLiteral("u"),
        )
        # without
        assert literals.without(
            PredLiteral("p", Number(0), Variable("X"))
        ) == LiteralCollection(PredLiteral("q", Minus(Variable("Y"))))
        assert (
            literals.without(PredLiteral("p", Number(1), Variable("X"))) == literals
        )  # not part of original literal collection
        # TODO: iter
