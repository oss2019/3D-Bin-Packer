from typing import List, Tuple
from dataclass.ULD import ULD
from dataclass.Package import Package
import numpy as np
import itertools


# Define the ULDPacker class
class ULDPackerBase:
    def __init__(
        self,
        ulds: List[ULD],
        packages: List[Package],
        priority_spread_cost: int,
        max_passes: int = 1,
    ):
        """
        Initializes the ULDPackerBase instance.

        :param ulds: A list of ULDs (Unit Load Devices) available for packing.
        :param packages: A list of packages to be packed into the ULDs.
        :param priority_spread_cost: The cost associated with spreading priority packages.
        :param max_passes: The maximum number of packing passes. Defaults to 1.
        """
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
        self.minimum_dimension = np.inf

    def _find_available_space(
        self, uld: ULD, package: Package, policy: str
    ) -> Tuple[bool, np.ndarray]:
        """
        Finds an available space in the given ULD for the specified package.

        :param uld: The ULD in which to find space.
        :param package: The package to be packed.
        :param policy: The packing policy to be used
        :return: Whether Space was found, and the coordinates of the space.
        """
        raise NotImplementedError("This method needs to be implemented.")

    def _update_available_spaces(
        self,
        uld: ULD,
        position: np.ndarray,
        orientation: Tuple[int],
        package: Package,
        space_index: int,
    ):
        """
        Updates the available spaces in the ULD after packing a package.

        :param uld: The ULD being updated.
        :param position: The position where the package was packed.
        :param orientation: The orientation of the package.
        :param package: The package that was packed.
        :param space_index: The index of the space that was used in list of spaces.
        """
        raise NotImplementedError("This method needs to be implemented.")

    def pack(self):
        """
        Needs to be overridden. Packs according to the Derived class policies

        :return: None
        """
        raise NotImplementedError("This method needs to be implemented.")

    def get_list_of_spaces(self, uld_id):
        """
        Wrapper for getting list of empty spaces in a ULD

        :return: None
        """
        pass

    def _try_pack_package(
        self,
        package: Package,
        uld: ULD,
        space_find_policy: str,
        orientation_choose_policy: str,
    ):
        """
        Attempts to pack a given package into the specified ULD using the provided policies.

        :param package: The package to be packed.
        :param uld: The ULD in which to attempt packing the package.
        :param space_find_policy: Policy to determine how to find available space (first_find, etc...).
        :param orientation_choose_policy: The policy to determine which orientation is chosen in the space.
        :return: True, orientation, if the package was successfully packed, False, None, tuple otherwise.
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
                uld.current_vol_occupied += np.prod(package.dimensions)
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
                self._update_available_spaces(
                    uld, position, orientation, package, space_index
                )
                package.rotation = orientation
                return True, orientation

            return False, (None, None, None)

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
                    uld.current_vol_occupied += np.prod(package.dimensions)
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
                    self._update_available_spaces(
                        uld, position, orientation, package, space_index
                    )
                    package.rotation = orientation
                    return True, orientation

            return False, (None, None, None)

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
                package.rotation = best_orientation
                return True, best_orientation
            return False, (None, None, None)

        else:
            raise RuntimeError(
                f"Invalid orientation choose policy  {orientation_choose_policy}"
            )

    def validate_packing(self) -> Tuple[bool, List[str]]:
        """
        Validates the packing performed
        Checks for package overlaps and package out of boundaries

        :return: Whether packing is valid. If not, also return list of errors
        """
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
        """
        Counts priority packages in each ULD.

        :return: A dictionary with ULD IDs as keys and counts of priority packages as values.
        """
        priority_count_per_uld = {}
        for package_id, uld_id, _, _, _, _, _, _ in self.packed_positions:
            package = next(pkg for pkg in self.packages if pkg.id == package_id)
            if package.is_priority:
                if uld_id not in priority_count_per_uld:
                    priority_count_per_uld[uld_id] = 0
                priority_count_per_uld[uld_id] += 1
        return priority_count_per_uld
