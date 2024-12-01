import numpy as np
import pandas as pd
from typing import List, Tuple
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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

# Define the ULDPacker class
class ULDPacker:
    def __init__(self, ulds: List[ULD], packages: List[Package], priority_spread_cost: int, max_passes: int = 5):
        self.ulds = ulds
        self.packages = packages
        self.priority_spread_cost = priority_spread_cost
        self.max_passes = max_passes  # Set the max number of packing passes
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

    def pack(self):
        priority_packages = sorted(
            [pkg for pkg in self.packages if pkg.is_priority], key=lambda p: p.delay_cost, reverse=True
        )
        economy_packages = sorted(
            [pkg for pkg in self.packages if not pkg.is_priority], key=lambda p: p.delay_cost, reverse=True
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
            {uld_id for _, uld_id, *_ in self.packed_positions if any(p.id == _ and p.is_priority for p in self.packages)}
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

    def count_priority_packages_in_uld(self):
        priority_count_per_uld = {}
        for package_id, uld_id, _, _, _ in self.packed_positions:
            package = next(pkg for pkg in self.packages if pkg.id == package_id)
            if package.is_priority:
                if uld_id not in priority_count_per_uld:
                    priority_count_per_uld[uld_id] = 0
                priority_count_per_uld[uld_id] += 1
        return priority_count_per_uld


# Read data from CSV
def read_data_from_csv(uld_file: str, package_file: str) -> Tuple[List[ULD], List[Package]]:
    uld_data = pd.read_csv(uld_file)
    package_data = pd.read_csv(package_file)

    ulds = [
        ULD(id=row['ULD Identifier'], length=row['Length (cm)'], width=row['Width (cm)'],
            height=row['Height (cm)'], weight_limit=row['Weight Limit (kg)'])
        for _, row in uld_data.iterrows()
    ]

    packages = [
        Package(
            id=row['Package Identifier'],
            length=row['Length (cm)'],
            width=row['Width (cm)'],
            height=row['Height (cm)'],
            weight=row['Weight (kg)'],
            is_priority=row['Type (P/E)'] == 'Priority',
            delay_cost=int(row['Cost of Delay']) if str(row['Cost of Delay']).isdigit() else 0
        )
        for _, row in package_data.iterrows()
    ]

    return ulds, packages


# Format and print the output
def format_output(packed_positions: List[Tuple], unpacked_packages: List[Package], total_cost: int) -> str:
    output = "Packing Results:\n"
    output += "Packed Positions:\n"
    for package_id, uld_id, x, y, z in packed_positions:
        output += f"Package {package_id} in ULD {uld_id} at position ({x}, {y}, {z})\n"

    output += "\nUnpacked Packages:\n"
    for pkg in unpacked_packages:
        output += f"Package {pkg.id} (Weight: {pkg.weight}kg, Delay Cost: {pkg.delay_cost})\n"

    output += f"\nTotal Delay Cost: {total_cost}\n"
    return output


# Main function
def main():
    uld_file = 'ulds.csv'
    package_file = 'packages.csv'

    ulds, packages = read_data_from_csv(uld_file, package_file)

    # Define priority spread cost
    priority_spread_cost = 10

    # Initialize the ULDPacker with multiple passes
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
