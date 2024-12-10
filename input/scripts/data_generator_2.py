import numpy as np

def generate_3d_points(n, a, b):
    """
    Generate n 3D points uniformly distributed in the range [a, b].

    Parameters:
    n (int): Number of 3D points to generate.
    a (float): Lower bound of the uniform distribution.
    b (float): Upper bound of the uniform distribution.

    Returns:
    np.ndarray: An array of shape (n, 3) containing the generated 3D points.
    """
    points = np.random.uniform(a, b, size=(n, 3))
    return points

# Example usage:
n = 400  # Number of points
a = 40   # Lower bound
b = 100   # Upper bound
points = generate_3d_points(n, a, b)

def generate_uniform_cost_of_delays(points, lcd, ucd):
    """
    Generate a 1D array of cost of delays drawn from a uniform distribution [lcd, ucd].

    Parameters:
    points (np.ndarray): An array of shape (n, 3).
    lcd (float): Lower bound of the uniform distribution.
    ucd (float): Upper bound of the uniform distribution.

    Returns:
    np.ndarray: A 1D array of shape (n,) with the generated uniform values.
    """
    if points.shape[1] != 3:
        raise ValueError("Input array must have shape (n, 3)")

    # Generate the uniform values
    uniform_values = np.random.uniform(lcd, ucd, size=points.shape[0])

    return uniform_values

# Example usage:
lcd = 60  # Lower bound for the uniform distribution
ucd = 140  # Upper bound for the uniform distribution
cost_of_delays = generate_uniform_cost_of_delays(points, lcd, ucd)
# print(cost_of_delays)

def generate_weights(points, k1, k2):
    """
    Generate a 1D list of weights based on the volume of points in an (n, 3) array.

    Parameters:
    points (np.ndarray): An array of shape (n, 3) where each row represents (x, y, z).
    k1 (float): Lower multiplier for the volume.
    k2 (float): Upper multiplier for the volume.

    Returns:
    list: A 1D list of sampled values.
    """
    if points.shape[1] != 3:
        raise ValueError("Input array must have shape (n, 3)")

    # Calculate the volume for each point
    volumes = np.prod(points, axis=1)  # vol = x * y * z

    # Generate uniform samples based on the calculated volumes
    uniform_samples = np.random.uniform(k1 * volumes, k2 * volumes)

    return uniform_samples.tolist()  # Convert to a list

# Example usage:
k1 = 100 / (1.2 * 10**6)  # Lower multiplier
k2 = 300 / (1.2 * 10**6)  # Upper multiplier
weights = generate_weights(points, k1, k2)
# print(weights)

def generate_priority_economy_array(n):
    """
    Generate an array of 'Priority' and 'Economy' strings, with approximately 25% being 'Priority'.

    Parameters:
    n (int): Size of the array to generate.

    Returns:
    np.ndarray: An array of strings with 'Priority' and 'Economy'.
    """
    # Generate random values between 0 and 1
    random_values = np.random.uniform(0, 1, size=n)

    # Assign 'Priority' if the random value is less than 0.25, otherwise 'Economy'
    priority_economy_array = np.where(random_values < 0.25, 'Priority', 'Economy')

    return priority_economy_array

# Example usage:
n = 400  # Size of the array
priority_economy_array = generate_priority_economy_array(n)

def generate_id(n):
    """
    Generate a list of numbers from 1 to n.

    Parameters:
    n (int): The upper limit of the list.

    Returns:
    list: A list of numbers from 1 to n.
    """
    return list(range(1, n + 1))

# Example usage:
n = 400  # Size of the list
ids = generate_id(n)
# print(ids)

# Function to truncate floats to integers
def truncate_to_int(x):
    return x.astype(int)

cost_of_delays = truncate_to_int(cost_of_delays)

import pandas as pd
import numpy as np

# Assuming ids, points, weights, priority_economy_array, and cost_of_delays are already defined

# Create a DataFrame from the generated data
data = {
    'Package Identifier': ids,
    'Length (cm)': points[:, 0],
    'Width (cm)': points[:, 1],
    'Height (cm)': points[:, 2],
    'Weight (kg)': weights,
    'Type (P/E)': priority_economy_array,
    'Cost of Delay': np.where(priority_economy_array == 'Priority', '-', cost_of_delays)
}

df = pd.DataFrame(data)


# Truncate the float columns to integers
df['Length (cm)'] = truncate_to_int(df['Length (cm)'])
df['Width (cm)'] = truncate_to_int(df['Width (cm)'])
df['Height (cm)'] = truncate_to_int(df['Height (cm)'])
df['Weight (kg)'] = truncate_to_int(df['Weight (kg)'])

# Save the DataFrame to a CSV file
df.to_csv('output.csv', index=False)

print("CSV file 'output.csv' has been generated.")






