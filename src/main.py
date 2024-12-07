#!/usr/bin/python

import pandas as pd
from typing import List, Tuple
import sys

from dataclass.Package import Package
from dataclass.ULD import ULD
from helpers.plot_images import generate_3d_plot
from helpers.visualize import visualize_3d_packing
import numpy as np

NOPRINT = True


# Read data from CSV
def read_data_from_csv(
    uld_file: str, package_file: str
) -> Tuple[List[ULD], List[Package]]:
    """
    Reads data from the specified CSV files and returns lists of ULD and Package objects.

    :param uld_file: ULD data file.
    :param package_file: Package data file.

    :return: A tuple containing two lists: the first list contains ULD objects,
             and the second list contains Package objects.
    """
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
    """
    Gives an output string to print

    :param packed_positions: All packages positions in ULDs.
    :param unpacked_packages: List of unpacked packages.
    :param total_cost: Total delay + spread cost of packing.

    :return: A string which is the output
    """
    invalid_soln = False
    output =''


    # output = "Packing Results:\n"
    # output += "Packed Positions:\n"


    for package_id, uld_id, x, y, z, l, b, h in packed_positions:
        output += f"{package_id},{uld_id},{x},{y},{z},{x+l},{y+b},{z+h}\n"

    # output += "\nUnpacked Packages:\n"

    for pkg in unpacked_packages:
        output += f"{pkg.id},NONE,-1,-1,-1,-1,-1,-1\n"
        if pkg.is_priority:
            invalid_soln = True

    if invalid_soln:
        output += (
            "\n"
            + "!-!" * 17
            + "\nSOLUTION IS INVALID AS PRIORITY PACKAGE WAS MISSED\n"
            + "!-!" * 17
        )
        raise RuntimeError("Priority unpacked")
    return output


# Main function
def main(uld_file, package_file, output_dir):
    # Read the ULD and Package files
    ulds, packages = read_data_from_csv(uld_file, package_file)

    # Define priority spread cost
    priority_spread_cost = 5000

    # Initialize the ULDPacker with multiple passes
    packer = ULDPacker(ulds, packages, priority_spread_cost)

    # This is to prevent printing. Set NOPRINT to True if
    # you do not want to print logs while packing
    global NOPRINT
    import builtins
    original_print = builtins.print

    if NOPRINT:
        builtins.print = lambda *args, **kwargs: None

    # Start packing
    (
        packed_positions,
        packed_packages,
        unpacked_packages,
        ulds_with_prio,
        total_cost,
    ) = packer.pack()

    # Reset print
    builtins.print = original_print

    # Validate the packing
    is_valid, validation_errors = packer.validate_packing()
    if not is_valid:
        print("Packing Validation Failed!")
        for error in validation_errors:
            print(f"Error: {error}")
    else:
        print("Packing validated successfully! No overlaps")

    # Generate 3D plots for ULDs
    generate_3d_plot(packer, output_dir)  # Matplotlib
    visualize_3d_packing(packer)  # Pyvista
    # visualize_individual_spaces(packer) # Do not use this with large datasets

    # Format and print output if required
    output = format_output(packed_positions, unpacked_packages, total_cost)
    # print(output)

    # Actual output to text file
    def OutputToText():
        with open(f"{output_dir}/output.txt" , "w") as file:
            print(f"{int(total_cost)},{len(packed_packages)},{sum(1 for x in ulds_with_prio if x)}",file=file)
            print(output,file=file)

    OutputToText()

    print("\nPacking Statistics:")
    print(f"Total packages          : {len(packages)}")
    print(f"Packed packages         : {len(packed_packages)}")
    print(f"Non-packed packages     : {len(unpacked_packages)}\n")
    print(f"Total Priority packages : {sum(1 for p in packages if p.is_priority)}")
    print(f"Packed Priority pkgs    : {sum(1 for p in packed_packages if p.is_priority)}")
    print(f"Non-packed Priority pkgs: {sum(1 for p in unpacked_packages if p.is_priority)}\n")
    print(f"Total Economy packages  : {sum(1 for p in packages if not p.is_priority)}")
    print(f"Packed Economy pkgs     : {sum(1 for p in packed_packages if not p.is_priority)}")
    print(f"Non-packed Economy pkgs : {sum(1 for p in unpacked_packages if not p.is_priority)}\n")
    print(f"ULDs used               : {sum(1 for u in ulds if u.current_weight > 0)}")
    print(f"ULDs with priority pkgs : {sum([1 if is_prio_uld else 0 for is_prio_uld in ulds_with_prio.values()])}")
    print(f"Priority pkgs per ULD   : {packer.count_priority_packages_in_uld()}\n")
    print(f"Total Weight Capacity   : {sum(u.weight_limit for u in ulds)}")
    print(f"Total Weight Used       : {sum(u.current_weight for u in ulds)}")
    print(f"Total Volume Capacity   : {sum(np.prod(u.dimensions) for u in ulds)}")
    print(f"Total Volume Used       : {sum(u.current_vol_occupied for u in ulds)}")
    wasted_spaces = []
    wasted_weights = []

    for uld in ulds:
        w1 = 1 - uld.current_vol_occupied / np.prod(uld.dimensions)
        w2 = 1 - uld.current_weight / uld.weight_limit

        wasted_spaces.append(int(w1 * 100))
        wasted_weights.append(int(w2 * 100))

    print(f"Total Volume Wasted     : {' '.join(str(w) for w in wasted_spaces)}")
    print(f"Total Weight Wasted     : {' '.join(str(w) for w in wasted_weights)}")
    print(f"Total cost: {total_cost:.2f}")


if __name__ == "__main__":
    if len(sys.argv) <= 4:
        print(
            """
Usage: python main.py <solver-type> <uld-file> <package-file> <output-dir>

Supported Solver Types:
  - BasicOverlap
  - BasicNonOverlap (not working for Priority 100% packing),
  - Tree
  - Mixed"""
        )
        exit(1)

    if sys.argv[1] == "BasicOverlap":
        from solvers.ULDPackerBasicOverlap import ULDPackerBasicOverlap as ULDPacker
    elif sys.argv[1] == "BasicNonOverlap":
        from solvers.ULDPackerBasicNonOverlap import ULDPackerBasicNonOverlap as ULDPacker
    elif sys.argv[1] == "Tree":
        from solvers.ULDPackerTree import ULDPackerTree as ULDPacker
    elif sys.argv[1] == "Mixed":
        from solvers.ULDPackerMixed import ULDPackerMixed as ULDPacker
    else:
        print(
"""Supported Solver Types:
  - BasicOverlap
  - BasicNonOverlap (not working for Priority 100% packing),
  - Tree
  - Mixed"""
        )
        exit(1)

    main(sys.argv[2], sys.argv[3], sys.argv[4])
