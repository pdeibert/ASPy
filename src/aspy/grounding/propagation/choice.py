from itertools import chain
from typing import TYPE_CHECKING, Dict, List, Set, Tuple

from aspy.program.literals import ChoicePlaceholder
from aspy.program.statements import Choice, ChoiceBaseRule, ChoiceElemRule

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import Literal
    from aspy.program.statements import Statement


class ChoicePropagator:
    def __init__(
        self,
        choice_map: Dict[
            int,
            Tuple["Choice", "ChoicePlaceholder", ChoiceBaseRule, List[ChoiceElemRule]],
        ],
    ) -> None:
        self.choice_map = choice_map
        self.instance_map = dict()

    def propagate(
        self,
        eps_instances,
        eta_instances,
        I: Set["Literal"],
        J: Set["Literal"],
        J_chi: Set["Literal"],
    ) -> Set[ChoicePlaceholder]:

        for rule in chain(eps_instances, eta_instances):

            # get corresponding chi_literal
            choice, chi_literal, *_ = self.choice_map[rule.choice_id]

            if isinstance(rule, ChoiceBaseRule):
                # gather variable substitution
                subst = rule.gather_var_assignment()
                # ground corresponding chi literal
                ground_chi_literal = chi_literal.substitute(subst)

                if ground_chi_literal not in self.instance_map:
                    self.instance_map[ground_chi_literal] = (
                        set(),
                        tuple(
                            guard.substitute(subst) if guard is not None else None
                            for guard in choice.guards
                        ),
                    )
            elif isinstance(rule, ChoiceElemRule):
                # gather variables
                subst = rule.gather_var_assignment()
                # ground corresponding chi literal
                ground_chi_literal = chi_literal.substitute(subst)

                if ground_chi_literal not in self.instance_map:
                    self.instance_map[ground_chi_literal] = (
                        set(),
                        tuple(
                            guard.substitute(subst) if guard is not None else None
                            for guard in choice.guards
                        ),
                    )

                self.instance_map[ground_chi_literal][0].add(
                    rule.element.substitute(subst)
                )

        possible_chi_literals = set()

        for ground_chi_literal, (
            ground_elements,
            ground_guards,
        ) in self.instance_map.items():
            # skip chi literal if already derived (in previous iteration)
            if ground_chi_literal in J_chi:
                possible_chi_literals.add(ground_chi_literal)
                continue

            # propagate choice to check satisfiability
            # TODO: choice.propagate
            satisfiable = choice.propagate(ground_guards, ground_elements, I, J)

            if satisfiable:
                possible_chi_literals.add(ground_chi_literal)

        return possible_chi_literals

    def assemble(
        self, rules: Set["Statement"], satisfiable: Set[ChoicePlaceholder]
    ) -> Set["Statement"]:

        # map ground chi literals to corresponding
        # assembled choice expressions to be replaced with
        assembling_map = {
            chi_literal: Choice(tuple(elements), guards)
            for chi_literal, (
                elements,
                guards,
            ) in self.instance_map.items()
            if chi_literal in satisfiable
        }

        # return assembled rules
        return set(rule.assemble_choices(assembling_map) for rule in rules)
