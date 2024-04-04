from typing import Self

import aspy
from aspy.grounding.graphs.component_graph import ComponentGraph
from aspy.program import Program


class TestComponentGraph:
    def test_component_graph(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        # example modified from Example 17 in Kaminski, Schaub (2022):
        # "On the Foundations of Grounding in Answer Set Programming".
        input = r"""
        u(1).
        u(2).
        v(2).
        v(3).

        p(X) :- not q(X), u(X).
        q(X) :- p(X), v(X). % modified to check refined component sequence
        x :- not p(1).
        y :- not q(3).
        """

        prog = Program.from_string(input)

        assert len(prog.statements) == 8  # make sure we have no extra statements
        u1, u2, v2, v3, pX, qX, x, y = prog.statements

        # create component graph
        graph = ComponentGraph(prog.statements)

        # check components (both component nodes as well as intra-component edges)
        assert len(graph.nodes) == 7  # no extra components

        u1_comp = [
            component for component in graph.nodes if component.nodes == {u1}
        ].pop()
        assert (
            u1_comp.nodes == {u1}
            and len(u1_comp.pos_edges) == len(u1_comp.neg_edges) == 0
        )
        assert u1_comp.stratified

        u2_comp = [
            component for component in graph.nodes if component.nodes == {u2}
        ].pop()
        assert (
            u2_comp.nodes == {u2}
            and len(u2_comp.pos_edges) == len(u2_comp.neg_edges) == 0
        )
        assert u2_comp.stratified

        v2_comp = [
            component for component in graph.nodes if component.nodes == {v2}
        ].pop()
        assert (
            v2_comp.nodes == {v2}
            and len(v2_comp.pos_edges) == len(v2_comp.neg_edges) == 0
        )
        assert v2_comp.stratified

        v3_comp = [
            component for component in graph.nodes if component.nodes == {v3}
        ].pop()
        assert (
            v3_comp.nodes == {v3}
            and len(v3_comp.pos_edges) == len(v3_comp.neg_edges) == 0
        )
        assert v3_comp.stratified

        pX_qX_comp = [
            component for component in graph.nodes if component.nodes == {pX, qX}
        ].pop()
        assert (
            pX_qX_comp.nodes == {pX, qX}
            and pX_qX_comp.pos_edges == {(qX, pX)}
            and pX_qX_comp.neg_edges == {(pX, qX)}
            and pX_qX_comp.edges == {(qX, pX), (pX, qX)}
        )
        assert not pX_qX_comp.stratified

        x_comp = [
            component for component in graph.nodes if component.nodes == {x}
        ].pop()
        assert (
            x_comp.nodes == {x} and len(x_comp.pos_edges) == len(x_comp.neg_edges) == 0
        )
        assert not x_comp.stratified

        y_comp = [
            component for component in graph.nodes if component.nodes == {y}
        ].pop()
        assert (
            y_comp.nodes == {y} and len(y_comp.pos_edges) == len(y_comp.neg_edges) == 0
        )
        assert not y_comp.stratified

        # check inter-component edges
        assert len(graph.edges) == 6  # no extra edges
        assert (pX_qX_comp, u1_comp) in graph.pos_edges
        assert (pX_qX_comp, u2_comp) in graph.pos_edges
        assert (pX_qX_comp, v2_comp) in graph.pos_edges
        assert (pX_qX_comp, v3_comp) in graph.pos_edges
        assert (x_comp, pX_qX_comp) in graph.neg_edges
        assert (y_comp, pX_qX_comp) in graph.neg_edges
        assert graph.edges == {
            (pX_qX_comp, u1_comp),
            (pX_qX_comp, u2_comp),
            (pX_qX_comp, v2_comp),
            (pX_qX_comp, v3_comp),
            (x_comp, pX_qX_comp),
            (y_comp, pX_qX_comp),
        }

        # check instantiation sequence
        inst_sequence = graph.sequence()
        assert set(inst_sequence[:4]) == {u1_comp, u2_comp, v2_comp, v3_comp}
        assert inst_sequence[4] == pX_qX_comp
        assert set(inst_sequence[5:]) == {x_comp, y_comp}

        # check refined rule sequence for components
        assert u1_comp.sequence() == [(u1,)]
        assert u2_comp.sequence() == [(u2,)]
        assert v2_comp.sequence() == [(v2,)]
        assert v3_comp.sequence() == [(v3,)]
        assert set(pX_qX_comp.sequence()) == {(pX,), (qX,)}
        assert x_comp.sequence() == [(x,)]
        assert y_comp.sequence() == [(y,)]
