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

    def _check_and_add_overlap(self, node1, node2):
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
            if node1.node_id == 34 and node2.node_id == 18:
                print(node1.overlaps)
                input()

    def _assign_node_id_and_parent(self, c, parent):
        global global_node_id

        c.parent = parent
        c.node_id = global_node_id
        print(f"Assigned ID {c.node_id} to child of {c.parent.node_id}")
        global_node_id += 1

    def _remove_unnecessary_children(self, node):
        # WARNING MUST BE CALLED BEFORE CLEARING NODE OVERLAPS
        # Remove unnecessary children

        if node.overlaps is None:
            raise Exception(f"{node.node_id} overlaps is None")

        children_to_remove = []
        for c in node.children:
            if node.overlaps is not None:
                for o in node.overlaps:
                    if c.is_completely_inside(o[1]):
                        if c not in children_to_remove:
                            children_to_remove.append(c)

            else:
                raise Exception(
                    f"{node.node_id} has None overlaps while child tries to retrieve them"
                )

        for c in children_to_remove:
            node.children.remove(c)
            print(f"Removed {c.node_id}")

    def _set_internal_overlaps(self, node):
        # Set internal overlaps (between children)
        for c1 in node.children:
            for c2 in node.children:
                self._check_and_add_overlap(c1, c2)

    def _set_external_overlaps(self, current_node):
        for neighbour_node, neighbour_overlap in current_node.overlaps:
            for current_child in current_node.children:
                if neighbour_node.is_leaf:
                    print(
                        f"           Setting ext of {current_child.node_id} to {neighbour_node.node_id}",
                        flush=True,
                    )
                    self._check_and_add_overlap(current_child, neighbour_node)

                else:
                    print(
                        f"           Setting ext of {current_child.node_id} children of {neighbour_node.node_id}",
                        flush=True,
                    )
                    for neighbour_child in neighbour_node.children:
                        print(
                            f"               Child {neighbour_child.node_id}",
                            flush=True,
                        )
                        self._check_and_add_overlap(current_child, neighbour_child)

    def divide_node_into_children_v2(self, node_to_divide: SpaceNode, package: Package):
        if not node_to_divide.is_leaf:
            raise Exception(f"Dividing non leaf node {node_to_divide.node_id}")

        print(f" --- Dividing {node_to_divide.node_id} ---")

        package_start_corner = node_to_divide.start_corner
        packed_space = SpaceNode(package_start_corner, package.rotation)

        if packed_space.is_completely_inside(node_to_divide):
            # Get possible children
            children = node_to_divide.divide_into_subspaces(packed_space)

            print(f"    --- Assigning children to {node_to_divide.node_id} ---")
            for c in children:
                self._assign_node_id_and_parent(c, node_to_divide)

            node_to_divide.children = children
            node_to_divide.is_leaf = False

            print(f"    --- Removing children from {node_to_divide.node_id} ---")
            self._remove_unnecessary_children(node_to_divide)

            # Set internal overlaps (between current node)
            print(f"    --- Setting int_overlaps of {node_to_divide.node_id} ---")
            self._set_internal_overlaps(node_to_divide)

            crossed_over_ext_node_list = []

            for ext_node, ext_overlaps in node_to_divide.overlaps:
                package_crossed_over = packed_space.get_overlap(ext_node)
                if package_crossed_over is not None:
                    if ext_node.is_leaf:
                        ext_children = ext_node.divide_into_subspaces(
                            package_crossed_over
                        )

                        print(
                            f"        --- Assigning children to {ext_node.node_id} ---"
                        )
                        for ec in ext_children:
                            self._assign_node_id_and_parent(ec, ext_node)

                        ext_node.children = ext_children
                        ext_node.is_leaf = False

                        print(
                            f"        --- Removing children from {ext_node.node_id} ---"
                        )
                        self._remove_unnecessary_children(ext_node)

                        # Set internal overlaps (between children of ext node)
                        print(
                            f"        --- Setting int_overlaps of {ext_node.node_id} ---"
                        )
                        self._set_internal_overlaps(ext_node)

                        crossed_over_ext_node_list.append(ext_node)

            for ext_node in crossed_over_ext_node_list:
                print(f"        --- Setting ext_overlaps of {ext_node.node_id} ---")
                self._set_external_overlaps(ext_node)

            for ext_node in crossed_over_ext_node_list:
                if not ext_node.is_leaf:
                    ext_node.overlaps = None
                    print(
                        f"            Setting {ext_node.node_id} overlaps to None as it's crossed over from {node_to_divide.node_id}"
                    )
                    print(ext_node.children)

            node_to_divide.overlaps = None
            print(
                f"Setting {node_to_divide.node_id} overlaps to None as its node_to_divide"
            )
            print()
            print()

    # def divide_node_into_children(self, node_to_divide: SpaceNode, package: Package):
    #     if not node_to_divide.is_leaf:
    #         raise Exception("Dividing non leaf node")
    #
    #     package_start_corner = node_to_divide.start_corner
    #     packed_space = SpaceNode(package_start_corner, package.rotation)
    #
    #     if packed_space.is_completely_inside(node_to_divide):
    #         # Convert node to parent
    #         node_to_divide.is_leaf = False
    #
    #         # Get possible children
    #         children = node_to_divide.divide_into_subspaces(packed_space)
    #
    #         for c in children:
    #             c.parent = node_to_divide
    #             c.node_id = global_node_id
    #             global_node_id += 1
    #
    #         # Remove children who are subspaces of overlaps
    #         remaining_children = []
    #
    #         for child in children:
    #             should_keep = True
    #             for ext_node, ext_overlap in node_to_divide.overlaps:
    #                 if child.is_completely_inside(ext_overlap):
    #                     should_keep = False  # Mark to remove this child
    #                     break
    #
    #             if should_keep:
    #                 remaining_children.append(child)
    #
    #         # Set children
    #         children[:] = remaining_children
    #         node_to_divide.children = children
    #
    #         # Set internal overlaps (between children)
    #         for c1 in node_to_divide.children:
    #             for c2 in node_to_divide.children:
    #                 if not c1 == c2 and c1.get_overlap(c2) is not None:
    #                     c1.overlaps.append((c2, c1.get_overlap(c2)))
    #
    #         # External subdivide and overlap section
    #         for ext_node, ext_overlap in node_to_divide.overlaps:
    #             package_crossed_over = packed_space.get_overlap(ext_node)
    #
    #             # If packed_space crosses over to another node, tell it to subdivide
    #             if package_crossed_over is not None:
    #                 ext_children = ext_node.divide_into_subspaces(package_crossed_over)
    #
    #                 for c in ext_children:
    #                     c.parent = ext_node
    #                     c.node_id = global_node_id
    #                     global_node_id += 1
    #
    #                 # Remove children who are subspaces of overlaps
    #                 ext_remaining_children = []
    #
    #                 for ext_child in ext_children:
    #                     # WARNING LOSS OF SUBSCPACES POSSIBLE?, INFINITE LOOP POSSIBLE?
    #                     should_keep = True
    #                     for ext_ext_node, ext_ext_overlap in ext_node.overlaps:
    #                         if ext_child.is_completely_inside(ext_ext_overlap):
    #                             should_keep = False  # Mark to remove this child
    #                             break
    #
    #                         if not ext_ext_node.is_leaf:
    #                             for ext_ext_child in ext_ext_node.children:
    #                                 child_to_child_overlap = ext_child.get_overlap(
    #                                     ext_ext_child
    #                                 )
    #
    #                                 if child_to_child_overlap is not None:
    #                                     ext_child.overlaps.append(
    #                                         (ext_ext_child, child_to_child_overlap)
    #                                     )
    #                                     ext_ext_child.overlaps.append(
    #                                         (ext_child, child_to_child_overlap)
    #                                     )
    #
    #                                     ext_node.is_leaf = False
    #                     if should_keep:
    #                         ext_remaining_children.append(ext_child)
    #
    #                 # Set children
    #                 ext_children[:] = ext_remaining_children
    #                 ext_node.children = ext_children
    #
    #                 # Set internal overlaps (between children)
    #                 for c1 in ext_node.children:
    #                     for c2 in ext_node.children:
    #                         if not c1 == c2 and c1.get_overlap(c2) is not None:
    #                             c1.overlaps.append((c2, c1.get_overlap(c2)))
    #
    #             # Package does not cross over to ext_node
    #             else:
    #                 remaining_overlaps = []
    #
    #                 # Keep overlaps that do not match node_to_divide
    #                 for ov in ext_node.overlaps:
    #                     if ov[0] != node_to_divide:
    #                         remaining_overlaps.append(ov)
    #
    #                 # Update the original overlaps list
    #                 ext_node.overlaps[:] = remaining_overlaps
    #
    #                 for child in node_to_divide.children:
    #                     o = child.get_overlap(ext_node)
    #
    #                     if o is not None:
    #                         ext_node.overlaps.append((child, o))
    #                         child.overlaps.append((ext_node, o))
    #     else:
    #         raise Exception(
    #             f"Trying to pack package outside boundaries of space {package.rotation} in {node_to_divide.dimensions}"
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
        # Start-{node.start_corner}, Dimensions={node.dimensions}
        print(
            f"{indent}Node: {node.node_id}, IsLeaf={node.is_leaf}, Overlaps={len(node.overlaps) if node.overlaps is not None else None}"
        )

        for child in node.children:
            self.display_tree(child, depth + 1)
