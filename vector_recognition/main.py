import numpy as np
import matplotlib.pyplot as plt
from skimage.measure import label, regionprops
from skimage.io import imread
from pathlib import Path

save_path = Path(__file__).parent

def extractor(region):
    cy,cx = region.centroid_local
    cy /= region.image.shape[0]
    cx /= region.image.shape[1]
    return np.array([region.area/region.image.size, cy,cx])

def classificator(region, templates):
    features = extractor(region)
    result = ""
    min_d = 10**6
    for symbol, t in templates.items():
        d = ((t-features)**2).sum() ** 0.5
        if d < min_d:
            result = symbol
            min_d = d
    return result

template = imread("alphabet/alphabet-small.png")[:,:,:-1]
print(template.shape)
template = template.sum(2)
binary = template != 765

labeled = label(binary)
props = regionprops(labeled)

templates = {}
for region,symbol in zip(props, ["8", "O", "A", "B", "1", "W", "X", "*", "/", "-"]):
    templates[symbol] = extractor(region)
print(templates)

print(classificator(props[5], templates))


print(type(props[0]))
print(props[0].area, props[0].centroid, props[0].label)


image = imread("alphabet/alphabet.png")[:,:,:-1]
abinary = image.mean(2) > 0
alabeled = label(abinary)
print(alabeled.max())

aprops = regionprops(alabeled)
result = {}
image_path = save_path / "out"
image_path.mkdir(exist_ok=True)

plt.figure(figsize=(5,7))
for region in aprops:
    symbol = classificator(region, templates)
    if symbol not in result:
        result[symbol] = 0
    result[symbol] += 1
    plt.cla()
    plt.title(f"Class - '{symbol}'")
    plt.imshow(region.image)
    plt.savefig(image_path/f"image_{region.label}.png")
print(result)

plt.imshow(alabeled)
plt.show()
