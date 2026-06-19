"""生成 PWA 应用图标 — 万年历"""
from PIL import Image, ImageDraw
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "static", "icons")
os.makedirs(OUT, exist_ok=True)

BG = "#313244"
FG = "#cdd6f4"
ACCENT = "#cba6f7"
BASE = "#1e1e2e"


def make_icon(size):
    img = Image.new("RGBA", (size, size), BASE)
    draw = ImageDraw.Draw(img)
    m = int(size * 0.1)          # margin
    r = int(size * 0.06)         # corner radius
    hh = int(size * 0.3)         # header height

    # 日历主体 (圆角矩形)
    draw.rounded_rectangle(
        [(m, m + hh), (size - m, size - m)],
        radius=r, fill=BG, outline=ACCENT, width=max(3, int(size * 0.03))
    )
    # 日历顶部色条
    draw.rounded_rectangle(
        [(m, m + hh), (size - m, m + hh + hh)],
        radius=r, fill=ACCENT
    )
    # 盖住顶部色条的下方圆角
    draw.rectangle([(m, m + hh + hh // 2), (size - m, m + hh + hh)], fill=ACCENT)

    # 日期模拟线
    lw = max(2, int(size * 0.02))
    lx1 = int(size * 0.22)
    lx2 = size - lx1
    for i in range(3):
        y = int(size * 0.48 + i * size * 0.13)
        draw.rounded_rectangle(
            [(lx1, y), (lx2, y + lw)],
            radius=lw // 2, fill=FG
        )

    path = os.path.join(OUT, f"icon-{size}.png")
    img.save(path)
    print(f"  ✓ icon-{size}.png ({size}x{size})")


if __name__ == "__main__":
    print("生成 PWA 图标...")
    make_icon(192)
    make_icon(512)
    print("完成")
