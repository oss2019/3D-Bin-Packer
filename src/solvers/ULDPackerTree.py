from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerBase import ULDPackerBase
from .structures.SpaceTree import SpaceTree


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

        self.space_trees = [(SpaceTree(u, 40), u.id) for u in ulds]

    def insert(self, package: Package):
        for st, uid in self.space_trees:
            space = st.search(package, search_policy="bfs")
            if space is not None:
                st.divide_node_into_children_v3(
                    space,
                    package,
                )
                print(f"\n{space.node_id} is for {package.id}\n")
                print(f"Tree {uid}")
                # st.display_tree()
                print("-" * 50)
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

    def get_list_of_spaces(self, uld_id):
        for st, uid in self.space_trees:
            if uid == uld_id:
                return st.create_list_of_spaces()


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
            # for st in packer.space_trees:
            #     st.display_tree()
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
