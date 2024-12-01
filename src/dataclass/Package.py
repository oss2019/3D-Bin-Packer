import numpy as np


# Define the Package class
class Package:
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
        self.id = id
        self.dimensions = np.array([length, width, height])
        self.weight = weight
        self.is_priority = is_priority
        self.delay_cost = delay_cost
