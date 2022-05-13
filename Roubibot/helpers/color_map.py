import numpy as np
import matplotlib.pyplot as plt

# H = np.array([[0, 0, 20, 0],
#           [5, 6, 7, 8],
#           [9, 10, 11, 12],
#           [13, 14, 15, 16]])
#
# plt.imshow(H, interpolation='none')
# plt.show()


def color_map(map):
    image = np.array(map)

    plt.imshow(image, interpolation='none')
    plt.show()