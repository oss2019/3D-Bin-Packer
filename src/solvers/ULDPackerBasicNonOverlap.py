from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerBase import ULDPackerBase


SIZE_BOUND = 5000


# Define the ULDPacker class
class ULDPackerBasicNonOverlap(ULDPackerBase):
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

    def _find_available_space(
        self, uld: ULD, package: Package, orientation: Tuple[int], policy: str
    ) -> Tuple[bool, np.ndarray]:
        length, width, height = package.dimensions
        best_position = None
        best_idx = None
        if policy != "max_surface_area" and policy != "max_volume":
            best_x = SIZE_BOUND
            best_y = SIZE_BOUND
            best_z = SIZE_BOUND

            best_surface_area = SIZE_BOUND**2
            best_volume = SIZE_BOUND**3
        else:
            best_x = 0
            best_y = 0
            best_z = 0

            best_surface_area = 0
            best_volume = 0

        for idx, area in enumerate(self.available_spaces[uld.id]):
            x, y, z, al, aw, ah = area
            if length <= al and width <= aw and height <= ah:
                if policy == "first_find":
                    best_position = np.array([x, y, z])
                    best_idx = idx
                    break

                elif policy == "origin_bias":
                    # Check for the best position based on best_x, best_y, and best_z
                    if (
                        (x < best_x)
                        or (x == best_x and y < best_y)
                        or (x == best_x and y == best_y and z < best_z)
                    ):
                        best_x = x
                        best_y = y
                        best_z = z
                        best_position = np.array([x, y, z])
                        best_idx = idx

                elif policy == "min_length_sum":
                    # Check for the best position based on sum of best_x, best_y, and best_z
                    if best_x + best_y + best_z > x + y + z:
                        best_x = x
                        best_y = y
                        best_z = z
                        best_position = np.array([x, y, z])
                        best_idx = idx

                elif policy == "min_surface_area":
                    # Check for the best position based on surface area
                    if best_surface_area > al * aw + aw + ah + ah * al:
                        best_surface_area = al * aw + aw + ah + ah * al
                        best_position = np.array([x, y, z])
                        best_idx = idx

                elif policy == "max_surface_area":
                    # Check for the best position based on surface area
                    if best_surface_area < al * aw + aw + ah + ah * al:
                        best_surface_area = al * aw + aw + ah + ah * al
                        best_position = np.array([x, y, z])
                        best_idx = idx

                elif policy == "min_volume":
                    # Check for the best position based on surface area
                    if best_volume > al * aw * ah:
                        best_volume = al * aw * ah
                        best_position = np.array([x, y, z])
                        best_idx = idx

                elif policy == "max_volume":
                    # Check for the best position based on surface area
                    if best_volume < al * aw * ah:
                        best_volume = al * aw * ah
                        best_position = np.array([x, y, z])
                        best_idx = idx

        if best_position is not None:
            return True, best_position, best_idx
        return False, None, -1

    def _update_available_spaces(
        self, uld: ULD, position: np.ndarray, orientation: np.ndarray, package: Package, space_index: int
    ):
        length, width, height = orientation
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
                if self._try_pack_package(package, uld, space_find_policy="first_find", orientation_choose_policy="no_rot"):
                    packed = True
                    break
            if not packed:
                self.unpacked_packages.append(package)

        total_delay_cost = sum(pkg.delay_cost for pkg in self.unpacked_packages)
        priority_spread_cost = sum(
            [self.priority_spread_cost if is_prio_uld else 0 for is_prio_uld in self.prio_ulds.values()]
        )
        total_cost = total_delay_cost + priority_spread_cost

        return (
            self.packed_positions,
            self.packed_packages,
            self.unpacked_packages,
            self.prio_ulds,
            total_cost,
        )
