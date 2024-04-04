from typing import Self

import pytest  # type: ignore

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
from aspy.program.statements import AggrBaseRule, AggrElemRule, WeakConstraint
from aspy.program.statements.weak_constraint import WeightAtLevel
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable, Minus, Number, String, TermTuple, Variable
from aspy.program.variable_table import VariableTable


class TestWeakConstraint:
    def test_weight_at_level(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_term = WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1)))
        var_term = WeightAtLevel(Number(0), Variable("X"), (Variable("Y"), Number(-1)))

        # string representation
        assert str(ground_term) == "0@1, 2,-1"
        str(var_term) == "0@X, Y,-1"
        # equality
        assert ground_term == WeightAtLevel(
            Number(0), Number(1), (Number(2), Number(-1))
        )
        assert var_term == WeightAtLevel(
            Number(0), Variable("X"), (Variable("Y"), Number(-1))
        )
        # hashing
        assert hash(ground_term) == hash(
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1)))
        )
        assert hash(var_term) == hash(
            WeightAtLevel(Number(0), Variable("X"), (Variable("Y"), Number(-1)))
        )
        # ground
        assert ground_term.ground
        assert not var_term.ground
        # safety characterization
        with pytest.raises(Exception):
            ground_term.safety()
        with pytest.raises(Exception):
            var_term.safety()
        # variables
        assert ground_term.vars() == ground_term.global_vars() == set()
        assert (
            var_term.vars() == var_term.global_vars() == {Variable("X"), Variable("Y")}
        )
        # replace arithmetic terms
        assert WeightAtLevel(
            Number(0), Minus(Variable("X")), (Variable("Y"), Number(-1))
        ).replace_arith(VariableTable()) == WeightAtLevel(
            Number(0),
            ArithVariable(0, Minus(Variable("X"))),
            (Variable("Y"), Number(-1)),
        )

        # substitution
        assert var_term.substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == WeightAtLevel(
            Number(0), Number(1), (Variable("Y"), Number(-1))
        )  # NOTE: substitution is invalid

    def test_weak_constraint(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_rule = WeakConstraint(
            (PredLiteral("p", Number(0)), PredLiteral("q")),
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
        )
        var_rule = WeakConstraint(
            (PredLiteral("p", Variable("X")), PredLiteral("q", Variable("X"))),
            WeightAtLevel(Number(0), Variable("X"), (Variable("Y"), Number(-1))),
        )

        # string representation
        assert str(ground_rule) == ":~ p(0),q. [0@1, 2,-1]"
        assert str(var_rule) == ":~ p(X),q(X). [0@X, Y,-1]"
        # equality
        assert ground_rule == WeakConstraint(
            (PredLiteral("p", Number(0)), PredLiteral("q")),
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
        )
        assert var_rule == WeakConstraint(
            (PredLiteral("p", Variable("X")), PredLiteral("q", Variable("X"))),
            WeightAtLevel(Number(0), Variable("X"), (Variable("Y"), Number(-1))),
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
            WeakConstraint(
                (PredLiteral("p", Number(0)), PredLiteral("q")),
                WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
            ),
        )
        assert hash(var_rule) == hash(
            WeakConstraint(
                (PredLiteral("p", Variable("X")), PredLiteral("q", Variable("X"))),
                WeightAtLevel(Number(0), Variable("X"), (Variable("Y"), Number(-1))),
            ),
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
        assert WeakConstraint(
            (
                PredLiteral("p", Variable("X")),
                AggrLiteral(AggrCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False)),
            ),
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
        ).contains_aggregates
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert var_rule.vars() == var_rule.global_vars() == {Variable("X")}
        # replace arithmetic terms
        assert WeakConstraint(
            (PredLiteral("p", Number(0), Minus(Variable("X"))),),
            WeightAtLevel(Number(0), Minus(Variable("X")), (Variable("Y"), Number(-1))),
        ).replace_arith(VariableTable()) == WeakConstraint(
            (PredLiteral("p", Number(0), ArithVariable(0, Minus(Variable("X")))),),
            WeightAtLevel(
                Number(0),
                ArithVariable(1, Minus(Variable("X"))),
                (Variable("Y"), Number(-1)),
            ),
        )

        # substitution
        rule = WeakConstraint(
            (
                PredLiteral("p", Variable("X"), Number(0)),
                PredLiteral("q", Variable("X")),
            ),
            WeightAtLevel(Number(0), Variable("X"), (Variable("Y"), Number(-1))),
        )
        assert rule.substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == WeakConstraint(
            (
                PredLiteral("p", Number(1), Number(0)),
                PredLiteral("q", Number(1)),
            ),
            WeightAtLevel(Number(0), Number(1), (Variable("Y"), Number(-1))),
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
        rule = WeakConstraint(
            (
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
            ),
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
        )
        target_rule = WeakConstraint(
            (
                PredLiteral("p", Variable("X"), Number(0)),
                AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
                AggrPlaceholder(2, TermTuple(), TermTuple()),
            ),
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
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
        target_rule = WeakConstraint(
            (
                PredLiteral("p", Variable("X"), Number(0)),
                AggrPlaceholder(1, TermTuple(Variable("X")), TermTuple(Variable("X"))),
                PredLiteral("q", Variable("X")),
                Equal(Number(0), Variable("X")),
                AggrPlaceholder(2, TermTuple(), TermTuple()),
            ),
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
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
        ) == WeakConstraint(
            (
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
            ),
            WeightAtLevel(Number(0), Number(1), (Number(2), Number(-1))),
        )

        # TODO: propagate
