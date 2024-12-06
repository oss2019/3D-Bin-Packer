from typing import List, Tuple
import numpy as np


class SpaceNode:
    """
    Represents a 3D space node for spatial subdivision and overlap management.

    Attributes:
        node_id (Any): Unique identifier for the node.
        parent (SpaceNode): Reference to the parent node, if any.
        length (float): Length of the node.
        width (float): Width of the node.
        height (float): Height of the node.
        dimensions (np.ndarray): Dimensions of the node as [length, width, height].
        start_corner (np.ndarray): Starting corner (origin) of the node.
        end_corner (np.ndarray): Ending corner of the node, calculated as start_corner + dimensions.
        is_leaf (bool): Indicates whether the node is a leaf node.
        minimum_dimension (int): Minimum allowable dimension for subdivisions.
        overlaps (List[Tuple[SpaceNode, SpaceNode]]): List of overlapping nodes and overlap regions.
        children (List[SpaceNode]): Subnodes created during subdivision.
        max_vols_in_children (List[Tuple[int, float]]): Tracks maximum volumes in child nodes.
    """

    def __init__(
        self,
        start_corner: np.ndarray,
        dimensions: np.ndarray,
        minimum_dimension: int,
        parent=None,
    ):
        """
        Initializes a SpaceNode instance.

        :param start_corner: Starting corner of the space.
        :param dimensions: Dimensions of the space [length, width, height].
        :param minimum_dimension: Minimum allowable dimension for subdivisions.
        :param parent: Parent node reference. Defaults to None.
        """
        self.node_id = None
        self.parent = parent
        self.length = dimensions[0]
        self.width = dimensions[1]
        self.height = dimensions[2]
        self.dimensions = np.array(dimensions)
        self.start_corner = start_corner
        self.end_corner = start_corner + self.dimensions

        self.is_leaf = True
        self.minimum_dimension = minimum_dimension
        # (which node, overlap region)
        self.overlaps: List[(SpaceNode, SpaceNode)] = []
        self.children: List[SpaceNode] = []
        self.max_vols_in_children: List[Tuple[int, float]] = []

    def __hash__(self):
        # Define hash behavior based on node_id
        return hash(self.node_id)

    def get_overlap(self, other):
        """
        Calculates the overlap between this node and another node.

        :param other: The other node to check for overlap.
        :return A new node representing the overlap region, or None if there is no overlap.
        """
        # Calculate the start and end corners of the overlap
        overlap_start = np.maximum(self.start_corner, other.start_corner)
        overlap_end = np.minimum(self.end_corner, other.end_corner)

        # Check if there is an overlap
        if np.all(overlap_start < overlap_end):
            overlap_dimensions = overlap_end - overlap_start
            return SpaceNode(overlap_start, overlap_dimensions, 40)
        else:
            # No overlap, return None or raise an exception as needed
            return None

    def is_completely_inside(self, other) -> bool:
        """
        Checks if this node is completely inside another node.

        :param other: The other node to check.
        :return True if this node is completely inside the other node, False otherwise.
        """
        return np.all(self.start_corner >= other.start_corner) and np.all(
            self.end_corner <= other.end_corner
        )

    def remove_links_to(self, other):
        """
        Removes references to overlaps with another node.

        :param other: The node to remove links to.
        """
        new_overlap_list = []
        for o_node, ov in self.overlaps:
            if o_node.node_id != other.node_id:
                new_overlap_list.append((o_node, ov))

        self.overlaps = new_overlap_list
        print(f"{self.node_id} removed links to {other.node_id}")

    def divide_into_subspaces(self, box_overlap):
        """
        Divides this node into subspaces by excluding a specified overlap region.

        :param box_overlap: The region to exclude.
        :return List of new subspaces created.
        """
        if not box_overlap.is_completely_inside(self):
            raise Exception("Overlap box is not inside space to divide")

        updated_spaces = []
        ax, ay, az = self.start_corner
        al, aw, ah = self.dimensions

        ox, oy, oz = box_overlap.start_corner
        ol, ow, oh = box_overlap.dimensions

        # Check for remaining free areas after packing
        # Convention: stand at origin and look towards x-infinity
        space1 = SpaceNode(
            start_corner=np.array([ax, oy + ow, az]),
            dimensions=np.array([al, aw - (oy + ow - ay), ah]),
            minimum_dimension=self.minimum_dimension,
        )  # Left full
        space2 = SpaceNode(
            start_corner=np.array([ax, ay, az]),
            dimensions=np.array([al, oy - ay, ah]),
            minimum_dimension=self.minimum_dimension,
        )  # Right full
        space3 = SpaceNode(
            start_corner=np.array([ax, ay, az]),
            dimensions=np.array([ox - ax, aw, ah]),
            minimum_dimension=self.minimum_dimension,
        )  # Back full
        # Front full
        space4 = SpaceNode(
            start_corner=np.array([ox + ol, ay, az]),
            dimensions=np.array([al - (ox + ol - ax), aw, ah]),
            minimum_dimension=self.minimum_dimension,
        )  # Front full
        space5 = SpaceNode(
            start_corner=np.array([ax, ay, az]),
            dimensions=np.array([al, aw, oz - az]),
            minimum_dimension=self.minimum_dimension,
        )  # Above full
        # Down full
        space6 = SpaceNode(
            start_corner=np.array([ax, ay, oz + oh]),
            dimensions=np.array([al, aw, ah - (oz + oh - az)]),
            minimum_dimension=self.minimum_dimension,
        )  # Down full

        # Append feasible spaces to updated_spaces
        if oy + ow < ay + aw and all(
            v >= self.minimum_dimension for v in space1.dimensions
        ):
            updated_spaces.append(space1)

        if oy > ay and all(v >= self.minimum_dimension for v in space2.dimensions):
            updated_spaces.append(space2)

        if ox > ax and all(v >= self.minimum_dimension for v in space3.dimensions):
            updated_spaces.append(space3)

        if ox + ol < ax + al and all(
            v >= self.minimum_dimension for v in space4.dimensions
        ):
            updated_spaces.append(space4)

        if oz > az and all(v >= self.minimum_dimension for v in space5.dimensions):
            updated_spaces.append(space5)

        if oz + oh < az + ah and all(
            v >= self.minimum_dimension for v in space6.dimensions
        ):
            updated_spaces.append(space6)

        return updated_spaces

    def shrink_to_avoid_overlap(self, other):
        """
        Shrinks this node and the other node to eliminate overlap.

        :param other: The node to resolve overlap with.
        """
        # Check if 'other' is completely inside 'self'
        if other.is_completely_inside(self):
            print("Other is completely inside self. No changes made.")
            return

        overlap = self.get_overlap(other)
        if not overlap:
            print("No overlap detected.")
            return

        print("Overlap detected. Shrinking both spaces.")

        # Shrink logic for both self and other based on the overlap region
        # Update end_corner for both nodes
        self.end_corner = self.start_corner + self.dimensions
        other.end_corner = other.start_corner + other.dimensions

    def _subtract(self, other):
        """
        Removes the overlap area between this node and another node.

        :param other: The node to subtract from this node.
        """
        if not (self.is_leaf and other.is_leaf):
            raise Exception("Cannot subtract from a non-empty space")

        overlap = self.get_overlap(other)
        if not overlap:  # No overlap, nothing to do
            return

        # Check if the overlap is feasible
        if all(dim < 40 for dim in overlap.dimensions):
            # Shrink both nodes to remove the overlap
            self.shrink_to_avoid_overlap(other)
        else:
            raise Exception("Overlap dimensions are too large to handle")

    def is_feasible(self):
        """
        Checks if the dimensions of this node are feasible based on the minimum_dimension.

        :return True if all dimensions are greater than or equal to minimum_dimension, False otherwise.
        """
        return all(v >= 40 for v in self.dimensions)

    def __eq__(self, other):
        """
        Checks if two nodes are equal based on their start and end corners.

        :param other: The node to compare with.
        :return True if the nodes are equal, False otherwise.
        """
        if (self.start_corner == other.start_corner).all() and (
            self.end_corner == other.end_corner
        ).all():
            return True
        return False
