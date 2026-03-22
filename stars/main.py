import numpy as np
from scipy import ndimage
from scipy.signal import convolve2d
img = np.load("stars.npy")
plus_kernel = np.array([[0,1,0],
                        [1,1,1],
                        [0,1,0]])
cross_kernel = np.array([[1,0,1],
                         [0,1,0],
                         [1,0,1]])
plus_match = convolve2d(img, plus_kernel, mode='same')
cross_match = convolve2d(img, cross_kernel, mode='same')
plus_centers = (plus_match == 5)
cross_centers = (cross_match == 5)
labeled_plus, num_plus = ndimage.label(plus_centers)
labeled_cross, num_cross = ndimage.label(cross_centers)
print(f"Количество плюсов: {num_plus}")
print(f"количество крестов: {num_cross}")
print(f"Всего звездочек:{num_plus + num_cross}")
