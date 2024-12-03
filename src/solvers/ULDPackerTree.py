from operator import truediv
from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerBase import ULDPackerBase
from itertools import permutations


class SpaceNode:
    def __init__(self, start_corner: np.ndarray, dimensions: np.ndarray, parent=None):
        self.parent = parent
        self.length = dimensions[0]
        self.width = dimensions[1]
        self.height = dimensions[2]
        self.dimensions = np.array(dimensions)
        self.start_corner = start_corner
        self.end_corner = start_corner + self.dimensions

        self.is_leaf = True

        self.overlaps: List[(SpaceNode, SpaceNode)] = []  # (which node, overlap region)
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
        self.root = SpaceNode(np.zeros(3), uld.dimensions)

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

            for ext_node, ext_overlap in node_to_divide.overlaps:
                package_crossed_over = packed_space.get_overlap(ext_node)

                # If packed_space crosses over to another node, tell it to subdivide
                if package_crossed_over is not None:
                    ext_children = ext_node.divide_into_subspaces(package_crossed_over)

                    for c in ext_children:
                        c.parent = ext_node

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
                                            ext_ext_child, child_to_child_overlap
                                        )
                                        ext_ext_child.overlaps.append(
                                            ext_child, child_to_child_overlap
                                        )

                                        ext_node.is_leaf = False
                        if should_keep:
                            ext_remaining_children.append(ext_child)

                    # Set children
                    ext_children[:] = ext_remaining_children
                    ext_node.children = ext_children

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
                            child.overlaps.append((child, o))

            # # For each child, update overlaps with external spaces
            # for child in node_to_divide.children:
            #     for ext_node, ext_overlap in node_to_divide.overlaps:
            #         new_overlap = child.get_overlap(ext_node)
            #         child.overlaps.append((ext_node, new_overlap))
            # # For each old external spaces, update overlaps with children
            # for ext_node, ext_overlap in node_to_divide.overlaps:
            #     # for a in ext_node:
            #     new_overlap = child.get_overlap(ext_node)
            #     child.overlaps.append((ext_node, new_overlap))
        else:
            raise Exception(
                f"Trying to pack package outside boundaries of space {package.rotation} in {node_to_divide.dimensions}"
            )

    def search(self, package: Package, search_policy="bfs"):
        volume = np.prod(package.rotation)

        if search_policy.lower() == "bfs":
            best_fit_vol = np.inf
            best_fit_node = None

            to_search = [self.root]
            while to_search:
                searching_node = to_search.pop(0)
                if searching_node.is_leaf:
                    if (np.prod(searching_node.dimensions) - volume >= 0) and (
                        np.prod(searching_node.dimensions) < best_fit_vol
                    ):
                        for rot in permutations(package.dimensions):
                            if (
                                rot[0] <= searching_node.dimensions[0]
                                and rot[1] <= searching_node.dimensions[1]
                                and rot[2] <= searching_node.dimensions[2]
                            ):
                                best_fit_vol = np.prod(searching_node.dimensions)
                                best_fit_node = searching_node
                                package.rotation = rot
                                break
                to_search.extend(searching_node.children)
            return best_fit_node
        return None

    def display_tree(self, node=None, depth=0):
        """
        Display the space tree, including overlaps, for debugging purposes.
        """
        if node is None:
            node = self.root

        indent = "  " * depth
        print(f"{indent}Node: Start={node.start_corner}, Dimensions={node.dimensions}")

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
                st.divide_node_into_children(space, package)
                print("-" * 50)
                print(f"Tree {uid}")
                # st.display_tree()
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
        # WARNING remove this n_packs vairable its for logging
        n_packs = 0

        priority_packages = sorted(
            [pkg for pkg in self.packages if pkg.is_priority],
            key=lambda p: np.prod(p.dimensions),
            reverse=True,
        )

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
