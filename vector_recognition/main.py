import numpy as np
import matplotlib.pyplot as plt
from skimage.measure import label, regionprops
from skimage.io import imread
from pathlib import Path

save_path = Path(__file__).parent

def count_holes(region):
    shape = region.image.shape
    padded = np.zeros((shape[0] + 2, shape[1] + 2))
    padded[1:-1, 1:-1] = region.image
    inverted = np.logical_not(padded)
    labeled = label(inverted)
    return np.max(labeled) - 1

def count_lines(region):
    img = region.image
    h, w = img.shape
    v_lines = (np.sum(img, axis=0) / h == 1).sum()
    h_lines = (np.sum(img, axis=1) / w == 1).sum()
    return v_lines, h_lines

def symmetry(region, transpose=False):
    img = region.image
    if transpose:
        img = img.T
    h = img.shape[0]
    top = img[:h // 2]
    bottom = img[h // 2 + (h % 2):][::-1]
    comparison = bottom == top
    return comparison.sum() / comparison.size

def extractor(region):
    h, w = region.image.shape
    cy, cx = region.centroid_local
    cy /= h
    cx /= w
    
    perimeter = region.perimeter / region.image.size
    holes = count_holes(region)
    
    v, h_lines = count_lines(region)
    v /= w
    h_lines /= h
    
    return np.array([
        region.area / region.image.size,
        cx, cy,
        perimeter,
        holes,
        v, h_lines,
        region.eccentricity,
        h / w,
        region.solidity,
        region.extent,
        symmetry(region),
        symmetry(region, transpose=True)
    ])

def classificator(region, templates):
    features = extractor(region)
    best_symbol = ""
    min_distance = float('inf')
    
    for symbol, template in templates.items():
        distance = np.linalg.norm(template - features)
        if distance < min_distance:
            min_distance = distance
            best_symbol = symbol
    return best_symbol

template_img = imread("alphabet/alphabet-small.png")[:, :, :-1]
template_gray = template_img.sum(axis=2)
template_binary = template_gray != 765

labeled_template = label(template_binary)
regions_template = regionprops(labeled_template)

symbols = ["8", "O", "A", "B", "1", "W", "X", "*", "/", "-"]
templates = {
    symbol: extractor(region)
    for symbol, region in zip(symbols, regions_template)
}

target_img = imread("alphabet/alphabet.png")[:, :, :-1]
target_binary = target_img.mean(axis=2) > 0

labeled_target = label(target_binary)
regions_target = regionprops(labeled_target)

output_dir = save_path / "out"
output_dir.mkdir(exist_ok=True)

counts = {}
plt.figure(figsize=(5, 7))

for i, region in enumerate(regions_target):
    symbol = classificator(region, templates)
    counts[symbol] = counts.get(symbol, 0) + 1
    
    plt.clf()
    plt.title(f"Class: '{symbol}'")
    plt.imshow(region.image, cmap='gray')
    plt.savefig(output_dir / f"region_{i:03d}.png")

print("Результаты")
print(counts)

plt.figure()
plt.imshow(labeled_target)
plt.show()
