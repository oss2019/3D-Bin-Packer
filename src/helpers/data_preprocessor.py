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
priority_packages = df[df["Type (P/E)"] != "Priority"].copy()

# Calculate total weight of priority packages
total_weight = priority_packages["Weight (kg)"].sum()

# Calculate total volume of priority packages
# Volume = Length * Width * Height
priority_packages["Volume (m^3)"] = (
    priority_packages["Length (cm)"]
    / 100
    * priority_packages["Width (cm)"]
    / 100
    * priority_packages["Height (cm)"]
    / 100
)
priority_packages["Density (kg/m^3)"] = (
    priority_packages["Weight (kg)"] / priority_packages["Volume (m^3)"]
)
total_volume = priority_packages["Volume (m^3)"].sum()

# Print results
print(f"Total Weight of Priority Packages: {total_weight} kg")
print(f"Total Volume of Priority Packages: {total_volume} m^3")
print(
    f"Average Density of Priority Packages: {priority_packages['Density (kg/m^3)'].mean()} kg/m^3"
)

# Create subplots for weight and density histograms
fig, axs = plt.subplots(2, 1, figsize=(10, 12))

# Weight histogram
axs[0].hist(
    priority_packages["Weight (kg)"],
    bins=int(sys.argv[3]),
    density=False,
    alpha=0.6,
    color="g",
    edgecolor="black",
)
axs[0].set_title("Frequency Distribution of Weights of Priority Packages")
axs[0].set_xlabel("Weight (kg)")
axs[0].set_ylabel("Frequency")
axs[0].grid()

# Density histogram
axs[1].hist(
    priority_packages["Density (kg/m^3)"],
    bins=int(sys.argv[3]),
    density=False,
    alpha=0.6,
    color="b",
    edgecolor="black",
)
axs[1].set_title("Frequency Distribution of Density of Priority Packages")
axs[1].set_xlabel("Density (kg/m^3)")
axs[1].set_ylabel("Frequency")
axs[1].grid()

# Save the figure as an image file
output_file = sys.argv[2]
plt.tight_layout()  # Adjust layout to prevent overlap
plt.savefig(output_file)
plt.close()
