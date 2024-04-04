from typing import Self

import aspy
from aspy.grounding.graphs import compute_SCCs


class TestSCC:
    def test_compute_SCCs(self: Self):
        # make sure debug mode is enabled
        assert aspy.debug()

        nodes = {"A", "B", "C", "D", "E"}
        edges = {("A", "B"), ("B", "C"), ("C", "B"), ("D", "C")}
        target_SCCs = [{"A"}, {"B", "C"}, {"D"}, {"E"}]
        graph_SCCs = compute_SCCs(nodes, edges)

        assert len(target_SCCs) == len(graph_SCCs)  # no extra SCCs

        for scc in target_SCCs:
            assert scc in graph_SCCs
