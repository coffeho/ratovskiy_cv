import numpy as np
import matplotlib.pyplot as plt
import glob
from scipy import ndimage

files = sorted(glob.glob("out/h_*.npy"), key=lambda x: int(x.split('_')[1].split('.')[0]))

traj = {}

for f, file in enumerate(files):
    img = np.load(file)
    labeled, n = ndimage.label(img > np.mean(img) + np.std(img))
    
    objs = []
    for i in range(1, n + 1):
        mask = labeled == i
        if mask.sum() > 10:
            y, x = ndimage.center_of_mass(mask)
            objs.append((x, y))
    
    if f == 0:
        for i, (x, y) in enumerate(objs):
            traj[i] = [(x, y)]
    else:
        used = set()
        for obj_id, points in traj.items():
            last_x, last_y = points[-1]
            if objs:
                dists = sorted([(abs(x - last_x) + abs(y - last_y), x, y) for x, y in objs])
                if dists[0][0] < 50:
                    traj[obj_id].append((dists[0][1], dists[0][2]))
                    objs.remove((dists[0][1], dists[0][2]))
                    used.add(obj_id)
        
        for x, y in objs:
            traj[max(traj.keys()) + 1 if traj else 0] = [(x, y)]

plt.figure()
for points in traj.values():
    if len(points) > 1:
        p = np.array(points)
        plt.plot(p[:, 0], p[:, 1], 'o-')
plt.axis('equal')
plt.show()
