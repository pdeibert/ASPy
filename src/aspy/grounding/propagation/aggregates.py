from itertools import chain
from typing import TYPE_CHECKING, Dict, List, Self, Set, Tuple

from aspy.program.literals import AggrLiteral, AggrPlaceholder
from aspy.program.statements import AggrBaseRule, AggrElemRule

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import Literal
    from aspy.program.statements import Statement


class AggrPropagator:
    def __init__(
        self: Self,
        aggr_map: Dict[
            int,
            Tuple["AggrLiteral", "AggrPlaceholder", AggrBaseRule, List[AggrElemRule]],
        ],
    ) -> None:
        self.aggr_map = aggr_map
        self.instance_map = dict()

    def propagate(
        self: Self,
        eps_instances,
        eta_instances,
        literals_I: Set["Literal"],
        literals_J: Set["Literal"],
        literals_J_alpha: Set["Literal"],
    ) -> Set[AggrPlaceholder]:
        for rule in chain(eps_instances, eta_instances):
            # get corresponding alpha_literal
            aggr_literal, alpha_literal, *_ = self.aggr_map[rule.ref_id]

            if isinstance(rule, AggrBaseRule):
                # gather variable substitution
                subst = rule.gather_var_assignment()
                # ground corresponding alpha literal
                ground_alpha_literal = alpha_literal.substitute(subst)

                if ground_alpha_literal not in self.instance_map:
                    self.instance_map[ground_alpha_literal] = (
                        aggr_literal.func,
                        set(),
                        tuple(
                            guard.substitute(subst) if guard is not None else None
                            for guard in aggr_literal.guards
                        ),
                    )
            elif isinstance(rule, AggrElemRule):
                # gather variables
                subst = rule.gather_var_assignment()
                # ground corresponding alpha literal
                ground_alpha_literal = alpha_literal.substitute(subst)

                if ground_alpha_literal not in self.instance_map:
                    self.instance_map[ground_alpha_literal] = (
                        aggr_literal.func,
                        set(),
                        tuple(
                            guard.substitute(subst) if guard is not None else None
                            for guard in aggr_literal.guards
                        ),
                    )

                self.instance_map[ground_alpha_literal][1].add(
                    rule.element.substitute(subst)
                )

        possible_alpha_literals = set()

        for ground_alpha_literal, (
            aggr_func,
            ground_elements,
            ground_guards,
        ) in self.instance_map.items():
            # skip alpha literal if already derived (in previous iteration)
            if ground_alpha_literal in literals_J_alpha:
                possible_alpha_literals.add(ground_alpha_literal)
                continue

            # propagate aggregate function to check satisfiability
            satisfiable = aggr_func.propagate(
                ground_guards, ground_elements, literals_I, literals_J
            )

            if satisfiable:
                possible_alpha_literals.add(ground_alpha_literal)

        return possible_alpha_literals

    def assemble(self: Self, statements: Set["Statement"]) -> Set["Statement"]:
        # map ground alpha literals to corresponding
        # assembled aggr. literals to be replaced with
        assembling_map = {
            alpha_literal: AggrLiteral(
                aggr_func, tuple(elements), guards, naf=alpha_literal.naf
            )
            for alpha_literal, (
                aggr_func,
                elements,
                guards,
            ) in self.instance_map.items()
        }

        # return assembled rules
        return set(
            statement.assemble_aggregates(assembling_map) for statement in statements
        )
