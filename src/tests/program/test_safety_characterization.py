from typing import Self

import aspy
from aspy.program.safety_characterization import SafetyRule
from aspy.program.terms import Variable


class TestSafetyCharacterization:
    def test_safety_rule(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        rule = SafetyRule(Variable("X"), {Variable("Y")})

        # equality
        assert rule == SafetyRule(Variable("X"), {Variable("Y")})
        # hashing
        assert hash(rule) == hash(SafetyRule(Variable("X"), {Variable("Y")}))

    def test_safety_triple(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # TODO
