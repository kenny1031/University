import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Create a 3D figure
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Generate meshgrid for X and Y
x = np.linspace(-2, 2, 100)
y = np.linspace(-2, 2, 100)
X, Y = np.meshgrid(x, y)

# Compute Z from xyz = 1 → Z = 1 / (XY)
Z = 1 / (X * Y)
Z[np.abs(X * Y) < 1e-6] = np.nan  # Avoid division by zero

# Plot the surface
ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='k', alpha=0.8)

# Labels and title
ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')
ax.set_zlabel('Z-axis')
ax.set_title('Plot of xyz = 1')

# Show the plot
plt.show()

