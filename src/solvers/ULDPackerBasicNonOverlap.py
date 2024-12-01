from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np

SIZE_BOUND = 10000


# Define the ULDPacker class
class ULDPacker:
    def __init__(
        self,
        ulds: List[ULD],
        packages: List[Package],
        priority_spread_cost: int,
        max_passes: int = 1,
    ):
        self.ulds = ulds
        self.packages = packages
        self.priority_spread_cost = priority_spread_cost
        self.max_passes = max_passes  # Set the max number of packing passes
        self.packed_positions = []  # [(package_id, uld_id, x, y, z)]
        self.unpacked_packages = []
        self.available_spaces = {
            u.id: [(0, 0, 0, u.dimensions[0], u.dimensions[1], u.dimensions[2])]
            for u in self.ulds
        }

    def _find_available_space(
        self, uld: ULD, package: Package, policy: str
    ) -> Tuple[bool, np.ndarray]:
        length, width, height = package.dimensions
        best_position = None
        best_idx = None
        min_x = SIZE_BOUND
        min_y = SIZE_BOUND
        min_z = SIZE_BOUND

        for idx, area in enumerate(self.available_spaces[uld.id]):
            x, y, z, al, aw, ah = area
            if length <= al and width <= aw and height <= ah:
                if policy == "first_find":
                    best_position = np.array([x, y, z])
                    best_idx = idx
                    break

                elif policy == "origin_bias":
                    # Check for the best position based on min_x, min_y, and min_z
                    if (
                        (x < min_x)
                        or (x == min_x and y < min_y)
                        or (x == min_x and y == min_y and z < min_z)
                    ):
                        min_x = x
                        min_y = y
                        min_z = z
                        best_position = np.array([x, y, z])
                        best_idx = idx

                elif policy == "min_length_sum":
                    # Check for the best position based on sum of min_x, min_y, and min_z
                    if min_x + min_y + min_z > x + y + z:
                        min_x = x
                        min_y = y
                        min_z = z
                        best_position = np.array([x, y, z])
                        best_idx = idx

                elif policy == "min_surface_area":
                    # Check for the best position based on surface area
                    if (
                        min_x * min_y + min_y * min_z + min_z * min_x
                        > x * y + y * z + z * x
                    ):
                        min_x = x
                        min_y = y
                        min_z = z
                        best_position = np.array([x, y, z])
                        best_idx = idx

        if best_position is not None:
            return True, best_position, best_idx
        return False, None, -1

    def _try_pack_package(self, package: Package, uld: ULD) -> bool:
        if package.weight + uld.current_weight > uld.weight_limit:
            return False  # Exceeds weight limit

        can_fit, position, space_index = self._find_available_space(
            uld, package, policy="min_surface_area"
        )
        if can_fit:
            x, y, z = position
            length, width, height = package.dimensions
            uld.current_weight += package.weight
            self.packed_positions.append((package.id, uld.id, x, y, z))
            self._update_available_spaces(uld, position, package, space_index)
            return True
        return False

    def _update_available_spaces(
        self, uld: ULD, position: np.ndarray, package: Package, space_index: int
    ):
        length, width, height = package.dimensions
        x, y, z = position

        ax, ay, az, al, aw, ah = self.available_spaces[uld.id][space_index]

        # 7 - cut
        # space2 = (ax + length, ay, az, al - length, width, height)
        # space3 = (ax + length, ay + width, az, al - length, aw - width, height)
        # space4 = (ax, ay + width, az, length, aw - width, height)
        # space5 = (ax, ay, az + height, length, width, ah - height)
        # space6 = (ax + length, ay, az, al - length, width, ah - height)
        # space7 = (ax + length, ay + width, az, al - length, aw - width, ah - height)
        # space8 = (ax, ay + width, az, length, aw - width, ah - height)

        # self.available_spaces[uld.id] += [space2, space3, space4, space5, space6, space7, space8]

        # 4 - cut Bias: column-verticals
        # space2 = (ax, ay, az + height, length, width, ah - height)
        # space3 = (ax + length, ay, az, al - length, width, ah)
        # space4 = (ax + length, ay + width, az, al - length, aw - width, ah)
        # space5 = (ax, ay + width, az, length, aw - width, ah)

        # self.available_spaces[uld.id] += [space2, space3, space54, space5]

        # 3 - cut Bias: front small, left horizontal full, top full
        space2 = (ax + length, ay, az, al - length, aw, height)
        space3 = (ax, ay + width, az, length, aw - width, height)
        space4 = (ax, ay, az + height, al, aw, ah - height)

        # 3 - cut Bias: left small, front horizontal full, top full
        # space2 = (ax + length, ay, az, al - length, width, height)
        # space3 = (ax, ay + width, az, ax, aw - width, height)
        # space4 = (ax, ay, az + height, al, aw, ah - height)

        # 3 - cut Bias: top small, front full, left column
        # space2 = (ax, ay, az + height, length, width, ah - height)
        # space3 = (ax + length, ay, az, al - length, aw, ah)
        # space4 = (ax, ay + width, az, length, aw - width, ah)

        # 3 - cut Bias: top small, left full, front column
        # space2 = (ax, ay, az + height, length, width, ah - height)
        # space3 = (ax + length, ay, az, al - length, width, ah)
        # space4 = (ax, ay + width, az, al, aw - width, ah)

        self.available_spaces[uld.id] += [space2, space3, space4]

        self.available_spaces[uld.id].pop(space_index)

    def pack(self):
        priority_packages = sorted(
            [pkg for pkg in self.packages if pkg.is_priority],
            key=lambda p: p.delay_cost,
            reverse=True,
        )
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority],
            key=lambda p: p.delay_cost,
            reverse=True,
        )

        # First pass - initial packing
        for package in priority_packages + economy_packages:
            packed = False
            for uld in self.ulds:
                if self._try_pack_package(package, uld):
                    packed = True
                    break
            if not packed:
                self.unpacked_packages.append(package)

        # Multi-pass strategy to optimize packing
        for pass_num in range(self.max_passes - 1):  # Exclude first pass
            # Try to repack packages into available spaces
            for package in self.unpacked_packages:
                packed = False
                for uld in self.ulds:
                    if self._try_pack_package(package, uld):
                        packed = True
                        break
                if packed:
                    self.unpacked_packages.remove(package)

        total_delay_cost = sum(pkg.delay_cost for pkg in self.unpacked_packages)
        priority_spread_cost = self.priority_spread_cost * len(
            {
                uld_id
                for _, uld_id, *_ in self.packed_positions
                if any(p.id == _ and p.is_priority for p in self.packages)
            }
        )
        total_cost = total_delay_cost + priority_spread_cost

        return self.packed_positions, self.unpacked_packages, total_cost

    def validate_packing(self) -> Tuple[bool, List[str]]:
        """Validate the packing process"""
        validation_errors = []

        # Check each ULD for validity
        for uld in self.ulds:
            # Check weight limits
            if uld.current_weight > uld.weight_limit:
                validation_errors.append(f"ULD {uld.id} exceeds weight limit!")

            # Check each packed position within the ULD
            for package_id, uld_id, x, y, z in self.packed_positions:
                if uld.id == uld_id:
                    # Retrieve the package
                    package = next(pkg for pkg in self.packages if pkg.id == package_id)
                    length, width, height = package.dimensions

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
                    ) in self.packed_positions:
                        if (other_package_id != package.id) and (
                            other_uld_id == uld_id
                        ):
                            other_package = next(
                                pkg
                                for pkg in self.packages
                                if pkg.id == other_package_id
                            )
                            other_length, other_width, other_height = (
                                other_package.dimensions
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
        for package_id, uld_id, _, _, _ in self.packed_positions:
            package = next(pkg for pkg in self.packages if pkg.id == package_id)
            if package.is_priority:
                if uld_id not in priority_count_per_uld:
                    priority_count_per_uld[uld_id] = 0
                priority_count_per_uld[uld_id] += 1
        return priority_count_per_uld
