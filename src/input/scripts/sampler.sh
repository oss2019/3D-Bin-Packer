#!/bin/bash

input_file="package.csv"
output_file="sample.csv"

num_economy=0
num_priority=0

while getopts "e:p:" opt; do
    case "$opt" in
        e) num_economy=$OPTARG ;;
        p) num_priority=$OPTARG ;;
	*) echo "Invalid."; exit 1 ;;
    esac
done

if [[ -n "$num_economy" && -n "$num_priority" ]]; then
    {
        head -n 1 "$input_file"
        shuf -n "$num_economy" <(awk -F, '$6 == "Economy"' "$input_file")
        shuf -n "$num_priority" <(awk -F, '$6 == "Priority"' "$input_file")
    } > "$output_file"

else
    echo "Specify."
fi

echo "Sampled."
