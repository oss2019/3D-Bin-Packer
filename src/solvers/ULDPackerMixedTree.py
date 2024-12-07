import logging
logging.basicConfig(level=logging.INFO)

from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
from .ULDPackerTree import ULDPackerTree
from .ULDPackerBase import ULDPackerBase
from .ULDPackerBasicOverlap import ULDPackerBasicOverlap
from .structures.SpaceTree import SpaceTree
from .structures.SpaceNode import SpaceNode

SIZE_BOUND = 5000

class ULDPackerMixedTree(ULDPackerTree):
    def __init__(
        self,
        ulds: List[ULD],
        packages: List[Package],
        priority_spread_cost: int,
        max_passes: int = 1,
    ):
        """
        Initialize the ULDPackerMixedTree.

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
        self.ulds = ulds
        self.prio_ulds = {u.id: False for u in ulds}
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
        self.minimum_dimension = np.inf

        self.unpacked_packages = []
        self.space_trees = [(SpaceTree(u, 40), u) for u in ulds]


    def _insert_into_space(self, space_node, package, uld):
        """
        Insert a package into a given space.

        :param space_node: SpaceNode where package is to be inserted
        :param package: Package to be inserted.
        :return: Tuple indicating success, position, and ULD ID.
        """

        for st, u in self.space_trees:
          if u.id == uld.id:
              space = st.search_for(space_node, search_policy="bfs")
              if space is not None:
                  st.place_package_in(
                      space,
                      package,
                  )
                  print(f"\n{space.node_id} is for {package.id}\n")
                  print(f"Tree {uld.id}")

                  # # Use for debugging
                  # st.display_tree()
                  # print("-" * 50)
                  # input()

                  if package.is_priority:
                      self.prio_ulds[uld.id] = True
                  u.current_weight += package.weight
                  u.current_vol_occupied += np.prod(package.dimensions)

                  return True, space.start_corner, uld.id
              break
        return False, None, None

    def pack(self):
        """
        Pack the packages into the ULDs.

        :return: Tuple containing packed positions, packed packages, unpacked packages, priority ULDs, and total cost.
        """
        n_packs = 1

        self.minimum_dimension = min([np.min(pkg.dimensions) for pkg in self.packages])

        # Get priority packages (sort if required)
        priority_packages = sorted(
            [pkg for pkg in self.packages if pkg.is_priority],
            key=lambda p: (p.volume),
            reverse=True,
        )

        # Get economy packages (sort if required)
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority],
            key=lambda p: p.delay_cost / np.prod(p.dimensions),
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
                can_fit, space_node = self._try_pack_package(
                    package,
                    uld,
                    space_find_policy="first_find",
                    orientation_choose_policy="no_rot",
                    return_space = True
                )
                if can_fit:
                    packed = True
                    n_packs += 1
                    print(
                        f"Packed Priority {package.id} in {uld.id}, {n_packs} "
                    )
                    self._insert_into_space(space_node, package, uld)
                    break
            if not packed:
                self.unpacked_packages.append(package)

        # Pack the economy packages next
        for package in economy_packages:
            packed, position, uldid = self.insert(package)
            if not packed:
                self.unpacked_packages.append(package)
            else:
                print(f"Packed Economy {package.id} in {uld.id}, {n_packs}")
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

    def _find_available_space(
        self, uld: ULD, package: Package, orientation: Tuple[int], policy: str
    ) -> Tuple[bool, np.ndarray]:
        """
        Finds available space in the specified ULD for the given package and given orientation.

        :param uld: The ULD in which to find space.
        :param package: The package to be packed.
        :param orientation: The orientation of the package.
        :param policy: The policy for finding available space (first_find, min_volume, ...)
        :return: A tuple indicating whether space was found and the coordinates of the space.
        """
        length, width, height = orientation
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
        self,
        uld: ULD,
        position: np.ndarray,
        orientation: Tuple[int],
        package: Package,
        space_index: int,
    ):
        length, width, height = orientation
        x, y, z = position

        # New spaces after the space is cut
        updated_spaces = []
        for space in self.available_spaces[uld.id]:
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
                space1 = [ax, y + width, az, al, aw - (y + width - ay), ah]  # Left full
                space2 = [ax, ay, az, al, y - ay, ah]  # Right full
                space3 = [ax, ay, az, x - ax, aw, ah]  # Back full
                # Front full
                space4 = [x + length, ay, az, al - (x + length - ax), aw, ah]
                space5 = [ax, ay, az, al, aw, z - az]  # Above full
                # Down full
                space6 = [ax, ay, z + height, al, aw, ah - (z + height - az)]

                if y + width < ay + aw and all(v >= self.minimum_dimension for v in space1[3::]):
                    updated_spaces.append(space1)
                    # print(f"Appending {space1}")

                if y > ay and all(v >= self.minimum_dimension for v in space2[3::]):
                    updated_spaces.append(space2)
                    # print(f"Appending {space2}")

                if x > ax and all(v >= self.minimum_dimension for v in space3[3::]):
                    updated_spaces.append(space3)
                    # print(f"Appending {space3}")

                if x + length < ax + al and all(v >= self.minimum_dimension for v in space4[3::]):
                    updated_spaces.append(space4)
                    # print(f"Appending {space4}")

                if z > az and all(v >= self.minimum_dimension for v in space5[3::]):
                    updated_spaces.append(space5)
                    # print(f"Appending {space5}")

                if z + height < az + ah and all(v >= self.minimum_dimension for v in space6[3::]):
                    updated_spaces.append(space6)
                    # print(f"Appending {space6}")

            else:
                updated_spaces.append(space)

        self.available_spaces[uld.id] = updated_spaces

    def _try_pack_package(
        self,
        package: Package,
        uld: ULD,
        space_find_policy: str,
        orientation_choose_policy: str,
        return_space: bool = False
    ):
        """
        Attempts to pack a given package into the specified ULD using the provided policies.

        :param package: The package to be packed.
        :param uld: The ULD in which to attempt packing the package.
        :param space_find_policy: Policy to determine how to find available space (first_find, etc...).
        :param orientation_choose_policy: The policy to determine which orientation is chosen in the space.
        :return: True if the package was successfully packed. False otherwise.
        """
        if package.weight + uld.current_weight > uld.weight_limit:
            return False, (None, None, None)  # Exceeds weight limit

        if orientation_choose_policy == "no_rot":
            # The package is taken as is and checked for fit inside the ULD
            orientation = package.dimensions

            can_fit, position, space_index = self._find_available_space(
                uld, package, orientation, policy=space_find_policy
            )

            # Update the state of the ULD if package fits
            if can_fit:
                uld.current_weight += package.weight
                uld.current_vol_occupied += package.volume
                if package.is_priority:
                    self.prio_ulds[uld.id] = True

                x, y, z = position
                self.packed_positions.append(
                    (
                        package.id,
                        uld.id,
                        x,
                        y,
                        z,
                        orientation[0],
                        orientation[1],
                        orientation[2],
                    )
                )
                (x,y,z,l,b,h) = self.available_spaces[uld.id][space_index]

                temp_space = SpaceNode(np.array([x, y, z]),np.array([l,b,h]), self.minimum_dimension)

                self._update_available_spaces(
                    uld, position, orientation, package, space_index
                )
                package.rotation = orientation
                self.packed_packages.append(package)
                if return_space:
                    return True, temp_space
                else:
                    return True
            if return_space:
                return False, None
            else:
                return False

        if orientation_choose_policy == "first_find":
            # All orientations of the package are checked and the first one
            # which is valid to pack is used
            package_rotations = list(itertools.permutations(package.dimensions))

            for orientation in package_rotations:
                can_fit, position, space_index = self._find_available_space(
                    uld, package, orientation, policy=space_find_policy
                )

                # If package fits, update the state of the ULD
                if can_fit:
                    uld.current_weight += package.weight
                    uld.current_vol_occupied += package.volume
                    if package.is_priority:
                        self.prio_ulds[uld.id] = True

                    x, y, z = position
                    self.packed_positions.append(
                        (
                            package.id,
                            uld.id,
                            x,
                            y,
                            z,
                            orientation[0],
                            orientation[1],
                            orientation[2],
                        )
                    )
                    (x, y, z, l, b, h) = self.available_spaces[uld.id][space_index]

                    temp_space = SpaceNode(np.array([x, y, z]), np.array([l, b, h]), self.minimum_dimension)

                    self._update_available_spaces(
                        uld, position, orientation, package, space_index
                    )
                    package.rotation = orientation
                    self.packed_packages.append(package)
                    if return_space:
                        return True, temp_space
                    else:
                        return True
                if return_space:
                    return False, None
                else:
                    return False

        elif orientation_choose_policy == "min_volume":
            # All orientations of the package are checked and the space with
            # minimum volume is used
            package_rotations = list(itertools.permutations(package.dimensions))
            list_of_fits = []
            minvol = np.inf
            best_space_index = None
            best_orientation = None
            best_position = None

            for orientation in package_rotations:
                can_fit, position, space_index = self._find_available_space(
                    uld, package, orientation, policy=space_find_policy
                )

                if can_fit:
                    list_of_fits.append((position, orientation, space_index))

            avail_s = self.available_spaces[uld.id]

            for pos, ori, sp_idx in list_of_fits:
                if np.prod(avail_s[sp_idx][3::]) < minvol:
                    minvol = np.prod(avail_s[sp_idx][3::])
                    best_position = pos
                    best_orientation = ori
                    best_space_index = sp_idx

            # If a minimum volume is found, place the package there
            if minvol != np.inf:
                x, y, z = best_position

                uld.current_weight += package.weight
                uld.current_vol_occupied += package.volume

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
                (x, y, z, l, b, h) = self.available_spaces[uld.id][space_index]

                temp_space = SpaceNode(np.array([x, y, z]), np.array([l, b, h]), self.minimum_dimension)

                self._update_available_spaces(
                    uld, position, orientation, package, space_index
                )
                package.rotation = orientation
                self.packed_packages.append(package)
                if return_space:
                    return True, temp_space
                else:
                    return True
            if return_space:
                return False, None
            else:
                return False

        else:
            raise RuntimeError(
                f"Invalid orientation choose policy  {orientation_choose_policy}"
            )

