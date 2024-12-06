from dataclass.Package import Package
from dataclass.ULD import ULD
from .SpaceNode import SpaceNode
import numpy as np
from itertools import permutations


global_node_id = 1

class SpaceTree:
    def __init__(
        self,
        uld: ULD,
        minimum_dimension: int,
    ):
        self.uld_no = uld.id
        self.uld_dimensions = uld.dimensions
        self.minimum_dimension = minimum_dimension
        self.root = SpaceNode(np.zeros(3), uld.dimensions, minimum_dimension)
        self.root.node_id = 0
        self.unidirectional_signalling_list = {}
        self.bidirectional_signalling_list = []

    def _add_link(self, node1, node2):
        ov = node1.get_overlap(node2)

        if not (node2, ov) in node1.overlaps and ov is not None:
            node1.overlaps.append((node2, ov))
            print(f"Added link {node1.node_id} -> {node2.node_id}")
        if not (node1, ov) in node2.overlaps and ov is not None:
            node2.overlaps.append((node1, ov))
            print(f"Added link {node2.node_id} -> {node1.node_id}")

    def _assign_node_id_and_parent(self, c, parent):
        global global_node_id

        c.parent = parent
        c.node_id = global_node_id
        print(f"Assigned ID {c.node_id} to child of {c.parent.node_id}")
        global_node_id += 1

    def _remove_unnecessary_children(self, node):
        if node.overlaps is None:
            raise RuntimeError(f"{node.node_id} overlaps is None")
        if node.overlaps == []:
            return

        not_children = []
        for c in node.children:
            for n, o in node.overlaps:
                if c.is_completely_inside(o):
                    not_children.append(c)
                    break

        for nc in not_children:
            node.children.remove(nc)
            print(f"Removed {nc.node_id}")

    def _set_internal_links(self, node):
        # Set internal overlaps (between children)
        for c1 in node.children:
            for c2 in node.children:
                if (
                    c1 != c2
                    and not c1.is_completely_inside(c2)
                    and not c2.is_completely_inside(c1)
                ):
                    self._add_link(c1, c2)

    def _add_neighbours_to_signalling_list(self, node):
        for neighbour, ov in node.overlaps:
            if neighbour in self.unidirectional_signalling_list:
                if node in self.unidirectional_signalling_list[neighbour]:
                    self.unidirectional_signalling_list[neighbour].remove(node)

                if (node, neighbour) not in self.bidirectional_signalling_list and (
                    neighbour,
                    node,
                ) not in self.bidirectional_signalling_list:
                    self.bidirectional_signalling_list.append((node, neighbour))
                    print(f"Signalling {node.node_id} - {neighbour.node_id} in BIDIR")

            elif neighbour not in self.unidirectional_signalling_list[node]:
                self.unidirectional_signalling_list[node].append(neighbour)
                print(f"Signalling {node.node_id} -> {neighbour.node_id} in UNIDIR")

    def _perform_link_updates(self):
        for nodeA, _nodeBs in self.unidirectional_signalling_list.items():
            for nodeB in _nodeBs:
                for nA_child in nodeA.children:
                    self._add_link(nodeB, nA_child)
                nodeB.remove_links_to(nodeA)
                nodeA.remove_links_to(nodeB)

        for nodeA, nodeB in self.bidirectional_signalling_list:
            nodeA.remove_links_to(nodeB)
            nodeB.remove_links_to(nodeA)

            for nA_child in nodeA.children:
                for nB_child in nodeB.children:
                    self._add_link(nA_child, nB_child)

        self.unidirectional_signalling_list = {}
        self.bidirectional_signalling_list = []

    def place_package_in(self, node_to_divide: SpaceNode, package: Package):
        if not node_to_divide.is_leaf:
            raise RuntimeError(f"Dividing non leaf node {node_to_divide.node_id}")

        print(f" --- Dividing {node_to_divide.node_id} ---")

        package_start_corner = node_to_divide.start_corner
        packed_space = SpaceNode(
            package_start_corner, package.rotation, self.minimum_dimension
        )
        p = packed_space.get_overlap(node_to_divide)

        if packed_space.is_completely_inside(node_to_divide):

            nodes_with_part_of_package = [(node_to_divide, p)]
            node_without_part_of_package = []

            for node, _ in node_to_divide.overlaps:
                package_crossed_over = packed_space.get_overlap(node)
                if package_crossed_over is not None:
                    nodes_with_part_of_package.append((node, package_crossed_over))
                else:
                    node_without_part_of_package.append(node)

            for node, package_crossed_over in nodes_with_part_of_package:
                if node.is_leaf:
                    children = node.divide_into_subspaces(package_crossed_over)

                    # Fragment node into smaller children
                    # print(f"        --- Assigning children to {node.node_id} ---")
                    for ec in children:
                        self._assign_node_id_and_parent(ec, node)


                    # Set children of node and set status to non-leaf
                    # print(f"{node.node_id} is now not a leaf")
                    node.children = children
                    node.is_leaf = False

                    # Remove unnecessary children of node
                    # print(f"        --- Removing children from {node.node_id} ---)
                    self._remove_unnecessary_children(node)

                    # Set internal overlaps (between children of node)
                    # print(f"        --- Setting int_overlaps of {node.node_id} ---")
                    self._set_internal_links(node)

                    # Initialize signalling list
                    if node not in self.unidirectional_signalling_list:
                        self.unidirectional_signalling_list[node] = []

                    # Populate signalling list with neighbours
                    self._add_neighbours_to_signalling_list(node)

                else:
                    raise RuntimeError(
                        f"{node_to_divide.node_id} is a neighbour of non leaf {node.node_id}?"
                    )

            # Perform the link updates from node to node
            self._perform_link_updates()
        else:
            raise RuntimeError(
                f"Package {package.id} does not fit in {node_to_divide.node_id}"
            )

    def search(self, package: Package, search_policy="bfs"):
        volume = np.prod(package.rotation)

        if search_policy.lower() == "bfs":
            to_search = [self.root]
            while to_search:
                searching_node = to_search.pop(0)
                if searching_node.is_leaf:
                    if np.prod(searching_node.dimensions) >= volume:
                        for rot in permutations(package.dimensions):
                            if (
                                (
                                    searching_node.start_corner[0] + rot[0]
                                    <= searching_node.end_corner[0]
                                )
                                and (
                                    searching_node.start_corner[1] + rot[1]
                                    <= searching_node.end_corner[1]
                                )
                                and (
                                    searching_node.start_corner[2] + rot[2]
                                    <= searching_node.end_corner[2]
                                )
                            ):
                                package.rotation = rot
                                return searching_node

                to_search.extend(searching_node.children)
        return None

    def display_tree(self, node=None, depth=0):
        """
        Display the space tree, including overlaps, for debugging purposes.
        """
        if node is None:
            node = self.root

        indent = "  " * depth

        print(
            f"{indent}Node: {node.node_id}, Start={node.start_corner}, Dimensions={node.dimensions}\n{indent}IsLeaf={node.is_leaf}, Overlaps={len(node.overlaps) if node.overlaps is not None else None}"
        )

        for child in node.children:
            self.display_tree(child, depth + 1)

    def create_list_of_spaces(self, search_policy="dfs"):
        list_of_spaces = []
        l_o_n = []

        if search_policy.lower() == "bfs":
            # Breadth-First Search
            to_search = [self.root]
            while to_search:
                searching_node = to_search.pop(0)  # Dequeue
                if searching_node.is_leaf:
                    list_of_spaces.append(
                        tuple(
                            list(searching_node.start_corner)
                            + list(searching_node.dimensions)
                        )
                    )
                    l_o_n.append(searching_node)
                to_search.extend(searching_node.children)  # Enqueue children

        elif search_policy.lower() == "dfs":
            # Depth-First Search
            to_search = [self.root]
            while to_search:
                searching_node = to_search.pop()  # Pop from the end (stack behavior)
                if searching_node.is_leaf:
                    list_of_spaces.append(
                        tuple(
                            list(searching_node.start_corner)
                            + list(searching_node.dimensions)
                        )
                    )
                    l_o_n.append(searching_node)
                to_search.extend(
                    searching_node.children
                )  # Push children onto the stack

        for x in l_o_n:
            for y in l_o_n:
                if x != y:
                    if x.is_completely_inside(y):
                        raise RuntimeError(f"{x.node_id} is completely inside {y.node_id}")
                    if y.is_completely_inside(x):
                        raise RuntimeError(f"{y.node_id} is completely inside {x.node_id}")
        return list_of_spaces
