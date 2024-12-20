#!/bin/bash

num_economy=0
num_priority=0
input_file=""
output_file=""

# Function to display usage instructions
usage() {
    echo "Usage: $0 -i <input_file> -o <output_file> -e <num_economy> -p <num_priority>"
    echo "  -i <input_file>     Path to the input CSV file"
    echo "  -o <output_file>    Path to the output CSV file"
    echo "  -e <num_economy>    Number of economy samples to select"
    echo "  -p <num_priority>   Number of priority samples to select"
    exit 1
}

# Parse command-line options
while getopts "i:o:e:p:" opt; do
    case "$opt" in
    i) input_file=$OPTARG ;;
    o) output_file=$OPTARG ;;
    e) num_economy=$OPTARG ;;
    p) num_priority=$OPTARG ;;
    *) usage ;; # Call usage function for invalid options
    esac
done

# Check if input file is provided
if [[ -z "$input_file" ]]; then
    echo "Error: Input file is required."
    usage
fi

# Check if output file is provided
if [[ -z "$output_file" ]]; then
    echo "Error: Output file is required."
    usage
fi

# Check if both sampling arguments are provided
if [[ -z "$num_economy" || -z "$num_priority" ]]; then
    usage # Call usage function if arguments are missing
fi

# Check if input file exists
if [[ ! -f "$input_file" ]]; then
    echo "Error: Input file '$input_file' not found."
    exit 1
fi

# Sampling logic
{
    head -n 1 "$input_file"                                             # Print header
    shuf -n "$num_economy" <(awk -F, '$6 == "Economy"' "$input_file")   # Sample economy
    shuf -n "$num_priority" <(awk -F, '$6 == "Priority"' "$input_file") # Sample priority
} >"$output_file"

{ head -n 1 "$output_file" && tail -n +2 "$output_file" | shuf; } >temp.csv && mv temp.csv "$output_file"

echo "Sampled $num_economy economy and $num_priority priority records into '$output_file'."
