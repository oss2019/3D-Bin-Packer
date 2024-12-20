#!/bin/bash

# Loop through the specified ranges
for i in {3..99..3}; do
    j=$((i * 3))  # Calculate the second number based on the first
    # Construct the output file name
    output_file="./input/splits/${i}_${j}.csv"
    
    # Run the sampler command
    ./input/scripts/sampler.sh -i ./input/packages.csv -o "$output_file" -p "$i" -e "$j"
    
    # Run the run.sh command and extract NUM_LINK
    ./run.sh Tree input/ulds.csv "$output_file" output/ | grep NUM_LINK
done
