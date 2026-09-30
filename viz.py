# -*- coding: utf-8 -*-
"""生成对比图：设备伪彩图 vs 逐像素温度热力图。"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
temp = np.load(os.path.join(OUT, "temperature.npy"))
jpeg = Image.open(os.path.join(OUT, "thermal.jpg"))

print(f"温度矩阵 {temp.shape} {temp.dtype}, JPEG {jpeg.size} {jpeg.mode}")
assert jpeg.size == (temp.shape[1], temp.shape[0]), "尺寸不一致！"

fig, axes = plt.subplots(1, 2, figsize=(15, 6.4))

axes[0].imshow(jpeg)
axes[0].set_title("device thermal JPEG (Fusion1 palette, 640x512)", fontsize=12)
axes[0].axis("off")

im = axes[1].imshow(temp, cmap="inferno")
axes[1].set_title("per-pixel temperature matrix (float32, degC)", fontsize=12)
axes[1].axis("off")
cb = fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.02)
cb.set_label("Temperature (degC)")

iy, ix = np.unravel_index(np.argmax(temp), temp.shape)
axes[1].plot(ix, iy, "c+", markersize=14, markeredgewidth=2)
axes[1].annotate(f"max {temp.max():.1f}degC",
                 xy=(ix, iy), xytext=(ix - 200, iy + 60), color="cyan", fontsize=10,
                 arrowprops=dict(arrowstyle="->", color="cyan"))

fig.suptitle(
    f"HIKMICRO HM-TD2AXXT-15C @192.168.1.64  |  "
    f"min {temp.min():.2f}  max {temp.max():.2f}  mean {temp.mean():.2f}  median {np.median(temp):.2f} degC",
    fontsize=12)
fig.tight_layout()
dst = os.path.join(OUT, "thermal_overview.png")
fig.savefig(dst, dpi=110)
print(f"已保存对比图: {dst}")
