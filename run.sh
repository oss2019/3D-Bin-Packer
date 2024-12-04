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

DIRECTORY="src/"
treat_warn_as_err=0
warn_found=0

# Find all .py files and search for lines containing 'WARNING'
while IFS= read -r -d '' file; do
    if grep -H "WARNING" "$file" &>/dev/null; then
        echo "Warning found in: $file"
        echo "-----------------------"
        grep -Hn "WARNING" "$file"
        echo "-----------------------"
        warn_found=1
    fi
done < <(find "$DIRECTORY" -name "*.py" -print0)

if [ "$warn_found" -eq 1 ]; then
    if [ "$treat_warn_as_err" -eq 1 ]; then
        echo "Treating warnings as errors."
        exit 1
    fi
else
    echo "No warnings found."
fi

# Assign arguments to variables for better readability
SOLVER_TYPE=$1
ULD_FILE=$2
PACKAGE_FILE=$3
OUTPUT_DIR=$4

mkdir -p "$OUTPUT_DIR"

# Validate solver type
if [[ "$SOLVER_TYPE" != "BasicOverlap" && "$SOLVER_TYPE" != "BasicNonOverlap" && "$SOLVER_TYPE" != "Tree" && "$SOLVER_TYPE" != "Mixed" ]]; then
    echo "Error: Invalid solver type '$SOLVER_TYPE'."
    usage
fi

# Run the main.py script with the provided arguments
python3 src/main.py "$SOLVER_TYPE" "$ULD_FILE" "$PACKAGE_FILE" "$OUTPUT_DIR"
