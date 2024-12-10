from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerBase import ULDPackerBase
from .structures.SpaceTree import SpaceTree
import copy

class ULDPackerTree(ULDPackerBase):
    def __init__(
        self,
        ulds: List[ULD],
        packages: List[Package],
        priority_spread_cost: int,
        max_passes: int = 1,
    ):
        """
        Initialize the ULDPackerTree.

        :param ulds: List of ULDs.
        :param packages: List of packages to be packed.
        :param priority_spread_cost: Cost associated with priority spread.
        :param max_passes: Maximum number of packing passes.
        """
        super().__init__(
            ulds,
            packages,
            priority_spread_cost,
            max_passes,
        )
        self.unpacked_packages = []
        self.prio_ulds = {}
        self.space_trees = None

    def insert(self, package: Package):
        """
        Insert a package into the appropriate space tree.

        :param package: Package to be inserted.
        :return: Tuple indicating success, position, and ULD ID.
        """

        for st, u in self.space_trees:
            space = st.search(package, search_policy="dfs", space_choose_policy="side_diff_vol_combo")
            if space is not None:
                st.place_package_in(
                    space,
                    package,
                )
                print(f"\n{space.node_id} is for {package.id}\n")
                print(f"Tree {u.id}")

                # # Use for debugging
                # st.display_tree()
                # print("-" * 50)
                # input()

                if package.is_priority:
                    self.prio_ulds[u.id] = True
                u.current_weight += package.weight
                u.current_vol_occupied += package.volume

                return True, space.start_corner, u.id
        return False, None, None

    def pack(self):
        """
        Pack the packages into the ULDs.

        :return: Tuple containing packed positions, packed packages, unpacked packages, priority ULDs, and total cost.
        """
        self.minimum_dimension = min([np.min(pkg.dimensions) for pkg in self.packages])
        self.space_trees = [(SpaceTree(u, self.minimum_dimension), u) for u in self.ulds]
        self.space_trees.sort(key = lambda t: np.prod(t[1].dimensions), reverse = True)

        n_packs = 1

        # Get priority packages (sort if required)
        # priority_packages = [pkg for pkg in self.packages if pkg.is_priority]
        priority_packages = sorted(
            [pkg for pkg in self.packages if pkg.is_priority],
            key=lambda p: (p.volume),
            reverse=True,
        )

        # Get economy packages (sort if required)
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority],
            key=lambda p: p.delay_cost / p.volume,
            reverse=True,
        )

        # Pack the priority packages first
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

        # Pack the economy packages next
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

        # Calculate some statistics to print
        total_delay_cost = sum(pkg.delay_cost for pkg in self.unpacked_packages)
        priority_spread_cost = sum(
            [self.priority_spread_cost if is_prio_uld else 0 for is_prio_uld in self.prio_ulds.values()]
        )
        total_cost = total_delay_cost + priority_spread_cost

        n_links = [st.n_links for st, u in self.space_trees]
        num_links = np.sum(n_links)
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.info(f"NUM_LINK: {num_links}, {n_links}")

        return (
            self.packed_positions,
            self.packed_packages,
            self.unpacked_packages,
            self.prio_ulds,
            total_cost,
        )

    def get_list_of_spaces(self, uld_id):
        """
        Retrieve a list of available spaces in a specific ULD.

        :param uld_id: ID of the ULD to retrieve spaces from.
        :return: List of available spaces.
        """
        for st, uid in self.space_trees:
            if uid == uld_id:
                return st.create_list_of_spaces()
