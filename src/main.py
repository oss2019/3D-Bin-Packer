#!/usr/bin/python

import pandas as pd
from typing import List, Tuple
import sys

from dataclass.Package import Package
from dataclass.ULD import ULD
from helpers.plot_images import generate_3d_plot


# Read data from CSV
def read_data_from_csv(
    uld_file: str, package_file: str
) -> Tuple[List[ULD], List[Package]]:
    uld_data = pd.read_csv(uld_file, comment="#")
    package_data = pd.read_csv(package_file, comment="#")

    ulds = [
        ULD(
            id=row["ULD Identifier"],
            length=row["Length (cm)"],
            width=row["Width (cm)"],
            height=row["Height (cm)"],
            weight_limit=row["Weight Limit (kg)"],
        )
        for _, row in uld_data.iterrows()
    ]

    packages = [
        Package(
            id=row["Package Identifier"],
            length=row["Length (cm)"],
            width=row["Width (cm)"],
            height=row["Height (cm)"],
            weight=row["Weight (kg)"],
            is_priority=row["Type (P/E)"] == "Priority",
            delay_cost=int(row["Cost of Delay"])
            if str(row["Cost of Delay"]).isdigit()
            else 0,
        )
        for _, row in package_data.iterrows()
    ]

    return ulds, packages


# Format and print the output
def format_output(
    packed_positions: List[Tuple], unpacked_packages: List[Package], total_cost: int
) -> str:
    invalid_soln = False
    output = "Packing Results:\n"
    output += "Packed Positions:\n"
    for package_id, uld_id, x, y, z in packed_positions:
        output += f"Package {package_id} in ULD {uld_id} at position ({x}, {y}, {z})\n"

    output += "\nUnpacked Packages:\n"
    for pkg in unpacked_packages:
        output += f"Package {pkg.id} (Weight: {pkg.weight}kg, Delay Cost: {pkg.delay_cost}, Priority: {pkg.is_priority})\n"
        if pkg.is_priority:
            invalid_soln = True

    output += f"\nTotal Delay Cost: {total_cost}\n"
    if invalid_soln:
        output += (
            "\n"
            + "!-!" * 17
            + "\nSOLUTION IS INVALID AS PRIORITY PACKAGE WAS MISSED\n"
            + "!-!" * 17
        )
    return output


# Main function
def main(uld_file, package_file, output_dir):
    # uld_file = "input/ulds2.csv"
    # package_file = "input/packages2.csv"

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
        print("Packing validated successfully! No overlaps")

    # Generate 3D plots for ULDs
    generate_3d_plot(packer, output_dir)

    # Format and print output
    output = format_output(packed_positions, unpacked_packages, total_cost)
    print(output)

    print("\nPacking Statistics:")
    print(f"Total packages          : {len(packages)}")
    print(f"Packed packages         : {len(packed_positions)}")
    print(f"Unpacked packages       : {len(unpacked_packages)}")
    print(f"Total Priority packages : {sum(1 for p in packages if p.is_priority)}")
    print(
        f"Unpacked Priority pkgs  : {sum(1 for p in unpacked_packages if p.is_priority)}"
    )
    print(
        f"Unpacked Economy pkgs   : {sum(1 for p in unpacked_packages if not p.is_priority)}"
    )
    print(f"ULDs used               : {len(set(pos[1] for pos in packed_positions))}")
    print(f"Total cost: {total_cost:.2f}")


if __name__ == "__main__":
    if len(sys.argv) <= 4:
        print(
            """
Usage: python main.py <solver-type> <uld-file> <package-file> <output-dir>

Supported Solver Types:
  - BasicOverlap
  - BasicNonOverlap (not working for Priority 100% packing),
  - Tree"""
        )
        exit(1)

    if sys.argv[1] == "BasicOverlap":
        from solvers.ULDPackerBasicOverlap import ULDPacker
    elif sys.argv[1] == "BasicNonOverlap":
        from solvers.ULDPackerBasicNonOverlap import ULDPacker
    elif sys.argv[1] == "Tree":
        from solvers.ULDPackerTree import ULDPacker
    else:
        print(
            """Supported Solver Types:
  - BasicOverlap
  - BasicNonOverlap (not working for Priority 100% packing),
  - Tree"""
        )
        exit(1)

    main(sys.argv[2], sys.argv[3], sys.argv[4])
