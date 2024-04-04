from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.literals import (
    AggrBaseLiteral,
    AggrElement,
    AggrElemLiteral,
    ChoiceBaseLiteral,
    ChoiceElemLiteral,
    GreaterEqual,
    Guard,
    LessEqual,
    LiteralCollection,
    PredLiteral,
)
from aspy.program.operators import RelOp
from aspy.program.statements import (
    AggrBaseRule,
    AggrElemRule,
    ChoiceBaseRule,
    ChoiceElement,
    ChoiceElemRule,
)
from aspy.program.substitution import Substitution
from aspy.program.symbols import SpecialChar
from aspy.program.terms import Number, TermTuple, Variable


class TestSpecial:
    def test_aggr_base_rule(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        global_vars = TermTuple(Variable("X"), Variable("Y"))
        base_value = Number(0)

        ground_guards = (
            Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            Guard(RelOp.LESS_OR_EQ, Number(10), True),
        )
        ground_guard_literals = LiteralCollection(
            GreaterEqual(Number(-1), base_value), LessEqual(base_value, Number(10))
        )
        ground_eps_literal = AggrBaseLiteral(
            1, global_vars, TermTuple(Number(10), Number(3))
        )
        ground_rule = AggrBaseRule(
            ground_eps_literal,
            *ground_guards,
            ground_guard_literals
            + LiteralCollection(PredLiteral("p", Number(2), Number(3))),
        )

        var_guards = (
            Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            Guard(RelOp.LESS_OR_EQ, Variable("X"), True),
        )
        var_guard_literals = LiteralCollection(
            GreaterEqual(Number(-1), base_value), LessEqual(base_value, Variable("X"))
        )
        var_eps_literal = AggrBaseLiteral(1, global_vars, global_vars)
        var_rule = AggrBaseRule(
            var_eps_literal,
            *var_guards,
            var_guard_literals
            + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
        )

        # invalid initialization
        with pytest.raises(ValueError):
            AggrBaseRule.from_scratch(
                1,
                {global_vars},
                *ground_guards,
                base_value,
                LiteralCollection(PredLiteral("p", Number(2), Number(3))),
            )  # non-tuple for 'global_vars'
        with pytest.raises(ValueError):
            AggrBaseRule.from_scratch(
                1,
                global_vars,
                Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
                Guard(RelOp.LESS_OR_EQ, Number(10), False),
                base_value,
                LiteralCollection(PredLiteral("p", Number(2), Number(3))),
            )  # two left guards
        # correct initialization
        assert ground_rule.ref_id == var_rule.ref_id == 1
        # string representation
        assert (
            str(ground_rule)
            == f"{SpecialChar.EPS.value}{SpecialChar.ALPHA.value}{1}(10,3) :- -1>=0,0<=10,p(2,3)."
        )  # noqa
        assert (
            str(var_rule)
            == f"{SpecialChar.EPS.value}{SpecialChar.ALPHA.value}{1}(X,Y) :- -1>=0,0<=X,p(2,Y)."
        )  # noqa
        # equality
        assert len(ground_rule.body) == 3
        assert ground_rule.body[0] == GreaterEqual(
            Number(-1), Number(0)
        )  # NOTE: order of operands in built-in terms
        assert ground_rule.body[1] == LessEqual(
            Number(0), Number(10)
        )  # NOTE: order of operands in built-in terms
        assert ground_rule.body[2] == PredLiteral("p", Number(2), Number(3))
        assert len(var_rule.body) == 3
        assert var_rule.body[0] == GreaterEqual(
            Number(-1), Number(0)
        )  # NOTE: order of operands in built-in terms
        assert var_rule.body[1] == LessEqual(
            Number(0), Variable("X")
        )  # NOTE: order of operands in built-in terms
        assert var_rule.body[2] == PredLiteral("p", Number(2), Variable("Y"))
        assert ground_rule.head == LiteralCollection(ground_eps_literal)
        assert ground_rule.body == ground_guard_literals + LiteralCollection(
            PredLiteral("p", Number(2), Number(3))
        )
        assert var_rule.head == LiteralCollection(var_eps_literal)
        assert var_rule.body == var_guard_literals + LiteralCollection(
            PredLiteral("p", Number(2), Variable("Y"))
        )
        # hashing
        assert hash(ground_rule) == hash(
            AggrBaseRule(
                ground_eps_literal,
                *ground_guards,
                ground_guard_literals
                + LiteralCollection(PredLiteral("p", Number(2), Number(3))),
            )
        )
        assert hash(var_rule) == hash(
            AggrBaseRule(
                var_eps_literal,
                *var_guards,
                var_guard_literals
                + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
            )
        )
        # ground
        assert ground_rule.ground
        assert not var_rule.ground
        # safety
        assert ground_rule.safe
        assert not var_rule.safe
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert var_rule.vars() == var_rule.global_vars() == set(global_vars)
        # TODO: replace arithmetic terms
        # TODO: gather variable assignement

        # substitution
        assert (
            var_rule.substitute(
                Substitution({Variable("X"): Number(10), Variable("Y"): Number(3)})
            )
            == ground_rule
        )
        # match
        # assert Eq var_rule.match(ground_rule), Substitution({Variable('X'): Number(10), Variable('Y'): Number(3)}))
        # TODO: ground terms don't match
        # TODO: assignment conflict

    def test_aggr_element_rule(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        local_vars = TermTuple(Variable("L"))
        global_vars = TermTuple(Variable("X"), Variable("Y"))
        element = AggrElement(
            TermTuple(Variable("L")), LiteralCollection(PredLiteral("p", Variable("L")))
        )

        ground_eta_literal = AggrElemLiteral(
            1, 3, local_vars, global_vars, TermTuple(Number(5), Number(10), Number(3))
        )
        ground_rule = AggrElemRule(
            ground_eta_literal,
            element,
            LiteralCollection(
                PredLiteral("p", Number(5)),
                PredLiteral("p", Number(2), Number(3)),
            ),
        )

        var_eta_literal = AggrElemLiteral(
            1, 3, local_vars, global_vars, local_vars + global_vars
        )
        var_rule = AggrElemRule(
            var_eta_literal,
            element,
            element.literals
            + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
        )

        # correct initialization
        assert ground_rule.ref_id == var_rule.ref_id == 1
        assert ground_rule.element_id == var_rule.element_id == 3
        assert ground_rule.element == var_rule.element == element
        # string representation
        assert (
            str(ground_rule)
            == f"{SpecialChar.ETA.value}{SpecialChar.ALPHA.value}{1}_{3}(5,10,3) :- p(5),p(2,3)."
        )  # noqa
        assert (
            str(var_rule)
            == f"{SpecialChar.ETA.value}{SpecialChar.ALPHA.value}{1}_{3}(L,X,Y) :- p(L),p(2,Y)."
        )  # noqa
        # equality
        assert len(ground_rule.body) == 2
        assert ground_rule.body[0] == PredLiteral("p", Number(5))
        assert ground_rule.body[1] == PredLiteral("p", Number(2), Number(3))
        assert len(var_rule.body) == 2
        assert var_rule.body[0] == PredLiteral("p", Variable("L"))
        assert var_rule.body[1] == PredLiteral("p", Number(2), Variable("Y"))
        # hashing
        assert hash(ground_rule) == hash(
            AggrElemRule(
                ground_eta_literal,
                element,
                LiteralCollection(
                    PredLiteral("p", Number(5)),
                    PredLiteral("p", Number(2), Number(3)),
                ),
            )
        )
        assert hash(var_rule) == hash(
            AggrElemRule(
                var_eta_literal,
                element,
                element.literals
                + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
            )
        )
        # ground
        assert ground_rule.ground
        assert not var_rule.ground
        # safety
        assert ground_rule.safe
        assert not var_rule.safe
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert (
            var_rule.vars() == var_rule.global_vars() == set(global_vars + local_vars)
        )
        # TODO: replace arithmetic terms
        # TODO: gather variable assignement

        # substitution
        assert (
            var_rule.substitute(
                Substitution(
                    {
                        Variable("L"): Number(5),
                        Variable("X"): Number(10),
                        Variable("Y"): Number(3),
                    }
                )
            )
            == ground_rule
        )
        # match
        # assert Eq var_rule.match(ground_rule), Substitution({Variable('L'): Number(5), Variable('X'): Number(10), Variable('Y'): Number(3)}))
        # TODO: ground terms don't match
        # TODO: assignment conflict

    def test_choice_base_rule(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        global_vars = TermTuple(Variable("X"), Variable("Y"))
        base_value = Number(0)

        ground_guards = (
            Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            Guard(RelOp.LESS_OR_EQ, Number(10), True),
        )
        ground_guard_literals = LiteralCollection(
            GreaterEqual(Number(-1), base_value), LessEqual(base_value, Number(10))
        )
        ground_eps_literal = ChoiceBaseLiteral(
            1, global_vars, TermTuple(Number(10), Number(3))
        )
        ground_rule = ChoiceBaseRule(
            ground_eps_literal,
            *ground_guards,
            ground_guard_literals
            + LiteralCollection(PredLiteral("p", Number(2), Number(3))),
        )

        var_guards = (
            Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            Guard(RelOp.LESS_OR_EQ, Variable("X"), True),
        )
        var_guard_literals = LiteralCollection(
            GreaterEqual(Number(-1), base_value), LessEqual(base_value, Variable("X"))
        )
        var_eps_literal = ChoiceBaseLiteral(1, global_vars, global_vars)
        var_rule = ChoiceBaseRule(
            var_eps_literal,
            *var_guards,
            var_guard_literals
            + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
        )

        # invalid initialization
        with pytest.raises(ValueError):
            ChoiceBaseRule.from_scratch(
                1,
                {global_vars},
                *ground_guards,
                LiteralCollection(PredLiteral("p", Number(2), Number(3))),
            )  # non-tuple for 'global_vars'
        with pytest.raises(ValueError):
            ChoiceBaseRule.from_scratch(
                1,
                global_vars,
                Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
                Guard(RelOp.LESS_OR_EQ, Number(10), False),
                LiteralCollection(PredLiteral("p", Number(2), Number(3))),
            )  # two left guards
        # correct initialization
        assert ground_rule.ref_id == var_rule.ref_id == 1
        # string representation
        assert (
            str(ground_rule)
            == f"{SpecialChar.EPS.value}{SpecialChar.CHI.value}{1}(10,3) :- -1>=0,0<=10,p(2,3)."
        )  # noqa
        assert (
            str(var_rule)
            == f"{SpecialChar.EPS.value}{SpecialChar.CHI.value}{1}(X,Y) :- -1>=0,0<=X,p(2,Y)."
        )  # noqa

        # equality
        assert len(ground_rule.body) == 3
        assert ground_rule.body[0] == GreaterEqual(
            Number(-1), Number(0)
        )  # NOTE: order of operands in built-in terms
        assert ground_rule.body[1] == LessEqual(
            Number(0), Number(10)
        )  # NOTE: order of operands in built-in terms
        assert ground_rule.body[2] == PredLiteral("p", Number(2), Number(3))
        assert len(var_rule.body) == 3
        assert var_rule.body[0] == GreaterEqual(
            Number(-1), Number(0)
        )  # NOTE: order of operands in built-in terms
        assert var_rule.body[1] == LessEqual(
            Number(0), Variable("X")
        )  # NOTE: order of operands in built-in terms
        assert var_rule.body[2] == PredLiteral("p", Number(2), Variable("Y"))
        assert ground_rule.head == LiteralCollection(ground_eps_literal)
        assert ground_rule.body == ground_guard_literals + LiteralCollection(
            PredLiteral("p", Number(2), Number(3))
        )
        assert var_rule.head == LiteralCollection(var_eps_literal)
        assert var_rule.body == var_guard_literals + LiteralCollection(
            PredLiteral("p", Number(2), Variable("Y"))
        )
        # hashing
        assert hash(ground_rule) == hash(
            AggrBaseRule(
                ground_eps_literal,
                *ground_guards,
                ground_guard_literals
                + LiteralCollection(PredLiteral("p", Number(2), Number(3))),
            )
        )
        assert hash(var_rule) == hash(
            ChoiceBaseRule(
                var_eps_literal,
                *var_guards,
                var_guard_literals
                + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
            )
        )
        # ground
        assert ground_rule.ground
        assert not var_rule.ground
        # safety
        assert ground_rule.safe
        assert not var_rule.safe
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert var_rule.vars() == var_rule.global_vars() == set(global_vars)
        # TODO: replace arithmetic terms
        # TODO: gather variable assignement

        # substitution
        assert (
            var_rule.substitute(
                Substitution({Variable("X"): Number(10), Variable("Y"): Number(3)})
            )
            == ground_rule
        )
        # match
        # assert Eq var_rule.match(ground_rule), Substitution({Variable('X'): Number(10), Variable('Y'): Number(3)}))
        # TODO: ground terms don't match
        # TODO: assignment conflict

    def test_choice_element_rule(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        local_vars = TermTuple(Variable("L"))
        global_vars = TermTuple(Variable("X"), Variable("Y"))
        element = ChoiceElement(
            PredLiteral("p", Variable("L")),
            LiteralCollection(PredLiteral("p", Variable("L"))),
        )

        ground_eta_literal = ChoiceElemLiteral(
            1, 3, local_vars, global_vars, TermTuple(Number(5), Number(10), Number(3))
        )
        ground_rule = ChoiceElemRule(
            ground_eta_literal,
            element,
            LiteralCollection(
                PredLiteral("p", Number(5)),
                PredLiteral("p", Number(2), Number(3)),
            ),
        )

        var_eta_literal = ChoiceElemLiteral(
            1, 3, local_vars, global_vars, local_vars + global_vars
        )
        var_rule = ChoiceElemRule(
            var_eta_literal,
            element,
            element.literals
            + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
        )

        # correct initialization
        assert ground_rule.ref_id == var_rule.ref_id == 1
        assert ground_rule.element_id == var_rule.element_id == 3
        assert ground_rule.element == var_rule.element == element
        # string representation
        assert (
            str(ground_rule)
            == f"{SpecialChar.ETA.value}{SpecialChar.CHI.value}{1}_{3}(5,10,3) :- p(5),p(2,3)."
        )  # noqa
        assert (
            str(var_rule)
            == f"{SpecialChar.ETA.value}{SpecialChar.CHI.value}{1}_{3}(L,X,Y) :- p(L),p(2,Y)."
        )  # noqa
        # equality
        assert len(ground_rule.body) == 2
        assert ground_rule.body[0] == PredLiteral("p", Number(5))
        assert ground_rule.body[1] == PredLiteral("p", Number(2), Number(3))
        assert len(var_rule.body) == 2
        assert var_rule.body[0] == PredLiteral("p", Variable("L"))
        assert var_rule.body[1] == PredLiteral("p", Number(2), Variable("Y"))
        # hashing
        assert hash(ground_rule) == hash(
            ChoiceElemRule(
                ground_eta_literal,
                element,
                LiteralCollection(
                    PredLiteral("p", Number(5)),
                    PredLiteral("p", Number(2), Number(3)),
                ),
            )
        )
        assert hash(var_rule) == hash(
            ChoiceElemRule(
                var_eta_literal,
                element,
                element.literals
                + LiteralCollection(PredLiteral("p", Number(2), Variable("Y"))),
            )
        )
        # ground
        assert ground_rule.ground
        assert not var_rule.ground
        # safety
        assert ground_rule.safe
        assert not var_rule.safe
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert (
            var_rule.vars() == var_rule.global_vars() == set(global_vars + local_vars)
        )
        # TODO: replace arithmetic terms
        # TODO: gather variable assignement

        # substitution
        assert (
            var_rule.substitute(
                Substitution(
                    {
                        Variable("L"): Number(5),
                        Variable("X"): Number(10),
                        Variable("Y"): Number(3),
                    }
                )
            )
            == ground_rule
        )
        # match
        # assert Eq var_rule.match(ground_rule), Substitution({Variable('L'): Number(5), Variable('X'): Number(10), Variable('Y'): Number(3)}))
        # TODO: ground terms don't match
        # TODO: assignment conflict
