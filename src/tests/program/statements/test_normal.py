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
from aspy.program.statements import AggrBaseRule, AggrElemRule, NormalRule
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable, Minus, Number, String, TermTuple, Variable


class TestNormal:
    def test_normal_fact(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_rule = NormalRule(PredLiteral("p", Number(0)))
        var_rule = NormalRule(PredLiteral("p", Variable("X")))

        # string representation
        assert str(ground_rule) == "p(0)."
        assert str(var_rule) == "p(X)."
        # equality
        assert ground_rule.head == LiteralCollection(PredLiteral("p", Number(0)))
        assert ground_rule.body == LiteralCollection()
        assert var_rule.head == LiteralCollection(PredLiteral("p", Variable("X")))
        assert var_rule.body == LiteralCollection()
        # hashing
        assert hash(ground_rule) == hash(NormalRule(PredLiteral("p", Number(0))))
        assert hash(var_rule) == hash(NormalRule(PredLiteral("p", Variable("X"))))
        # ground
        assert ground_rule.ground
        assert not var_rule.ground
        # safety
        assert ground_rule.safe
        assert not var_rule.safe
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert var_rule.vars() == var_rule.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert NormalRule(
            PredLiteral("p", Minus(Variable("X"))),
        ).replace_arith() == NormalRule(
            PredLiteral("p", ArithVariable(0, Minus(Variable("X")))),
        )

        # substitution
        rule = NormalRule(PredLiteral("p", Variable("X"), Number(0)))
        assert rule.substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == NormalRule(
            PredLiteral("p", Number(1), Number(0))
        )  # NOTE: substitution is invalid

        # rewrite aggregates
        assert rule == rule.rewrite_aggregates(0, dict())
        # assembling
        assert rule == rule.assemble_aggregates(dict())

        # TODO: propagate

    def test_normal_rule(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_rule = NormalRule(PredLiteral("p", Number(0)), [PredLiteral("q")])
        unsafe_var_rule = NormalRule(
            PredLiteral("p", Variable("X")), [PredLiteral("q")]
        )
        safe_var_rule = NormalRule(
            PredLiteral("p", Variable("X")), [PredLiteral("q", Variable("X"))]
        )

        # string representation
        assert str(ground_rule) == "p(0) :- q."
        assert str(unsafe_var_rule) == "p(X) :- q."
        assert str(safe_var_rule) == "p(X) :- q(X)."
        # equality
        assert ground_rule.head == LiteralCollection(PredLiteral("p", Number(0)))
        assert ground_rule.body == LiteralCollection(PredLiteral("q"))
        assert unsafe_var_rule.head == LiteralCollection(
            PredLiteral("p", Variable("X"))
        )
        assert unsafe_var_rule.body == LiteralCollection(PredLiteral("q"))
        assert safe_var_rule.head == LiteralCollection(PredLiteral("p", Variable("X")))
        assert safe_var_rule.body == LiteralCollection(PredLiteral("q", Variable("X")))
        # hashing
        assert hash(ground_rule) == hash(
            NormalRule(PredLiteral("p", Number(0)), [PredLiteral("q")])
        )
        assert hash(unsafe_var_rule) == hash(
            NormalRule(PredLiteral("p", Variable("X")), [PredLiteral("q")])
        )
        assert hash(safe_var_rule) == hash(
            NormalRule(
                PredLiteral("p", Variable("X")),
                [PredLiteral("q", Variable("X"))],
            )
        )
        # ground
        assert ground_rule.ground
        assert not unsafe_var_rule.ground
        assert not safe_var_rule.ground
        # safety
        assert ground_rule.safe
        assert not unsafe_var_rule.safe
        assert safe_var_rule.safe
        # contains aggregates
        assert not ground_rule.contains_aggregates
        assert not unsafe_var_rule.contains_aggregates
        assert not safe_var_rule.contains_aggregates
        assert NormalRule(
            PredLiteral("p", Variable("X")),
            [AggrLiteral(AggrCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False))],
        ).contains_aggregates
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert (
            unsafe_var_rule.vars() == unsafe_var_rule.global_vars() == {Variable("X")}
        )
        assert safe_var_rule.vars() == safe_var_rule.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert NormalRule(
            PredLiteral("p", Minus(Variable("X"))),
            [PredLiteral("q", Minus(Variable("Y")))],
        ).replace_arith() == NormalRule(
            PredLiteral("p", ArithVariable(0, Minus(Variable("X")))),
            [PredLiteral("q", ArithVariable(1, Minus(Variable("Y"))))],
        )

        # substitution
        rule = NormalRule(
            PredLiteral("p", Variable("X"), Number(0)),
            [
                PredLiteral("q", Variable("X")),
            ],
        )
        assert rule.substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == NormalRule(
            PredLiteral("p", Number(1), Number(0)),
            [PredLiteral("q", Number(1))],
        )  # NOTE: substitution is invalid

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
        elements_2 = (
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("q", Number(0)))
            ),
        )
        rule = NormalRule(
            PredLiteral("p", Variable("X"), Number(0)),
            [
                AggrLiteral(
                    AggrCount(),
                    elements_1,
                    Guard(RelOp.GREATER_OR_EQ, Variable("X"), False),
                ),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
                AggrLiteral(
                    AggrCount(), elements_2, Guard(RelOp.LESS_OR_EQ, Number(0), True)
                ),
            ],
        )
        target_rule = NormalRule(
            PredLiteral("p", Variable("X"), Number(0)),
            [
                AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
                AggrPlaceholder(2, TermTuple(), TermTuple()),
            ],
        )
        aggr_map = dict()

        assert rule.rewrite_aggregates(1, aggr_map) == target_rule
        assert len(aggr_map) == 2

        aggr_literal, alpha_literal, eps_rule, eta_rules = aggr_map[1]
        assert aggr_literal == rule.body[0]
        assert alpha_literal == target_rule.body[0]
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

        aggr_literal, alpha_literal, eps_rule, eta_rules = aggr_map[2]
        assert aggr_literal == rule.body[-1]
        assert alpha_literal == target_rule.body[-1]
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

        # assembling
        assert target_rule.assemble_aggregates(
            {
                AggrPlaceholder(
                    1, TermTuple(Variable("X")), TermTuple(Variable("X"))
                ): AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("p", Number(0))),
                        ),
                        AggrElement(TermTuple(String("f")), LiteralCollection()),
                    ),
                    Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
                ),
                AggrPlaceholder(2, TermTuple(), TermTuple()): AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                    ),
                    Guard(RelOp.LESS_OR_EQ, Number(0), True),
                ),
            }
        ) == NormalRule(
            PredLiteral("p", Variable("X"), Number(0)),
            [
                AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("p", Number(0))),
                        ),
                        AggrElement(TermTuple(String("f")), LiteralCollection()),
                    ),
                    Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
                ),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
                AggrLiteral(
                    AggrCount(),
                    (
                        AggrElement(
                            TermTuple(Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                    ),
                    Guard(RelOp.LESS_OR_EQ, Number(0), True),
                ),
            ],
        )

        # TODO: propagate
