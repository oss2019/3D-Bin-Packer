from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerBasicOverlap import ULDPackerBasicOverlap

SIZE_BOUND = 5000


class ULDPackerMixed(ULDPackerBasicOverlap):
    """
    A class for packing packages into ULDs using a mixed packing strategy.

    This class extends the ULDPackerBasicOverlap and implements specific packing
    strategies that consider priority packages and available space in ULDs.
    """

    def __init__(
        self,
        ulds: List[ULD],
        packages: List[Package],
        priority_spread_cost: int,
        max_passes: int = 1,
    ):
        """
        Initializes the ULDPackerMixed instance.

        :param ulds: List of ULDs available for packing.
        :param packages: List of packages to be packed.
        :param priority_spread_cost: Cost associated with spreading priority packages.
        :param max_passes: Maximum number of packing passes (default is 1).
        """
        super().__init__(
            ulds,
            packages,
            priority_spread_cost,
            max_passes,
        )

    def pack(self):
        """
        Pack the packages into the ULDs.

        :return: Tuple containing packed positions, packed packages,
                    unpacked packages, priority ULDs, and total cost.
        """
        n_packs = 0

        # Calculate minimum dimension of a Package
        # Used in optimising empty space tracking
        self.minimum_dimension = min([np.min(pkg.dimensions) for pkg in self.packages])

        # Get priority packages (sort if required)
        priority_packages = sorted(
            [pkg for pkg in self.packages if pkg.is_priority],
            key=lambda p: (np.prod(p.dimensions)),
            reverse=True,
        )

        # Get economy packages (sort if required)
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority],
            key=lambda p: (
                p.delay_cost / np.prod(p.dimensions),
                1 / p.weight * np.prod(p.dimensions),
            ),
            reverse=True,
        )

        # Pack the priority packages first
        for package in priority_packages:
            packed = False
            for uld in sorted(
                self.ulds,
                key=lambda u: np.prod(u.dimensions),
                reverse=True,
            ):
                can_fit, orientation = self._try_pack_package(
                    package,
                    uld,
                    space_find_policy="first_find",
                    orientation_choose_policy="no_rot",
                )
                if can_fit:
                    packed = True
                    n_packs += 1
                    print(
                        f"Packed Priority {package.id} in {uld.id}, with orientation {tuple(orientation)}, {n_packs} "
                    )
                    break
            if not packed:
                self.unpacked_packages.append(package)
            else:
                self.packed_packages.append(package)

        # Pack the economy packages first
        for package in economy_packages[:50]:
            packed = False
            for uld in sorted(
                self.ulds,
                key=lambda u: (1 - u.current_vol_occupied / np.prod(u.dimensions)),
                reverse=False,
            ):
                can_fit, orientation = self._try_pack_package(
                    package,
                    uld,
                    space_find_policy="max_surface_area",
                    orientation_choose_policy="min_volume",
                )
                if can_fit:
                    packed = True
                    n_packs += 1
                    print(
                        f"Packed Economy {package.id} in {uld.id}, with orientation {tuple(orientation)}, {n_packs} "
                    )
                    break
            if not packed:
                self.unpacked_packages.append(package)
            else:
                self.packed_packages.append(package)

        for package in economy_packages[50:]:
            packed = False
            for uld in sorted(
                self.ulds,
                key=lambda u: (u.current_weight / u.weight_limit),
                reverse=True,
            ):
                can_fit, orientation = self._try_pack_package(
                    package,
                    uld,
                    space_find_policy="first_find",
                    orientation_choose_policy="first_find",
                )
                if can_fit:
                    packed = True
                    n_packs += 1
                    print(
                        f"Packed Economy {package.id} in {uld.id}, with orientation {tuple(orientation)}, {n_packs} "
                    )
                    break
            if not packed:
                self.unpacked_packages.append(package)
            else:
                self.packed_packages.append(package)

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