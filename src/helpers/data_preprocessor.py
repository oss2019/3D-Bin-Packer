import pandas as pd
import matplotlib.pyplot as plt
import sys

# Usage check
if len(sys.argv) != 4:
    print(
        "Usage: python script.py <input_csv_file> <output_image_file> <number-of-bins>"
    )
    sys.exit(1)

# Read data from CSV file
input_file = sys.argv[1]
df = pd.read_csv(input_file)

# Filter for priority packages and create a new DataFrame
priority_packages = df[df["Type (P/E)"] == "Priority"].copy()

# Calculate total weight of priority packages
total_weight = priority_packages["Weight (kg)"].sum()

# Calculate total volume of priority packages
# Volume = Length * Width * Height
priority_packages["Volume (cm^3)"] = (
    priority_packages["Length (cm)"]
    * priority_packages["Width (cm)"]
    * priority_packages["Height (cm)"]
)
total_volume = priority_packages["Volume (cm^3)"].sum()

# Calculate average density (Density = Weight / Volume)
# Note: We need to ensure we don't divide by zero
average_density = (
    priority_packages["Weight (kg)"] / priority_packages["Volume (cm^3)"]
).mean()

# Print results
print(f"Total Weight of Priority Packages: {total_weight} kg")
print(f"Total Volume of Priority Packages: {total_volume} cm^3")
print(f"Average Density of Priority Packages: {average_density} kg/cm^3")

# Plotting the frequency distribution curve of weights
plt.figure(figsize=(10, 6))
plt.hist(
    priority_packages["Weight (kg)"],
    bins=int(sys.argv[3]),
    density=False,
    alpha=0.6,
    color="g",
    edgecolor="black",
)
plt.title("Frequency Distribution of Weights of Priority Packages")
plt.xlabel("Weight (kg)")
plt.ylabel("Frequency")
plt.grid()

# Save the figure as an image file
output_file = sys.argv[2]
plt.savefig(output_file)  # Save as PNG file
plt.close()  # Close the plot to free up memory
