# pyvista==0.44.2
import pyvista as pv
import numpy as np


def draw_cuboid(grid, x, y, z, l, w, h):
    """
    Create a cuboid and add it to the plot.
    :param grid: The PyVista grid to add the cuboid to.
    :param x, y, z: Coordinates of the bottom-left-front corner.
    :param l, w, h: Length, width, and height of the cuboid.
    """
    # Define vertices of the cuboid
    points = np.array(
        [
            [x, y, z],
            [x + l, y, z],
            [x + l, y + w, z],
            [x, y + w, z],  # Bottom face
            [x, y, z + h],
            [x + l, y, z + h],
            [x + l, y + w, z + h],
            [x, y + w, z + h],  # Top face
        ],
        dtype=np.int32,
    )

    points = points.astype(np.float32)
    # Define the faces of the cuboid (each face consists of four vertices)
    faces = np.array(
        [
            [4, 0, 1, 2, 3],  # Bottom face
            [4, 7, 6, 5, 4],  # Top face
            [4, 0, 3, 7, 4],  # Left face
            [4, 1, 2, 6, 5],  # Right face
            [4, 0, 1, 5, 4],  # Front face
            [4, 3, 2, 6, 7],  # Back face
        ],
        dtype=np.int32,
    )

    # Create the cuboid mesh
    cuboid = pv.PolyData(points, faces)

    # Color the cuboid with a random color
    color = np.random.rand(
        3,
    )  # Random color
    grid.add_mesh(
        cuboid, color=color, show_edges=True, edge_color="black"
    )  # Add the cuboid mesh


def visualize_3d_packing(
    ULD_L: int,
    ULD_W: int,
    ULD_H: int,
    x_vals: list[int],
    y_vals: list[int],
    z_vals: list[int],
    lengths: list[int],
    widths: list[int],
    heights: list[int],
    fitted_flags: list[int],
    title: str,
):
    # Create a PyVista plotter object
    plotter = pv.Plotter(title=title, window_size=(800, 600))

    # Add a 3D container box
    container_points = np.array(
        [
            [0, 0, 0],
            [ULD_L, 0, 0],
            [ULD_L, ULD_W, 0],
            [0, ULD_W, 0],  # Bottom face
            [0, 0, ULD_H],
            [ULD_L, 0, ULD_H],
            [ULD_L, ULD_W, ULD_H],
            [0, ULD_W, ULD_H],  # Top face
        ],
        dtype=np.float32,
    )

    container_faces = np.hstack(
        [
            [4, 0, 1, 2, 3],  # Bottom face
            [4, 7, 6, 5, 4],  # Top face
            [4, 0, 3, 7, 4],  # Left face
            [4, 1, 2, 6, 5],  # Right face
            [4, 0, 1, 5, 4],  # Front face
            [4, 3, 2, 6, 7],  # Back face
        ]
    ).reshape(-1, 5)

    # Create the container as a mesh
    container = pv.PolyData(container_points, container_faces)

    # Add the container mesh with edge color
    plotter.add_mesh(
        container, color="lightgray", opacity=0.5, show_edges=True, edge_color="black"
    )

    # Add the cuboids to the plot
    for i in range(len(fitted_flags)):
        if fitted_flags[i] == 0:  # If the cuboid is not fitted, skip it
            continue
        x, y, z = x_vals[i], y_vals[i], z_vals[i]
        l, w, h = lengths[i], widths[i], heights[i]
        draw_cuboid(plotter, x, y, z, l, w, h)

    # Set the camera position for a good view
    plotter.view_isometric()

    # Show the plot interactively
    plotter.show(title=title)