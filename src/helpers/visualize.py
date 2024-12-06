import numpy as np
import pyvista as pv


def draw_cuboid(grid, x, y, z, length, width, height, opacity):
    """
    Creates a cuboid and adds it to the plot.

    :param grid: The PyVista grid to add the cuboid to.
    :param x, y, z: Coordinates of the bottom-left-front corner.
    :param length, width, height: Length, width, and height of the cuboid.
    :param opacity: Opacity of the cuboid, where 1 is fully opaque and 0 is fully transparent.
    """
    # Define vertices of the cuboid in 3D space
    points = np.array([[x, y, z],  # Bottom-left-front corner
        [x + length, y, z],  # Bottom-right-front corner
        [x + length, y + width, z],  # Bottom-right-back corner
        [x, y + width, z],  # Bottom-left-back corner
        [x, y, z + height],  # Top-left-front corner
        [x + length, y, z + height],  # Top-right-front corner
        [x + length, y + width, z + height],  # Top-right-back corner
        [x, y + width, z + height],  # Top-left-back corner
    ], dtype=np.int32, )

    points = points.astype(np.float32)

    # Define the faces of the cuboid using the vertices (4 vertices per face)
    faces = np.array([[4, 0, 1, 2, 3],  # Bottom face
        [4, 7, 6, 5, 4],  # Top face
        [4, 0, 3, 7, 4],  # Left face
        [4, 1, 2, 6, 5],  # Right face
        [4, 0, 1, 5, 4],  # Front face
        [4, 3, 2, 6, 7],  # Back face
    ], dtype=np.int32, )

    # Create the cuboid mesh using PyVista
    cuboid = pv.PolyData(points, faces)

    # Color the cuboid with a random color
    color = np.random.rand(3)  # Random color (RGB)
    # Add the cuboid to the plot with the specified opacity and edges
    grid.add_mesh(cuboid, color=color, show_edges=True, opacity=opacity, edge_color="black")


def visualize_3d_packing(packer_instance):
    """
    Visualizes the packed 3D space by adding containers (ULDs) and their packed packages.

    :param packer_instance: The packer instance that holds information about ULDs and packages.
    """
    for uld in packer_instance.ulds:
        # Create a PyVista plotter for each ULD (unit load device)
        title = f"Packed ULD {uld.id}"
        plotter = pv.Plotter(title=title, window_size=(800, 600))

        ULD_L, ULD_W, ULD_H = uld.dimensions

        # Define the 3D points for the ULD container box
        container_points = np.array([[0, 0, 0],  # Bottom-left-front corner
            [ULD_L, 0, 0],  # Bottom-right-front corner
            [ULD_L, ULD_W, 0],  # Bottom-right-back corner
            [0, ULD_W, 0],  # Bottom-left-back corner
            [0, 0, ULD_H],  # Top-left-front corner
            [ULD_L, 0, ULD_H],  # Top-right-front corner
            [ULD_L, ULD_W, ULD_H],  # Top-right-back corner
            [0, ULD_W, ULD_H],  # Top-left-back corner
        ], dtype=np.float32, )

        # Define the faces of the ULD container
        container_faces = np.hstack([[4, 0, 1, 2, 3],  # Bottom face
            [4, 7, 6, 5, 4],  # Top face
            [4, 0, 3, 7, 4],  # Left face
            [4, 1, 2, 6, 5],  # Right face
            [4, 0, 1, 5, 4],  # Front face
            [4, 3, 2, 6, 7],  # Back face
        ]).reshape(-1, 5)

        # Create the ULD container mesh
        container = pv.PolyData(container_points, container_faces)

        # Add the ULD container mesh to the plot with edges
        plotter.add_mesh(container, color="lightgray", opacity=0.5, show_edges=True, edge_color="black", )

        # Add packed packages (cuboids) to the plot
        for package_id, uld_id, x, y, z, l, w, h in packer_instance.packed_positions:
            if uld_id != uld.id:
                continue
            package = next(pkg for pkg in packer_instance.packages if pkg.id == package_id)
            l, w, h = package.rotation
            draw_cuboid(plotter, x, y, z, l, w, h, 1)

        # Set the camera for an isometric view of the plot
        plotter.view_isometric()
        plotter.show(title=title)


def visualize_individual_spaces(packer_instance):
    """
    Visualizes the individual empty spaces available in the ULDs (unit load devices).

    :param packer_instance: The packer instance that contains the empty space data.
    """
    for uld in packer_instance.ulds:
        # Retrieve the list of empty spaces for the current ULD
        lsp = packer_instance.get_list_of_spaces(uld.id)
        if lsp is not None:
            for x, y, z, l, w, h in lsp:
                # Create a PyVista plotter for the current ULD
                title = f"Packed ULD {uld.id}"
                plotter = pv.Plotter(title=title, window_size=(800, 600))

                ULD_L, ULD_W, ULD_H = uld.dimensions

                # Define the 3D points for the ULD container box
                container_points = np.array([[0, 0, 0],  # Bottom-left-front corner
                    [ULD_L, 0, 0],  # Bottom-right-front corner
                    [ULD_L, ULD_W, 0],  # Bottom-right-back corner
                    [0, ULD_W, 0],  # Bottom-left-back corner
                    [0, 0, ULD_H],  # Top-left-front corner
                    [ULD_L, 0, ULD_H],  # Top-right-front corner
                    [ULD_L, ULD_W, ULD_H],  # Top-right-back corner
                    [0, ULD_W, ULD_H],  # Top-left-back corner
                ], dtype=np.float32, )

                container_faces = np.hstack([[4, 0, 1, 2, 3],  # Bottom face
                    [4, 7, 6, 5, 4],  # Top face
                    [4, 0, 3, 7, 4],  # Left face
                    [4, 1, 2, 6, 5],  # Right face
                    [4, 0, 1, 5, 4],  # Front face
                    [4, 3, 2, 6, 7],  # Back face
                ]).reshape(-1, 5)

                # Create the ULD container mesh
                container = pv.PolyData(container_points, container_faces)

                # Add the container mesh with edge color
                plotter.add_mesh(container, color="lightgray", opacity=0.5, show_edges=True, edge_color="black", )

                # Add empty spaces into the box with reduced opacity
                draw_cuboid(plotter, x, y, z, l, w, h, 0.3)

                # Add the packed packages to the plot
                for (package_id, uld_id, x, y, z, l, w, h,) in packer_instance.packed_positions:
                    if uld_id != uld.id:
                        continue
                    package = next(pkg for pkg in packer_instance.packages if pkg.id == package_id)
                    l, w, h = package.rotation
                    draw_cuboid(plotter, x, y, z, l, w, h, 1)

                # Set the camera for a good view
                plotter.view_isometric()
                plotter.show(title=title)
