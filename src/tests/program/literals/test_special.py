from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.literals import (
    AggrBaseLiteral,
    AggrElemLiteral,
    AggrPlaceholder,
    ChoiceBaseLiteral,
    ChoiceElemLiteral,
    ChoicePlaceholder,
    LiteralCollection,
    Naf,
)
from aspy.program.safety_characterization import SafetyTriplet
from aspy.program.substitution import Substitution
from aspy.program.symbols import SpecialChar
from aspy.program.terms import Number, String, TermTuple, Variable
from aspy.program.variable_table import VariableTable


class TestSpecial:
    def test_aggr_placeholder(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        vars = TermTuple(Variable("X"), Variable("Y"))
        literal = AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        naf_literal = Naf(AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y"))))

        # check initialization
        assert literal.ref_id == naf_literal.ref_id == 1
        assert literal.glob_vars == naf_literal.glob_vars == vars
        assert literal.terms == naf_literal.terms == TermTuple(Number(1), Variable("Y"))
        # string representation
        assert str(literal) == f"{SpecialChar.ALPHA.value}{1}(1,Y)"
        assert str(naf_literal) == f"not {SpecialChar.ALPHA.value}{1}(1,Y)"
        # equality
        assert literal == AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        # hashing
        assert hash(literal) == hash(
            AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        # arity
        assert literal.arity == 2
        # predicate tuple
        assert literal.pred() == (f"{SpecialChar.ALPHA.value}{1}", 2)
        # ground
        assert literal.ground == naf_literal.ground == False  # noqa
        # TODO: variables
        # replace arithmetic terms
        assert literal.replace_arith(VariableTable()) == literal
        # positive/negative literal occurrences
        assert literal.pos_occ() == LiteralCollection(
            AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        assert literal.neg_occ() == LiteralCollection()
        assert naf_literal.pos_occ() == LiteralCollection()
        assert naf_literal.neg_occ() == LiteralCollection(
            AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        # safety characterization
        assert literal.safety() == SafetyTriplet({Variable("Y")})

        # classical negation and negation-as-failure
        assert literal.naf == (not naf_literal.naf) == literal.neg == False  # noqa
        with pytest.raises(Exception):
            literal.set_neg()
        literal.set_naf(True)
        assert literal.naf is True

        # substitute
        assert AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y"))).substitute(
            Substitution({Variable("Y"): Number(0), Number(1): String("f")})
        ) == AggrPlaceholder(
            1, vars, TermTuple(Number(1), Number(0))
        )  # NOTE: substitution is invalid
        # match
        assert AggrPlaceholder(1, vars, TermTuple(Variable("X"), Variable("Y"))).match(
            AggrPlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            Naf(AggrPlaceholder(1, vars, TermTuple(Variable("X"), String("f")))).match(
                Naf(AggrPlaceholder(1, vars, TermTuple(Number(1), String("g"))))
            )
            is None
        )  # ground terms don't match

        # gather variable assignment
        assert AggrPlaceholder(
            1, vars, TermTuple(Number(1), Variable("Y"))
        ).gather_var_assignment() == Substitution({Variable("X"): Number(1)})

    def test_aggr_base_literal(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        vars = TermTuple(Variable("X"), Variable("Y"))
        literal = AggrBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))

        # check initialization
        assert literal.ref_id == 1
        assert literal.glob_vars == vars
        assert literal.terms == TermTuple(Number(1), Variable("Y"))
        # string representation
        assert (
            str(literal) == f"{SpecialChar.EPS.value}{SpecialChar.ALPHA.value}{1}(1,Y)"
        )
        # equality
        assert literal == AggrBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))
        # hashing
        assert hash(literal) == hash(
            AggrBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        # arity
        assert literal.arity == 2
        # predicate tuple
        assert literal.pred() == (
            f"{SpecialChar.EPS.value}{SpecialChar.ALPHA.value}{1}",
            2,
        )
        # ground
        assert not literal.ground
        # TODO: variables
        # replace arithmetic terms
        assert literal.replace_arith(VariableTable()) == literal
        # positive/negative literal occurrences
        assert literal.pos_occ() == LiteralCollection(
            AggrBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        assert literal.neg_occ() == LiteralCollection()
        # safety characterization
        assert literal.safety() == SafetyTriplet({Variable("Y")})

        # classical negation and negation-as-failure
        assert literal.naf == literal.neg == False  # noqa
        with pytest.raises(Exception):
            literal.set_neg()
        with pytest.raises(Exception):
            literal.set_naf()

        # substitute
        assert AggrBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y"))).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == AggrBaseLiteral(
            1, vars, TermTuple(Number(1), Variable("Y"))
        )  # NOTE: substitution is invalid
        # match
        assert AggrBaseLiteral(1, vars, TermTuple(Variable("X"), Variable("Y"))).match(
            AggrBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))
        ) == Substitution({Variable("X"): Number(1)})
        assert (
            AggrBaseLiteral(1, vars, TermTuple(Variable("X"), String("f"))).match(
                AggrBaseLiteral(1, vars, TermTuple(Number(1), String("g")))
            )
            is None
        )  # ground terms don't match

        # gather variable assignment
        assert AggrBaseLiteral(
            1, vars, TermTuple(Number(1), Variable("Y"))
        ).gather_var_assignment() == Substitution({Variable("X"): Number(1)})

    def test_aggr_elem_literal(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        global_vars = TermTuple(Variable("L"))
        local_vars = TermTuple(Variable("X"), Variable("Y"))
        literal = AggrElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Number(1), Variable("Y")),
        )

        # check initialization
        assert literal.ref_id == 1
        assert literal.element_id == 3
        assert literal.local_vars == local_vars
        assert literal.glob_vars == global_vars
        assert literal.terms == TermTuple(Variable("L"), Number(1), Variable("Y"))
        # string representation
        assert (
            str(literal)
            == f"{SpecialChar.ETA.value}{SpecialChar.ALPHA.value}{1}_{3}(L,1,Y)"
        )
        # equality
        assert literal == AggrElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Number(1), Variable("Y")),
        )
        # hashing
        assert hash(literal) == hash(
            AggrElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Variable("L"), Number(1), Variable("Y")),
            )
        )
        # arity
        assert literal.arity == 3
        # predicate tuple
        assert literal.pred() == (
            f"{SpecialChar.ETA.value}{SpecialChar.ALPHA.value}{1}_{3}",
            3,
        )
        # ground
        assert not literal.ground
        # TODO: variables
        # replace arithmetic terms
        assert literal.replace_arith(VariableTable()) == literal
        # positive/negative literal occurrences
        assert literal.pos_occ() == LiteralCollection(
            AggrElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Variable("L"), Number(1), Variable("Y")),
            )
        )
        assert literal.neg_occ() == LiteralCollection()
        # safety characterization
        assert literal.safety() == SafetyTriplet({Variable("L"), Variable("Y")})

        # classical negation and negation-as-failure
        assert literal.naf == literal.neg == False  # noqa
        with pytest.raises(Exception):
            literal.set_neg()
        with pytest.raises(Exception):
            literal.set_naf()

        # substitute
        assert AggrElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Variable("X"), Variable("Y")),
        ).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == AggrElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Number(1), Variable("Y")),
        )  # NOTE: substitution is invalid
        # match
        assert AggrElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Variable("X"), Variable("Y")),
        ).match(
            AggrElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Number(1), Variable("X"), String("f")),
            )
        ) == Substitution(
            {Variable("L"): Number(1), Variable("Y"): String("f")}
        )
        assert (
            AggrElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Variable("L"), Variable("X"), String("f")),
            ).match(
                AggrElemLiteral(
                    1,
                    3,
                    local_vars,
                    global_vars,
                    TermTuple(Number(1), Number(0), String("g")),
                )
            )
            is None
        )  # ground terms don't match

    def test_choice_placeholder(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        vars = TermTuple(Variable("X"), Variable("Y"))
        literal = ChoicePlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        with pytest.raises(Exception):
            Naf(ChoicePlaceholder(1, vars, TermTuple(Number(1), Variable("Y"))))

        # check initialization
        assert literal.ref_id == 1
        assert literal.glob_vars == vars
        assert literal.terms == TermTuple(Number(1), Variable("Y"))
        # string representation
        assert str(literal) == f"{SpecialChar.CHI.value}{1}(1,Y)"
        # equality
        assert literal == ChoicePlaceholder(
            1, vars, TermTuple(Number(1), Variable("Y"))
        )
        # hashing
        assert hash(literal) == hash(
            ChoicePlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        # arity
        assert literal.arity == 2
        # predicate tuple
        assert literal.pred() == (f"{SpecialChar.CHI.value}{1}", 2)
        # ground
        assert not literal.ground
        # TODO: variables

        # replace arithmetic terms
        assert literal.replace_arith(VariableTable()) == literal
        # positive/negative literal occurrences
        assert literal.pos_occ() == LiteralCollection(
            ChoicePlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        assert literal.neg_occ() == LiteralCollection()

        # safety characterization
        assert literal.safety() == SafetyTriplet({Variable("Y")})

        # classical negation and negation-as-failure
        assert literal.naf == literal.neg == False  # noqa
        with pytest.raises(Exception):
            literal.set_neg()
        with pytest.raises(Exception):
            literal.set_naf()

        # substitute
        assert ChoicePlaceholder(
            1, vars, TermTuple(Number(1), Variable("Y"))
        ).substitute(
            Substitution({Variable("Y"): Number(0), Number(1): String("f")})
        ) == ChoicePlaceholder(
            1, vars, TermTuple(Number(1), Number(0))
        )  # NOTE: substitution is invalid
        # match
        assert ChoicePlaceholder(
            1, vars, TermTuple(Variable("X"), Variable("Y"))
        ).match(
            ChoicePlaceholder(1, vars, TermTuple(Number(1), Variable("Y")))
        ) == Substitution(
            {Variable("X"): Number(1)}
        )
        assert (
            ChoicePlaceholder(1, vars, TermTuple(Variable("X"), String("f"))).match(
                ChoicePlaceholder(1, vars, TermTuple(Number(1), String("g")))
            )
            is None
        )  # ground terms don't match

        # gather variable assignment
        assert ChoicePlaceholder(
            1, vars, TermTuple(Number(1), Variable("Y"))
        ).gather_var_assignment() == Substitution({Variable("X"): Number(1)})

    def test_choice_base_literal(self):
        # make sure debug mode is enabled
        assert aspy.debug()

        vars = TermTuple(Variable("X"), Variable("Y"))
        literal = ChoiceBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))

        # check initialization
        assert literal.ref_id == 1
        assert literal.glob_vars == vars
        assert literal.terms == TermTuple(Number(1), Variable("Y"))
        # string representation
        assert str(literal) == f"{SpecialChar.EPS.value}{SpecialChar.CHI.value}{1}(1,Y)"
        # equality
        assert literal == ChoiceBaseLiteral(
            1, vars, TermTuple(Number(1), Variable("Y"))
        )
        # hashing
        assert hash(literal) == hash(
            ChoiceBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        # arity
        assert literal.arity == 2
        # predicate tuple
        assert literal.pred() == (
            f"{SpecialChar.EPS.value}{SpecialChar.CHI.value}{1}",
            2,
        )
        # ground
        assert not literal.ground
        # TODO: variables
        # replace arithmetic terms
        assert literal.replace_arith(VariableTable()) == literal
        # positive/negative literal occurrences
        assert literal.pos_occ() == LiteralCollection(
            ChoiceBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))
        )
        assert literal.neg_occ() == LiteralCollection()
        # safety characterization
        assert literal.safety() == SafetyTriplet({Variable("Y")})

        # classical negation and negation-as-failure
        assert literal.naf == literal.neg == False  # noqa
        with pytest.raises(Exception):
            literal.set_neg()
        with pytest.raises(Exception):
            literal.set_naf()

        # substitute
        assert ChoiceBaseLiteral(
            1, vars, TermTuple(Number(1), Variable("Y"))
        ).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == ChoiceBaseLiteral(
            1, vars, TermTuple(Number(1), Variable("Y"))
        )  # NOTE: substitution is invalid
        # match
        assert ChoiceBaseLiteral(
            1, vars, TermTuple(Variable("X"), Variable("Y"))
        ).match(
            ChoiceBaseLiteral(1, vars, TermTuple(Number(1), Variable("Y")))
        ) == Substitution(
            {Variable("X"): Number(1)}
        )
        assert (
            ChoiceBaseLiteral(1, vars, TermTuple(Variable("X"), String("f"))).match(
                ChoiceBaseLiteral(1, vars, TermTuple(Number(1), String("g")))
            )
            is None
        )  # ground terms don't match

        # gather variable assignment
        assert ChoiceBaseLiteral(
            1, vars, TermTuple(Number(1), Variable("Y"))
        ).gather_var_assignment() == Substitution({Variable("X"): Number(1)})

    def test_choice_elem_literal(self):
        # make sure debug mode is enabled
        assert aspy.debug()

        global_vars = TermTuple(Variable("L"))
        local_vars = TermTuple(Variable("X"), Variable("Y"))
        literal = ChoiceElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Number(1), Variable("Y")),
        )

        # check initialization
        assert literal.ref_id == 1
        assert literal.element_id == 3
        assert literal.local_vars == local_vars
        assert literal.glob_vars == global_vars
        assert literal.terms == TermTuple(Variable("L"), Number(1), Variable("Y"))
        # string representation
        assert (
            str(literal)
            == f"{SpecialChar.ETA.value}{SpecialChar.CHI.value}{1}_{3}(L,1,Y)"
        )
        # equality
        assert literal == ChoiceElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Number(1), Variable("Y")),
        )
        # hashing
        assert hash(literal) == hash(
            ChoiceElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Variable("L"), Number(1), Variable("Y")),
            )
        )
        # arity
        assert literal.arity == 3
        # predicate tuple
        assert literal.pred() == (
            f"{SpecialChar.ETA.value}{SpecialChar.CHI.value}{1}_{3}",
            3,
        )
        # ground
        assert not literal.ground
        # TODO: variables
        # replace arithmetic terms
        assert literal.replace_arith(VariableTable()) == literal
        # positive/negative literal occurrences
        assert literal.pos_occ() == LiteralCollection(
            ChoiceElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Variable("L"), Number(1), Variable("Y")),
            )
        )
        assert literal.neg_occ() == LiteralCollection()
        # safety characterization
        assert literal.safety() == SafetyTriplet({Variable("L"), Variable("Y")})

        # classical negation and negation-as-failure
        assert literal.naf == literal.neg == False  # noqa
        with pytest.raises(Exception):
            literal.set_neg()
        with pytest.raises(Exception):
            literal.set_naf()

        # substitute
        assert ChoiceElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Variable("X"), Variable("Y")),
        ).substitute(
            Substitution({Variable("X"): Number(1), Number(0): String("f")})
        ) == ChoiceElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Number(1), Variable("Y")),
        )  # NOTE: substitution is invalid
        # match
        assert ChoiceElemLiteral(
            1,
            3,
            local_vars,
            global_vars,
            TermTuple(Variable("L"), Variable("X"), Variable("Y")),
        ).match(
            ChoiceElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Number(1), Variable("X"), String("f")),
            )
        ) == Substitution(
            {Variable("L"): Number(1), Variable("Y"): String("f")}
        )
        assert (
            ChoiceElemLiteral(
                1,
                3,
                local_vars,
                global_vars,
                TermTuple(Variable("L"), Variable("X"), String("f")),
            ).match(
                ChoiceElemLiteral(
                    1,
                    3,
                    local_vars,
                    global_vars,
                    TermTuple(Number(1), Number(0), String("g")),
                )
            )
            is None
        )  # ground terms don't match
