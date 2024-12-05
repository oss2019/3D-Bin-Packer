from typing import List, Tuple
import numpy as np


class SpaceNode:
    def __init__(self, start_corner: np.ndarray, dimensions: np.ndarray, parent=None):
        self.node_id = None
        self.parent = parent
        self.length = dimensions[0]
        self.width = dimensions[1]
        self.height = dimensions[2]
        self.dimensions = np.array(dimensions)
        self.start_corner = start_corner
        self.end_corner = start_corner + self.dimensions

        self.is_leaf = True

        # (which node, overlap region)
        self.overlaps: List[(SpaceNode, SpaceNode)] = []
        self.children: List[SpaceNode] = []
        self.max_vols_in_children: List[Tuple[int, float]] = []

    def __hash__(self):
        return hash(self.node_id)

    def get_overlap(self, other):
        # Calculate the start and end corners of the overlap
        overlap_start = np.maximum(self.start_corner, other.start_corner)
        overlap_end = np.minimum(self.end_corner, other.end_corner)

        # Check if there is an overlap
        if np.all(overlap_start < overlap_end):
            overlap_dimensions = overlap_end - overlap_start
            return SpaceNode(overlap_start, overlap_dimensions)
        else:
            # No overlap, return None or raise an exception as needed
            return None

    def is_completely_inside(self, other) -> bool:
        return np.all(self.start_corner >= other.start_corner) and np.all(
            self.end_corner <= other.end_corner
        )

    def remove_links_to(self, other):
        new_overlap_list = []
        for o_node, ov in self.overlaps:
            if o_node.node_id != other.node_id:
                new_overlap_list.append((o_node, ov))

        self.overlaps = new_overlap_list
        print(f"{self.node_id} removed links to {other.node_id}")

    # Unused function
    # def is_shrinkable_after_placing(self, box_overlap):
    #     if (
    #         (box_overlap.length * box_overlap.width == self.length * self.width)
    #         or (box_overlap.height * box_overlap.width == self.height * self.width)
    #         or (box_overlap.height * box_overlap.length == self.height * self.length)
    #     ):
    #         return True
    #
    #     return False

    def divide_into_subspaces(self, box_overlap):
        if not box_overlap.is_completely_inside(self):
            raise Exception("Overlap box is not inside space to divide")

        updated_spaces = []
        ax, ay, az = self.start_corner
        al, aw, ah = self.dimensions

        ox, oy, oz = box_overlap.start_corner
        ol, ow, oh = box_overlap.dimensions

        # Check for remaining free areas after packing
        # Convention, stand at origin and look towards x-infty
        space1 = SpaceNode(
            start_corner=np.array([ax, oy + ow, az]),
            dimensions=np.array([al, aw - (oy + ow - ay), ah]),
        )  # Left full
        space2 = SpaceNode(
            start_corner=np.array([ax, ay, az]), dimensions=np.array([al, oy - ay, ah])
        )  # Right full
        space3 = SpaceNode(
            start_corner=np.array([ax, ay, az]), dimensions=np.array([ox - ax, aw, ah])
        )  # Back full
        # Front full
        space4 = SpaceNode(
            start_corner=np.array([ox + ol, ay, az]),
            dimensions=np.array([al - (ox + ol - ax), aw, ah]),
        )  # Front full
        space5 = SpaceNode(
            start_corner=np.array([ax, ay, az]), dimensions=np.array([al, aw, oz - az])
        )  # Above full
        # Down full
        space6 = SpaceNode(
            start_corner=np.array([ax, ay, oz + oh]),
            dimensions=np.array([al, aw, ah - (oz + oh - az)]),
        )  # Down full

        if oy + ow < ay + aw and all(v > 0 for v in space1.dimensions):
            updated_spaces.append(space1)
            # print(f"Appending {space1}")

        if oy > ay and all(v > 40 for v in space2.dimensions):
            updated_spaces.append(space2)
            # print(f"Appending {space2}")

        if ox > ax and all(v > 40 for v in space3.dimensions):
            updated_spaces.append(space3)
            # print(f"Appending {space3}")

        if ox + ol < ax + al and all(v > 40 for v in space4.dimensions):
            updated_spaces.append(space4)
            # print(f"Appending {space4}")

        if oz > az and all(v > 40 for v in space5.dimensions):
            updated_spaces.append(space5)
            # print(f"Appending {space5}")

        if oz + oh < az + ah and all(v > 40 for v in space6.dimensions):
            updated_spaces.append(space6)
            # print(f"Appending {space6}")

        return updated_spaces

    def shrink_to_avoid_overlap(self, other):
        # Check if 'other' is completely inside 'self'
        if other.is_completely_inside(self):
            print("Other is completely inside self. No changes made.")
            return

        overlap = self.get_overlap(other)
        if not overlap:
            print("No overlap detected.")
            return

        print("Overlap detected. Shrinking both spaces.")

        # Get the overlap dimensions and positions
        ax, ay, az = self.start_corner
        al, aw, ah = self.dimensions

        bx, by, bz = other.start_corner
        bl, bw, bh = other.dimensions

        ox, oy, oz = overlap.start_corner
        ol, ow, oh = overlap.dimensions

        # Shrink self (self needs to shrink in direction of overlap)
        # Shrink along the x-axis
        if ox > ax:
            self.dimensions[0] = ox - ax  # Shrink self from left
        elif ox + ol < ax + al:
            self.start_corner[0] = ox + ol
            self.dimensions[0] = ax + al - (ox + ol)  # Shrink self from right

        # Shrink along the y-axis
        if oy > ay:
            self.dimensions[1] = oy - ay  # Shrink self from bottom
        elif oy + ow < ay + aw:
            self.start_corner[1] = oy + ow
            self.dimensions[1] = ay + aw - (oy + ow)  # Shrink self from top

        # Shrink along the z-axis
        if oz > az:
            self.dimensions[2] = oz - az  # Shrink self from below
        elif oz + oh < az + ah:
            self.start_corner[2] = oz + oh
            self.dimensions[2] = az + ah - (oz + oh)  # Shrink self from above

        # Shrink other (other needs to shrink in direction of overlap)
        # Shrink along the x-axis
        if ox > bx:
            other.dimensions[0] = ox - bx  # Shrink other from left
        elif ox + ol < bx + bl:
            other.start_corner[0] = ox + ol
            other.dimensions[0] = bx + bl - (ox + ol)  # Shrink other from right

        # Shrink along the y-axis
        if oy > by:
            other.dimensions[1] = oy - by  # Shrink other from bottom
        elif oy + ow < by + bw:
            other.start_corner[1] = oy + ow
            other.dimensions[1] = by + bw - (oy + ow)  # Shrink other from top

        # Shrink along the z-axis
        if oz > bz:
            other.dimensions[2] = oz - bz  # Shrink other from below
        elif oz + oh < bz + bh:
            other.start_corner[2] = oz + oh
            other.dimensions[2] = bz + bh - (oz + oh)  # Shrink other from above

        # Update end_corner for both nodes
        self.end_corner = self.start_corner + self.dimensions
        other.end_corner = other.start_corner + other.dimensions

    def _subtract(self, other):
        if not (self.is_leaf and other.is_leaf):
            raise Exception("Cannot subtract from a non-empty space")

        overlap = self.get_overlap(other)
        if not overlap:  # No overlap, nothing to do
            return

        # Check if the overlap is feasible (all dimensions are less than 40)
        if all(dim < 40 for dim in overlap.dimensions):
            # Shrink both nodes to remove the overlap
            self.shrink_to_avoid_overlap(other)
        else:
            raise Exception("Overlap dimensions are too large to handle")

    def is_feasible(self):
        return all(v >= 40 for v in self.dimensions)

    def __eq__(self, other):
        if (self.start_corner == other.start_corner).all() and (
            self.end_corner == other.end_corner
        ).all():
            return True
        return False
