import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def generate_3d_plot(packer_instance, output_dir):
    """
    Generates 3D plots of packed ULDs (unit load devices) and their packages, and saves them as images.

    :param packer_instance: The packer instance containing information about ULDs, packages, and their positions.
    :param output_dir: The directory where the generated plots will be saved.
    """
    for uld in packer_instance.ulds:
        # Create a new figure for each ULD
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        # Set limits for the 3D axes based on ULD dimensions
        ax.set_xlim(0, uld.dimensions[0])
        ax.set_ylim(0, uld.dimensions[1])
        ax.set_zlim(0, uld.dimensions[2])

        # Set axis labels and plot title
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(f"Packed ULD {uld.id}")

        # Initialize a variable to generate distinct colors for each package
        random_int = 0

        # Loop through the packed positions and plot each package
        for (package_id, uld_id, x, y, z, length, width, height) in packer_instance.packed_positions:
            if uld.id == uld_id:
                # Retrieve the package details (could be used if needed)
                next(pkg for pkg in packer_instance.packages if pkg.id == package_id)

                # Define the vertices for the package (cuboid) in 3D space
                vertices = [
                    [x, y, z],  # Bottom-left-front corner
                    [x + length, y, z],  # Bottom-right-front corner
                    [x + length, y + width, z],  # Bottom-right-back corner
                    [x, y + width, z],  # Bottom-left-back corner
                    [x, y, z + height],  # Top-left-front corner
                    [x + length, y, z + height],  # Top-right-front corner
                    [x + length, y + width, z + height],  # Top-right-back corner
                    [x, y + width, z + height],  # Top-left-back corner
                ]

                # Define the faces of the package (each face is a quadrilateral defined by 4 vertices)
                faces = [
                    [vertices[0], vertices[1], vertices[5], vertices[4]],  # Front face
                    [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right face
                    [vertices[2], vertices[3], vertices[7], vertices[6]],  # Back face
                    [vertices[3], vertices[0], vertices[4], vertices[7]],  # Left face
                    [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom face
                    [vertices[4], vertices[5], vertices[6], vertices[7]],  # Top face
                ]

                # Assign a color to the package using a colormap, ensuring distinct colors
                random_int += 1
                color = plt.cm.Paired(random_int % 12)  # Use the Paired colormap for different colors

                # Add the package faces to the 3D plot with the specified color and edge color
                ax.add_collection3d(Poly3DCollection(faces, facecolors=color, edgecolors="black", alpha=0.7))

        # Set the view angle to get a good perspective of the packed ULD
        ax.view_init(elev=35, azim=45)  # Adjust the camera elevation and azimuth

        # Save the 3D plot as an image in the specified output directory
        plt.savefig(f"{output_dir}/packed_uld_{uld.id}.png")

        # Display the plot
        plt.show()
