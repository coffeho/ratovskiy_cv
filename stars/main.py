import numpy as np
img = np.load("stars.npy")  
h, w = img.shape
plus_centers = []  
cross_centers = []
def is_plus(img, x, y):   
    if (x+1 < w and img[y, x+1] == 1 and
        x-1 >= 0 and img[y, x-1] == 1 and  
        y+1 < h and img[y+1, x] == 1 and 
        y-1 >= 0 and img[y-1, x] == 1):
        return True
    return False
def is_cross(img, x, y):
    if (x+1 < w and y+1 < h and img[y+1, x+1] == 1 and  
        x-1 >= 0 and y-1 >= 0 and img[y-1, x-1] == 1 and   
        x+1 < w and y-1 >= 0 and img[y-1, x+1] == 1 and 
        x-1 >= 0 and y+1 < h and img[y+1, x-1] == 1): 
        return True  
    return False  
for y in range(h):  
    for x in range(w):  
        if img[y, x] == 1:  
            if is_plus(img, x, y):  
                plus_centers.append((x, y))  
            elif is_cross(img, x, y): 
                cross_centers.append((x, y)) 
print(f"Плюсов:{len(plus_centers)}")  
print(f"крестов: {len(cross_centers)}") 
print(f"всего звезд: {len(plus_centers) + len(cross_centers)}")
