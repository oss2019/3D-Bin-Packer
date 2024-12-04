from operator import truediv
from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerBase import ULDPackerBase
from itertools import permutations


global_node_id = 1


class SpaceNode:
    def __init__(self, start_corner: np.ndarray, dimensions: np.ndarray, parent=None):
        self.node_id = None
        self.parent = parent
        self.length = dimensions[0]
        self.width = dimensions[1]
        self.height = dimensions[2]
        self.dimensions = np.array(dimensions)
        self.start_corner = start_corner
        self.end_corner = start_corner + self.dimensions

        self.is_leaf = True

        # (which node, overlap region)
        self.overlaps: List[(SpaceNode, SpaceNode)] = []
        self.children: List[SpaceNode] = []
        self.max_vols_in_children: List[Tuple[int, float]] = []

    def get_overlap(self, other):
        # Calculate the start and end corners of the overlap
        overlap_start = np.maximum(self.start_corner, other.start_corner)
        overlap_end = np.minimum(self.end_corner, other.end_corner)

        # Check if there is an overlap
        if np.all(overlap_start < overlap_end):
            overlap_dimensions = overlap_end - overlap_start
            return SpaceNode(overlap_start, overlap_dimensions)
        else:
            # No overlap, return None or raise an exception as needed
            return None

    def is_completely_inside(self, other) -> bool:
        return np.all(self.start_corner >= other.start_corner) and np.all(
            self.end_corner <= other.end_corner
        )

    # Unused function
    # def is_shrinkable_after_placing(self, box_overlap):
    #     if (
    #         (box_overlap.length * box_overlap.width == self.length * self.width)
    #         or (box_overlap.height * box_overlap.width == self.height * self.width)
    #         or (box_overlap.height * box_overlap.length == self.height * self.length)
    #     ):
    #         return True
    #
    #     return False

    def divide_into_subspaces(self, box_overlap):
        if not box_overlap.is_completely_inside(self):
            raise Exception("Overlap box is not inside space to divide")

        updated_spaces = []
        ax, ay, az = self.start_corner
        al, aw, ah = self.dimensions

        ox, oy, oz = box_overlap.start_corner
        ol, ow, oh = box_overlap.dimensions

        # Check for remaining free areas after packing
        # Convention, stand at origin and look towards x-infty
        space1 = SpaceNode(
            start_corner=np.array([ax, oy + ow, az]),
            dimensions=np.array([al, aw - (oy + ow - ay), ah]),
        )  # Left full
        space2 = SpaceNode(
            start_corner=np.array([ax, ay, az]), dimensions=np.array([al, oy - ay, ah])
        )  # Right full
        space3 = SpaceNode(
            start_corner=np.array([ax, ay, az]), dimensions=np.array([ox - ax, aw, ah])
        )  # Back full
        # Front full
        space4 = SpaceNode(
            start_corner=np.array([ox + ol, ay, az]),
            dimensions=np.array([al - (ox + ol - ax), aw, ah]),
        )  # Front full
        space5 = SpaceNode(
            start_corner=np.array([ax, ay, az]), dimensions=np.array([al, aw, oz - az])
        )  # Above full
        # Down full
        space6 = SpaceNode(
            start_corner=np.array([ax, ay, oz + oh]),
            dimensions=np.array([al, aw, ah - (oz + oh - az)]),
        )  # Down full

        if oy + ow < ay + aw and all(v > 0 for v in space1.dimensions):
            updated_spaces.append(space1)
            # print(f"Appending {space1}")

        if oy > ay and all(v > 0 for v in space2.dimensions):
            updated_spaces.append(space2)
            # print(f"Appending {space2}")

        if ox > ax and all(v > 0 for v in space3.dimensions):
            updated_spaces.append(space3)
            # print(f"Appending {space3}")

        if ox + ol < ax + al and all(v > 0 for v in space4.dimensions):
            updated_spaces.append(space4)
            # print(f"Appending {space4}")

        if oz > az and all(v > 0 for v in space5.dimensions):
            updated_spaces.append(space5)
            # print(f"Appending {space5}")

        if oz + oh < az + ah and all(v > 0 for v in space6.dimensions):
            updated_spaces.append(space6)
            # print(f"Appending {space6}")

        return updated_spaces


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

        # if node1.overlaps is None or node2.overlaps is None:
        #     raise Exception(
        #         f"One of these nodes in completely inside a box {node1.node_id} {node1.overlaps is None} and {node2.node_id} {node2.overlaps is None}"
        #     )

        if node1 != node2:
            # raise Exception(f"Overlap detected to itself {node1.node_id}")
            overlap = node1.get_overlap(node2)
            if overlap is not None:
                node1.overlaps.append((node2, overlap))
                node2.overlaps.append((node1, overlap))
                print(f"Added overlap between {node1.node_id} - {node2.node_id}")

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

        children_to_remove = set([])
        for c in node.children:
            if node.overlaps is not None:
                for o in node.overlaps:
                    if c.is_completely_inside(o[1]):
                        children_to_remove.add(c)
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
                    self._check_and_add_overlap(current_child, neighbour_node)

                else:
                    for neighbour_child in neighbour_node.children:
                        self._check_and_add_overlap(neighbour_child, current_child)

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

    def divide_node_into_children(self, node_to_divide: SpaceNode, package: Package):
        if not node_to_divide.is_leaf:
            raise Exception("Dividing non leaf node")

        package_start_corner = node_to_divide.start_corner
        packed_space = SpaceNode(package_start_corner, package.rotation)

        if packed_space.is_completely_inside(node_to_divide):
            # Convert node to parent
            node_to_divide.is_leaf = False

            # Get possible children
            children = node_to_divide.divide_into_subspaces(packed_space)

            for c in children:
                c.parent = node_to_divide
                c.node_id = global_node_id
                global_node_id += 1

            # Remove children who are subspaces of overlaps
            remaining_children = []

            for child in children:
                should_keep = True
                for ext_node, ext_overlap in node_to_divide.overlaps:
                    if child.is_completely_inside(ext_overlap):
                        should_keep = False  # Mark to remove this child
                        break

                if should_keep:
                    remaining_children.append(child)

            # Set children
            children[:] = remaining_children
            node_to_divide.children = children

            # Set internal overlaps (between children)
            for c1 in node_to_divide.children:
                for c2 in node_to_divide.children:
                    if not c1 == c2 and c1.get_overlap(c2) is not None:
                        c1.overlaps.append((c2, c1.get_overlap(c2)))

            # External subdivide and overlap section
            for ext_node, ext_overlap in node_to_divide.overlaps:
                package_crossed_over = packed_space.get_overlap(ext_node)

                # If packed_space crosses over to another node, tell it to subdivide
                if package_crossed_over is not None:
                    ext_children = ext_node.divide_into_subspaces(package_crossed_over)

                    for c in ext_children:
                        c.parent = ext_node
                        c.node_id = global_node_id
                        global_node_id += 1

                    # Remove children who are subspaces of overlaps
                    ext_remaining_children = []

                    for ext_child in ext_children:
                        # WARNING LOSS OF SUBSCPACES POSSIBLE?, INFINITE LOOP POSSIBLE?
                        should_keep = True
                        for ext_ext_node, ext_ext_overlap in ext_node.overlaps:
                            if ext_child.is_completely_inside(ext_ext_overlap):
                                should_keep = False  # Mark to remove this child
                                break

                            if not ext_ext_node.is_leaf:
                                for ext_ext_child in ext_ext_node.children:
                                    child_to_child_overlap = ext_child.get_overlap(
                                        ext_ext_child
                                    )

                                    if child_to_child_overlap is not None:
                                        ext_child.overlaps.append(
                                            (ext_ext_child, child_to_child_overlap)
                                        )
                                        ext_ext_child.overlaps.append(
                                            (ext_child, child_to_child_overlap)
                                        )

                                        ext_node.is_leaf = False
                        if should_keep:
                            ext_remaining_children.append(ext_child)

                    # Set children
                    ext_children[:] = ext_remaining_children
                    ext_node.children = ext_children

                    # Set internal overlaps (between children)
                    for c1 in ext_node.children:
                        for c2 in ext_node.children:
                            if not c1 == c2 and c1.get_overlap(c2) is not None:
                                c1.overlaps.append((c2, c1.get_overlap(c2)))

                # Package does not cross over to ext_node
                else:
                    remaining_overlaps = []

                    # Keep overlaps that do not match node_to_divide
                    for ov in ext_node.overlaps:
                        if ov[0] != node_to_divide:
                            remaining_overlaps.append(ov)

                    # Update the original overlaps list
                    ext_node.overlaps[:] = remaining_overlaps

                    for child in node_to_divide.children:
                        o = child.get_overlap(ext_node)

                        if o is not None:
                            ext_node.overlaps.append((child, o))
                            child.overlaps.append((ext_node, o))
        else:
            raise Exception(
                f"Trying to pack package outside boundaries of space {package.rotation} in {node_to_divide.dimensions}"
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
        # Start-{node.start_corner}, Dimensions={node.dimensions}
        print(
            f"{indent}Node: {node.node_id}, IsLeaf={node.is_leaf}, Overlaps={len(node.overlaps) if node.overlaps is not None else None}"
        )

        for child in node.children:
            self.display_tree(child, depth + 1)


class ULDPackerTree(ULDPackerBase):
    def __init__(
        self,
        ulds: List[ULD],
        packages: List[Package],
        priority_spread_cost: int,
        max_passes: int = 1,
    ):
        super().__init__(
            ulds,
            packages,
            priority_spread_cost,
            max_passes,
        )
        self.unpacked_packages = []

        self.space_trees = [(SpaceTree(u), u.id) for u in ulds]

    def insert(self, package: Package):
        for st, uid in self.space_trees:
            space = st.search(package, search_policy="bfs")
            if space is not None:
                st.divide_node_into_children_v2(
                    space,
                    package,
                )
                print("-" * 50)
                print(f"{space.node_id} is for {package.id}")
                # print(space.start_corner)
                # print(space.end_corner)
                # print(package.rotation)
                print(f"Tree {uid}")
                st.display_tree()
                # input()
                return True, space.start_corner, uid
        return False, None, None

    def _find_available_space(
        self, uld: ULD, package: Package, policy: str
    ) -> Tuple[bool, np.ndarray]:
        pass

    def _update_available_spaces(
        self,
        uld: ULD,
        position: np.ndarray,
        orientation: Tuple[int],
        package: Package,
        space_index: int,
    ):
        pass

    def pack(self):
        # WARNING remove this n_packs variable its for logging
        n_packs = 0

        priority_packages = [pkg for pkg in self.packages if pkg.is_priority]
        # priority_packages = sorted(
        #     [pkg for pkg in self.packages if pkg.is_priority],
        #     key=lambda p: np.prod(p.dimensions),
        #     reverse=True,
        # )

        # WARNING Normalization not done for sorting eco_pkg
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority],
            key=lambda p: p.delay_cost / np.prod(p.dimensions),
            reverse=True,
        )

        # First pass - initial packing
        for package in priority_packages:
            packed, position, uldid = self.insert(package)
            if not packed:
                self.unpacked_packages.append(package)
            else:
                print(f"Packed Priority {package.id} in {uldid}, {n_packs}")
                self.packed_packages.append(package)
                self.packed_positions.append(
                    (
                        package.id,
                        uldid,
                        position[0],
                        position[1],
                        position[2],
                        package.rotation[0],
                        package.rotation[1],
                        package.rotation[2],
                    )
                )
                # if self.validate_packing():
                #     input()
                # else:
                #     raise ("Invalid")
                n_packs += 1

        for package in economy_packages:
            packed, position, uldid = self.insert(package)
            if not packed:
                self.unpacked_packages.append(package)
            else:
                print(f"Packed Economy {package.id} in {uldid}, {n_packs}")
                self.packed_packages.append(package)
                self.packed_positions.append(
                    (
                        package.id,
                        uldid,
                        position[0],
                        position[1],
                        position[2],
                        package.rotation[0],
                        package.rotation[1],
                        package.rotation[2],
                    )
                )
                n_packs += 1

        total_delay_cost = sum(pkg.delay_cost for pkg in self.unpacked_packages)
        priority_spread_cost = sum(
            self.priority_spread_cost for is_prio_uld in self.prio_ulds if is_prio_uld
        )
        total_cost = total_delay_cost + priority_spread_cost

        return (
            self.packed_positions,
            self.packed_packages,
            self.unpacked_packages,
            self.prio_ulds,
            total_cost,
        )


def run_bulk_insert_test_cases():
    # Initialize ULDs
    ulds = [
        ULD(id="ULD1", length=10, width=10, height=10, weight_limit=500),
        ULD(id="ULD2", length=10, width=10, height=10, weight_limit=300),
        ULD(id="ULD3", length=10, width=10, height=10, weight_limit=200),
    ]

    # Bulk test cases
    test_cases = [
        # Test case 6: Mixed batch for maximum utilization
        {
            "name": "Mixed batch for maximum utilization",
            "packages": [
                Package(
                    id=f"P{i}",
                    length=(i % 6) + 2,
                    width=(i % 5) + 2,
                    height=(i % 4) + 2,
                    weight=10,
                    is_priority=(i % 3 == 0),
                    delay_cost=6,
                )
                for i in range(1, 50)  # 50 packages of varying sizes
            ],
            "expected_unpacked": [],  # Should distribute effectively across ULDs
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Running Test Case {i}: {test['name']}")
        packer = ULDPackerTree(
            ulds=ulds,
            packages=[],
            priority_spread_cost=5,
        )

        # Sequentially insert packages
        for package in test["packages"]:
            packer.insert(package)
            for st in packer.space_trees:
                st.display_tree()
            print("-" * 40)

        # Check for unpacked packages
        unpacked_ids = [pkg.id for pkg in packer.unpacked_packages]
        passed = unpacked_ids == test["expected_unpacked"]
        print(f"Test Passed: {passed}")
        if not passed:
            print(
                f"Expected unpacked: {test['expected_unpacked']}, Got: {unpacked_ids}"
            )
        print("-" * 40)


# # Run the bulk test cases
# run_bulk_insert_test_cases()
