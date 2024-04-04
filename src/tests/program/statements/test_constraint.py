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
from aspy.program.statements import AggrBaseRule, AggrElemRule, Constraint
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable, Minus, Number, String, TermTuple, Variable
from aspy.program.variable_table import VariableTable


class TestConstraint:
    def test_constraint(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_rule = Constraint(PredLiteral("p", Number(0)), PredLiteral("q"))
        var_rule = Constraint(
            PredLiteral("p", Variable("X")), PredLiteral("q", Variable("X"))
        )

        # string representation
        assert str(ground_rule) == ":- p(0), q."
        assert str(var_rule) == ":- p(X), q(X)."
        # equality
        assert ground_rule == Constraint(PredLiteral("p", Number(0)), PredLiteral("q"))
        assert var_rule == Constraint(
            PredLiteral("p", Variable("X")),
            PredLiteral("q", Variable("X")),
        )
        assert ground_rule.head == LiteralCollection()
        assert ground_rule.body == LiteralCollection(
            PredLiteral("p", Number(0)), PredLiteral("q")
        )
        assert var_rule.head == LiteralCollection()
        assert var_rule.body == LiteralCollection(
            PredLiteral("p", Variable("X")),
            PredLiteral("q", Variable("X")),
        )
        # hashing
        assert hash(ground_rule) == hash(
            Constraint(PredLiteral("p", Number(0)), PredLiteral("q"))
        )
        assert hash(var_rule) == hash(
            Constraint(
                PredLiteral("p", Variable("X")),
                PredLiteral("q", Variable("X")),
            )
        )
        # ground
        assert ground_rule.ground
        assert not var_rule.ground
        # safety
        assert ground_rule.safe
        assert var_rule.safe
        # contains aggregates
        assert not ground_rule.contains_aggregates
        assert not var_rule.contains_aggregates
        assert Constraint(
            PredLiteral("p", Variable("X")),
            AggrLiteral(AggrCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False)),
        ).contains_aggregates
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert var_rule.vars() == var_rule.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert Constraint(
            PredLiteral("p", Number(0), Minus(Variable("X")))
        ).replace_arith(VariableTable()) == Constraint(
            PredLiteral("p", Number(0), ArithVariable(0, Minus(Variable("X")))),
        )

        # substitution
        rule = Constraint(
            PredLiteral("p", Variable("X"), Number(0)),
            PredLiteral("q", Variable("X")),
        )
        assert rule.substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == Constraint(
            PredLiteral("p", Number(1), Number(0)),
            PredLiteral("q", Number(1)),
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
        rule = Constraint(
            PredLiteral("p", Variable("X"), Number(0)),
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
        )
        target_rule = Constraint(
            PredLiteral("p", Variable("X"), Number(0)),
            AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
            PredLiteral("q", Variable("X")),
            Equal(Number(0), Variable("X")),
            AggrPlaceholder(2, TermTuple(), TermTuple()),
        )
        aggr_map = dict()

        assert rule.rewrite_aggregates(1, aggr_map) == target_rule
        assert len(aggr_map) == 2

        aggr_literal, alpha_literal, eps_rule, eta_rules = aggr_map[1]
        assert aggr_literal == rule.body[1]
        assert alpha_literal == target_rule.body[1]
        assert eps_rule == AggrBaseRule(
            AggrBaseLiteral(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
            Guard(RelOp.GREATER_OR_EQ, Variable("X"), False),
            None,
            LiteralCollection(
                GreaterEqual(Variable("X"), AggrCount().base),
                PredLiteral("p", Variable("X"), Number(0)),
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
                PredLiteral("p", Variable("X"), Number(0)),
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
                PredLiteral("p", Variable("X"), Number(0)),
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
                PredLiteral("p", Variable("X"), Number(0)),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
            ),
        )
        assert len(eta_rules) == 1
        assert eta_rules[0] == AggrElemRule(
            AggrElemLiteral(2, 0, TermTuple(), TermTuple(), TermTuple()),
            elements_2[0],
            LiteralCollection(
                PredLiteral("p", Variable("X"), Number(0)),
                PredLiteral("q", Number(0)),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
            ),
        )

        # assembling
        target_rule = Constraint(
            PredLiteral("p", Variable("X"), Number(0)),
            AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
            PredLiteral("q", Variable("X")),
            Equal(Number(0), Variable("X")),
            AggrPlaceholder(2, TermTuple(), TermTuple()),
        )
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
        ) == Constraint(
            PredLiteral("p", Variable("X"), Number(0)),
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
        )

        # TODO: propagate
