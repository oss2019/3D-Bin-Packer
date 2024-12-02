from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerBase import ULDPackerBase


class SpaceNode:
    def __init__(
        self,
        dimensions: np.ndarray,
        start_corner: np.ndarray,
    ):
        self.length = dimensions[0]
        self.width = dimensions[1]
        self.height = dimensions[2]
        self.dimensions = np.array(dimensions)
        self.start_corner = start_corner
        self.end_corner = start_corner + self.dimensions

        self.overlaps: List[(SpaceNode, SpaceNode)] = []
        self.children: List[SpaceNode] = []
        self.max_vols_in_children: List[Tuple[int, float]] = []


class SpaceTree:
    def __init__(
        self,
        uld: ULD,
    ):
        self.uld_no = uld.id
        self.root = SpaceNode(uld.dimensions, (0, 0, 0))


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
        self, uld: ULD, package: Package
    ) -> Tuple[bool, np.ndarray]:
        length, width, height = package.dimensions

        # TODO CHANGE THIS
        # for area in uld.available_spaces:
        #     x, y, z, al, aw, ah = area
        #     if length <= al and width <= aw and height <= ah:
        #         return True, np.array([x, y, z])
        # return False, None

    def _update_available_spaces(
        self, uld: ULD, position: np.ndarray, package: Package
    ):
        length, width, height = package.dimensions
        x, y, z = position

        updated_spaces = []
        for space in uld.available_spaces:
            ax, ay, az, al, aw, ah = space

            # Check for remaining free areas after packing
            if not (
                x + length <= ax
                or x >= ax + al
                or y + width <= ay
                or y >= ay + aw
                or z + height <= az
                or z >= az + ah
            ):
                if y + width <= ay + aw:
                    updated_spaces.append(
                        [ax, y + width, az, al, aw - (y + width - ay), ah]
                    )
                if y > ay:
                    updated_spaces.append([ax, ay, az, al, y - ay, ah])
                if x > ax:
                    updated_spaces.append([ax, ay, az, x - ax, aw, ah])
                if x + length <= ax + al:
                    updated_spaces.append(
                        [x + length, ay, az, al - (x + length - ax), aw, ah]
                    )
                if z > az:
                    updated_spaces.append([ax, ay, az, al, aw, z - az])
                if z + height <= az + ah:
                    updated_spaces.append(
                        [ax, ay, z + height, al, aw, ah - (z + height - az)]
                    )
            else:
                updated_spaces.append(space)

        uld.available_spaces = updated_spaces

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

        return (
            self.packed_positions,
            self.packed_packages,
            self.unpacked_packages,
            self.uld_has_prio,
            total_cost,
        )
