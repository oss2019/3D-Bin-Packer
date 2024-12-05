from dataclass.Package import Package
from dataclass.ULD import ULD
from .SpaceNode import SpaceNode
import numpy as np
from itertools import permutations


import builtins

# This is to disable prints
builtins.print = lambda *args, **kwargs: None
# This is to enable prints
# builtins.print = print


global_node_id = 1

nodes_to_delete = []


class SpaceTree:
    def __init__(
        self,
        uld: ULD,
    ):
        self.uld_no = uld.id
        self.uld_dimensions = uld.dimensions
        self.root = SpaceNode(np.zeros(3), uld.dimensions)
        self.root.node_id = 0
        self.unidirectional_signalling_list = {}
        self.bidirectional_signalling_list = []

    def _add_link(self, node1, node2):
        ov = node1.get_overlap(node2)

        if not (node2, ov) in node1.overlaps:
            node1.overlaps.append((node2, ov))
            print(f"Added link {node1.node_id} -> {node2.node_id}")
        if not (node1, ov) in node2.overlaps:
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
            raise Exception(f"{node.node_id} overlaps is None")

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
            print(f"Removed {c.node_id}")

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
            print(f"{node_to_divide.node_id} is now not a leaf")

            # Set internal overlaps (between current node)
            # print(f"    --- Setting int_overlaps of {node_to_divide.node_id} ---")
            self._set_internal_links(node_to_divide)

            # print(f"    --- Removing children from {node_to_divide.node_id} ---")
            # self._remove_unnecessary_children(node_to_divide)

            if node_to_divide not in self.unidirectional_signalling_list:
                self.unidirectional_signalling_list[node_to_divide] = []

            self._add_neighbours_to_signalling_list(node_to_divide)

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
                    # self._remove_unnecessary_children(ext_node)

                    if ext_node not in self.unidirectional_signalling_list:
                        self.unidirectional_signalling_list[ext_node] = []

                    self._add_neighbours_to_signalling_list(ext_node)

                else:
                    raise Exception(
                        f"{node_to_divide.node_id} is a neighbour of non leaf {ext_node.node_id}?"
                    )

            self._perform_link_updates()
        else:
            raise Exception(
                f"Package {package.id} does not fit in {node_to_divide.node_id}"
            )

    # def _check_and_add_link(self, node1, node2):
    #     if not node1.is_leaf or not node2.is_leaf:
    #         raise Exception(
    #             f"Overlap detected between non-leaf nodes {node1.node_id} {node1.is_leaf} and {node2.node_id} {node2.is_leaf}"
    #         )
    #
    #     if node1.node_id != node2.node_id:
    #         # raise Exception(f"Overlap detected to itself {node1.node_id}")
    #         overlap = node1.get_overlap(node2)
    #
    #         if (node1, overlap) not in node2.overlaps and (
    #             node2,
    #             overlap,
    #         ) not in node1.overlaps:
    #             if overlap is not None:
    #                 node1.overlaps.append((node2, overlap))
    #                 node2.overlaps.append((node1, overlap))
    #                 print(f"Linked {node1.node_id} - {node2.node_id}")

    # def _signal_neighbour_to_update_links(self, signalling_node, signalled_node):
    #     if signalling_node.node_id == signalled_node.node_id:
    #         return
    #
    #     for child in signalling_node.children:
    #         if signalled_node.is_leaf:
    #             print(
    #                 f"{signalling_node.node_id} signalled {signalled_node.node_id} to connect to {child.node_id} "
    #             )
    #             self._check_and_add_link(child, signalled_node)
    #             self._unlink_B_to_A(signalled_node, signalled_node)
    #
    #         else:
    #             raise Exception(
    #                 f"{signalling_node.node_id} trying to signal non leaf node {signalled_node.node_id}"
    #             )

    # def _signal_neighbours_children_to_update_links(
    #     self, signalling_node, signalled_node
    # ):
    #     if signalling_node.node_id == signalled_node.node_id:
    #         return
    #
    #     for child_1 in signalling_node.children:
    #         if signalled_node.is_leaf:
    #             raise Exception(
    #                 f"{signalling_node.node_id} trying to signal leaf node {signalled_node.node_id} to update its children"
    #             )
    #         else:
    #             for child_2 in signalled_node.children:
    #                 print(
    #                     f"{signalling_node.node_id} signalled {signalled_node.node_id}'s child {child_2.node_id} to connect to {child_1.node_id}"
    #                 )
    #                 self._check_and_add_link(child_1, child_2)

    # def divide_node_into_children_v3(self, node_to_divide: SpaceNode, package: Package):
    #     if not node_to_divide.is_leaf:
    #         raise Exception(f"Dividing non leaf node {node_to_divide.node_id}")
    #
    #     print(f" --- Dividing {node_to_divide.node_id} ---")
    #
    #     package_start_corner = node_to_divide.start_corner
    #     packed_space = SpaceNode(package_start_corner, package.rotation)
    #
    #     if packed_space.is_completely_inside(node_to_divide):
    #         # Get possible children
    #         children = node_to_divide.divide_into_subspaces(packed_space)
    #
    #         # print(f"    --- Assigning children to {node_to_divide.node_id} ---")
    #         for c in children:
    #             self._assign_node_id_and_parent(c, node_to_divide)
    #
    #         node_to_divide.children = children
    #         node_to_divide.is_leaf = False
    #
    #         # Set internal overlaps (between current node)
    #         # print(f"    --- Setting int_overlaps of {node_to_divide.node_id} ---")
    #         self._set_internal_links(node_to_divide)
    #
    #         # print(f"    --- Removing children from {node_to_divide.node_id} ---")
    #         self._remove_unnecessary_children(node_to_divide)
    #
    #         neighbour_list = []
    #         for neighbour, ov in node_to_divide.overlaps:
    #             if neighbour not in neighbour_list:
    #                 neighbour_list.append(neighbour)
    #
    #         for neighbour in neighbour_list:
    #             self._signal_neighbour_to_update_links(node_to_divide, neighbour)
    #             self._unlink_B_to_A(node_to_divide, neighbour)
    #
    #         crossed_over_ext_node_list = []
    #         not_crossed_over_ext_node_list = []
    #
    #         for ext_node, ext_overlaps in node_to_divide.overlaps:
    #             package_crossed_over = packed_space.get_overlap(ext_node)
    #             if package_crossed_over is not None:
    #                 crossed_over_ext_node_list.append((ext_node, package_crossed_over))
    #             else:
    #                 not_crossed_over_ext_node_list.append(ext_node)
    #
    #         for ext_node, package_crossed_over in crossed_over_ext_node_list:
    #             if ext_node.is_leaf:
    #                 ext_children = ext_node.divide_into_subspaces(package_crossed_over)
    #
    #                 # print(f"        --- Assigning children to {ext_node.node_id} ---")
    #                 for ec in ext_children:
    #                     self._assign_node_id_and_parent(ec, ext_node)
    #
    #                 ext_node.children = ext_children
    #                 ext_node.is_leaf = False
    #                 print(f"{ext_node.node_id} is now not a leaf")
    #
    #                 # Set internal overlaps (between children of ext node)
    #                 # print(f"        --- Setting int_overlaps of {ext_node.node_id} ---")
    #                 self._set_internal_links(ext_node)
    #
    #                 # print(f"        --- Removing children from {ext_node.node_id} ---)
    #                 self._remove_unnecessary_children(ext_node)
    #
    #                 e_neighbour_list = []
    #                 for e_neighbour, e_ov in ext_node.overlaps:
    #                     if e_neighbour not in e_neighbour_list:
    #                         e_neighbour_list.append(e_neighbour)
    #
    #                 for e_neighbour in e_neighbour_list:
    #                     if e_neighbour.is_leaf:
    #                         self._signal_neighbour_to_update_links(
    #                             ext_node, e_neighbour
    #                         )
    #                         self._unlink_B_to_A(ext_node, e_neighbour)
    #                     else:
    #                         self._signal_neighbours_children_to_update_links(
    #                             ext_node, e_neighbour
    #                         )
    #                         self._unlink_B_to_A(e_neighbour, ext_node)
    #                         self._unlink_B_to_A(ext_node, e_neighbour)
    #
    #             else:
    #                 raise Exception(
    #                     f"{node_to_divide.node_id} is a neighbour of non leaf {ext_node.node_id}?"
    #                 )
    #
    #         for ext_node in not_crossed_over_ext_node_list:
    #             if ext_node.is_leaf:
    #                 self._signal_neighbour_to_update_links(node_to_divide, ext_node)
    #                 self._unlink_B_to_A(node_to_divide, ext_node)
    #             else:
    #                 raise Exception(
    #                     f"{node_to_divide.node_id} is a neighbour of non leaf {ext_node.node_id}?"
    #                 )
    #
    #         node_to_divide.overlaps = None
    #         for n, o in crossed_over_ext_node_list:
    #             n.overlaps = None
    #     else:
    #         raise Exception(
    #             f"Package {package.id} does not fit in {node_to_divide.node_id}"
    #         )

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
                        raise Exception(f"{x.node_id} is completely inside {y.node_id}")
                    if y.is_completely_inside(x):
                        raise Exception(f"{y.node_id} is completely inside {x.node_id}")
        return list_of_spaces
