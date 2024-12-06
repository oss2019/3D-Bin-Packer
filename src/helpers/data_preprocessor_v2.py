import pandas as pd
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
import os

# Read data from CSV
df = pd.read_csv("input/packages.csv")

# Convert Length, Width, and Height from cm to m
df["Length (m)"] = df["Length (cm)"] / 100
df["Width (m)"] = df["Width (cm)"] / 100
df["Height (m)"] = df["Height (cm)"] / 100
# df["Cost of Delay"] = df["Cost of Delay"] * 2

# Calculate volume in cubic meters (Length * Width * Height)
df["Volume (m^3)"] = df["Length (m)"] * df["Width (m)"] * df["Height (m)"]

# Filter out rows with 'Cost of Delay' as '-' and convert to numeric
df["Cost of Delay"] = pd.to_numeric(df["Cost of Delay"], errors="coerce")

# Drop rows with NaN values in 'Cost of Delay'
df = df.dropna(subset=["Cost of Delay"])

# Extract relevant columns
weights = df["Weight (kg)"].values
volumes = df["Volume (m^3)"].values  # Use the volume in cubic meters
cost_of_delay = df["Cost of Delay"].values

# Check for NaN values in the extracted columns
if (
    np.any(np.isnan(weights))
    or np.any(np.isnan(volumes))
    or np.any(np.isnan(cost_of_delay))
):
    raise ValueError("One or more extracted columns contain NaN values.")

# Scale the Cost of Delay to fit between 60 and 200
cost_of_delay_scaled = np.interp(
    cost_of_delay, (cost_of_delay.min(), cost_of_delay.max()), (60, 200)
)

# Create a PyVista plot
plotter = pv.Plotter()

# Create a point cloud
points = np.column_stack((weights, volumes, cost_of_delay_scaled))
cloud = pv.PolyData(points)

# Add the point cloud to the plotter
plotter.add_mesh(
    cloud, scalars=cost_of_delay_scaled, point_size=10, render_points_as_spheres=True
)

# Add a color bar
plotter.add_scalar_bar(title="Cost of Delay", n_labels=5)

# Set the axes labels
plotter.set_background("white")
plotter.add_axes()
plotter.show_grid()

# Set camera position for better view
plotter.camera_position = "iso"  # or you can set a custom position

# Show the plot
plotter.show()

# Now, let's save the plot using Matplotlib
# Create output directory if it doesn't exist
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Create a Matplotlib figure
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

# Create a scatter plot
scatter = ax.scatter(
    weights, volumes, cost_of_delay_scaled, c=cost_of_delay_scaled, cmap="viridis"
)

# Add color bar
cbar = plt.colorbar(scatter)
cbar.set_label("Cost of Delay")

# Set labels
ax.set_xlabel("Weight (kg)")
ax.set_ylabel("Volume (m^3)")  # Update label to reflect cubic meters
ax.set_zlabel("Cost of Delay")

# Save the plot
plt.savefig(os.path.join(output_dir, "economy_wvd.png"))
plt.close()  # Close the plot to free up memory
