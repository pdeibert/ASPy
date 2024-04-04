from typing import TYPE_CHECKING, List, Optional, Self, Set, Tuple, Type

from .dependency_graph import DependencyGraph
from .scc import compute_SCCs
from .topological_sort import topological_sort

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.statements import Statement


class Component:
    def __init__(
        self: Self,
        rules: Set["Statement"],
        pos_edges: Optional[Set[Tuple["Statement", "Statement"]]] = None,
        neg_edges: Optional[Set[Tuple["Statement", "Statement"]]] = None,
        stratified: bool = False,
    ) -> None:
        self.nodes = rules
        self.pos_edges = pos_edges if pos_edges is not None else set()
        self.neg_edges = neg_edges if neg_edges is not None else set()
        self.stratified = stratified

    @property
    def edges(self: Self) -> Set[Tuple["Statement", "Statement"]]:
        return self.pos_edges.union(self.neg_edges)

    def sequence(self: Self) -> List[Tuple["Statement", ...]]:
        # compute strong connected components (convert to tuples for dict hashing)
        sccs = [
            tuple(component) for component in compute_SCCs(self.nodes, self.pos_edges)
        ]

        # map rules to SCC (for sorting edges)
        rule2scc = dict()

        for node in self.nodes:
            for scc in sccs:
                if node in scc:
                    rule2scc[node] = scc

        # inter-component edges
        pos_edges = set()

        # group positive edges
        for src, dst in self.pos_edges:
            src_component = rule2scc[src]
            dst_component = rule2scc[dst]

            if src_component is not dst_component:
                pos_edges.add((src, dst))

        """Returns the refined instantiation sequence for the component."""
        # seq = topological_sort(self.nodes, self.pos_edges)
        seq = topological_sort(set(sccs), pos_edges)
        # reverse order
        seq.reverse()

        return seq


class ComponentGraph(object):
    def __new__(
        cls: Type["ComponentGraph"], rules: Set["Statement"]
    ) -> "ComponentGraph":
        # create dependency graph
        dep_graph = DependencyGraph(rules)

        # create component graph from dependency graph
        return cls.from_dependency_graph(dep_graph)

    @classmethod
    def from_dependency_graph(
        cls: Type["ComponentGraph"], dep_graph: DependencyGraph
    ) -> "ComponentGraph":
        # compute strong connected components (convert to tuples for dict hashing)
        sccs = [
            tuple(component)
            for component in compute_SCCs(dep_graph.nodes, dep_graph.edges)
        ]

        # map rules to SCC (for sorting edges)
        rule2scc = dict()

        for node in dep_graph.nodes:
            for scc in sccs:
                if node in scc:
                    rule2scc[node] = scc

        # intra-component edges
        scc_edges = {scc: (set(), set()) for scc in sccs}
        # inter-component edges
        pos_edges = set()
        neg_edges = set()

        # group positive edges
        for src, dst in dep_graph.pos_edges:
            src_component = rule2scc[src]
            dst_component = rule2scc[dst]

            if src_component is dst_component:
                scc_edges[src_component][0].add((src, dst))
            else:
                pos_edges.add((src, dst))

        # group negative edges
        for src, dst in dep_graph.neg_edges:
            src_scc = rule2scc[src]
            dst_scc = rule2scc[dst]

            if src_scc is dst_scc:
                scc_edges[src_scc][1].add((src, dst))
            else:
                neg_edges.add((src, dst))

        graph = object.__new__(cls)

        # create component instances (i.e., nodes)
        # marking components as unstratified where possible
        # (i.e., if they negatively depend on themselves)
        components = {
            Component(set(scc), *scc_edges[scc], stratified=not bool(scc_edges[scc][1]))
            for scc in sccs
        }

        # map rules to actual components
        rule2component = dict()

        for component in components:
            for rule in component.nodes:
                rule2component[rule] = component

        graph.nodes = components
        graph.pos_edges = {
            (rule2component[src], rule2component[dst]) for (src, dst) in pos_edges
        }
        graph.neg_edges = {
            (rule2component[src], rule2component[dst]) for (src, dst) in neg_edges
        }

        # indicate whether or not component are stratified
        converged = False
        # group components
        stratified_components = {
            component for component in components if component.stratified
        }
        unstratified_components = set()

        for component in components:
            (
                stratified_components
                if component.stratified
                else unstratified_components
            ).add(component)

        while not converged:
            converged = True

            for component in stratified_components.copy():
                for src_component, dst_component in graph.edges:
                    # if component depends on an unstratified component,
                    # mark it as unstratisfied
                    if (
                        src_component == component
                        and dst_component not in stratified_components
                    ):
                        component.stratified = False
                        stratified_components.remove(component)
                        converged = False

        return graph

    @property
    def edges(self: Self) -> Set[Tuple["Statement", "Statement"]]:
        return self.pos_edges.union(self.neg_edges)

    def sequence(self: Self) -> List[Component]:
        """Returns the instantiation sequence for the components."""
        seq = topological_sort(self.nodes, self.edges)
        # reverse order
        seq.reverse()

        return seq
