import numpy as np


# Define the ULD class
class ULD:
    def __init__(
        self, id: str, length: int, width: int, height: int, weight_limit: int
    ):
        self.id = id
        self.dimensions = np.array([length, width, height])
        self.weight_limit = weight_limit
        self.current_weight = 0
        self.occupied_positions = []  # List of occupied spaces (x, y, z, length, width, height)
        self.available_spaces = [
            (0, 0, 0, length, width, height)
        ]  # List of available spaces
