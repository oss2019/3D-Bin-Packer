import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
import random

def generate_packages(volumes):
    cubes = []
    cuboids = []
    key = 0
    for V in volumes:
            delta = (V**(1/3) + ((V**(1/3))/5)* np.random.randn()) 
            if (key % 2 == 0):
              # Cube dimensions
              length = int((V + delta)**(1/3))
              delta = (V**(1/3) + ((V**(1/3))/5)* np.random.randn()) 
              width = int((V + delta)**(1/3))
              delta = (V**(1/3) + ((V**(1/3))/5)* np.random.randn()) 
              height = int((V + delta)**(1/3))
              cubes.append((length, width, height))
            if (key % 2 == 1):  
              # Cuboid dimensions
              base = int(((V + delta)**(1/3)) / math.sqrt(2))
              delta = (V**(1/3) + ((V**(1/3))/5)* np.random.randn()) 
              base2 = int(((V + delta)**(1/3)) / math.sqrt(2))
              delta = (V**(1/3) + ((V**(1/3))/5)* np.random.randn()) 
              height = 2 * base + delta
              cuboids.append((base, base2, 2 * base))
            key += 1  
    
    return cubes, cuboids
  
csv_file = 'data.csv'  # Replace with your actual file path
data = pd.read_csv(csv_file)
volumes = data['Volume'].tolist()
weights = data['Weight'].tolist()
cubes, cuboids = generate_packages(volumes)
with open('packages.csv', 'w') as f:
    # Write the header
    output = "Id,Length,Width,Height,Weight,Type,Cost of Delay"
    print(output, file=f)
    
    # Initialize a counter for unique IDs
    package_id = 1
    types = ['Economy'] * (len(cubes) + len(cuboids))  # Start by assuming all packages are Economy

    # Randomly assign 25% of packages as Priority
    priority_count = int(0.25 * len(types))
    priority_indices = random.sample(range(len(types)), priority_count)  # Randomly pick indices

    # Assign "Priority" to the selected indices
    for i in priority_indices:
        types[i] = 'Priority'    
    
    # Write cubes with IDs
    for i, cube in enumerate(cubes):
        weight = int(weights[i])  # Serial assignment of weights
        package_type = types[i]
        if package_type == 'Economy':
            cost_of_delay = random.randint(60, 200)  # Random delay cost between 60 and 200 for Economy
        else:
            cost_of_delay = '-'
        output = f"P-{package_id},{cube[0]},{cube[1]},{cube[2]},{weight},{package_type},{cost_of_delay}"
        print(output, file=f)
        package_id += 1
    
    # Assign weights to cuboids
    for i, cuboid in enumerate(cuboids):
        weight = int(weights[len(cubes) + i])  # Continue from where cubes ended
        package_type = types[len(cubes) + i]  # Use the corresponding type
        if package_type == 'Economy':
            cost_of_delay = random.randint(60, 200)  # Random delay cost between 60 and 200 for Economy
        else:
            cost_of_delay = '-'
        output = f"P-{package_id},{cuboid[0]},{cuboid[1]},{cuboid[2]},{weight},{package_type},{cost_of_delay}"
        print(output, file=f)
        package_id += 1   
