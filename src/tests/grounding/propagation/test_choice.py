from typing import Self

import aspy
from aspy.grounding.propagation import ChoicePropagator
from aspy.program.literals import (
    ChoiceBaseLiteral,
    ChoiceElemLiteral,
    ChoicePlaceholder,
    Equal,
    GreaterEqual,
    Guard,
    LessEqual,
    LiteralCollection,
    PredLiteral,
)
from aspy.program.operators import RelOp
from aspy.program.statements import (
    Choice,
    ChoiceBaseRule,
    ChoiceElement,
    ChoiceElemRule,
    ChoiceRule,
    NormalRule,
)
from aspy.program.terms import Number, TermTuple, Variable


class TestChoicePropagator:
    def test_choice_propagator(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        elements_1 = (
            ChoiceElement(
                PredLiteral("p", Variable("Y")),
                LiteralCollection(PredLiteral("q", Variable("Y"))),
            ),
            ChoiceElement(
                PredLiteral("q", Number(0)),
                LiteralCollection(PredLiteral("p", Number(0))),
            ),
        )
        elements_2 = (
            ChoiceElement(
                PredLiteral("p", Number(0)),
                LiteralCollection(PredLiteral("q", Number(0))),
            ),
        )

        # initialization of propagator
        choice_map = {
            1: (
                Choice(
                    elements_1,
                    Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                ),
                ChoicePlaceholder(
                    1, TermTuple(Variable("X")), TermTuple(Variable("X"))
                ),
                ChoiceBaseRule(
                    ChoiceBaseLiteral(
                        1, TermTuple(Variable("X")), TermTuple(Variable("X"))
                    ),
                    Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                    None,
                    LiteralCollection(
                        GreaterEqual(Number(0), Variable("X")),
                        PredLiteral("q", Variable("X")),
                        Equal(Number(0), Variable("X")),
                    ),
                ),
                [
                    ChoiceElemRule(
                        ChoiceElemLiteral(
                            1,
                            0,
                            TermTuple(Variable("Y")),
                            TermTuple(Variable("X")),
                            TermTuple(Variable("Y"), Variable("X")),
                        ),
                        elements_1[0],
                        LiteralCollection(
                            PredLiteral("p", Variable("Y")),
                            PredLiteral("q", Variable("X")),
                            Equal(Number(0), Variable("X")),
                        ),
                    ),
                    ChoiceElemRule(
                        ChoiceElemLiteral(
                            1,
                            1,
                            TermTuple(),
                            TermTuple(Variable("X")),
                            TermTuple(Variable("X")),
                        ),
                        elements_1[1],
                        LiteralCollection(
                            PredLiteral("p", Number(0)),
                            PredLiteral("q", Variable("X")),
                            Equal(Number(0), Variable("X")),
                        ),
                    ),
                ],
            ),
            2: (
                Choice(
                    elements_2,
                    Guard(RelOp.LESS_OR_EQ, Number(0), False),
                ),
                ChoicePlaceholder(2, TermTuple(), TermTuple()),
                ChoiceBaseRule(
                    ChoiceBaseLiteral(2, TermTuple(), TermTuple()),
                    None,
                    Guard(RelOp.LESS_OR_EQ, Number(0), False),
                    LiteralCollection(
                        LessEqual(Number(0), Number(0)),
                        PredLiteral("q", Variable("X")),
                        Equal(Number(0), Variable("X")),
                    ),
                ),
                [
                    ChoiceElemRule(
                        ChoiceElemLiteral(2, 0, TermTuple(), TermTuple(), TermTuple()),
                        elements_2[0],
                        LiteralCollection(
                            PredLiteral("q", Number(0)),
                            PredLiteral("q", Variable("X")),
                            Equal(Number(0), Variable("X")),
                        ),
                    )
                ],
            ),
        }
        propagator = ChoicePropagator(choice_map)
        assert propagator.choice_map == choice_map
        assert propagator.instance_map == dict()

        # propagation
        eps_instances = {
            # choice 1
            ChoiceBaseRule(
                ChoiceBaseLiteral(1, TermTuple(Variable("X")), TermTuple(Number(0))),
                Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                None,
                LiteralCollection(
                    GreaterEqual(Number(0), Number(0)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
            # choice 2
            ChoiceBaseRule(
                ChoiceBaseLiteral(2, TermTuple(), TermTuple()),
                None,
                Guard(RelOp.LESS_OR_EQ, Number(0), False),
                LiteralCollection(
                    LessEqual(Number(0), Number(0)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
        }

        eta_instances = {
            # choice 1
            # element 0
            ChoiceElemRule(
                ChoiceElemLiteral(
                    1,
                    0,
                    TermTuple(Variable("Y")),
                    TermTuple(Variable("X")),
                    TermTuple(Number(0), Number(0)),
                ),
                elements_1[0],
                LiteralCollection(
                    PredLiteral("p", Number(0)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
            ChoiceElemRule(
                ChoiceElemLiteral(
                    1,
                    0,
                    TermTuple(Variable("Y")),
                    TermTuple(Variable("X")),
                    TermTuple(Number(1), Number(0)),
                ),
                elements_1[0],
                LiteralCollection(
                    PredLiteral("p", Number(1)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
            # element 1
            ChoiceElemRule(
                ChoiceElemLiteral(
                    1, 1, TermTuple(), TermTuple(Variable("X")), TermTuple(Number(0))
                ),
                elements_1[1],
                LiteralCollection(
                    PredLiteral("p", Number(0)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
            # choice 2
            ChoiceElemRule(
                ChoiceElemLiteral(2, 0, TermTuple(), TermTuple(), TermTuple()),
                elements_2[0],
                LiteralCollection(
                    PredLiteral("q", Number(0)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
        }

        domain = {
            PredLiteral("p", Number(0)),
            PredLiteral("p", Number(1)),
            PredLiteral("q", Number(0)),
            PredLiteral("q", Number(1)),
        }
        J_chi = propagator.propagate(
            eps_instances, eta_instances, domain, domain, set()
        )

        assert J_chi == {
            ChoicePlaceholder(1, TermTuple(Variable("X")), TermTuple(Number(0))),
            ChoicePlaceholder(2, TermTuple(), TermTuple()),
        }

        # assembling
        rule_1 = NormalRule(
            ChoicePlaceholder(1, TermTuple(Variable("X")), TermTuple(Number(0))),
            [PredLiteral("q", Number(0)), Equal(Number(0), Number(0))],
        )
        rule_2 = NormalRule(
            ChoicePlaceholder(2, TermTuple(), TermTuple()),
            [PredLiteral("q", Number(0)), Equal(Number(0), Number(0))],
        )
        rules = propagator.assemble({rule_1, rule_2}, J_chi)

        assert len(rules) == 2
        assert set(rules) == {
            ChoiceRule(
                Choice(
                    (
                        ChoiceElement(
                            PredLiteral("q", Number(0)),
                            LiteralCollection(PredLiteral("p", Number(0))),
                        ),
                        ChoiceElement(
                            PredLiteral("p", Number(1)),
                            LiteralCollection(PredLiteral("q", Number(1))),
                        ),
                        ChoiceElement(
                            PredLiteral("p", Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                    ),
                    Guard(RelOp.GREATER_OR_EQ, Number(0), True),
                ),
                (
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
            ChoiceRule(
                Choice(
                    (
                        ChoiceElement(
                            PredLiteral("p", Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                    ),
                    Guard(RelOp.LESS_OR_EQ, Number(0), False),
                ),
                (
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
        }
