from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.literals import Naf, PredLiteral
from aspy.program.statements import NormalRule
from aspy.program.symbols import SpecialChar
from aspy.program.terms import AnonVariable, ArithVariable, Minus, Variable
from aspy.program.variable_table import VariableTable


class TestVariableTable:
    def test_variable_table(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        statement = NormalRule(
            PredLiteral("p", Variable("X")),
            [
                Naf(PredLiteral("q", AnonVariable(0))),
                PredLiteral("u", AnonVariable(1)),
                PredLiteral("v", Variable("Y")),
                PredLiteral("q", ArithVariable(0, Variable("Z"))),
            ],
        )

        var_table = statement.var_table
        # variables
        assert all(
            var in var_table and var_table[var] == is_global
            for (var, is_global) in [
                (Variable("X"), True),
                (Variable("Y"), True),
                (AnonVariable(0), True),
                (AnonVariable(1), True),
                (ArithVariable(0, Variable("Z")), True),
            ]
        )
        assert (
            var_table.vars()
            == var_table.global_vars()
            == {
                Variable("X"),
                Variable("Y"),
                AnonVariable(0),
                AnonVariable(1),
                ArithVariable(0, Variable("Z")),
            }
        )
        assert var_table.arith_vars() == {ArithVariable(0, Variable("Z"))}
        # counters
        assert var_table.anon_counter == 2
        assert var_table.arith_counter == 1

        # set global
        var_table[Variable("X")] = False
        # string representation
        table_str = str(var_table)
        assert table_str.startswith("{")
        assert table_str.endswith("}")
        assert set(table_str[1:-1].split(",")) == {
            "X",
            "Y*",
            "_0*",
            "_1*",
            f"{SpecialChar.TAU.value}0*",
        }
        # contains
        assert Variable("X") in var_table
        assert Variable("Z") not in var_table
        # add
        var_table = VariableTable()  # init new empty table
        var_table.register(Variable("X"))
        var_table.register(Variable("Y"), True)
        var_table.register(AnonVariable(0))
        assert not var_table[Variable("X")]
        assert var_table[Variable("Y")]
        assert not var_table[AnonVariable(0)]
        # update
        var_table.update({Variable("Z")})
        assert not var_table[Variable("Z")]
        var_table.update({Variable("U"): True})
        assert var_table[Variable("U")]
        # create
        assert var_table.create("X", register=False) == Variable("X")
        assert var_table.create("_", register=False) == AnonVariable(1)
        with pytest.raises(ValueError):
            var_table.create(SpecialChar.TAU.value)
        assert var_table.create(
            SpecialChar.TAU.value,
            orig_term=Minus(Variable("A")),
            register=True,
        ) == ArithVariable(0, Minus(Variable("A")))
        assert ArithVariable(0, Minus(Variable("A"))) in var_table
