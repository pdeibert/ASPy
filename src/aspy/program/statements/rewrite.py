from typing import TYPE_CHECKING, Iterable, List, Set, Tuple

from aspy.program.literals import AggrPlaceholder, ChoicePlaceholder, LiteralCollection
from aspy.program.terms import TermTuple

from .choice import Choice
from .special import AggrBaseRule, AggrElemRule, ChoiceBaseRule, ChoiceElemRule

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import AggrLiteral, Literal
    from aspy.program.terms import Variable


def rewrite_aggregate(
    literal: "AggrLiteral",
    aggr_counter: int,
    glob_vars: Set["Variable"],
    body_literals: Iterable["Literal"],
) -> Tuple["AggrPlaceholder", "AggrBaseRule", List["AggrElemRule"]]:
    # TODO: necessary?
    aggr_glob_vars = glob_vars.intersection(literal.vars())
    var_tuple = TermTuple(*aggr_glob_vars)

    # ----- create predicate literal for each aggregate occurrence -----
    alpha_literal = AggrPlaceholder(aggr_counter, var_tuple, var_tuple, naf=literal.naf)

    # ----- epsilon rule -----
    eps_rule = AggrBaseRule.from_scratch(
        aggr_counter,
        var_tuple,
        *literal.guards,
        literal.func.base,
        LiteralCollection(*body_literals)
    )

    # ----- eta rules -----
    eta_rules = []

    for element_counter, element in enumerate(literal.elements):
        eta_rules.append(
            AggrElemRule.from_scratch(
                aggr_counter,
                element_counter,
                var_tuple,
                element,
                LiteralCollection(*body_literals),
            )
        )

    return (alpha_literal, eps_rule, eta_rules)


def rewrite_choice(
    choice: "Choice",
    choice_counter: int,
    glob_vars: Set["Variable"],
    body_literals: Iterable["Literal"],
) -> Tuple["ChoicePlaceholder", "ChoiceBaseRule", List["ChoiceElemRule"]]:
    # TODO: necessary?
    choice_glob_vars = glob_vars.intersection(choice.vars())
    var_tuple = TermTuple(*choice_glob_vars)

    # ----- create predicate literal for each aggregate occurrence -----
    chi_literal = ChoicePlaceholder(choice_counter, var_tuple, var_tuple)

    # ----- epsilon rule -----
    eps_rule = ChoiceBaseRule.from_scratch(
        choice_counter, var_tuple, *choice.guards, LiteralCollection(*body_literals)
    )

    # ----- eta rules -----
    eta_rules = []

    for element_counter, element in enumerate(choice.elements):
        eta_rules.append(
            ChoiceElemRule.from_scratch(
                choice_counter,
                element_counter,
                var_tuple,
                element,
                LiteralCollection(*body_literals),
            )
        )

    return (chi_literal, eps_rule, eta_rules)
