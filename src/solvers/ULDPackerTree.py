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
        self.space_trees = [(SpaceTree(u, 40), u.id, u) for u in ulds]

    def insert(self, package: Package):
        """
        Insert a package into the appropriate space tree.

        :param package: Package to be inserted.
        :return: Tuple indicating success, position, and ULD ID.
        """

        self.space_trees.sort(key = lambda s: (self.prio_ulds[s[2].id],
                                               -np.prod(s[2].dimensions)))
        for st, uid, u in self.space_trees:
            space = st.search(package, search_policy="bfs")
            if space is not None:
                st.place_package_in(
                    space,
                    package,
                )
                print(f"\n{space.node_id} is for {package.id}\n")
                print(f"Tree {uid}")

                # # Use for debugging
                # st.display_tree()
                # print("-" * 50)
                # input()

                if package.is_priority:
                    self.prio_ulds[uid] = True
                u.current_weight += package.weight
                u.current_vol_occupied += np.prod(package.dimensions)

                return True, space.start_corner, uid
        return False, None, None

    def _find_available_space(
        self, uld: ULD, package: Package, policy: str
    ) -> Tuple[bool, np.ndarray]:
        """
        Find available space for a package in a ULD.

        :param uld: ULD to search in.
        :param package: Package to find space for.
        :param policy: Search policy to use.
        :return: Tuple indicating success and position.
        """
        pass

    def _update_available_spaces(
        self,
        uld: ULD,
        position: np.ndarray,
        orientation: Tuple[int],
        package: Package,
        space_index: int,
    ):
        """
        Update available spaces after placing a package.

        :param uld: ULD being updated.
        :param position: Position of the package.
        :param orientation: Orientation of the package.
        :param package: Package being placed.
        :param space_index: Index of the space being updated.
        """
        pass

    def pack(self):
        """
        Pack the packages into the ULDs.

        :return: Tuple containing packed positions, packed packages, unpacked packages, priority ULDs, and total cost.
        """
        n_packs = 1

        # Get priority packages (sort if required)
        priority_packages = [pkg for pkg in self.packages if pkg.is_priority]

        # Get economy packages (sort if required)
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority],
            key=lambda p: p.delay_cost / np.prod(p.dimensions),
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
        """
        Retrieve a list of available spaces in a specific ULD.

        :param uld_id: ID of the ULD to retrieve spaces from.
        :return: List of available spaces.
        """
        for st, uid in self.space_trees:
            if uid == uld_id:
                return st.create_list_of_spaces()
