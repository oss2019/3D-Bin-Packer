import numpy as np

# Define the Package class
class Package:
    """
    A class representing a package with specific dimensions, weight, and priority.

    :param id: The unique identifier for the package.
    :param length: The length of the package.
    :param width: The width of the package.
    :param height: The height of the package.
    :param weight: The weight of the package.
    :param is_priority: A boolean indicating if the package is a priority package.
    :param delay_cost: The cost incurred if the package is delayed.
    """
    def __init__(
        self,
        id: str,
        length: int,
        width: int,
        height: int,
        weight: int,
        is_priority: bool,
        delay_cost: int,
    ):
        # Initialize the package attributes
        self.id = id  # Unique identifier for the package
        self.length = length  # Length of the package
        self.width = width  # Width of the package
        self.height = height  # Height of the package
        self.dimensions = np.array([length, width, height])  # Package dimensions as a numpy array
        self.volume = length * width * height # Volume of the package
        self.weight = weight  # Weight of the package
        self.rotation = self.dimensions  # Rotation of the package (initially same as the dimensions)
        self.is_priority = is_priority  # Whether the package is a priority package
        self.delay_cost = delay_cost  # The cost associated with delays for this package
