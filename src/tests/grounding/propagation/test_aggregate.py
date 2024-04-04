from typing import Self

import aspy
from aspy.grounding.propagation import AggrPropagator
from aspy.program.literals import (
    AggrBaseLiteral,
    AggrCount,
    AggrElement,
    AggrElemLiteral,
    AggrLiteral,
    AggrPlaceholder,
    Equal,
    GreaterEqual,
    Guard,
    LessEqual,
    LiteralCollection,
    PredLiteral,
)
from aspy.program.operators import RelOp
from aspy.program.statements import AggrBaseRule, AggrElemRule, NormalRule
from aspy.program.terms import Number, TermTuple, Variable


class TestAggrPropagator:
    def test_aggr_propagator(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        elements_1 = (
            AggrElement(
                TermTuple(Variable("Y")),
                LiteralCollection(PredLiteral("p", Variable("Y"))),
            ),
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("p", Number(0)))
            ),
        )
        elements_2 = (
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("q", Number(0)))
            ),
        )

        # initialization of propagator
        aggr_map = {
            1: (
                AggrLiteral(
                    AggrCount(),
                    elements_1,
                    Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                ),
                AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
                AggrBaseRule(
                    AggrBaseLiteral(
                        1, TermTuple(Variable("X")), TermTuple(Variable("X"))
                    ),
                    Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                    None,
                    LiteralCollection(
                        GreaterEqual(AggrCount().base, Variable("X")),
                        PredLiteral("q", Variable("X")),
                        Equal(Number(0), Variable("X")),
                    ),
                ),
                [
                    AggrElemRule(
                        AggrElemLiteral(
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
                    AggrElemRule(
                        AggrElemLiteral(
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
                AggrLiteral(
                    AggrCount(),
                    elements_2,
                    Guard(RelOp.LESS_OR_EQ, Number(0), False),
                ),
                AggrPlaceholder(2, TermTuple(), TermTuple()),
                AggrBaseRule(
                    AggrBaseLiteral(2, TermTuple(), TermTuple()),
                    None,
                    Guard(RelOp.LESS_OR_EQ, Number(0), False),
                    LiteralCollection(
                        LessEqual(Number(0), AggrCount().base),
                        PredLiteral("q", Variable("X")),
                        Equal(Number(0), Variable("X")),
                    ),
                ),
                [
                    AggrElemRule(
                        AggrElemLiteral(2, 0, TermTuple(), TermTuple(), TermTuple()),
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
        propagator = AggrPropagator(aggr_map)
        assert propagator.aggr_map == aggr_map
        assert propagator.instance_map == dict()

        # propagation
        eps_instances = {
            # aggregate 1
            AggrBaseRule(
                AggrBaseLiteral(1, TermTuple(Variable("X")), TermTuple(Number(0))),
                Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                None,
                LiteralCollection(
                    GreaterEqual(AggrCount().base, Number(0)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
            # aggregate 2
            AggrBaseRule(
                AggrBaseLiteral(2, TermTuple(), TermTuple()),
                None,
                Guard(RelOp.LESS_OR_EQ, Number(0), False),
                LiteralCollection(
                    LessEqual(Number(0), AggrCount().base),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
        }
        eta_instances = {
            # aggregate 1
            # element 0
            AggrElemRule(
                AggrElemLiteral(
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
            AggrElemRule(
                AggrElemLiteral(
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
            AggrElemRule(
                AggrElemLiteral(
                    1, 1, TermTuple(), TermTuple(Variable("X")), TermTuple(Number(0))
                ),
                elements_1[1],
                LiteralCollection(
                    PredLiteral("p", Number(0)),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                ),
            ),
            # aggregate 2
            AggrElemRule(
                AggrElemLiteral(2, 0, TermTuple(), TermTuple(), TermTuple()),
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
        J_alpha = propagator.propagate(
            eps_instances, eta_instances, domain, domain, set()
        )
        assert J_alpha == {
            AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Number(0))),
            AggrPlaceholder(2, TermTuple(), TermTuple()),
        }

        # assembling
        rule = NormalRule(
            PredLiteral("p", Variable("X"), Number(0)),
            [
                AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
                AggrPlaceholder(2, TermTuple(), TermTuple()),
            ],
        )
        print(rule)
        rules = propagator.assemble({rule})
        assert len(rules) == 1

        # TODO: variable X ???
        # TODO: something goes wrong here, or is the test wrong???

        rule = rules.pop()
        print(rule)
        print(
            NormalRule(
                PredLiteral("p", Variable("X"), Number(0)),
                [
                    AggrLiteral(
                        AggrCount(),
                        (
                            AggrElement(
                                TermTuple(Number(0)),
                                LiteralCollection(PredLiteral("p", Number(0))),
                            ),
                            AggrElement(
                                TermTuple(Number(1)),
                                LiteralCollection(PredLiteral("p", Number(1))),
                            ),
                        ),  # first possible element order
                        Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                    ),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                    AggrLiteral(
                        AggrCount(),
                        (
                            AggrElement(
                                TermTuple(Number(0)),
                                LiteralCollection(PredLiteral("q", Number(0))),
                            ),
                        ),
                        Guard(RelOp.LESS_OR_EQ, Number(0), False),
                    ),
                ],
            )
        )
        print(
            NormalRule(
                PredLiteral("p", Variable("X"), Number(0)),
                [
                    AggrLiteral(
                        AggrCount(),
                        (
                            AggrElement(
                                TermTuple(Number(1)),
                                LiteralCollection(PredLiteral("p", Number(1))),
                            ),
                            AggrElement(
                                TermTuple(Number(0)),
                                LiteralCollection(PredLiteral("p", Number(0))),
                            ),
                        ),  # second possible element order
                        Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                    ),
                    PredLiteral("q", Number(0)),
                    Equal(Number(0), Number(0)),
                    AggrLiteral(
                        AggrCount(),
                        (
                            AggrElement(
                                TermTuple(Number(0)),
                                LiteralCollection(PredLiteral("q", Number(0))),
                            ),
                        ),
                        Guard(RelOp.LESS_OR_EQ, Number(0), False),
                    ),
                ],
            )
        )
        assert rule == NormalRule(
            PredLiteral("p", Variable("X"), Number(0)),
            [
                AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("p", Number(0))),
                        ),
                        AggrElement(
                            TermTuple(Number(1)),
                            LiteralCollection(PredLiteral("p", Number(1))),
                        ),
                    ),  # first possible element order
                    Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                ),
                PredLiteral("q", Number(0)),
                Equal(Number(0), Number(0)),
                AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                    ),
                    Guard(RelOp.LESS_OR_EQ, Number(0), False),
                ),
            ],
        ) or NormalRule(
            PredLiteral("p", Variable("X"), Number(0)),
            [
                AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(1)),
                            LiteralCollection(PredLiteral("p", Number(1))),
                        ),
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("p", Number(0))),
                        ),
                    ),  # second possible element order
                    Guard(RelOp.GREATER_OR_EQ, Variable("X"), True),
                ),
                PredLiteral("q", Number(0)),
                Equal(Number(0), Number(0)),
                AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                    ),
                    Guard(RelOp.LESS_OR_EQ, Number(0), False),
                ),
            ],
        )
