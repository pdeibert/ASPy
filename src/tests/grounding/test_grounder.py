from typing import List, Tuple, Set, FrozenSet
import unittest

import aspy
import clingo # type: ignore

from aspy.grounding import Grounder
from aspy.program.terms import Variable, Number, Add, ArithVariable, TermTuple, SymbolicConstant
from aspy.program.literals import Neg, Naf, LiteralTuple, PredicateLiteral, Equal, AggregateLiteral, AggregateCount, AggregateSum, AggregateElement, Guard
from aspy.program.operators import RelOp
from aspy.program.substitution import Substitution
from aspy.program.statements import NormalFact, NormalRule
from aspy.program.program import Program


def solve_using_clingo(prog) -> Tuple[bool, Set[FrozenSet[str]]]:

    ctl = clingo.Control(message_limit=0)
    # instruct to return all models
    ctl.configuration.solve.models = 0
    ctl.add("prog", [], prog)
    # TODO: optional?
    ctl.ground([("prog", [])])

    models = []
    sat = ctl.solve(on_model=lambda m: models.append(frozenset(str(m).split(' '))))

    return sat.satisfiable, set(models)


class TestGrounder(unittest.TestCase):
    def test_select(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        self.assertEqual(Grounder.select(LiteralTuple(Neg(PredicateLiteral('p', Variable('X'))), PredicateLiteral('q', Number(1)))), Neg(PredicateLiteral('p', Variable('X')))) # first predicate literal gets selected (even if it is non-ground)
        self.assertEqual(Grounder.select(LiteralTuple(Naf(PredicateLiteral('p', Variable('X'))), PredicateLiteral('q', Number(1)))), PredicateLiteral('q', Number(1))) # first predicate literal gets skipped (NAF and NON-ground)
        self.assertEqual(Grounder.select(LiteralTuple(Naf(PredicateLiteral('p', Number(1))), PredicateLiteral('q', Number(1)))), Naf(PredicateLiteral('p', Number(1)))) # first predicate literal gets select (NAF and ground)
        self.assertEqual(Grounder.select(LiteralTuple(Equal(Variable('X'), Number(1)), PredicateLiteral('q', Number(1)))), PredicateLiteral('q', Number(1))) # first built-in literal gets skipped (NON-ground)
        self.assertEqual(Grounder.select(LiteralTuple(Equal(Number(0), Number(1)), PredicateLiteral('q', Number(1)))), Equal(Number(0), Number(1))) # first built-in literal gets selected (ground)
        # aggregate literals should always be skipped (NAF or not)
        self.assertRaises(ValueError, Grounder.select, LiteralTuple(AggregateLiteral(AggregateCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False)), Naf(AggregateLiteral(AggregateCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False))), PredicateLiteral('p', Variable('X')))), PredicateLiteral('p', Variable('X'))
        # no selectable literal
        self.assertRaises(ValueError, Grounder.select, LiteralTuple(AggregateLiteral(AggregateCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False)), Naf(PredicateLiteral('p', Variable('X')))))

    def test_matches(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        # ground positive predicate literal
        self.assertEqual(Grounder.matches(Neg(PredicateLiteral('p', Number(0))), possible={Neg(PredicateLiteral('p', Number(0)))}), {Substitution()}) # in set of possible literals
        self.assertEqual(Grounder.matches(Neg(PredicateLiteral('p', Number(0)))), set()) # not in set of possible literals
        # non-ground positive predicate literal
        self.assertEqual(Grounder.matches(Neg(PredicateLiteral('p', Variable('X'))), possible={Neg(PredicateLiteral('p', Number(0)))}), {Substitution({Variable('X'): Number(0)})}) # match
        self.assertEqual(Grounder.matches(Neg(PredicateLiteral('p', Variable('X'))), possible={Neg(PredicateLiteral('q', Number(0)))}), set()) # no match
        # ground negative predicate literal
        self.assertEqual(Grounder.matches(Naf(Neg(PredicateLiteral('p', Number(0))))), {Substitution()}) # not in set of certain literals
        self.assertEqual(Grounder.matches(Naf(Neg(PredicateLiteral('p', Number(0)))), certain={Neg(PredicateLiteral('p', Number(0)))}), set()) # in set of certain literals
        # ground builtin literal
        self.assertEqual(Grounder.matches(Equal(Number(0), Number(0))), {Substitution()}) # relation holds
        self.assertEqual(Grounder.matches(Equal(Number(0), Number(1))), set()) # relation does not hold
        # invalid input literal
        self.assertRaises(ValueError, Grounder.matches, Naf(PredicateLiteral('p', Variable('X')))) # non-ground negative predicate literal
        self.assertRaises(ValueError, Grounder.matches, Equal(Number(0), Variable('X')))# non-ground builtin predicate literal
        self.assertRaises(ValueError, Grounder.matches, AggregateLiteral(AggregateCount(), tuple(), Guard(RelOp.EQUAL, Number(1), False)))# aggregate literal

    def test_ground_statement(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        # unsafe statement
        self.assertRaises(ValueError, Grounder.ground_statement, NormalFact(PredicateLiteral('p', Variable('X'))))
        # statement containing aggregates
        self.assertRaises(ValueError, Grounder.ground_statement, NormalRule(PredicateLiteral('p', Variable('X')), AggregateLiteral(AggregateCount(), tuple(), Guard(RelOp.EQUAL, Number(0), False))))

        # ----- normal facts -----

        # ground fact (no need to ground)
        self.assertEqual(Grounder.ground_statement(NormalFact(PredicateLiteral('p', Number(1)))), {NormalFact(PredicateLiteral('p', Number(1)))})

        # ----- normal rules -----

        # ground rule (no need to ground)
        self.assertEqual(
            Grounder.ground_statement(
                NormalRule(PredicateLiteral('p', Number(1)), PredicateLiteral('q', Number(0))),
                possible={PredicateLiteral('q', Number(0))}
            ),
            {NormalRule(PredicateLiteral('p', Number(1)), PredicateLiteral('q', Number(0)))})
        # non-ground rule
        self.assertEqual(Grounder.ground_statement(
                NormalRule(PredicateLiteral('p', Variable('X')), PredicateLiteral('q', Variable('X')), PredicateLiteral('q', Number(0))),
                possible={PredicateLiteral('q', Number(1)), PredicateLiteral('q', Number(0))}
            ),
            {
                NormalRule(PredicateLiteral('p', Number(0)), PredicateLiteral('q', Number(0)), PredicateLiteral('q', Number(0))),
                NormalRule(PredicateLiteral('p', Number(1)), PredicateLiteral('q', Number(1)), PredicateLiteral('q', Number(0)))
            }
        ) # all literals have matches in 'possible'
        self.assertEqual(Grounder.ground_statement(
                NormalRule(PredicateLiteral('p', Variable('X')), PredicateLiteral('q', Variable('X')), PredicateLiteral('q', Number(0))),
                possible={PredicateLiteral('q', Number(1))}
            ),
            set()
        ) # not all literals have matches in 'possible'

        # ----- disjunctive facts -----
        # TODO
        # ----- disjunctive rules -----
        # TODO
        # ----- choice facts -----
        # TODO
        # ----- choice rules -----
        # TODO
        # ----- strong constraints -----
        # TODO
        # ----- weak constraints -----
        # TODO
        # ----- optimize statements -----
        # TODO

        # TODO: redundancey check (duplicate and body literals)

        # arithmetic terms
        rule = NormalRule(
            # due to safety, all variables in arithmetic terms occurr outside of it as well
            PredicateLiteral('p', Number(0)),
            PredicateLiteral('q', ArithVariable(0, Add(Variable('X'), Variable('Y')))),
            PredicateLiteral('q', Variable('X')),
            PredicateLiteral('q', Variable('Y'))
        )
        self.assertEqual(Grounder.ground_statement(
                rule,
                possible={PredicateLiteral('q', Number(1)), PredicateLiteral('q', Number(3)), PredicateLiteral('q', Number(5)), PredicateLiteral('q', Number(2))}
            ),
            {
                NormalRule(PredicateLiteral('p', Number(0)), PredicateLiteral('q', Number(5)), PredicateLiteral('q', Number(3)), PredicateLiteral('q', Number(2))),
                # NormalRule(PredicateLiteral('p', Number(0)), PredicateLiteral('q', Number(5)), PredicateLiteral('q', Number(2)), PredicateLiteral('q', Number(3))), (DUPLICATE)
                NormalRule(PredicateLiteral('p', Number(0)), PredicateLiteral('q', Number(3)), PredicateLiteral('q', Number(2)), PredicateLiteral('q', Number(1))),
                # NormalRule(PredicateLiteral('p', Number(0)), PredicateLiteral('q', Number(3)), PredicateLiteral('q', Number(1)), PredicateLiteral('q', Number(2))), (DUPLICATE)
                NormalRule(PredicateLiteral('p', Number(0)), PredicateLiteral('q', Number(2)), PredicateLiteral('q', Number(1)), PredicateLiteral('q', Number(1)))
            }
        )

        # TODO: aggregates

    def test_ground_component(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        # TODO

    def test_example_1(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        prog_str = r'''
        p(X) :- not q(X), u(X).  u(1). u(2).
        q(X) :- not p(X), v(X).        v(2).  v(3).

        x :- not p(1).
        y :- not q(3).
        '''

        # build & ground program
        prog = Program.from_string(prog_str)
        grounder = Grounder(prog)
        ground_prog = grounder.ground()

        # solve our ground program using clingo
        our_sat, our_models = solve_using_clingo(str(ground_prog))
        # ground & solve original program using clingo
        gringo_sat, gringo_models = solve_using_clingo(str(prog))

        self.assertTrue(our_sat == gringo_sat == True)
        self.assertEqual(len(our_models), len(gringo_models))
        self.assertEqual(our_models, gringo_models)

    def test_example_2(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        prog_str = r'''
        p(1).
        p(2).
        p(3).

        a :- #count { X: p(X) } <= 3.
        b :- #count { X: p(X) } <= 2.
        c :- not a.
        d :- not b.
        '''

        # build & ground program
        prog = Program.from_string(prog_str)
        grounder = Grounder(prog)
        ground_prog = grounder.ground()

        # solve our ground program using clingo
        our_sat, our_models = solve_using_clingo(str(ground_prog))
        # ground & solve original program using clingo
        gringo_sat, gringo_models = solve_using_clingo(str(prog))

        self.assertTrue(our_sat == gringo_sat == True)
        self.assertEqual(len(our_models), len(gringo_models))
        self.assertEqual(our_models, gringo_models)

    def test_example_3(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        prog_str = r'''
        d(1).
        d(2).
        d(3).

        p(X) :- not q(X), d(X).
        q(X) :- not p(X), d(X).

        a :- #count { X: p(X) } <= 3.
        b :- #count { X: p(X) } <= 2.
        c :- not a.
        d :- not b.
        '''

        # build & ground program
        prog = Program.from_string(prog_str)
        grounder = Grounder(prog)
        ground_prog = grounder.ground()

        # solve our ground program using clingo
        our_sat, our_models = solve_using_clingo(str(ground_prog))
        # ground & solve original program using clingo
        gringo_sat, gringo_models = solve_using_clingo(prog_str)

        self.assertTrue(our_sat == gringo_sat == True)
        self.assertEqual(len(our_models), len(gringo_models))
        self.assertEqual(our_models, gringo_models)

    def test_example_4(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        prog_str = r'''
        p(1).
        p(2).
        q(3) :- not r(3).
        r(3) :- not q(3).

        a :- #count { X: p(X) } != 1.
        b :- #count { X: p(X) } != 2.
        c :- #count { X: p(X) } != 3.
        d :- #count { X: p(X); X: q(X) } != 3.
        '''
        
        # build & ground program
        prog = Program.from_string(prog_str)
        grounder = Grounder(prog)
        ground_prog = grounder.ground()

        # solve our ground program using clingo
        our_sat, our_models = solve_using_clingo(str(ground_prog))
        # ground & solve original program using clingo
        gringo_sat, gringo_models = solve_using_clingo(prog_str)

        self.assertTrue(our_sat == gringo_sat == True)
        self.assertEqual(len(our_models), len(gringo_models))
        self.assertEqual(our_models, gringo_models)

    def test_example_5(self):

        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        prog_str = r'''
        p(a,1).
        p(b,-2).
        p(c,3).
        q(c,-4) :- not r(c,-4).
        r(c,-4) :- not q(c,-4).
        q(c,5) :- not r(c,5).
        r(c,5) :- not q(c,5).

        b(-3).
        b(-2).
        b(7).
        b(8).

        a :- #sum { W,X: p(X,W) } >= 1.
        b :- #sum { W,X: p(X,W) } >= 2.
        c :- #sum { W,X: p(X,W) } >= 3.
        d :- #sum { W,X: p(X,W) } <= 1.
        e :- #sum { W,X: p(X,W) } <= 2.
        f :- #sum { W,X: p(X,W) } <= 3.

        g(B) :- #sum { W,X: p(X,W); W,X: q(X,W) } >= B, b(B).
        h(B) :- #sum { W,X: p(X,W); W,X: q(X,W) } <= B, b(B).
        fh(B) :- b(B), not g(B).
        gh(B) :- b(B), not h(B).
        '''

        # TODO: something wrong with SUM propagation!

        # build & ground program
        prog = Program.from_string(prog_str)
        grounder = Grounder(prog)
        ground_prog = grounder.ground()

        # solve our ground program using clingo
        our_sat, our_models = solve_using_clingo(str(ground_prog))
        # ground & solve original program using clingo
        gringo_sat, gringo_models = solve_using_clingo(prog_str)

        self.assertTrue(our_sat == gringo_sat == True)
        self.assertEqual(len(our_models), len(gringo_models))
        self.assertEqual(our_models, gringo_models)

    def test_example_6(self):
    
        # make sure debug mode is enabled
        self.assertTrue(aspy.debug())

        prog_str = r'''
        p(a,1).
        p(b,-2).

        q(c,-3) :- not q(d,4).
        q(d,4) :- not q(c,-3).

        b(-5).
        b(-4).
        b(-3).
        b(-2).
        b(-1).
        b(0).
        b(1).
        b(2).
        b(3).
        b(4).

        a :- #sum { W,X: p(X,W) } = -2.
        b :- #sum { W,X: p(X,W) } = -1.
        c :- #sum { W,X: p(X,W) } = 0.

        d(B) :- #sum { W,X: p(X,W); W,X: q(X,W) } = B, b(B).
        f(B) :- b(B), not d(B).
        g(B) :- b(B), not f(B).
        '''

        # build & ground program
        prog = Program.from_string(prog_str)
        grounder = Grounder(prog)
        ground_prog = grounder.ground()

        # solve our ground program using clingo
        our_sat, our_models = solve_using_clingo(str(ground_prog))
        # ground & solve original program using clingo
        gringo_sat, gringo_models = solve_using_clingo(prog_str)

        self.assertTrue(our_sat == gringo_sat == True)
        self.assertEqual(len(our_models), len(gringo_models))
        self.assertEqual(our_models, gringo_models)


if __name__ == "__main__":
    unittest.main()