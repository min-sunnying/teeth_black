import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib import style

plt.figure('SPLTV', figsize=(10, 5))
custom=plt.subplot(121, projection='3d')
x1=np.array([1, -2, 1])
y1=np.array([5, 3, 7])
z1=np.array([0, 0, 6])

custom.scatter(x1, y1, z1)

verts=[list(zip(x1, y1, z1))]
srf=Poly3DCollection(verts, alpha=.25, facecolor='#800000')
plt.gca.add_collection3d(srf)

custom.set_xlabel('X')
custom.set_ylabel('Y')
custom.set_zlabel('Z')
plt.show()