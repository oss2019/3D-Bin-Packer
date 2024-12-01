#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 <solver-type> <uld-file> <package-file> <output-dir>"
    echo ""
    echo "Supported Solver Types:"
    echo "  - BasicOverlap"
    echo "  - BasicNonOverlap (not working for Priority 100% packing)"
    echo "  - Tree"
    exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 4 ]; then
    usage
fi

# Assign arguments to variables for better readability
SOLVER_TYPE=$1
ULD_FILE=$2
PACKAGE_FILE=$3
OUTPUT_DIR=$4

mkdir -p "$OUTPUT_DIR"

# Validate solver type
if [[ "$SOLVER_TYPE" != "BasicOverlap" && "$SOLVER_TYPE" != "BasicNonOverlap" && "$SOLVER_TYPE" != "Tree" ]]; then
    echo "Error: Invalid solver type '$SOLVER_TYPE'."
    usage
fi

# Run the main.py script with the provided arguments
python3 src/main.py "$SOLVER_TYPE" "$ULD_FILE" "$PACKAGE_FILE" "$OUTPUT_DIR"
