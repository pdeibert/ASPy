import pytest  # type: ignore

import aspy
from aspy.grounding.graphs import topological_sort


class TestSCC:
    def test_topological_sort_acyclic(self):
        # make sure debug mode is enabled
        assert aspy.debug()

        nodes = {"A", "B", "C", "D", "E"}
        edges = {("A", "C"), ("B", "C"), ("B", "E"), ("C", "D")}

        sequence = topological_sort(nodes, edges)
        valid_sequences = [
            ["A", "B", "C", "D", "E"],
            ["A", "B", "E", "C", "D"],
            ["B", "E", "A", "C", "D"],
        ]

        assert sequence in valid_sequences

    def test_topological_sort_cyclic(self):
        # make sure debug mode is enabled
        assert aspy.debug()

        nodes = {"A", "B", "C", "D", "E"}
        edges = {("A", "C"), ("B", "C"), ("C", "D"), ("C", "E"), ("E", "B")}

        with pytest.raises(ValueError):
            topological_sort(nodes, edges)
