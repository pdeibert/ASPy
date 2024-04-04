import warnings
from collections import defaultdict
from copy import deepcopy
from typing import TYPE_CHECKING, Optional, Self, Set, Type

from aspy.program.literals import AggrLiteral, BuiltinLiteral, Equal, Naf, PredLiteral
from aspy.program.program import Program
from aspy.program.statements import Constraint
from aspy.program.substitution import Substitution
from aspy.program.terms import ArithVariable

from .graphs import ComponentGraph
from .propagation import AggrPropagator, ChoicePropagator

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import Literal, LiteralCollection
    from aspy.program.statements import Statement


class Grounder:
    def __init__(self: Self, prog: Program) -> None:
        if not prog.safe:
            raise ValueError("Grounding requires program to be safe.")

        self.prog = prog
        self.certain_literals = set()

    @classmethod
    def select(
        cls: Type["Grounder"],
        literals: "LiteralCollection",
        subst: Optional[Substitution] = None,
    ) -> "Literal":
        if subst is None:
            # initialize with empty/identity substitution
            subst = Substitution()

        # TODO: apply subst?

        # find appropriate literal
        for literal in literals:
            if isinstance(literal, AggrLiteral):
                # TODO: raise exception (should have been replaced)
                raise ValueError(
                    f"Aggregate literals should be replaced before calling {cls.select} during grounding."  # noqa
                )

            # either literal is positive (pos_occ() is non-empy) or literal is ground
            # under the substitution (all variables in 'literal' replaced by 'subst')
            if literal.pos_occ() or all(subst[var].ground for var in literal.vars()):
                return literal

        raise ValueError(
            f"Tuple of literals {tuple(str(literal.substitute(subst)) for literal in literals)} does not contain any appropriate literals for 'select'."
        )

    @classmethod
    def matches(
        cls: Type["Grounder"],
        literal: "Literal",
        certain: Optional[Set["Literal"]] = None,
        possible: Optional[Set["Literal"]] = None,
        subst: Optional["Substitution"] = None,
    ) -> Set["Substitution"]:
        # initialize optional arguments
        if subst is None:
            subst = Substitution()
        if certain is None:
            certain = set()
        if possible is None:
            possible = set()

        # apply (partial) substitution
        literal = literal.substitute(subst)

        if isinstance(literal, PredLiteral):
            # positive predicate literal
            if not literal.naf:
                matches = set()

                if literal.ground:
                    if literal in possible:
                        matches.add(subst)
                else:
                    # compute possible match substitutions
                    for target in possible:
                        match = literal.substitute(subst).match(target)

                        if match is not None:
                            matches.add(subst.compose(match))

                return matches
            # ground negative predicate literal
            elif literal.ground:
                # literal does not contradict set of certain (positive) literals
                # (used as a check)
                return (
                    {subst} if Naf(deepcopy(literal), False) not in certain else set()
                )
        # ground built-in literal
        elif isinstance(literal, BuiltinLiteral) and literal.ground:
            # relation holds (used as a check)
            return {subst} if literal.eval() else set()

        # should not happen (just in case)
        raise ValueError(f"{cls.matches} undefined for literal {str(literal)}.")

    @classmethod
    def ground_statement(
        cls: Type["Grounder"],
        statement: "Statement",
        literals: Optional["LiteralCollection"] = None,
        certain: Optional[Set["Literal"]] = None,
        possible: Optional[Set["Literal"]] = None,
        prev_possible: Optional[Set["Literal"]] = None,
        subst: Optional["Substitution"] = None,
        duplicate: bool = False,
    ) -> Set["Statement"]:
        """Algorithm 1 from TODO."""
        if statement.contains_aggregates:
            raise ValueError(
                f"{cls.ground_statement} requires statement to be free of aggregates."
            )
        if not statement.safe:
            raise ValueError(
                f"{cls.ground_statement} can only instantiate safe statements."
            )

        # initialize optional arguments
        if subst is None:
            subst = Substitution()
        if certain is None:
            certain = set()
        if possible is None:
            possible = set()
        if prev_possible is None:
            prev_possible = set()
        if literals is None:
            # get body literals
            literals = statement.body

        # while literals to be processed
        if literals:
            # select positive predicate or ground literal
            literal = cls.select(literals, subst)

            # compute matches for selected literal and ground remaining literals
            return set().union(
                *tuple(
                    cls.ground_statement(
                        statement,
                        literals.without(literal),
                        certain,
                        possible,
                        prev_possible,
                        match,
                        duplicate,
                    )
                    for match in cls.matches(literal, certain, possible, subst)
                )
            )
        else:
            # check replaced arithmetic terms
            for var, target in subst.items():
                if isinstance(var, ArithVariable):
                    # if arithmetic term is not valid -> no valid instantiation
                    if not Equal(target, var.orig_term.substitute(subst)).eval():
                        return set()

            # instantiate final (ground) statement
            ground_statement = statement.substitute(subst)

            if not duplicate or not ground_statement.body.pos_occ() <= prev_possible:
                return {ground_statement}

        # duplicate instantiation
        return set()

    def ground_component(
        self: Self,
        component: Program,
        literals_I: Optional[Set["Literal"]] = None,
        literals_J: Optional[Set["Literal"]] = None,
    ) -> Set["Statement"]:
        if not component.statements:
            return set()

        # initialize optional arguments
        if literals_I is None:
            literals_I = set()
        if literals_J is None:
            literals_J = set()

        # initialize sets of instances/literals
        alpha_instances = set()
        aggr_eps_instances = set()
        aggr_eta_instances = set()
        choice_eps_instances = set()
        choice_eta_instances = set()

        # NOTE: as implemented by 'mu-gringo', different from original algorithm.
        # Use of J,J' during grounding of epsilon/eta rules yields incorrect groundings.
        literals_K = literals_I.union(literals_J)
        prev_literals_K = set()

        literals_J_alpha = set()
        prev_literals_J_alpha = set()
        literals_J_chi = set()
        prev_literals_J = set()

        # initialize flag
        duplicate = False

        (
            prog_alpha,
            prog_aggr_eps,
            prog_aggr_eta,
            aggr_map,
        ) = component.rewrite_aggregates()
        (
            prog_alpha,
            prog_choice_eps,
            prog_choice_eta,
            choice_map,
        ) = prog_alpha.rewrite_choices()
        # TODO: rewrite choice expressions!

        # initialize propagator
        aggr_propagator = AggrPropagator(aggr_map)
        choice_propagator = ChoicePropagator(choice_map)

        converged = False

        while not converged:
            # ground aggregate epsilon rules
            # (encode the satisfiability of aggregates without any element instances)
            aggr_eps_instances.update(
                set().union(
                    *tuple(
                        self.ground_statement(
                            rule,
                            rule.body,
                            literals_I,
                            literals_K,
                            prev_literals_K,
                            Substitution(),
                            duplicate,
                        )
                        for rule in prog_aggr_eps.statements
                    )
                )
            )
            # ground eta rules (encode the satisfiability of aggregate elements)
            aggr_eta_instances.update(
                set().union(
                    *tuple(
                        self.ground_statement(
                            rule,
                            rule.body,
                            literals_I,
                            literals_K,
                            prev_literals_K,
                            Substitution(),
                            duplicate,
                        )
                        for rule in prog_aggr_eta.statements
                    )
                )
            )

            # propagate aggregates
            literals_J_alpha = aggr_propagator.propagate(
                aggr_eps_instances,
                aggr_eta_instances,
                literals_I,
                literals_J,
                literals_J_alpha,
            )

            # ground remaining rules (including non-aggregate rules)
            alpha_instances.update(
                set().union(
                    *tuple(
                        self.ground_statement(
                            rule,
                            rule.body,
                            literals_I,
                            literals_J.union(literals_J_alpha),
                            prev_literals_J.union(prev_literals_J_alpha),
                            Substitution(),
                            duplicate,
                        )
                        for rule in prog_alpha.statements
                    )
                )
            )
            choice_eps_instances.update(
                set().union(
                    *tuple(
                        self.ground_statement(
                            rule,
                            rule.body,
                            literals_I,
                            literals_J.union(literals_J_alpha),
                            prev_literals_J.union(prev_literals_J_alpha),
                            Substitution(),
                            duplicate,
                        )
                        for rule in prog_choice_eps.statements
                    )
                )
            )
            choice_eta_instances.update(
                set().union(
                    *tuple(
                        self.ground_statement(
                            rule,
                            rule.body,
                            literals_I,
                            literals_J.union(literals_J_alpha),
                            prev_literals_J.union(prev_literals_J_alpha),
                            Substitution(),
                            duplicate,
                        )
                        for rule in prog_choice_eta.statements
                    )
                )
            )

            # propagate choice expressions
            literals_J_chi = choice_propagator.propagate(
                choice_eps_instances,
                choice_eta_instances,
                literals_I,
                literals_J,
                literals_J_chi,
            )

            # update state
            duplicate = True
            prev_literals_J_alpha = literals_J_alpha.copy()
            prev_literals_J = literals_J.copy()
            prev_literals_K = literals_K.copy()

            # NOTE: 'pos_occ' applicable (all head literals are pos. predicate literals)
            head_literals = set().union(
                *tuple(rule.head.pos_occ() for rule in alpha_instances)
            )

            literals_J.update(head_literals)
            literals_K.update(head_literals)

            # enough to check lengths instead of elements (much cheaper)
            if len(literals_J) == len(prev_literals_J):
                converged = True

        # assemble aggregates (if present)
        assembled_instances = aggr_propagator.assemble(alpha_instances)
        assembled_instances = choice_propagator.assemble(
            assembled_instances, literals_J_chi
        )

        # return re-assembled rules
        return assembled_instances

    def ground(self: Self) -> Program:
        # compute component graph for rules/facts only
        component_graph = ComponentGraph(self.prog.statements)  # rules/facts only???

        # compute component instantiation sequence
        inst_sequence = component_graph.sequence()

        # initialize sets of certain and possible statement instantiations
        certain_inst = set()
        possible_inst = set()

        # initialize sets of certain and possible literal instantiations
        # (follow from head literals of statement instantiations)
        certain_literals = set()
        possible_literals = set()

        for component in inst_sequence:
            # compute counter of occurring head predicates
            # (used to indicate which predicates have been fully processed)
            pred_counter = defaultdict(int)

            for statement in component.nodes:
                for literal in statement.consequents():
                    # increment counter for literal predicate signature
                    pred_counter[literal.pred()] += 1

            ref_component_seq = component.sequence()

            for ref_component in ref_component_seq:
                # wrap refined component in 'Program' object
                ref_component_prog = Program(tuple(ref_component))

                # predicates which are still open (have not been fully processed yet)
                open_preds = {var for (var, count) in pred_counter.items() if count > 0}

                # can be pre-computed (used for both set updates)
                # TODO: make more efficient by updating incrementally?
                possible_literals = set().union(
                    *tuple(inst.consequents() for inst in possible_inst)
                )

                instances = self.ground_component(
                    ref_component_prog.reduct(open_preds),
                    possible_literals,
                    certain_literals,
                )

                # check if any constraint was derived
                # (resulting in an unsatisfiable program)
                if any(isinstance(inst, Constraint) for inst in instances):
                    warnings.warn(
                        "Derived certain constraint instance. Program is unsatisfiable"
                    )
                # update certain instances
                certain_inst.update(instances)

                # compute & update possible instances
                # TODO: make more efficient by updating incrementally?
                certain_literals = set().union(
                    *tuple(
                        inst.consequents()
                        for inst in certain_inst
                        if inst.deterministic
                    )
                )

                possible_inst.update(
                    self.ground_component(
                        ref_component_prog, certain_literals, possible_literals
                    )
                )

                for statement in ref_component:
                    for literal in statement.consequents():
                        # increment counter for literal predicate signature
                        pred_counter[literal.pred()] -= 1

        # keep track of possible and certain atoms & rules
        self.certain_literals = certain_literals
        self.possible_literals = possible_literals
        self.certain_instances = certain_inst
        self.possible_instances = possible_inst

        # return possible instances (includes certain instances)
        return Program(tuple(possible_inst))
