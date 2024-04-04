from collections import defaultdict
from typing import Hashable, List, Set, Tuple


def topological_sort(
    nodes: Set[Hashable], edges: Set[Tuple[Hashable, Hashable]]
) -> List[Hashable]:
    """Implements Kahns's algorithm for topological sorting.

    See Kahn (1962): "Topological sorting of large networks" for details.
    """

    # number of incoming edges per node
    in_degrees = defaultdict(int)
    # maps nodes to children
    child_dict = defaultdict(list)

    for src, dst in edges:
        # increment in-degree
        in_degrees[dst] += 1

        # add 'dst' as child of 'src'
        child_dict[src].append(dst)

    # initialize queue with root nodes (i.e., nodes without any incoming edges)
    queue = [node for node in nodes if in_degrees[node] == 0]

    # number of visited nodes
    count = 0

    # topological sequence of nodes
    sequence = []

    while queue:
        # select node from queue and add it to sequence
        node = queue.pop()
        sequence.append(node)

        # iterate over children
        for child in child_dict[node]:
            # decrement in-degree of child
            in_degrees[child] -= 1

            # add child to queue for processing all parents have been processed
            if in_degrees[child] == 0:
                queue.append(child)

        # increase node counter
        count += 1

    # check if graph has a cycle
    if count != len(nodes):
        raise ValueError("Graph cannot be topolically sorted.")

    return sequence
