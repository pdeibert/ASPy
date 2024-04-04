from typing import Self

import pytest  # type: ignore

import aspy
from aspy.program.substitution import AssignmentError, Substitution
from aspy.program.terms import Number, String, Variable


class TestSubstitution:
    def test_substitution(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # empty substitution
        subst = Substitution()
        # equality
        assert subst == Substitution()
        # hashing
        assert hash(subst) == hash(Substitution())
        # __getitem__
        assert subst[Variable("X")] == Variable(
            "X"
        )  # map non-specified variables to themselves
        # identity
        assert Substitution().is_identity()
        assert Substitution({Variable("X"): Variable("X")}).is_identity()
        assert not Substitution({Variable("X"): Variable("Y")}).is_identity()

        # non-empty substitution
        subst = Substitution({Variable("X"): Number(0), Variable("Y"): String("str")})
        # equality
        assert subst == Substitution(
            {Variable("X"): Number(0), Variable("Y"): String("str")}
        )
        # hashing
        assert hash(subst) == hash(
            Substitution({Variable("X"): Number(0), Variable("Y"): String("str")})
        )
        # __getitem__
        assert subst[Variable("X")] == Number(0)
        assert subst[Variable("Y")] == String("str")
        assert subst[Variable("X")] == Number(0)
        assert subst[Variable("Z")] == Variable(
            "Z"
        )  # map non-specified variables to themselves

        # adding substitutions
        subst = Substitution(
            {Variable("X"): Number(0), Variable("Y"): String("str")}
        ) + Substitution({Variable("Y"): String("str"), Variable("Z"): Number(3)})
        assert subst == Substitution(
            {
                Variable("X"): Number(0),
                Variable("Y"): String("str"),
                Variable("Z"): Number(3),
            }
        )
        with pytest.raises(AssignmentError):
            Substitution(
                {Variable("X"): Number(0), Variable("Y"): String("str")}
            ) + Substitution({Variable("Y"): Number(3), Variable("Z"): Number(3)})

        # composing substitutions
        subst1 = Substitution({Variable("X"): Variable("Y")})
        subst2 = Substitution(
            {
                Variable("X"): Number(1),
                Variable("Y"): Number(0),
                Variable("Z"): String("a"),
            }
        )
        assert subst1.compose(subst2) == Substitution(
            {
                Variable("X"): Number(0),
                Variable("Y"): Number(0),
                Variable("Z"): String("a"),
            }
        )
        subst3 = Substitution({Variable("A"): Variable("B")})
        subst4 = Substitution({Variable("B"): String("b")})
        assert subst1.compose(subst2).compose(subst3).compose(
            subst4
        ) == Substitution.composition(subst1, subst2, subst3, subst4)
