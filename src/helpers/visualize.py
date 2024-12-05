# pyvista==0.44.2
import pyvista as pv
import numpy as np


def draw_cuboid(grid, x, y, z, length, width, height, opacity):
    """
    Create a cuboid and add it to the plot.

    :param grid: The PyVista grid to add the cuboid to.
    :param x, y, z: Coordinates of the bottom-left-front corner.
    :param length, width, height: Length, width, and height of the cuboid.
    :param opacity: Opacity of the cuboid.
    """
    # Define vertices of the cuboid
    points = np.array(
        [
            [x, y, z],
            [x + length, y, z],
            [x + length, y + width, z],
            [x, y + width, z],  # Bottom face
            [x, y, z + height],
            [x + length, y, z + height],
            [x + length, y + width, z + height],
            [x, y + width, z + height],  # Top face
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
    color = np.random.rand(3)  # Random color
    grid.add_mesh(
        cuboid, color=color, show_edges=True, opacity=opacity, edge_color="black"
    )  # Add the cuboid mesh


def visualize_3d_packing(packer_instance):
    for uld in packer_instance.ulds:
        # Create a PyVista plotter object
        title = f"Packed ULD {uld.id}"
        plotter = pv.Plotter(title=title, window_size=(800, 600))

        ULD_L, ULD_W, ULD_H = uld.dimensions

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
        # print(container_points)

        # Add the container mesh with edge color
        plotter.add_mesh(
            container,
            color="lightgray",
            opacity=0.5,
            show_edges=True,
            edge_color="black",
        )

        # Add the cuboids to the plot
        for package_id, uld_id, x, y, z, l, w, h in packer_instance.packed_positions:
            if uld_id != uld.id:
                continue
            package = next(
                pkg for pkg in packer_instance.packages if pkg.id == package_id
            )
            l, w, h = package.rotation
            draw_cuboid(plotter, x, y, z, l, w, h, 1)

        # WARNING: Remove this later
        lsp = packer_instance.get_list_of_spaces(uld.id)
        # if lsp is not None:
        #     for x, y, z, l, w, h in lsp:
        #         draw_cuboid(plotter, x, y, z, l, w, h, 0)

        # Set the camera position for a good view
        plotter.view_isometric()
        plotter.show(title=title)


def visualize_individual_spaces(packer_instance):
    for uld in packer_instance.ulds:
        lsp = packer_instance.get_list_of_spaces(uld.id)
        if lsp is not None:
            for x, y, z, l, w, h in lsp:
                # Create a PyVista plotter object
                title = f"Packed ULD {uld.id}"
                plotter = pv.Plotter(title=title, window_size=(800, 600))

                ULD_L, ULD_W, ULD_H = uld.dimensions

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
                # print(container_points)

                # Add the container mesh with edge color
                plotter.add_mesh(
                    container,
                    color="lightgray",
                    opacity=0.5,
                    show_edges=True,
                    edge_color="black",
                )

                # Add spaces into the box
                draw_cuboid(plotter, x, y, z, l, w, h, 0.3)

                # Add the cuboids to the plot
                for (
                    package_id,
                    uld_id,
                    x,
                    y,
                    z,
                    l,
                    w,
                    h,
                ) in packer_instance.packed_positions:
                    if uld_id != uld.id:
                        continue
                    package = next(
                        pkg for pkg in packer_instance.packages if pkg.id == package_id
                    )
                    l, w, h = package.rotation
                    draw_cuboid(plotter, x, y, z, l, w, h, 1)

                # Set the camera position for a good view
                plotter.view_isometric()
                plotter.show(title=title)
