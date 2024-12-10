from dataclass.Package import Package
from dataclass.ULD import ULD
from .SpaceNode import SpaceNode
import numpy as np
from itertools import permutations

global_node_id = 0

class SpaceTree:
    """
    Represents a hierarchical tree structure for managing spatial divisions within a container.
    """

    def __init__(self, uld: ULD, minimum_dimension: int):
        """
        Initializes the SpaceTree.

        :param uld: The ULD (Unit Load Device) associated with the space tree.
        :param minimum_dimension: The smallest allowable dimension for subdivisions.
        """
        self.uld_no = uld.id
        self.uld_dimensions = uld.dimensions
        self.minimum_dimension = minimum_dimension
        self.root = SpaceNode(np.zeros(3), uld.dimensions, minimum_dimension)
        self.root.node_id = 0
        self.unidirectional_signalling_list = {}
        self.bidirectional_signalling_list = []
        self.n_links = 0

    def _add_link(self, node1: SpaceNode, node2: SpaceNode):
        """
        Adds a link between two nodes if they overlap.

        :param node1: The first node.
        :param node2: The second node.
        """
        overlap = node1.get_overlap(node2)
        if overlap is not None:
            if (node2, overlap) not in node1.overlaps:
                node1.overlaps.append((node2, overlap))
                print(f"Added link {node1.node_id} -> {node2.node_id}")
                self.n_links += 1

            if (node1, overlap) not in node2.overlaps:
                node2.overlaps.append((node1, overlap))
                print(f"Added link {node2.node_id} -> {node1.node_id}")
                self.n_links += 1


    def _assign_node_id_and_parent(self, child: SpaceNode, parent: SpaceNode):
        """
        Assigns a unique ID to a node and sets its parent.

        :param child: The child node to update.
        :param parent: The parent node.
        """
        global global_node_id
        child.parent = parent
        child.node_id = global_node_id
        print(f"Assigned ID {child.node_id} to child of {child.parent.node_id}")
        global_node_id += 1

    def _remove_unnecessary_children(self, node: SpaceNode):
        """
        Removes child nodes that are completely covered by other overlaps.

        :param node: The node whose children are to be evaluated.
        """
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

        for not_child in not_children:
            node.children.remove(not_child)
            print(f"Removed {not_child.node_id}")

    def _set_internal_links(self, node: SpaceNode):
        """
        Establishes links between the children of a node based on overlaps.

        :param node: The parent node.
        """
        for c1 in node.children:
            for c2 in node.children:
                if c1 != c2 and not c1.is_completely_inside(c2) and not c2.is_completely_inside(c1):
                    self._add_link(c1, c2)

    def _add_neighbours_to_signalling_list(self, node: SpaceNode):
        """
        Updates signalling lists with neighboring nodes based on overlaps.

        :param node: The node to process.
        """
        for neighbour, overlap in node.overlaps:
            if neighbour in self.unidirectional_signalling_list:
                if node in self.unidirectional_signalling_list[neighbour]:
                    self.unidirectional_signalling_list[neighbour].remove(node)

                if (node, neighbour) not in self.bidirectional_signalling_list and \
                   (neighbour, node) not in self.bidirectional_signalling_list:
                    self.bidirectional_signalling_list.append((node, neighbour))
                    print(f"Signalling {node.node_id} - {neighbour.node_id} in BIDIR")
            elif neighbour not in self.unidirectional_signalling_list[node]:
                self.unidirectional_signalling_list[node].append(neighbour)
                print(f"Signalling {node.node_id} -> {neighbour.node_id} in UNIDIR")

    def _perform_link_updates(self):
        """
        Performs updates to links based on the signalling lists.
        """
        for nodeA, nodeBs in self.unidirectional_signalling_list.items():
            for nodeB in nodeBs:
                for child in nodeA.children:
                    self._add_link(nodeB, child)
                nodeB.remove_links_to(nodeA)
                nodeA.remove_links_to(nodeB)
                self.n_links += 2

        for nodeA, nodeB in self.bidirectional_signalling_list:
            nodeA.remove_links_to(nodeB)
            nodeB.remove_links_to(nodeA)
            self.n_links += 2
            for childA in nodeA.children:
                for childB in nodeB.children:
                    self._add_link(childA, childB)

        self.unidirectional_signalling_list = {}
        self.bidirectional_signalling_list = []

    def place_package_in(self, node_to_divide: SpaceNode, package: Package, remove_unnecessary = True):
        """
        Places a package within the specified node by dividing the node.

        :param node: The node to divide.
        :param package: The package to place.
        """
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
                    if remove_unnecessary:
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

    def search_for(self, node_to_search: SpaceNode, search_policy: str = "bfs") -> SpaceNode:
        """
        Searches for a given node in the tree.

        :param node_to_search: Space Node to search for.
        :param search_policy: The search policy ('bfs' or 'dfs').
        :return: The node where the package can be placed, or None.
        """
        if search_policy.lower() == "bfs":
            to_search = [self.root]
            while to_search:
                searching_node = to_search.pop(0)
                if (
                    (searching_node.start_corner ==  node_to_search.start_corner).all() and
                    searching_node.is_completely_inside(node_to_search)
                ):
                    return searching_node

                to_search.extend(searching_node.children)

            # raise Exception(f"Not found {node_to_search.start_corner, node_to_search.dimensions}")
        else:
            raise RuntimeError("Invalid Search Policy")

        return None

    def search(self, package: Package,
               search_policy: str = "bfs",
               space_choose_policy: str = "first_find") -> SpaceNode:
        """
        Searches for a suitable node to place the package.

        :param package: The package to place.
        :param search_policy: The search policy ('bfs', 'dfs').
        :param space_choose_policy: The space choosing policy ('first_find', 'min_volume').
        :return: The node where the package can be placed, or None.
        """
        if search_policy.lower() == "bfs":
            to_search = [self.root]
            best_node = None
            best_diff = np.inf

            while to_search:
                searching_node = to_search.pop(0)
                if np.prod(searching_node.dimensions) < package.volume:
                    continue
                if searching_node.is_leaf:
                    if np.prod(searching_node.dimensions) >= package.volume:
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
                                if space_choose_policy == "first_find":
                                    package.rotation = rot
                                    return searching_node
                                elif space_choose_policy == "min_volume":
                                    if best_node is None or np.prod(searching_node.dimensions) < np.prod(best_node.dimensions):
                                        package.rotation = rot
                                        best_node = searching_node
                                elif space_choose_policy == "least_diff_in_sides":
                                    diff = np.sum(searching_node.dimensions - rot)
                                    if best_node is None or diff < best_diff:
                                        package.rotation = rot
                                        best_node = searching_node
                                        best_diff = diff
                                else:
                                    raise RuntimeError(f"Invalid space choose policy {space_choose_policy}")

                to_search.extend(searching_node.children)

            return best_node

        elif search_policy.lower() == "dfs":
            stack = [self.root]
            best_node = None
            best_diff = np.inf
            best_score = np.inf

            while stack:
                searching_node = stack.pop()
                if np.prod(searching_node.dimensions) < package.volume:
                    continue
                if searching_node.is_leaf:
                    if np.prod(searching_node.dimensions) >= package.volume:
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
                                if space_choose_policy == "first_find":
                                    package.rotation = rot
                                    return searching_node
                                elif space_choose_policy == "min_volume":
                                    if best_node is None or np.prod(searching_node.dimensions) < np.prod(best_node.dimensions):
                                        package.rotation = rot
                                        best_node = searching_node
                                elif space_choose_policy == "least_diff_in_sides":
                                    diff = np.sum(searching_node.dimensions - rot)
                                    if best_node is None or diff < best_diff:
                                        package.rotation = rot
                                        best_node = searching_node
                                        best_diff = diff
                                elif space_choose_policy == "side_diff_vol_combo":
                                    score = (np.sum(searching_node.dimensions - rot) +
                                            np.prod(searching_node.dimensions) - package.volume)
                                    if best_node is None or score < best_score:
                                        package.rotation = rot
                                        best_node = searching_node
                                        best_score = score
                                else:
                                    raise RuntimeError(f"Invalid space choose policy {space_choose_policy}")

                # Add children to the stack in reverse order to maintain the correct order of processing
                stack.extend(reversed(searching_node.children))

            return best_node
        else:
            raise RuntimeError(f"Invalid search policy {search_policy}")

        return None