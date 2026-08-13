#!/usr/bin/env python3


import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "source-prepped.png")

ALPHA_THRESHOLD = 128  # anything at/above this stays opaque; below -> forced 0


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/prep_photo.py <image-path>")

    src = sys.argv[1]
    if not os.path.exists(src):
        sys.exit(f"input image not found: {src}")

    # --- 1. Background removal (ONNX U-Net via rembg) ---------------------
    image = Image.open(src).convert("RGBA")
    cutout = remove(image).convert("RGBA")  # alpha already 0 outside subject

    arr = np.asarray(cutout)
    alpha = arr[..., 3]

    # Force the alpha channel to a hard 0/255 mask: any semi-transparent
    # fringe residue from the matte is removed completely.
    alpha = np.where(alpha < ALPHA_THRESHOLD, 0, 255).astype(np.uint8)

    # --- 2. Grayscale ------------------------------------------------------
    rgb = arr[..., :3]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # --- 3. CLAHE contrast boost ------------------------------------------
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # --- 4. Apply the mask: background -> 0 (black) ------------------------
    mask = alpha.astype(np.float32) / 255.0
    result = gray.astype(np.float32) * mask

    # --- 5. Film-noir tone curve -------------------------------------------
    # smoothstep S-curve: shadows are crushed toward black, highlights lifted
    # toward white.  The extra midtone lift keeps facial structure readable.
    v = result / 255.0
    v = v * v * (3.0 - 2.0 * v)
    v = np.power(v, 0.92)
    result = (np.clip(v, 0.0, 1.0) * 255.0).astype(np.uint8)

    Image.fromarray(result, mode="L").save(OUT_PATH)
    print(f"saved {OUT_PATH} ({result.shape[1]}x{result.shape[0]})")


if __name__ == "__main__":
    main()
