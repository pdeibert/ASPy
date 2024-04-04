from typing import Self, Set

import pytest  # type: ignore

import aspy
from aspy.program.literals import (
    AggrCount,
    AggrLiteral,
    ChoiceBaseLiteral,
    ChoiceElemLiteral,
    ChoicePlaceholder,
    Equal,
    GreaterEqual,
    Guard,
    LiteralCollection,
    Naf,
    PredLiteral,
)
from aspy.program.operators import RelOp
from aspy.program.statements import (
    Choice,
    ChoiceBaseRule,
    ChoiceElement,
    ChoiceElemRule,
    ChoiceRule,
    Constraint,
    NormalRule,
)
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable, Minus, Number, String, TermTuple, Variable
from aspy.program.variable_table import VariableTable


class DummyBody:  # pragma: no cover
    def __init__(self: Self, vars: Set["Variable"]) -> None:
        self.vars = vars

    def global_vars(self: Self) -> Set["Variable"]:
        return self.vars


class DummyRule:  # pragma: no cover
    def __init__(self: Self, vars: Set["Variable"]) -> None:
        self.body = DummyBody(vars)


class TestChoice:
    def test_choice_element(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        element = ChoiceElement(
            PredLiteral("p", String("str")),
            LiteralCollection(
                PredLiteral("p", Number(0)),
                Naf(PredLiteral("q", Variable("Y"))),
            ),
        )
        # string representation
        assert str(element) == 'p("str"):p(0),not q(Y)'
        # equality
        assert element == ChoiceElement(
            PredLiteral("p", String("str")),
            LiteralCollection(
                PredLiteral("p", Number(0)),
                Naf(PredLiteral("q", Variable("Y"))),
            ),
        )
        # head
        assert element.head == LiteralCollection(
            PredLiteral("p", String("str")),
        )
        # body
        assert element.body == LiteralCollection(
            PredLiteral("p", Number(0)),
            Naf(PredLiteral("q", Variable("Y"))),
        )
        # hashing
        assert hash(element) == hash(
            ChoiceElement(
                PredLiteral("p", String("str")),
                LiteralCollection(
                    PredLiteral("p", Number(0)),
                    Naf(PredLiteral("q", Variable("Y"))),
                ),
            ),
        )
        # ground
        assert not element.ground
        # positive/negative literal occurrences
        assert element.pos_occ() == LiteralCollection(
            PredLiteral("p", String("str")), PredLiteral("p", Number(0))
        )
        assert element.neg_occ() == LiteralCollection(PredLiteral("q", Variable("Y")))
        # vars
        assert element.vars() == element.global_vars() == {Variable("Y")}
        # safety
        with pytest.raises(Exception):
            element.safety()
        # replace arithmetic terms
        assert element.replace_arith(VariableTable()) == element
        element = ChoiceElement(
            PredLiteral("p", String("str")),
            LiteralCollection(
                PredLiteral("p", Number(0)),
                Naf(PredLiteral("q", Minus(Variable("Y")))),
            ),
        )
        assert element.replace_arith(VariableTable()) == ChoiceElement(
            PredLiteral("p", String("str")),
            LiteralCollection(
                PredLiteral("p", Number(0)),
                Naf(PredLiteral("q", ArithVariable(0, Minus(Variable("Y"))))),
            ),
        )
        # substitute
        assert element.substitute(
            Substitution({Variable("Y"): Number(1), Number(5): String("f")})
        ) == ChoiceElement(
            PredLiteral("p", String("str")),
            LiteralCollection(
                PredLiteral("p", Number(0)),
                Naf(PredLiteral("q", Number(-1))),
            ),
        )  # NOTE: substitution is invalid
        # match
        with pytest.raises(Exception):
            element.match(element)

    def test_choice(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", String("str")), Naf(PredLiteral("q"))
                ),
            ),
            ChoiceElement(
                PredLiteral("p", Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )

        # no guards
        ground_choice = Choice(ground_elements, guards=())
        assert ground_choice.lguard is None
        assert ground_choice.rguard is None
        assert ground_choice.guards == (None, None)
        assert str(ground_choice) == '{p(5):p("str"),not q;p(-3):not p("str")}'
        # left guard only
        ground_choice = Choice(
            ground_elements, guards=Guard(RelOp.LESS, Number(3), False)
        )
        assert ground_choice.lguard == Guard(RelOp.LESS, Number(3), False)
        assert ground_choice.rguard is None
        assert ground_choice.guards == (Guard(RelOp.LESS, Number(3), False), None)
        assert str(ground_choice) == '3 < {p(5):p("str"),not q;p(-3):not p("str")}'
        # right guard only
        ground_choice = Choice(ground_elements, Guard(RelOp.LESS, Number(3), True))
        assert ground_choice.lguard is None
        assert ground_choice.rguard == Guard(RelOp.LESS, Number(3), True)
        assert ground_choice.guards == (None, Guard(RelOp.LESS, Number(3), True))
        assert str(ground_choice) == '{p(5):p("str"),not q;p(-3):not p("str")} < 3'
        # both guards
        ground_choice = Choice(
            ground_elements,
            guards=(
                Guard(RelOp.LESS, Number(3), False),
                Guard(RelOp.LESS, Number(3), True),
            ),
        )
        assert ground_choice.lguard == Guard(RelOp.LESS, Number(3), False)
        assert ground_choice.rguard == Guard(RelOp.LESS, Number(3), True)
        assert ground_choice.guards == (
            Guard(RelOp.LESS, Number(3), False),
            Guard(RelOp.LESS, Number(3), True),
        )
        assert str(ground_choice) == '3 < {p(5):p("str"),not q;p(-3):not p("str")} < 3'

        var_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", Variable("X")), Naf(PredLiteral("q"))
                ),
            ),
            ChoiceElement(
                PredLiteral("p", Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        var_choice = Choice(
            var_elements, guards=Guard(RelOp.LESS, Variable("Y"), False)
        )

        # equality
        assert ground_choice == Choice(
            ground_elements,
            guards=(
                Guard(RelOp.LESS, Number(3), False),
                Guard(RelOp.LESS, Number(3), True),
            ),
        )
        # hashing
        assert hash(ground_choice) == hash(
            Choice(
                ground_elements,
                guards=(
                    Guard(RelOp.LESS, Number(3), False),
                    Guard(RelOp.LESS, Number(3), True),
                ),
            )
        )
        # head
        assert ground_choice.head == LiteralCollection(
            PredLiteral("p", Number(5)),
            PredLiteral("p", Number(-3)),
        )
        # body
        assert ground_choice.body == LiteralCollection(
            PredLiteral("p", String("str")),
            Naf(PredLiteral("q")),
            Naf(PredLiteral("p", String("str"))),
        )
        # ground
        assert ground_choice.ground
        assert not var_choice.ground
        # variables
        assert (
            ground_choice.invars()
            == ground_choice.outvars()
            == ground_choice.vars()
            == ground_choice.global_vars(DummyRule({Variable("Y")}))
            == set()
        )
        assert var_choice.invars() == {Variable("X")}
        assert var_choice.outvars() == {Variable("Y")}
        assert var_choice.vars() == {Variable("X"), Variable("Y")}
        assert var_choice.global_vars(DummyRule({Variable("Y")})) == {Variable("Y")}
        # assert Eq var_choice.global_vars(), {Variable("X"), Variable("Y")})
        # positive/negative literal occurrences
        assert var_choice.pos_occ() == LiteralCollection(
            PredLiteral("p", Number(5)),
            PredLiteral("p", Number(-3)),
            PredLiteral("p", Variable("X")),
        )
        assert var_choice.neg_occ() == LiteralCollection(
            PredLiteral("p", String("str")), PredLiteral("q")
        )
        # evaluation
        assert Choice.eval(
            ground_elements,
            # satisfiable lower bound
            guards=(Guard(RelOp.LESS, Number(1), False), None),
        )
        assert not Choice.eval(
            ground_elements,
            # unsatisfiable lower bound
            guards=(Guard(RelOp.LESS, Number(2), False), None),
        )
        assert Choice.eval(
            ground_elements,
            # satisfiable lower bound
            guards=(Guard(RelOp.LESS_OR_EQ, Number(2), False), None),
        )
        assert not Choice.eval(
            ground_elements,
            # unsatisfiable lower bound
            guards=(Guard(RelOp.LESS_OR_EQ, Number(3), False), None),
        )
        assert Choice.eval(
            ground_elements,
            # satisfiable upper bound
            guards=(Guard(RelOp.GREATER, Number(1), False), None),
        )
        assert not Choice.eval(
            ground_elements,
            # unsatisfiable upper bound
            guards=(Guard(RelOp.GREATER, Number(0), False), None),
        )
        assert Choice.eval(
            ground_elements,
            # satisfiable upper bound
            guards=(Guard(RelOp.GREATER_OR_EQ, Number(0), False), None),
        )
        assert not Choice.eval(
            ground_elements,
            # unsatisfiable upper bound
            guards=(Guard(RelOp.GREATER_OR_EQ, Number(-1), False), None),
        )
        assert Choice.eval(
            ground_elements,
            # satisfiable equality bound
            guards=(Guard(RelOp.EQUAL, Number(2), False), None),
        )
        assert not Choice.eval(
            ground_elements,
            # unsatisfiable equality bound
            guards=(Guard(RelOp.EQUAL, Number(-1), False), None),
        )
        assert not Choice.eval(
            ground_elements,
            # unsatisfiable equality bound
            guards=(Guard(RelOp.EQUAL, Number(3), False), None),
        )
        assert Choice.eval(
            # no elements
            tuple(),
            # satisfiable unequality bound
            guards=(Guard(RelOp.UNEQUAL, Number(-1), False), None),
        )
        assert not Choice.eval(
            # no elements
            tuple(),
            # unsatisfiable unequality bound
            guards=(Guard(RelOp.UNEQUAL, Number(0), False), None),
        )
        assert Choice.eval(
            ground_elements,
            # satisfiable unequality bound
            guards=(Guard(RelOp.UNEQUAL, Number(-1), False), None),
        )
        assert Choice.eval(
            ground_elements,
            # satisfiable unequality bound
            guards=(Guard(RelOp.UNEQUAL, Number(0), False), None),
        )
        # TODO: test evaluation with two guards

        # safety characterization
        with pytest.raises(Exception):
            var_choice.safety()
        # replace arithmetic terms
        arith_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", Minus(Variable("X"))),
                    Naf(PredLiteral("q")),
                ),
            ),
        )
        choice = Choice(
            arith_elements,
            Guard(RelOp.EQUAL, Minus(Variable("X")), True),
        )
        assert choice.replace_arith(VariableTable()) == Choice(
            (
                ChoiceElement(
                    PredLiteral("p", Number(5)),
                    LiteralCollection(
                        PredLiteral("p", ArithVariable(0, Minus(Variable("X")))),
                        Naf(PredLiteral("q")),
                    ),
                ),
            ),
            Guard(RelOp.EQUAL, ArithVariable(1, Minus(Variable("X"))), True),
        )

        # substitute
        var_choice = Choice(var_elements, Guard(RelOp.LESS, Variable("X"), False))
        assert var_choice.substitute(
            Substitution({Variable("X"): Number(1), Number(-3): String("f")})
        ) == Choice(
            (
                ChoiceElement(
                    PredLiteral("p", Number(5)),
                    LiteralCollection(
                        PredLiteral("p", Number(1)), Naf(PredLiteral("q"))
                    ),
                ),
                ChoiceElement(
                    PredLiteral("p", Number(-3)),
                    LiteralCollection(Naf(PredLiteral("p", String("str")))),
                ),
            ),
            guards=Guard(RelOp.LESS, Number(1), False),
        )  # NOTE: substitution is invalid

    def test_choice_fact(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", String("str")), Naf(PredLiteral("q"))
                ),
            ),
            ChoiceElement(
                PredLiteral("p", Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        ground_choice = Choice(
            ground_elements,
            guards=Guard(RelOp.LESS, Number(3), False),
        )
        ground_rule = ChoiceRule(ground_choice)

        var_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", Variable("X")), Naf(PredLiteral("q"))
                ),
            ),
            ChoiceElement(
                PredLiteral("p", Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        var_choice = Choice(
            var_elements, guards=Guard(RelOp.LESS, Variable("Y"), False)
        )
        var_rule = ChoiceRule(var_choice)

        # string representation
        assert str(ground_rule) == '3 < {p(5):p("str"),not q;p(-3):not p("str")}.'
        assert str(var_rule) == 'Y < {p(5):p(X),not q;p(-3):not p("str")}.'
        # equality
        assert ground_rule.choice == Choice(
            ground_elements,
            guards=Guard(RelOp.LESS, Number(3), False),
        )  # TODO: head
        assert ground_rule.body == LiteralCollection()
        assert var_rule.choice == Choice(
            var_elements, guards=Guard(RelOp.LESS, Variable("Y"), False)
        )  # TODO: head
        assert var_rule.body == LiteralCollection()
        # hashing
        assert hash(ground_rule) == hash(
            ChoiceRule(
                Choice(
                    ground_elements,
                    guards=Guard(RelOp.LESS, Number(3), False),
                ),
            )
        )
        assert hash(var_rule) == hash(
            ChoiceRule(
                Choice(var_elements, guards=Guard(RelOp.LESS, Variable("Y"), False)),
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
        assert var_rule.vars() == {Variable("X"), Variable("Y")}
        # TODO:
        # assert
        #    var_rule.vars() == var_rule.global_vars() == {Variable("X"), Variable("Y")}
        # )
        assert var_rule.global_vars() == {Variable("Y")}
        # replace arithmetic terms
        arith_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", Minus(Variable("X"))),
                    Naf(PredLiteral("q")),
                ),
            ),
        )
        rule = ChoiceRule(
            Choice(
                arith_elements,
                Guard(RelOp.EQUAL, Minus(Variable("X")), True),
            ),
        )
        assert rule.replace_arith() == ChoiceRule(
            Choice(
                (
                    ChoiceElement(
                        PredLiteral("p", Number(5)),
                        LiteralCollection(
                            PredLiteral("p", ArithVariable(0, Minus(Variable("X")))),
                            Naf(PredLiteral("q")),
                        ),
                    ),
                ),
                Guard(RelOp.EQUAL, ArithVariable(1, Minus(Variable("X"))), True),
            ),
        )

        # substitution
        rule = ChoiceRule(Choice(var_elements, Guard(RelOp.LESS, Variable("X"), False)))
        assert rule.substitute(
            Substitution({Variable("X"): Number(1), Number(-3): String("f")})
        ) == ChoiceRule(
            Choice(
                (
                    ChoiceElement(
                        PredLiteral("p", Number(5)),
                        LiteralCollection(
                            PredLiteral("p", Number(1)),
                            Naf(PredLiteral("q")),
                        ),
                    ),
                    ChoiceElement(
                        PredLiteral("p", Number(-3)),
                        LiteralCollection(Naf(PredLiteral("p", String("str")))),
                    ),
                ),
                guards=Guard(RelOp.LESS, Number(1), False),
            ),
        )  # NOTE: substitution is invalid

        # rewrite aggregates
        assert rule == rule.rewrite_aggregates(0, dict())

        # assembling
        assert rule == rule.assemble_aggregates(dict())

        # rewrite choice
        elements = (
            ChoiceElement(
                PredLiteral("p", Variable("X")),
                LiteralCollection(PredLiteral("q", Variable("X"))),
            ),
            ChoiceElement(
                PredLiteral("p", Number(1)),
                LiteralCollection(PredLiteral("p", Number(0))),
            ),
        )
        rule = ChoiceRule(
            Choice(
                elements,
                Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            ),
        )
        target_rule = NormalRule(
            ChoicePlaceholder(
                1,
                TermTuple(),
                TermTuple(),
            ),
        )
        choice_map = dict()
        assert rule.rewrite_choices(1, choice_map) == target_rule
        assert len(choice_map) == 1

        choice, chi_literal, eps_rule, eta_rules = choice_map[1]
        assert choice == rule.head

        assert chi_literal == target_rule.atom
        assert eps_rule == ChoiceBaseRule(
            ChoiceBaseLiteral(
                1,
                TermTuple(),
                TermTuple(),
            ),
            Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            None,
            LiteralCollection(
                GreaterEqual(Number(-1), Number(0)),
            ),
        )

        assert len(eta_rules) == 2
        # """
        assert eta_rules[0] == ChoiceElemRule(
            ChoiceElemLiteral(
                1,
                0,
                TermTuple(Variable("X")),
                TermTuple(),
                TermTuple(Variable("X")),
            ),
            elements[0],
            LiteralCollection(
                PredLiteral("q", Variable("X")),
            ),
        )
        assert eta_rules[1] == ChoiceElemRule(
            ChoiceElemLiteral(
                1,
                1,
                TermTuple(),
                TermTuple(),
                TermTuple(),
            ),
            elements[1],
            LiteralCollection(
                PredLiteral("p", Number(0)),
            ),
        )

        # assembling choice
        assert target_rule.assemble_choices(
            {
                ChoicePlaceholder(
                    1,
                    TermTuple(),
                    TermTuple(),
                ): Choice(
                    (
                        ChoiceElement(
                            PredLiteral("p", Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                        ChoiceElement(
                            PredLiteral("p", Number(1)),
                            LiteralCollection(PredLiteral("p", Number(0))),
                        ),
                    ),
                    Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
                ),
            },
        ) == ChoiceRule(
            Choice(
                (
                    ChoiceElement(
                        PredLiteral("p", Number(0)),
                        LiteralCollection(PredLiteral("q", Number(0))),
                    ),
                    ChoiceElement(
                        PredLiteral("p", Number(1)),
                        LiteralCollection(PredLiteral("p", Number(0))),
                    ),
                ),
                Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            ),
        )  # choice is satisfiable

        assert (
            target_rule.assemble_choices(
                dict(),
            )
            == Constraint()
        )  # choice is unsatisfiable (yields constraint)

    def test_choice_rule(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", String("str")), Naf(PredLiteral("q"))
                ),
            ),
            ChoiceElement(
                PredLiteral("p", Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        ground_choice = Choice(
            ground_elements,
            guards=Guard(RelOp.LESS, Number(3), False),
        )
        ground_rule = ChoiceRule(ground_choice, (PredLiteral("q", Number(1)),))

        var_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", Variable("X")), Naf(PredLiteral("q"))
                ),
            ),
            ChoiceElement(
                PredLiteral("p", Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        var_choice = Choice(
            var_elements, guards=Guard(RelOp.LESS, Variable("Y"), False)
        )
        safe_var_rule = ChoiceRule(
            var_choice,
            (
                PredLiteral("q", Variable("X")),
                PredLiteral("q", Variable("Y")),
            ),
        )
        unsafe_var_rule = ChoiceRule(var_choice, (PredLiteral("q", Variable("X")),))

        # string representation
        assert (
            str(ground_rule) == '3 < {p(5):p("str"),not q;p(-3):not p("str")} :- q(1).'
        )
        assert (
            str(safe_var_rule)
            == 'Y < {p(5):p(X),not q;p(-3):not p("str")} :- q(X),q(Y).'
        )
        assert (
            str(unsafe_var_rule) == 'Y < {p(5):p(X),not q;p(-3):not p("str")} :- q(X).'
        )
        # TODO:
        # assert str(unsafe_var_rule) == "p(1) | p(X) :- q.")
        # equality
        assert ground_rule == ChoiceRule(ground_choice, (PredLiteral("q", Number(1)),))
        assert safe_var_rule == ChoiceRule(
            var_choice,
            (
                PredLiteral("q", Variable("X")),
                PredLiteral("q", Variable("Y")),
            ),
        )
        assert unsafe_var_rule == ChoiceRule(
            var_choice,
            (PredLiteral("q", Variable("X")),),
        )
        assert ground_rule.body == LiteralCollection(PredLiteral("q", Number(1)))
        assert ground_rule.head == Choice(
            ground_elements,
            guards=Guard(RelOp.LESS, Number(3), False),
        )
        assert ground_rule.body == LiteralCollection(PredLiteral("q", Number(1)))
        # hashing
        assert hash(ground_rule) == hash(
            ChoiceRule(ground_choice, (PredLiteral("q", Number(1)),))
        )
        assert hash(unsafe_var_rule) == hash(
            ChoiceRule(
                var_choice,
                (PredLiteral("q", Variable("X")),),
            ),
        )
        assert hash(safe_var_rule) == hash(
            ChoiceRule(
                var_choice,
                (
                    PredLiteral("q", Variable("X")),
                    PredLiteral("q", Variable("Y")),
                ),
            ),
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
        assert ChoiceRule(
            ground_choice,
            (AggrLiteral(AggrCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False)),),
        ).contains_aggregates
        # variables
        assert ground_rule.vars() == ground_rule.global_vars() == set()
        assert unsafe_var_rule.vars() == {Variable("Y"), Variable("X")}
        assert unsafe_var_rule.global_vars() == {Variable("Y"), Variable("X")}
        assert (
            safe_var_rule.vars()
            == safe_var_rule.global_vars()
            == {Variable("X"), Variable("Y")}
        )
        # TODO: replace arithmetic terms

        var_elements = (
            ChoiceElement(
                PredLiteral("p", Number(5)),
                LiteralCollection(
                    PredLiteral("p", Variable("X")), Naf(PredLiteral("q"))
                ),
            ),
            ChoiceElement(
                PredLiteral("p", Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        var_choice = Choice(
            var_elements, guards=Guard(RelOp.LESS, Variable("Y"), False)
        )
        safe_var_rule = ChoiceRule(
            var_choice,
            (
                PredLiteral("q", Variable("X")),
                PredLiteral("q", Variable("Y")),
            ),
        )

        # substitution
        assert safe_var_rule.substitute(
            Substitution({Variable("X"): Number(1), Variable("Y"): String("f")})
        ) == ChoiceRule(
            Choice(
                (
                    ChoiceElement(
                        PredLiteral("p", Number(5)),
                        LiteralCollection(
                            PredLiteral("p", Number(1)),
                            Naf(PredLiteral("q")),
                        ),
                    ),
                    ChoiceElement(
                        PredLiteral("p", Number(-3)),
                        LiteralCollection(Naf(PredLiteral("p", String("str")))),
                    ),
                ),
                guards=Guard(RelOp.LESS, String("f"), False),
            ),
            (PredLiteral("q", Number(1)), PredLiteral("q", String("f"))),
        )

        # rewrite choice
        elements = (
            ChoiceElement(
                PredLiteral("p", Variable("X")),
                LiteralCollection(PredLiteral("q", Variable("X"))),
            ),
            ChoiceElement(
                PredLiteral("p", Number(1)),
                LiteralCollection(PredLiteral("p", Number(0))),
            ),
        )
        rule = ChoiceRule(
            Choice(
                elements,
                Guard(RelOp.GREATER_OR_EQ, Variable("Y"), False),
            ),
            (
                PredLiteral("q", Variable("Y")),
                Equal(Number(0), Variable("X")),
            ),
        )
        target_rule = NormalRule(
            ChoicePlaceholder(
                1,
                TermTuple(Variable("X"), Variable("Y")),
                TermTuple(Variable("X"), Variable("Y")),
            ),
            [PredLiteral("q", Variable("Y")), Equal(Number(0), Variable("X"))],
        )
        choice_map = dict()

        assert rule.rewrite_choices(1, choice_map) == target_rule
        assert len(choice_map) == 1

        choice, chi_literal, eps_rule, eta_rules = choice_map[1]
        assert choice == rule.head

        assert chi_literal == target_rule.atom
        assert eps_rule == ChoiceBaseRule(
            ChoiceBaseLiteral(
                1,
                TermTuple(Variable("X"), Variable("Y")),
                TermTuple(Variable("X"), Variable("Y")),
            ),
            Guard(RelOp.GREATER_OR_EQ, Variable("Y"), False),
            None,
            LiteralCollection(
                GreaterEqual(Variable("Y"), Number(0)),
                PredLiteral("q", Variable("Y")),
                Equal(Number(0), Variable("X")),
            ),
        )

        assert len(eta_rules) == 2
        assert eta_rules[0] == ChoiceElemRule(
            ChoiceElemLiteral(
                1,
                0,
                TermTuple(),
                TermTuple(Variable("X"), Variable("Y")),
                TermTuple(Variable("X"), Variable("Y")),
            ),
            elements[0],
            LiteralCollection(
                PredLiteral("q", Variable("X")),
                PredLiteral("q", Variable("Y")),
                Equal(Number(0), Variable("X")),
            ),
        )
        assert eta_rules[1] == ChoiceElemRule(
            ChoiceElemLiteral(
                1,
                1,
                TermTuple(),
                TermTuple(Variable("X"), Variable("Y")),
                TermTuple(Variable("X"), Variable("Y")),
            ),
            elements[1],
            LiteralCollection(
                PredLiteral("p", Number(0)),
                PredLiteral("q", Variable("Y")),
                Equal(Number(0), Variable("X")),
            ),
        )

        # assembling choice
        assert target_rule.assemble_choices(
            {
                ChoicePlaceholder(
                    1,
                    TermTuple(Variable("X"), Variable("Y")),
                    TermTuple(Variable("X"), Variable("Y")),
                ): Choice(
                    (
                        ChoiceElement(
                            PredLiteral("p", Number(0)),
                            LiteralCollection(PredLiteral("q", Number(0))),
                        ),
                        ChoiceElement(
                            PredLiteral("p", Number(1)),
                            LiteralCollection(PredLiteral("p", Number(0))),
                        ),
                    ),
                    Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
                ),
            },
        ) == ChoiceRule(
            Choice(
                (
                    ChoiceElement(
                        PredLiteral("p", Number(0)),
                        LiteralCollection(PredLiteral("q", Number(0))),
                    ),
                    ChoiceElement(
                        PredLiteral("p", Number(1)),
                        LiteralCollection(PredLiteral("p", Number(0))),
                    ),
                ),
                Guard(RelOp.GREATER_OR_EQ, Number(-1), False),
            ),
            (
                PredLiteral("q", Variable("Y")),
                Equal(Number(0), Variable("X")),
            ),
        )  # choice is satisfiable

        assert target_rule.assemble_choices(
            dict(),
        ) == Constraint(
            PredLiteral("q", Variable("Y")),
            Equal(Number(0), Variable("X")),
        )  # choice is unsatisfiable (yields constraint)

        # TODO: propagate
