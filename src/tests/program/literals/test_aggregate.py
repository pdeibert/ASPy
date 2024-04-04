from typing import Self, Set

import pytest  # type: ignore

import aspy
from aspy.program.literals import (
    AggrCount,
    AggrElement,
    AggrLiteral,
    AggrMax,
    AggrMin,
    AggrSum,
    Guard,
    LiteralCollection,
    Naf,
    PredLiteral,
)
from aspy.program.operators import RelOp
from aspy.program.safety_characterization import SafetyRule, SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.terms import (
    ArithVariable,
    Infimum,
    Minus,
    Number,
    String,
    Supremum,
    TermTuple,
    Variable,
)
from aspy.program.variable_table import VariableTable


class DummyRule:
    def __init__(self: Self, vars: Set["Variable"]) -> None:
        self.vars = vars

    def global_vars(self: Self) -> Set["Variable"]:
        return self.vars


class TestAggregate:
    def test_aggregate_element(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        element = AggrElement(
            TermTuple(Number(5), Variable("X")),
            LiteralCollection(
                PredLiteral("p", String("str")),
                Naf(PredLiteral("q", Variable("Y"))),
            ),
        )
        # string representation
        assert str(element) == '5,X:p("str"),not q(Y)'
        # equality
        assert element == AggrElement(
            TermTuple(Number(5), Variable("X")),
            LiteralCollection(
                PredLiteral("p", String("str")),
                Naf(PredLiteral("q", Variable("Y"))),
            ),
        )
        # head
        assert element.head == TermTuple(Number(5), Variable("X"))
        # body
        assert element.body == LiteralCollection(
            PredLiteral("p", String("str")),
            Naf(PredLiteral("q", Variable("Y"))),
        )
        # hashing
        assert hash(element) == hash(
            AggrElement(
                TermTuple(Number(5), Variable("X")),
                LiteralCollection(
                    PredLiteral("p", String("str")),
                    Naf(PredLiteral("q", Variable("Y"))),
                ),
            )
        )
        # ground
        assert not element.ground
        # positive/negative literal occurrences
        assert element.pos_occ() == LiteralCollection(PredLiteral("p", String("str")))
        assert element.neg_occ() == LiteralCollection(PredLiteral("q", Variable("Y")))
        # weight
        assert element.weight == 5
        assert AggrElement(TermTuple(Variable("X"), Number(5))).weight == 0
        # vars
        assert element.vars() == element.global_vars() == {Variable("X"), Variable("Y")}
        # safety
        with pytest.raises(ValueError):
            element.safety()
        # replace arithmetic terms
        assert element.replace_arith(VariableTable()) == element
        element = AggrElement(
            TermTuple(Number(5), Minus(Variable("X"))),
            LiteralCollection(
                PredLiteral("p", String("str")),
                Naf(PredLiteral("q", Variable("Y"))),
            ),
        )
        assert element.replace_arith(VariableTable()) == AggrElement(
            TermTuple(Number(5), ArithVariable(0, Minus(Variable("X")))),
            LiteralCollection(
                PredLiteral("p", String("str")),
                Naf(PredLiteral("q", Variable("Y"))),
            ),
        )

        # substitute
        assert element.substitute(
            Substitution({Variable("X"): Number(1), Number(5): String("f")})
        ) == AggrElement(
            TermTuple(Number(5), Number(-1)),
            LiteralCollection(
                PredLiteral("p", String("str")),
                Naf(PredLiteral("q", Variable("Y"))),
            ),
        )  # NOTE: substitution is invalid
        # match
        with pytest.raises(Exception):
            element.match(element)

    def test_aggregate_count(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        aggr_func = AggrCount()
        # equality
        assert aggr_func == AggrCount()
        # hashing
        assert hash(aggr_func) == hash(AggrCount())
        # string representation
        assert str(aggr_func) == "#count"
        # base value
        assert aggr_func.base == Number(0)
        # evaluation
        assert aggr_func.eval({TermTuple(Number(5)), TermTuple(Number(-3))}) == Number(
            2
        )

        # ----- propagation -----
        element_instances = {
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("p", Number(0)))
            ),
            AggrElement(
                TermTuple(Number(1)),
                LiteralCollection(PredLiteral("p", Number(1))),
            ),
        }

        # >, >=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            A,
            B,
        )
        assert aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            B,
            A,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None), element_instances, B, A
        )

        # <, <=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            A,
            B,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            B,
            A,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None), element_instances, B, A
        )

        # =
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None), element_instances, B, A
        )

        # !=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None), element_instances, B, A
        )

        # TODO: two different guards at a time
        # TODO: special cases?

    def test_aggregate_sum(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        aggr_func = AggrSum()
        # equality
        assert aggr_func == AggrSum()
        # hashing
        assert hash(aggr_func) == hash(AggrSum())
        # string representation
        assert str(aggr_func) == "#sum"
        # base value
        assert aggr_func.base == Number(0)
        # evaluation
        assert aggr_func.eval({TermTuple(Number(5)), TermTuple(Number(-3))}) == Number(
            2
        )

        # ----- propagation -----
        element_instances = {
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("p", Number(0)))
            ),
            AggrElement(
                TermTuple(Number(1)),
                LiteralCollection(PredLiteral("p", Number(1))),
            ),
        }

        # >, >=
        # TODO: correct ???
        literals_I = {PredLiteral("p", Number(0))}
        literals_J = {
            PredLiteral("p", Number(0)),
            PredLiteral("p", Number(1)),
        }
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            literals_I,
            literals_J,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None),
            element_instances,
            literals_I,
            literals_J,
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            literals_J,
            literals_I,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None),
            element_instances,
            literals_J,
            literals_I,
        )

        # <, <=
        # TODO: correct ???
        literals_I = {PredLiteral("p", Number(0))}
        literals_J = {
            PredLiteral("p", Number(0)),
            PredLiteral("p", Number(1)),
        }
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            literals_I,
            literals_J,
        )
        assert aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None),
            element_instances,
            literals_I,
            literals_J,
        )
        # J subset I
        assert aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            literals_J,
            literals_I,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None),
            element_instances,
            literals_J,
            literals_I,
        )

        # =
        # TODO: correct ???
        literals_I = {PredLiteral("p", Number(0))}
        literals_J = {
            PredLiteral("p", Number(0)),
            PredLiteral("p", Number(1)),
        }
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None),
            element_instances,
            literals_I,
            literals_J,
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None),
            element_instances,
            literals_J,
            literals_I,
        )

        # !=
        # TODO: correct ???
        literals_I = {PredLiteral("p", Number(0))}
        literals_J = {
            PredLiteral("p", Number(0)),
            PredLiteral("p", Number(1)),
        }
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None),
            element_instances,
            literals_I,
            literals_J,
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None),
            element_instances,
            literals_J,
            literals_I,
        )

        # TODO: two different guards at a time
        # TODO: special cases?

    def test_aggregate_max(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        aggr_func = AggrMax()
        # equality
        assert aggr_func == AggrMax()
        # hashing
        assert hash(aggr_func) == hash(AggrMax())
        # string representation
        assert str(aggr_func) == "#max"
        # base value
        assert aggr_func.base == Infimum()
        # evaluation
        assert aggr_func.eval({TermTuple(Number(5)), TermTuple(Number(-3))}) == Number(
            5
        )

        # ----- propagation -----
        element_instances = {
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("p", Number(0)))
            ),
            AggrElement(
                TermTuple(Number(1)),
                LiteralCollection(PredLiteral("p", Number(1))),
            ),
        }

        # >, >=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            A,
            B,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            B,
            A,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None), element_instances, B, A
        )

        # <, <=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            A,
            B,
        )
        assert aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            B,
            A,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None), element_instances, B, A
        )

        # =
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None), element_instances, B, A
        )

        # !=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None), element_instances, B, A
        )

        # TODO: two different guards at a time
        # TODO: special cases?

    def test_aggregate_min(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        aggr_func = AggrMin()
        # equality
        assert aggr_func == AggrMin()
        # hashing
        assert hash(aggr_func) == hash(AggrMin())
        # string representation
        assert str(aggr_func) == "#min"
        # base value
        assert aggr_func.base == Supremum()
        # evaluation
        assert aggr_func.eval({TermTuple(Number(5)), TermTuple(Number(-3))}) == Number(
            -3
        )

        # ----- propagation -----
        element_instances = {
            AggrElement(
                TermTuple(Number(0)), LiteralCollection(PredLiteral("p", Number(0)))
            ),
            AggrElement(
                TermTuple(Number(1)),
                LiteralCollection(PredLiteral("p", Number(1))),
            ),
        }

        # >, >=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            A,
            B,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER_OR_EQ, Number(1), True), None),
            element_instances,
            B,
            A,
        )
        assert not aggr_func.propagate(
            (Guard(RelOp.GREATER, Number(1), True), None), element_instances, B, A
        )

        # <, <=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            A,
            B,
        )
        assert aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert aggr_func.propagate(
            (Guard(RelOp.LESS_OR_EQ, Number(1), True), None),
            element_instances,
            B,
            A,
        )
        assert aggr_func.propagate(
            (Guard(RelOp.LESS, Number(1), True), None), element_instances, B, A
        )

        # =
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert not aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert not aggr_func.propagate(
            (Guard(RelOp.EQUAL, Number(1), True), None), element_instances, B, A
        )

        # !=
        # TODO: correct ???
        A = {PredLiteral("p", Number(0))}
        B = {PredLiteral("p", Number(0)), PredLiteral("p", Number(1))}
        # I subset J
        assert aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None), element_instances, A, B
        )
        # J subset I
        assert aggr_func.propagate(
            (Guard(RelOp.UNEQUAL, Number(1), True), None), element_instances, B, A
        )

        # TODO: two different guards at a time
        # TODO: special cases?

    def test_aggregate_literal(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        ground_elements = (
            AggrElement(
                TermTuple(Number(5)),
                LiteralCollection(
                    PredLiteral("p", String("str")), Naf(PredLiteral("q"))
                ),
            ),
            AggrElement(
                TermTuple(Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        aggr_func = AggrCount()

        # no guards
        with pytest.raises(ValueError):
            AggrLiteral(aggr_func, ground_elements, tuple())
        # left guard only
        ground_literal = AggrLiteral(
            aggr_func, ground_elements, guards=Guard(RelOp.LESS, Number(3), False)
        )
        assert ground_literal.lguard == Guard(RelOp.LESS, Number(3), False)
        assert ground_literal.rguard is None
        assert ground_literal.guards, (Guard(RelOp.LESS, Number(3), False), None)
        assert not ground_literal.eval()
        assert str(ground_literal) == '3 < #count{5:p("str"),not q;-3:not p("str")}'
        # right guard only
        ground_literal = AggrLiteral(
            aggr_func, ground_elements, Guard(RelOp.LESS, Number(3), True), naf=True
        )
        assert ground_literal.lguard is None
        assert ground_literal.rguard == Guard(RelOp.LESS, Number(3), True)
        assert ground_literal.guards == (None, Guard(RelOp.LESS, Number(3), True))
        assert ground_literal.eval()
        assert str(ground_literal) == 'not #count{5:p("str"),not q;-3:not p("str")} < 3'
        # both guards
        ground_literal = AggrLiteral(
            aggr_func,
            ground_elements,
            guards=(
                Guard(RelOp.LESS, Number(3), False),
                Guard(RelOp.LESS, Number(3), True),
            ),
        )
        assert ground_literal.lguard == Guard(RelOp.LESS, Number(3), False)
        assert ground_literal.rguard == Guard(RelOp.LESS, Number(3), True)
        assert ground_literal.guards == (
            Guard(RelOp.LESS, Number(3), False),
            Guard(RelOp.LESS, Number(3), True),
        )
        assert not ground_literal.eval()
        assert str(ground_literal) == '3 < #count{5:p("str"),not q;-3:not p("str")} < 3'

        var_elements = (
            AggrElement(
                TermTuple(Number(5)),
                LiteralCollection(
                    PredLiteral("p", Variable("X")), Naf(PredLiteral("q"))
                ),
            ),
            AggrElement(
                TermTuple(Number(-3)),
                LiteralCollection(Naf(PredLiteral("p", String("str")))),
            ),
        )
        var_literal = AggrLiteral(
            aggr_func, var_elements, guards=Guard(RelOp.LESS, Variable("Y"), False)
        )

        # equality
        assert ground_literal == AggrLiteral(
            aggr_func,
            ground_elements,
            guards=(
                Guard(RelOp.LESS, Number(3), False),
                Guard(RelOp.LESS, Number(3), True),
            ),
        )
        # hashing
        assert hash(ground_literal) == hash(
            AggrLiteral(
                aggr_func,
                ground_elements,
                guards=(
                    Guard(RelOp.LESS, Number(3), False),
                    Guard(RelOp.LESS, Number(3), True),
                ),
            )
        )
        # ground
        assert ground_literal.ground
        assert not var_literal.ground
        # negation
        assert not ground_literal.naf
        ground_literal.set_naf()
        assert ground_literal.naf
        ground_literal.set_naf(False)
        assert not ground_literal.naf
        ground_literal.set_naf(True)
        assert ground_literal.naf
        # variables
        assert (
            ground_literal.invars()
            == ground_literal.outvars()
            == ground_literal.vars()
            == ground_literal.global_vars()
            == set()
        )
        assert var_literal.invars() == {Variable("X")}
        assert var_literal.outvars() == {Variable("Y")}
        assert var_literal.vars() == {Variable("X"), Variable("Y")}
        assert var_literal.global_vars() == {Variable("Y")}
        # positive/negative literal occurrences
        assert var_literal.pos_occ() == LiteralCollection(
            PredLiteral("p", Variable("X"))
        )
        assert var_literal.neg_occ() == LiteralCollection(
            PredLiteral("p", String("str")), PredLiteral("q")
        )

        # safety characterization
        assert var_literal.safety(DummyRule({Variable("X")})) == SafetyTriplet(
            unsafe={Variable("X")}
        )
        assert var_literal.safety(DummyRule({Variable("Y")})) == SafetyTriplet()
        assert AggrLiteral(
            aggr_func, var_elements, Guard(RelOp.LESS, Variable("X"), False)
        ).safety(DummyRule({Variable("X")})) == SafetyTriplet(unsafe={Variable("X")})
        assert (
            AggrLiteral(
                aggr_func, var_elements, Guard(RelOp.LESS, Variable("X"), False)
            ).safety(DummyRule({Variable("Y")}))
            == SafetyTriplet()
        )
        # aggr_global_invars = {'X'}
        # aggr_global_vars = {'X','Y'} -> unsafe
        # rules = { ('Y', {'X'}) }
        assert AggrLiteral(
            aggr_func, var_elements, guards=Guard(RelOp.EQUAL, Variable("Y"), False)
        ).safety(DummyRule({Variable("X"), Variable("Y")})) == SafetyTriplet(
            unsafe={Variable("X"), Variable("Y")},
            rules={SafetyRule(Variable("Y"), {Variable("X")})},
        )
        # aggr_global_invars = {}
        # aggr_global_vars = {'Y'} -> unsafe
        # rules = { ('Y', {}) } -> makes 'Y' safe
        assert AggrLiteral(
            aggr_func, var_elements, guards=Guard(RelOp.EQUAL, Variable("Y"), False)
        ).safety(DummyRule({Variable("Y")})) == SafetyTriplet(safe={Variable("Y")})
        # aggr_global_invars = {'X'}
        # aggr_global_vars = {'X'} -> unsafe
        # rules = { ('X', {'X'}) } -> removes (without making 'X' safe)
        assert AggrLiteral(
            aggr_func, var_elements, guards=Guard(RelOp.EQUAL, Variable("X"), False)
        ).safety(DummyRule({Variable("X")})) == SafetyTriplet(unsafe={Variable("X")})
        # aggr_global_invars = {}
        # aggr_global_vars = {'X'} -> unsafe
        # rules = { ('X', {}) } -> makes 'X' safe
        assert AggrLiteral(
            aggr_func, var_elements, guards=Guard(RelOp.EQUAL, Variable("X"), False)
        ).safety(DummyRule({Variable("Y")})) == SafetyTriplet(safe={Variable("X")})
        # TODO: safety characterization for case with two guards

        # replace arithmetic terms
        arith_elements = (
            AggrElement(
                TermTuple(Number(5)),
                LiteralCollection(
                    PredLiteral("p", Minus(Variable("X"))),
                    Naf(PredLiteral("q")),
                ),
            ),
        )
        arith_literal = Naf(
            AggrLiteral(
                aggr_func,
                arith_elements,
                Guard(RelOp.EQUAL, Minus(Variable("X")), True),
            )
        )
        assert arith_literal.replace_arith(VariableTable()) == Naf(
            AggrLiteral(
                aggr_func,
                (
                    AggrElement(
                        TermTuple(Number(5)),
                        LiteralCollection(
                            PredLiteral("p", ArithVariable(0, Minus(Variable("X")))),
                            Naf(PredLiteral("q")),
                        ),
                    ),
                ),
                Guard(RelOp.EQUAL, ArithVariable(1, Minus(Variable("X"))), True),
            )
        )

        # substitute
        var_literal = AggrLiteral(
            aggr_func, var_elements, Guard(RelOp.LESS, Variable("X"), False)
        )
        assert var_literal.substitute(
            Substitution({Variable("X"): Number(1), Number(-3): String("f")})
        ) == AggrLiteral(
            AggrCount(),
            (
                AggrElement(
                    TermTuple(Number(5)),
                    LiteralCollection(
                        PredLiteral("p", Number(1)), Naf(PredLiteral("q"))
                    ),
                ),
                AggrElement(
                    TermTuple(Number(-3)),
                    LiteralCollection(Naf(PredLiteral("p", String("str")))),
                ),
            ),
            guards=Guard(RelOp.LESS, Number(1), False),
        )  # NOTE: substitution is invalid
