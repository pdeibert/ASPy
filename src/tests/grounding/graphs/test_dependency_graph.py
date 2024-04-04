from typing import Self

import aspy
from aspy.grounding.graphs import DependencyGraph
from aspy.program import Program


class TestDependencyGraph:
    def test_dependency_graph(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # example from Example 17 in Kaminski, Schaub (2022):
        # "On the Foundations of Grounding in Answer Set Programming".
        input = r"""
        u(1).
        u(2).
        v(2).
        v(3).

        p(X) :- not q(X), u(X).
        q(X) :- not p(X), v(X).
        x :- not p(1).
        y :- not q(3).
        """

        prog = Program.from_string(input)

        assert len(prog.statements) == 8  # make sure we have no extra statements
        u1, u2, v2, v3, pX, qX, x, y = prog.statements

        # create dependency graph
        graph = DependencyGraph(prog.statements)

        # check nodes
        assert u1 in graph.nodes
        assert u2 in graph.nodes
        assert v2 in graph.nodes
        assert v3 in graph.nodes
        assert pX in graph.nodes
        assert qX in graph.nodes
        assert x in graph.nodes
        assert y in graph.nodes

        assert len(graph.nodes) == 8  # no extra nodes

        # check positive edges
        assert (pX, u1) in graph.pos_edges
        assert (pX, u2) in graph.pos_edges
        assert (qX, v2) in graph.pos_edges
        assert (qX, v3) in graph.pos_edges
        # check negative edges
        assert (pX, qX) in graph.neg_edges
        assert (qX, pX) in graph.neg_edges
        assert (x, pX) in graph.neg_edges
        assert (y, qX) in graph.neg_edges

        assert len(graph.edges) == 8  # no extra edges
