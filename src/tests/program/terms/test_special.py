from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.substitution import Substitution
from aspy.program.symbols import SpecialChar
from aspy.program.terms import Add, ArithVariable, Minus, Number, Variable


class TestSpecial:
    def test_arith_variable(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # invalid initialization
        with pytest.raises(ValueError):
            ArithVariable(-1, Add(Variable("X"), Number(1)))

        # valid initialization
        var = ArithVariable(0, Add(Variable("X"), Number(1)))
        # equality
        assert var == ArithVariable(0, Add(Variable("X"), Number(1)))
        # hashing
        assert hash(var) == hash(ArithVariable(0, Add(Variable("X"), Number(1))))
        # string representation
        assert str(var) == f"{SpecialChar.TAU.value}0"
        # total order for terms
        with pytest.raises(Exception):
            var.precedes(Number(1))
        # ground
        assert not var.ground

        # substitute
        assert ArithVariable(0, Add(Variable("X"), Number(1))).substitute(
            Substitution(
                {
                    ArithVariable(0, Add(Variable("X"), Number(1))): Number(0),
                    Variable("X"): Number(1),
                }
            )
        ) == Number(
            0
        )  # NOTE: substitution is invalid
        # match
        assert (
            ArithVariable(0, Minus(Variable("X"))).match(
                ArithVariable(0, Minus(Variable("X")))
            )
            == Substitution()
        )
        assert ArithVariable(0, Minus(Variable("X"))).match(Number(1)) == Substitution(
            {ArithVariable(0, Minus(Variable("X"))): Number(1)}
        )

    """ TODO
    def test_replace_arith(self: Self):

        # make sure debug mode is enabled
        assert aspy.debug()

        # ----- terms -----
        for expr in (Infimum(), Supremum(), Variable('X'), AnonVariable(0), Number(10), SymbolicConstant('f'), String('!?$#b'), TermTuple(Number(0), Variable('X'))):
            assert replace_arith(expr, VariableTable()) == expr

        # minus
        assert replace_arith(Minus(Number(1)), VariableTable()) == Minus(Number(1)).simplify() == Number(-1)
        assert replace_arith(Minus(Variable('X')), VariableTable()) == ArithVariable(0, Minus(Variable('X')))
        # add
        assert replace_arith(Add(Number(1), Number(2)), VariableTable()) == Add(Number(1), Number(2)).simplify() == Number(3)
        assert replace_arith(Add(Number(1), Variable('X')), VariableTable()) == ArithVariable(0, Add(Number(1), Variable('X')))
        # sub
        assert replace_arith(Sub(Number(1), Number(2)), VariableTable()) == Sub(Number(1), Number(2)).simplify() == Number(-1)
        assert replace_arith(Sub(Number(1), Variable('X')), VariableTable()) == ArithVariable(0, Sub(Number(1), Variable('X')))
        # mult
        assert replace_arith(Mult(Number(3), Number(2)), VariableTable()) == Mult(Number(3), Number(2)).simplify() == Number(6)
        assert replace_arith(Mult(Number(3), Variable('X')), VariableTable()) == ArithVariable(0, Mult(Number(3), Variable('X')))
        # div
        assert replace_arith(Div(Number(1), Number(2)), VariableTable()) == Div(Number(1), Number(2)).simplify() == Number(0)
        assert replace_arith(Div(Number(1), Variable('X')), VariableTable()) == ArithVariable(0, Div(Number(1), Variable('X')))

        # functional
        assert replace_arith(Functional('f', Minus(Number(1)), String('x'), VariableTable())) == Functional('f', ArithVariable(0, Minus(Number(1))), String('x'))

        # ----- literals -----

        # predicate literals
        assert replace_arith(Naf(Neg(PredLiteral('p', Number(0), Minus(Variable('X'))))), VariableTable()), Naf(Neg(PredLiteral('p', Number(0), ArithVariable(0, Minus(Variable('X'))))))

        # equal
        assert Equal(Number(0), Minus(Variable(('X')))).replace_arith(VariableTable()) == Equal(Number(0), ArithVariable(0, Minus(Variable('X'))))
        # unequal
        assert Unequal(Number(0), Minus(Variable(('X')))).replace_arith(VariableTable()) == Unequal(Number(0), ArithVariable(0, Minus(Variable('X'))))
        # less
        assert Less(Number(0), Minus(Variable(('X')))).replace_arith(VariableTable()) == Less(Number(0), ArithVariable(0, Minus(Variable('X'))))   
        # greater
        assert Greater(Number(0), Minus(Variable(('X')))).replace_arith(VariableTable()) == Greater(Number(0), ArithVariable(0, Minus(Variable('X'))))
        # less than or equal
        assert LessEqual(Number(0), Minus(Variable(('X')))).replace_arith(VariableTable()) == LessEqual(Number(0), ArithVariable(0, Minus(Variable('X'))))  
        # greater than or equal
        assert GreaterEqual(Number(0), Minus(Variable(('X')))).replace_arith(VariableTable()) == GreaterEqual(Number(0), ArithVariable(0, Minus(Variable('X'))))

        # aggregate element
        element = AggrElement(
            TermTuple(Number(5), Minus(Variable('X'))),
            LiteralCollection(PredLiteral('p', String('str')), Naf(PredLiteral('q', Variable('Y'))))
        )
        assert replace_arith(element, VariableTable()) == AggrElement(
                TermTuple(Number(5), ArithVariable(0, Minus(Variable('X')))),
                LiteralCollection(PredLiteral('p', String('str')), Naf(PredLiteral('q', Variable('Y'))))
            )
        # count
        aggregate = AggrCount(AggrElement(TermTuple(Number(5)), LiteralCollection(PredLiteral('p', Minus(Variable('X'))), Naf(PredLiteral('q')))))
        assert replace_arith(aggregate, VariableTable()) == AggrCount(
                AggrElement(
                    TermTuple(Number(5)),
                    LiteralCollection(
                        PredLiteral('p', ArithVariable(0, Minus(Variable('X')))),
                        Naf(PredLiteral('q'))
                    )
                )
            )
        # sum
        aggregate = AggrSum(AggrElement(TermTuple(Number(5)), LiteralCollection(PredLiteral('p', Minus(Variable('X'))), Naf(PredLiteral('q')))))
        assert replace_arith(aggregate, VariableTable()) == AggrSum(
                AggrElement(
                    TermTuple(Number(5)),
                    LiteralCollection(
                        PredLiteral('p', ArithVariable(0, Minus(Variable('X')))),
                        Naf(PredLiteral('q'))
                    )
                )
            )
        # min
        aggregate = AggrMax(AggrElement(TermTuple(Number(5)), LiteralCollection(PredLiteral('p', Minus(Variable('X'))), Naf(PredLiteral('q')))))
        assert replace_arith(aggregate, VariableTable()) == AggrMax(
                AggrElement(
                    TermTuple(Number(5)),
                    LiteralCollection(
                        PredLiteral('p', ArithVariable(0, Minus(Variable('X')))),
                        Naf(PredLiteral('q'))
                    )
                )
            )
        # max
        aggregate = AggrMin(AggrElement(TermTuple(Number(5)), LiteralCollection(PredLiteral('p', Minus(Variable('X'))), Naf(PredLiteral('q')))))
        assert replace_arith(aggregate, VariableTable()) == AggrMin(
                AggrElement(
                    TermTuple(Number(5)),
                    LiteralCollection(
                        PredLiteral('p', ArithVariable(0, Minus(Variable('X')))),
                        Naf(PredLiteral('q'))
                    )
                )
            )
        # guard
        assert replace_arith(Guard(RelOp.EQUAL, Minus(Variable('X')), True)) == Guard(RelOp.EQUAL, ArithVariable(0, Variable('X')), True)
        # aggregate literal
        aggregate = AggrCount(AggrElement(TermTuple(Number(5)), LiteralCollection(PredLiteral('p', Minus(Variable('X'))), Naf(PredLiteral('q')))))
        literal = Naf(AggrLiteral(aggregate, Guard(RelOp.EQUAL, Minus(Variable('X')), True)))
        assert replace_arith(literal, VariableTable()) == Naf(AggrLiteral(
                    AggrCount(
                    AggrElement(
                        TermTuple(Number(5)),
                        LiteralCollection(
                            PredLiteral('p', ArithVariable(0, Minus(Variable('X')))),
                            Naf(PredLiteral('q'))
                        )
                    ),
                    Guard(RelOp.EQUAL, ArithVariable(0, Variable('X')), True)
                )
            ))

        # literal collection
        assert replace_arith(LiteralCollection(PredLiteral('p', Number(0), Variable('X')), PredLiteral('q', Minus(Variable('X')))), VariableTable()), LiteralCollection(PredLiteral('p', Number(0), Variable('X')) == PredLiteral('q', ArithVariable(0, Minus(Variable('Y')))))

        # ----- statements -----
    #"""
