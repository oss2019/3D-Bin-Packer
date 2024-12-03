from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
import itertools

import pprint

SIZE_BOUND = 5000


# Define the ULDPacker class
class ULDPackerBase:
    def __init__(
        self,
        ulds: List[ULD],
        packages: List[Package],
        priority_spread_cost: int,
        max_passes: int = 1,
    ):
        self.ulds = ulds
        self.prio_ulds = {}
        self.packages = packages
        self.priority_spread_cost = priority_spread_cost
        self.max_passes = max_passes  # Set the max number of packing passes
        self.unpacked_packages = []
        self.packed_packages = []
        self.packed_positions = []  # [(package_id, uld_id, x, y, z)]
        self.available_spaces = {
            u.id: [(0, 0, 0, u.dimensions[0], u.dimensions[1], u.dimensions[2])]
            for u in self.ulds
        }

    def _find_available_space(
        self, uld: ULD, package: Package, policy: str
    ) -> Tuple[bool, np.ndarray]:
        raise NotImplementedError("This method needs to be implemented.")

    def _update_available_spaces(
        self,
        uld: ULD,
        position: np.ndarray,
        orientation: Tuple[int],
        package: Package,
        space_index: int,
    ):
        raise NotImplementedError("This method needs to be implemented.")

    def pack(self):
        raise NotImplementedError("This method needs to be implemented.")

    def _try_pack_package(
        self, package: Package, uld: ULD, space_find_policy: str
    ) -> bool:
        if package.weight + uld.current_weight > uld.weight_limit:
            return False  # Exceeds weight limit

        # Define the package dimensions
        # package_rotations = list(itertools.permutations(package.dimensions))
        package_rotations = [package.dimensions]

        list_of_fits = []
        for orientation in package_rotations:
            can_fit, position, space_index = self._find_available_space(
                uld, package, orientation, policy=space_find_policy
            )

            list_of_fits.append((can_fit, position, orientation, space_index))

        # Find the element in list_of_fits with the minimum np.prod
        minvol = None
        best_space_index = None
        best_orientation = None
        best_position = None

        for fit in list_of_fits:
            s = self.available_spaces[uld.id]

            if minvol is None and fit[0]:
                minvol = np.prod(s[3::])
                can_fit = fit[0]
                best_position = fit[1]
                best_orientation = fit[2]
                best_space_index = fit[3]

            elif minvol is not None:
                if np.prod(s[3::]) < minvol and fit[0]:
                    minvol = np.prod(s[3::])
                    can_fit = fit[0]
                    best_position = fit[1]
                    best_orientation = fit[2]
                    best_space_index = fit[3]

        if minvol is not None:
            x, y, z = best_position

            uld.current_weight += package.weight
            uld.current_vol_occupied += np.prod(package.dimensions)

            if package.is_priority:
                self.prio_ulds[uld.id] = True

            self.packed_positions.append(
                (
                    package.id,
                    uld.id,
                    x,
                    y,
                    z,
                    best_orientation[0],
                    best_orientation[1],
                    best_orientation[2],
                )
            )
            self._update_available_spaces(
                uld, best_position, best_orientation, package, best_space_index
            )

            return True, best_orientation
        return False, (None, None, None)

    def validate_packing(self) -> Tuple[bool, List[str]]:
        """Validate the packing process"""
        validation_errors = []

        # Check each ULD for validity
        for uld in self.ulds:
            # Check weight limits
            if uld.current_weight > uld.weight_limit:
                validation_errors.append(f"ULD {uld.id} exceeds weight limit!")

            # Check each packed position within the ULD
            for (
                package_id,
                uld_id,
                x,
                y,
                z,
                length,
                width,
                height,
            ) in self.packed_positions:
                if uld.id == uld_id:
                    # Retrieve the package
                    package = next(pkg for pkg in self.packages if pkg.id == package_id)

                    # Boundary check: Ensure package fits within ULD
                    if (
                        x + length > uld.dimensions[0]
                        or y + width > uld.dimensions[1]
                        or z + height > uld.dimensions[2]
                    ):
                        validation_errors.append(
                            f"Package {package.id} in ULD {uld.id} extends beyond ULD boundaries!"
                        )

                    # Check for overlap with other packages
                    for (
                        other_package_id,
                        other_uld_id,
                        other_x,
                        other_y,
                        other_z,
                        other_length,
                        other_width,
                        other_height,
                    ) in self.packed_positions:
                        if (other_package_id != package.id) and (
                            other_uld_id == uld_id
                        ):
                            other_package = next(
                                pkg
                                for pkg in self.packages
                                if pkg.id == other_package_id
                            )

                            # Check for overlap (if packages share space)
                            if not (
                                x + length <= other_x
                                or x >= other_x + other_length
                                or y + width <= other_y
                                or y >= other_y + other_width
                                or z + height <= other_z
                                or z >= other_z + other_height
                            ):
                                validation_errors.append(
                                    f"Package {package.id} overlaps with Package {other_package.id} in ULD {uld.id}!"
                                )

        # Return validation status and any errors found
        is_valid = len(validation_errors) == 0
        return is_valid, validation_errors

    def count_priority_packages_in_uld(self):
        priority_count_per_uld = {}
        for package_id, uld_id, _, _, _, _, _, _ in self.packed_positions:
            package = next(pkg for pkg in self.packages if pkg.id == package_id)
            if package.is_priority:
                if uld_id not in priority_count_per_uld:
                    priority_count_per_uld[uld_id] = 0
                priority_count_per_uld[uld_id] += 1
        return priority_count_per_uld


# Multi-pass strategy to optimize packing
# for pass_num in range(self.max_passes - 1):  # Exclude first pass
#     # Try to repack packages into available spaces
#     for package in self.unpacked_packages:
#         packed = False
#         for uld in self.ulds:
#             if self._try_pack_package(
#                 package, uldspace_find_policy="first_find"
#             ):
#                 packed = True
#                 break
#         if packed:
#             self.unpacked_packages.remove(package)