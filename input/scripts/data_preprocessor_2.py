import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from mpl_toolkits.mplot3d import Axes3D

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <package-file>")
    exit()

# Load the data from CSV
df = pd.read_csv(sys.argv[1])

# Convert 'Cost of Delay' to numeric, coercing errors to NaN
df['Cost of Delay'] = pd.to_numeric(df['Cost of Delay'], errors='coerce')

# Drop rows with NaN in 'Cost of Delay'
df.dropna(subset=['Cost of Delay'], inplace=True)

# Calculate volume
df['Volume (cm^3)'] = df['Length (cm)'] * df['Width (cm)'] * df['Height (cm)']

# Create subplots
fig, axs = plt.subplots(3, 3, figsize=(15, 15))
fig.suptitle('Data Analysis', fontsize=16)

# 1. Histogram of Length
axs[0, 0].hist(df['Length (cm)'], bins=20, color='blue', alpha=0.7)
axs[0, 0].set_title('Histogram of Length')
axs[0, 0].set_xlabel('Length (cm)')
axs[0, 0].set_ylabel('Frequency')

# 2. Histogram of Width
axs[0, 1].hist(df['Width (cm)'], bins=20, color='green', alpha=0.7)
axs[0, 1].set_title('Histogram of Width')
axs[0, 1].set_xlabel('Width (cm)')
axs[0, 1].set_ylabel('Frequency')

# 3. Histogram of Height
axs[0, 2].hist(df['Height (cm)'], bins=20, color='red', alpha=0.7)
axs[0, 2].set_title('Histogram of Height')
axs[0, 2].set_xlabel('Height (cm)')
axs[0, 2].set_ylabel('Frequency')

# 4. Histogram of Weight
axs[1, 0].hist(df['Weight (kg)'], bins=20, color='purple', alpha=0.7)
axs[1, 0].set_title('Histogram of Weight')
axs[1, 0].set_xlabel('Weight (kg)')
axs[1, 0].set_ylabel('Frequency')

# 5. Histogram of Cost of Delay
axs[1, 1].hist(df['Cost of Delay'], bins=20, color='orange', alpha=0.7)
axs[1, 1].set_title('Histogram of Cost of Delay')
axs[1, 1].set_xlabel('Cost of Delay')
axs[1, 1].set_ylabel('Frequency')

# 6. LWH scatter with colors for Cost of Delay
scatter = axs[1, 2].scatter(df['Length (cm)'], df['Width (cm)'], c=df['Cost of Delay'], cmap='viridis', alpha=0.7)
axs[1, 2].set_title('LWH Scatter (Color by Cost of Delay)')
axs[1, 2].set_xlabel('Length (cm)')
axs[1, 2].set_ylabel('Width (cm)')
fig.colorbar(scatter, ax=axs[1, 2], label='Cost of Delay')

# 7. Weight vs Volume
axs[2, 0].scatter(df['Volume (cm^3)'], df['Weight (kg)'], color='cyan', alpha=0.7)
axs[2, 0].set_title('Weight vs Volume')
axs[2, 0].set_xlabel('Volume (cm^3)')
axs[2, 0].set_ylabel('Weight (kg)')

# 8. Cost of Delay vs Weight
axs[2, 1].scatter(df['Weight (kg)'], df['Cost of Delay'], color='magenta', alpha=0.7)
axs[2, 1].set_title('Cost of Delay vs Weight')
axs[2, 1].set_xlabel('Weight (kg)')
axs[2, 1].set_ylabel('Cost of Delay')

# 9. Cost of Delay vs Volume
axs[2, 2].scatter(df['Volume (cm^3)'], df['Cost of Delay'], color='brown', alpha=0.7)
axs[2, 2].set_title('Cost of Delay vs Volume')
axs[2, 2].set_xlabel('Volume (cm^3)')
axs[2, 2].set_ylabel('Cost of Delay')

plt.savefig('data_analysis_plots_1.png')

# Create a 3D subplot for LWH scatter
fig_3d = plt.figure(figsize=(10, 10))
ax = fig_3d.add_subplot(111, projection='3d')

# 3D scatter plot
scatter_3d = ax.scatter(df['Length (cm)'], df['Width (cm)'], df['Height (cm)'], c=df['Cost of Delay'], cmap='viridis', alpha=0.7)
ax.set_title('3D LWH Scatter (Color by Cost of Delay)')
ax.set_xlabel('Length (cm)')
ax.set_ylabel('Width (cm)')
ax.set_zlabel('Height (cm)')
fig_3d.colorbar(scatter_3d, ax=ax, label='Cost of Delay')

# Save the figure
plt.savefig('data_analysis_plots_2.png')

# Show the plots
# plt.show()

# Create a 3D subplot for LWH scatter
fig_3d = plt.figure(figsize=(10, 10))
ax = fig_3d.add_subplot(111, projection='3d')

# 3D scatter plot
scatter_3d = ax.scatter(df['Length (cm)'], df['Width (cm)'], df['Height (cm)'], c=df['Weight (kg)'], cmap='viridis', alpha=0.7)
ax.set_title('3D LWH Scatter (Color by Weight)')
ax.set_xlabel('Length (cm)')
ax.set_ylabel('Width (cm)')
ax.set_zlabel('Height (cm)')
fig_3d.colorbar(scatter_3d, ax=ax, label='Weight (kg)')

# Save the figure
plt.savefig('data_analysis_plots_3.png')
