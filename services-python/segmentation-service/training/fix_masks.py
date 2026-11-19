from PIL import Image, ImageOps
from pathlib import Path
import numpy as np

for split in ['train', 'val']:
    for mask_path in Path(f'data/segmentation/{split}/masks').glob('*.png'):
        mask = Image.open(mask_path).convert('L')
        mask_np = np.array(mask)
        if (mask_np > 127).sum() / mask_np.size > 0.5:
            ImageOps.invert(mask).save(mask_path)

print('Done')