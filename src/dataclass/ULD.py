import numpy as np

# Define the ULD class
class ULD:
    """
    A class representing a Unit Load Device (ULD), which is used to store and transport packages.

    :param id: The unique identifier for the ULD.
    :param length: The length of the ULD.
    :param width: The width of the ULD.
    :param height: The height of the ULD.
    :param weight_limit: The maximum weight the ULD can carry.
    """
    def __init__(
        self, id: str, length: int, width: int, height: int, weight_limit: int
    ):
        # Initialize the ULD attributes
        self.id = id  # Unique identifier for the ULD
        self.dimensions = np.array([length, width, height])  # ULD dimensions as a numpy array
        self.weight_limit = weight_limit  # Maximum weight capacity for the ULD
        self.current_weight = 0  # The current weight of the ULD (initialized to 0)
        self.current_vol_occupied = 0  # The current volume occupied in the ULD (initialized to 0)
