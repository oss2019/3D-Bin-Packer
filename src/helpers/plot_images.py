import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
# import warnings
#
# warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")


def generate_3d_plot(packer_instance, output_dir):
    for uld in packer_instance.ulds:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        # Set limits for the axes
        ax.set_xlim(0, uld.dimensions[0])
        ax.set_ylim(0, uld.dimensions[1])
        ax.set_zlim(0, uld.dimensions[2])

        # Set labels and title
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(f"Packed ULD {uld.id}")

        random_int = 0

        # Plot each package
        for (
            package_id,
            uld_id,
            x,
            y,
            z,
            length,
            width,
            height,
        ) in packer_instance.packed_positions:
            if uld.id == uld_id:
                package = next(
                    pkg for pkg in packer_instance.packages if pkg.id == package_id
                )

                # Create vertices for the package
                vertices = [
                    [x, y, z],
                    [x + length, y, z],
                    [x + length, y + width, z],
                    [x, y + width, z],
                    [x, y, z + height],
                    [x + length, y, z + height],
                    [x + length, y + width, z + height],
                    [x, y + width, z + height],
                ]

                # Define the faces of the package
                faces = [
                    [vertices[0], vertices[1], vertices[5], vertices[4]],
                    [vertices[1], vertices[2], vertices[6], vertices[5]],
                    [vertices[2], vertices[3], vertices[7], vertices[6]],
                    [vertices[3], vertices[0], vertices[4], vertices[7]],
                    [vertices[0], vertices[1], vertices[2], vertices[3]],
                    [vertices[4], vertices[5], vertices[6], vertices[7]],
                ]

                # Assign a color to the package
                random_int += 1
                color = plt.cm.Paired(random_int % 12)
                ax.add_collection3d(
                    Poly3DCollection(
                        faces,
                        facecolors=color,
                        edgecolors="black",
                        alpha=0.8,
                    )
                )

        # Set the view angle
        ax.view_init(elev=35, azim=45)  # Looking at (0,0,0) from ~(1,1,1)

        # Save the 3D plot as an image
        plt.savefig(f"{output_dir}/packed_uld_{uld.id}.png")
        plt.show()