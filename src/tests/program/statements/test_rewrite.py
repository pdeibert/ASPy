from typing import Self

import aspy
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
from aspy.program.statements import AggrBaseRule, AggrElemRule, rewrite_aggregate
from aspy.program.terms import Number, TermTuple, Variable


class TestRewrite:
    def test_rewrite_aggregate(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # rewrite aggregates
        elements_1 = (
            AggrElement(
                TermTuple(Variable("Y")),
                LiteralCollection(PredLiteral("p", Variable("Y"))),
            ),
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("p", Number(0)))
            ),
        )
        aggregate_1 = AggrLiteral(
            AggrCount(),
            elements_1,
            Guard(RelOp.GREATER_OR_EQ, Variable("X"), False),
        )

        elements_2 = (
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("q", Number(0)))
            ),
        )
        aggregate_2 = AggrLiteral(
            AggrCount(), elements_2, Guard(RelOp.LESS_OR_EQ, Number(0), True)
        )

        alpha_literal, eps_rule, eta_rules = rewrite_aggregate(
            aggregate_1,
            1,
            {Variable("X")},
            [PredLiteral("q", Variable("X")), Equal(Number(0), Variable("X"))],
        )
        assert alpha_literal == AggrPlaceholder(
            1, TermTuple(Variable("X")), TermTuple(Variable("X"))
        )
        assert eps_rule == AggrBaseRule(
            AggrBaseLiteral(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
            Guard(RelOp.GREATER_OR_EQ, Variable("X"), False),
            None,
            LiteralCollection(
                GreaterEqual(Variable("X"), AggrCount().base),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
            ),
        )
        assert len(eta_rules) == 2
        assert eta_rules[0] == AggrElemRule(
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
        )
        assert eta_rules[1] == AggrElemRule(
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
        )

        alpha_literal, eps_rule, eta_rules = rewrite_aggregate(
            aggregate_2,
            2,
            {Variable("X")},
            [PredLiteral("q", Variable("X")), Equal(Number(0), Variable("X"))],
        )
        assert alpha_literal == AggrPlaceholder(2, TermTuple(), TermTuple())
        assert eps_rule == AggrBaseRule(
            AggrBaseLiteral(2, TermTuple(), TermTuple()),
            None,
            Guard(RelOp.LESS_OR_EQ, Number(0), True),
            LiteralCollection(
                LessEqual(AggrCount().base, Number(0)),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
            ),
        )
        assert len(eta_rules) == 1
        assert eta_rules[0] == AggrElemRule(
            AggrElemLiteral(2, 0, TermTuple(), TermTuple(), TermTuple()),
            elements_2[0],
            LiteralCollection(
                PredLiteral("q", Number(0)),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
            ),
        )
