import numpy as np
import pandas as pd
from typing import List, Tuple
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from itertools import permutations

# Define the ULD class
class ULD:
    def __init__(self, id: str, length: int, width: int, height: int, weight_limit: int):
        self.id = id
        self.dimensions = np.array([length, width, height])
        self.weight_limit = weight_limit
        self.current_weight = 0
        self.occupied_positions = []  # List of occupied spaces (x, y, z, length, width, height)
        self.available_spaces = [(0, 0, 0, length, width, height)]  # List of available spaces


# Define the Package class
class Package:
    def __init__(self, id: str, length: int, width: int, height: int, weight: int, is_priority: bool, delay_cost: int):
        self.id = id
        self.dimensions = np.array([length, width, height])
        self.weight = weight
        self.is_priority = is_priority
        self.delay_cost = delay_cost

    def get_rotations(self) -> List[np.ndarray]:
        """Generate all possible rotations of the package"""
        return [np.array([l, w, h]) for l, w, h in permutations(self.dimensions)]

    def best_rotation(self, available_space: Tuple[int, int, int, int, int, int]) -> np.ndarray:
        """Select the best rotation with minimal surface area exposed"""
        best_rotation = None
        min_surface_area = float('inf')
        for rotation in self.get_rotations():
            l, w, h = rotation
            if l <= available_space[3] and w <= available_space[4] and h <= available_space[5]:
                surface_area = 2 * (l * w + w * h + h * l)  # Surface area of the package
                if surface_area < min_surface_area:
                    min_surface_area = surface_area
                    best_rotation = rotation
        return best_rotation


# Define the ULDPacker class
class ULDPacker:
    def __init__(self, ulds: List[ULD], packages: List[Package], priority_spread_cost: int):
        self.ulds = ulds
        self.packages = packages
        self.priority_spread_cost = priority_spread_cost
        self.packed_positions = []  # [(package_id, uld_id, x, y, z)]
        self.unpacked_packages = []

    def _find_available_space(self, uld: ULD, package: Package) -> Tuple[bool, np.ndarray]:
        length, width, height = package.dimensions
        for area in uld.available_spaces:
            x, y, z, al, aw, ah = area
            if length <= al and width <= aw and height <= ah:
                return True, np.array([x, y, z])
        return False, None

    def _try_pack_package(self, package: Package, uld: ULD) -> bool:
        if package.weight + uld.current_weight > uld.weight_limit:
            return False  # Exceeds weight limit

        can_fit, position = self._find_available_space(uld, package)
        if can_fit:
            x, y, z = position
            length, width, height = package.dimensions
            uld.occupied_positions.append(np.array([x, y, z, length, width, height]))
            uld.current_weight += package.weight
            self.packed_positions.append((package.id, uld.id, x, y, z))
            self._update_available_spaces(uld, position, package)
            return True
        return False

    def _update_available_spaces(self, uld: ULD, position: np.ndarray, package: Package):
        length, width, height = package.dimensions
        x, y, z = position

        updated_spaces = []
        for space in uld.available_spaces:
            ax, ay, az, al, aw, ah = space

            # Check for remaining free areas after packing
            if not (x + length <= ax or x >= ax + al or
                    y + width <= ay or y >= ay + aw or
                    z + height <= az or z >= az + ah):
                if y + width < ay + aw:
                    updated_spaces.append([ax, y + width, az, al, aw - (y + width - ay), ah])
                if y > ay:
                    updated_spaces.append([ax, ay, az, al, y - ay, ah])
                if x > ax:
                    updated_spaces.append([ax, ay, az, x - ax, aw, ah])
                if x + length < ax + al:
                    updated_spaces.append([x + length, ay, az, al - (x + length - ax), aw, ah])
                if z > az:
                    updated_spaces.append([ax, ay, az, al, aw, z - az])
                if z + height < az + ah:
                    updated_spaces.append([ax, ay, z + height, al, aw, ah - (z + height - az)])
            else:
                updated_spaces.append(space)

        uld.available_spaces = updated_spaces

    def _generate_3d_plot(self):
        for uld in self.ulds:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

            for package_id, uld_id, x, y, z in self.packed_positions:
                if uld.id == uld_id:
                    package = next(pkg for pkg in self.packages if pkg.id == package_id)
                    length, width, height = package.dimensions

                    # Create vertices for the package
                    vertices = [
                        [x, y, z],
                        [x + length, y, z],
                        [x + length, y + width, z],
                        [x, y + width, z],
                        [x, y, z + height],
                        [x + length, y, z + height],
                        [x + length, y + width, z + height],
                        [x, y + width, z + height],
                    ]

                    # Define the faces of the package
                    faces = [
                        [vertices[0], vertices[1], vertices[5], vertices[4]],
                        [vertices[1], vertices[2], vertices[6], vertices[5]],
                        [vertices[2], vertices[3], vertices[7], vertices[6]],
                        [vertices[3], vertices[0], vertices[4], vertices[7]],
                        [vertices[0], vertices[1], vertices[2], vertices[3]],
                        [vertices[4], vertices[5], vertices[6], vertices[7]],
                    ]

                    ax.add_collection3d(Poly3DCollection(faces, facecolors='cyan', linewidths=1, edgecolors='r', alpha=0.25))

            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title(f'Packed ULD {uld.id}')
            ax.set_xlim(0, uld.dimensions[0])
            ax.set_ylim(0, uld.dimensions[1])
            ax.set_zlim(0, uld.dimensions[2])

            # Save the 3D plot as an image
            plt.savefig(f'packed_uld_{uld.id}.png')
            plt.show()

    def _group_pack(self):
        """Cluster small packages together into blocks for efficient packing"""
        sorted_packages = sorted(self.packages, key=lambda p: (p.dimensions[0], p.dimensions[1], p.dimensions[2]))
        grouped_packages = []

        # Group packages by similar dimensions
        temp_group = []
        last_dim = None
        for pkg in sorted_packages:
            if last_dim is None or np.all(pkg.dimensions == last_dim):
                temp_group.append(pkg)
            else:
                grouped_packages.append(temp_group)
                temp_group = [pkg]
            last_dim = pkg.dimensions

        if temp_group:
            grouped_packages.append(temp_group)

        # Try to pack each block of grouped packages
        for group in grouped_packages:
            uld = self.ulds[0]  # Start with the first ULD, could also optimize further
            # Add logic to pack the block into ULD
            # To be expanded...
            
    def pack(self):
        priority_packages = sorted(
            [pkg for pkg in self.packages if pkg.is_priority], key=lambda p: p.delay_cost, reverse=True
        )
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority], key=lambda p: p.delay_cost, reverse=True
        )

        for package in priority_packages + economy_packages:
            packed = False
            for uld in self.ulds:
                # Try all rotations to fit the best one
                rotations = package.get_rotations()
                for rotation in rotations:
                    package.dimensions = rotation
                    if self._try_pack_package(package, uld):
                        packed = True
                        break
                if packed:
                    break
            if not packed:
                self.unpacked_packages.append(package)

        # Apply Group Packing after individual packing
        self._group_pack()

        total_delay_cost = sum(pkg.delay_cost for pkg in self.unpacked_packages)
        priority_spread_cost = len(set([pos[1] for pos in self.packed_positions])) * self.priority_spread_cost
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
                    if x + length > uld.dimensions[0] or y + width > uld.dimensions[1] or z + height > uld.dimensions[2]:
                        validation_errors.append(f"Package {package.id} in ULD {uld.id} extends beyond ULD boundaries!")
                    
                    # Check for overlap with other packages
                    for other_package_id, other_uld_id, other_x, other_y, other_z in self.packed_positions:
                        if (other_package_id != package.id) and (other_uld_id == uld_id):
                            other_package = next(pkg for pkg in self.packages if pkg.id == other_package_id)
                            other_length, other_width, other_height = other_package.dimensions

                            # Check for overlap (if packages share space)
                            if not (x + length <= other_x or x >= other_x + other_length or
                                    y + width <= other_y or y >= other_y + other_width or
                                    z + height <= other_z or z >= other_z + other_height):
                                validation_errors.append(f"Package {package.id} overlaps with Package {other_package.id} in ULD {uld.id}!")
        
        
        # Return validation status and any errors found
        is_valid = len(validation_errors) == 0
        return is_valid, validation_errors


# Main function
def main():
    uld_file = 'ulds.csv'
    package_file = 'packages.csv'

    ulds, packages = read_data_from_csv(uld_file, package_file)

    # Define priority spread cost
    priority_spread_cost = 10

    # Initialize the ULDPacker
    packer = ULDPacker(ulds, packages, priority_spread_cost)

    # Start packing
    packed_positions, unpacked_packages, total_cost = packer.pack()

    # Validate the packing
    is_valid, validation_errors = packer.validate_packing()
    if not is_valid:
        print("Packing Validation Failed!")
        for error in validation_errors:
            print(f"Error: {error}")
    else:
        print("Packing validated successfully!")

    # Generate 3D plots for ULDs
    packer._generate_3d_plot()

    # Format and print output
    output = format_output(packed_positions, unpacked_packages, total_cost)
    print(output)

    print("\nPacking Statistics:")
    print(f"Total packages: {len(packages)}")
    print(f"Packed packages: {len(packed_positions)}")
    print(f"Unpacked packages: {len(unpacked_packages)}")
    print(f"Priority packages: {sum(1 for p in packages if p.is_priority)}")
    print(f"ULDs used: {len(set(pos[1] for pos in packed_positions))}")
    print(f"Total cost: {total_cost:.2f}")


if __name__ == "__main__":
    main()
