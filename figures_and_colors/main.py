import numpy as np
import matplotlib.pyplot as plt
from skimage.measure import label, regionprops
from skimage.io import imread
from skimage.color import rgb2hsv
from pathlib import Path

source_dir = Path(__file__).parent
pic_path = source_dir / "balls_and_rects.png"
img_data = imread(str(pic_path))

hsv_matrix = rgb2hsv(img_data)
hue_channel = hsv_matrix[:, :, 0]
val_channel = hsv_matrix[:, :, 2]

segments_map = label(val_channel > 0.3)
print(f"Количество всех фигур на изображении: {segments_map.max()}\n")

sorted_figures = {"circle": {}, "rectangle": {}}

for prop in regionprops(segments_map):
    object_mask = (segments_map == prop.label)
    avg_hue = hue_channel[object_mask].mean()

    form_factor = (4 * np.pi * prop.area) / (prop.perimeter ** 2)
    fill_ratio = prop.extent

    type_key = "circle" if (fill_ratio < 0.9 and form_factor > 0.85) else "rectangle"
    
    current_dict = sorted_figures[type_key]
    current_dict[avg_hue] = current_dict.get(avg_hue, 0) + 1

for name, color_groups in sorted_figures.items():
    print(f"{name}:")
    for hue_key, amount in color_groups.items():
        print(f"   оттенок {hue_key:.3f}: {amount} шт.")
    print()

plt.imshow(hue_channel, cmap="gray")
plt.title("Карта оттенков (H)")
plt.axis("off")
plt.show()
