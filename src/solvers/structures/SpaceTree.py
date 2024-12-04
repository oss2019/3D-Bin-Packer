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
    ):
        self.uld_no = uld.id
        self.uld_dimensions = uld.dimensions
        self.root = SpaceNode(np.zeros(3), uld.dimensions)
        self.root.node_id = 0

    def _check_and_add_link(self, node1, node2):
        if not node1.is_leaf or not node2.is_leaf:
            raise Exception(
                f"Overlap detected between non-leaf nodes {node1.node_id} {node1.is_leaf} and {node2.node_id} {node2.is_leaf}"
            )

        if node1.node_id != node2.node_id:
            # raise Exception(f"Overlap detected to itself {node1.node_id}")
            overlap = node1.get_overlap(node2)
            if (node1, overlap) not in node2.overlaps and (
                node2,
                overlap,
            ) not in node1.overlaps:
                if overlap is not None:
                    node1.overlaps.append((node2, overlap))
                    node2.overlaps.append((node1, overlap))
                    print(f"Added overlap between {node1.node_id} - {node2.node_id}")

    def _unlink_B_to_A(self, nodeA, nodeB):
        new_overlap_list = []
        for o_node, ov in nodeB.overlaps:
            if o_node.node_id != nodeA.node_id:
                new_overlap_list.append((o_node, ov))

        nodeB.overlaps = new_overlap_list

    def _assign_node_id_and_parent(self, c, parent):
        global global_node_id

        c.parent = parent
        c.node_id = global_node_id
        print(f"Assigned ID {c.node_id} to child of {c.parent.node_id}")
        global_node_id += 1

    def _remove_unnecessary_children(self, node):
        if node.overlaps is None:
            raise Exception(f"{node.node_id} overlaps is None")

        if node.overlaps == []:
            return

        new_children = []
        for c in node.children:
            appended_c = False
            for n, o in node.overlaps:
                if not c.is_completely_inside(o):
                    if not appended_c:
                        new_children.append(c)
                        appended_c = True

            if not appended_c:
                print(f"Removed {c.node_id}")

        node.children = new_children

    def _set_internal_links(self, node):
        # Set internal overlaps (between children)
        for c1 in node.children:
            for c2 in node.children:
                if c1 != c2:
                    self._check_and_add_link(c1, c2)

    def _signal_neighbour_to_update_links(self, signalling_node, signalled_node):
        if signalling_node.node_id == signalled_node.node_id:
            return

        for child in signalling_node.children:
            if signalled_node.is_leaf:
                print(
                    f"{signalling_node.node_id} signalled {signalled_node.node_id} to connect to {child.node_id} "
                )
                self._check_and_add_link(child, signalled_node)
                self._unlink_B_to_A(signalled_node, signalled_node)

            else:
                raise Exception(
                    f"{signalling_node.node_id} trying to signal non leaf node {signalled_node.node_id}"
                )

    def _signal_neighbours_children_to_update_links(
        self, signalling_node, signalled_node
    ):
        if signalling_node.node_id == signalled_node.node_id:
            return

        for child_1 in signalling_node.children:
            if signalled_node.is_leaf:
                raise Exception(
                    f"{signalling_node.node_id} trying to signal leaf node {signalled_node.node_id} to update its children"
                )
            else:
                for child_2 in signalled_node.children:
                    print(
                        f"{signalling_node.node_id} signalled {signalled_node.node_id}'s child {child_2.node_id} to connect to {child_1.node_id}"
                    )
                    self._check_and_add_link(child_1, child_2)

    def divide_node_into_children_v3(self, node_to_divide: SpaceNode, package: Package):
        if not node_to_divide.is_leaf:
            raise Exception(f"Dividing non leaf node {node_to_divide.node_id}")

        print(f" --- Dividing {node_to_divide.node_id} ---")

        package_start_corner = node_to_divide.start_corner
        packed_space = SpaceNode(package_start_corner, package.rotation)

        if packed_space.is_completely_inside(node_to_divide):
            # Get possible children
            children = node_to_divide.divide_into_subspaces(packed_space)

            # print(f"    --- Assigning children to {node_to_divide.node_id} ---")
            for c in children:
                self._assign_node_id_and_parent(c, node_to_divide)

            node_to_divide.children = children
            node_to_divide.is_leaf = False

            # Set internal overlaps (between current node)
            # print(f"    --- Setting int_overlaps of {node_to_divide.node_id} ---")
            self._set_internal_links(node_to_divide)

            # print(f"    --- Removing children from {node_to_divide.node_id} ---")
            self._remove_unnecessary_children(node_to_divide)

            neighbour_list = []
            for neighbour, ov in node_to_divide.overlaps:
                if neighbour not in neighbour_list:
                    neighbour_list.append(neighbour)

            for neighbour in neighbour_list:
                self._signal_neighbour_to_update_links(node_to_divide, neighbour)
                self._unlink_B_to_A(node_to_divide, neighbour)

            crossed_over_ext_node_list = []
            not_crossed_over_ext_node_list = []

            for ext_node, ext_overlaps in node_to_divide.overlaps:
                package_crossed_over = packed_space.get_overlap(ext_node)
                if package_crossed_over is not None:
                    crossed_over_ext_node_list.append((ext_node, package_crossed_over))
                else:
                    not_crossed_over_ext_node_list.append(ext_node)

            for ext_node, package_crossed_over in crossed_over_ext_node_list:
                if ext_node.is_leaf:
                    ext_children = ext_node.divide_into_subspaces(package_crossed_over)

                    # print(f"        --- Assigning children to {ext_node.node_id} ---")
                    for ec in ext_children:
                        self._assign_node_id_and_parent(ec, ext_node)

                    ext_node.children = ext_children
                    ext_node.is_leaf = False
                    print(f"{ext_node.node_id} is now not a leaf")

                    # Set internal overlaps (between children of ext node)
                    # print(f"        --- Setting int_overlaps of {ext_node.node_id} ---")
                    self._set_internal_links(ext_node)

                    # print(f"        --- Removing children from {ext_node.node_id} ---)
                    self._remove_unnecessary_children(ext_node)

                    e_neighbour_list = []
                    for e_neighbour, e_ov in ext_node.overlaps:
                        if e_neighbour not in e_neighbour_list:
                            e_neighbour_list.append(e_neighbour)

                    for e_neighbour in e_neighbour_list:
                        if e_neighbour.is_leaf:
                            self._signal_neighbour_to_update_links(
                                ext_node, e_neighbour
                            )
                            self._unlink_B_to_A(ext_node, e_neighbour)
                        else:
                            self._signal_neighbours_children_to_update_links(
                                ext_node, e_neighbour
                            )
                            self._unlink_B_to_A(e_neighbour, ext_node)
                            self._unlink_B_to_A(ext_node, e_neighbour)

                else:
                    raise Exception(
                        f"{node_to_divide.node_id} is a neighbour of non leaf {ext_node.node_id}?"
                    )

            for ext_node in not_crossed_over_ext_node_list:
                if ext_node.is_leaf:
                    self._signal_neighbour_to_update_links(node_to_divide, ext_node)
                    self._unlink_B_to_A(node_to_divide, ext_node)
                else:
                    raise Exception(
                        f"{node_to_divide.node_id} is a neighbour of non leaf {ext_node.node_id}?"
                    )

            node_to_divide.overlaps = None
            for n, o in crossed_over_ext_node_list:
                n.overlaps = None
        else:
            raise Exception(
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

    def create_list_of_spaces(self, search_policy="bfs"):
        list_of_spaces = []
        if search_policy.lower() == "bfs":
            to_search = [self.root]
            while to_search:
                searching_node = to_search.pop(0)
                if searching_node.is_leaf:
                    list_of_spaces.append(
                        tuple(
                            list(searching_node.start_corner)
                            + list(searching_node.dimensions)
                        )
                    )

                to_search.extend(searching_node.children)
        return list_of_spaces
