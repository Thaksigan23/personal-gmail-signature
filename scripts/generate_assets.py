"""Generate Gmail-safe signature images: circular portrait, social icons, arrow."""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

TEAL = (26, 155, 150, 255)  # #1A9B96
WHITE = (255, 255, 255, 255)
ICON_SIZE = 112  # retina; displayed at 28px
PHOTO_SIZE = 400  # retina; displayed at 120px

ICON_URLS = {
    "linkedin": "https://img.icons8.com/material-rounded/96/ffffff/linkedin.png",
    "github": "https://img.icons8.com/material-rounded/96/ffffff/github.png",
    "instagram": "https://img.icons8.com/material-rounded/96/ffffff/instagram-new.png",
    "whatsapp": "https://img.icons8.com/material-rounded/96/ffffff/whatsapp.png",
}


def fetch(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as res:
        data = res.read()
    return Image.open(io.BytesIO(data)).convert("RGBA")


def circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def make_portrait() -> None:
    src = Image.open(ASSETS / "profile-original.jpg").convert("RGB")
    w, h = src.size
    # Tight-ish head-and-shoulders crop, slightly above center for hair.
    side = int(min(w, h) * 0.92)
    left = (w - side) // 2
    top = max(0, int((h - side) * 0.18))
    if top + side > h:
        top = h - side
    cropped = src.crop((left, top, left + side, top + side))
    cropped = cropped.resize((PHOTO_SIZE, PHOTO_SIZE), Image.Resampling.LANCZOS)

    gray = ImageOps.grayscale(cropped).convert("RGB")
    gray = ImageEnhance.Contrast(gray).enhance(1.08)
    gray = ImageEnhance.Brightness(gray).enhance(1.02)

    rgba = gray.convert("RGBA")
    rgba.putalpha(circle_mask(PHOTO_SIZE))
    rgba.save(ASSETS / "profile-circle.png", "PNG")
    print("wrote profile-circle.png")


def make_linkedin_in() -> Image.Image:
    """Classic LinkedIn 'in' letters — matches the sample better than the boxed logo."""
    canvas = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((0, 0, ICON_SIZE - 1, ICON_SIZE - 1), fill=TEAL)
    font_path = Path(r"C:\Windows\Fonts\arialbd.ttf")
    font = ImageFont.truetype(str(font_path), 58)
    text = "in"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (ICON_SIZE - tw) // 2 - bbox[0]
    y = (ICON_SIZE - th) // 2 - bbox[1] - 2
    draw.text((x, y), text, font=font, fill=WHITE)
    return canvas


def make_icon(name: str, glyph: Image.Image) -> None:
    canvas = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((0, 0, ICON_SIZE - 1, ICON_SIZE - 1), fill=TEAL)

    glyph = glyph.convert("RGBA")
    pixels = list(glyph.getdata())
    cleaned = []
    for r, g, b, a in pixels:
        if a < 40 or (r < 30 and g < 30 and b < 30):
            cleaned.append((255, 255, 255, 0))
        else:
            cleaned.append((255, 255, 255, a if a > 80 else 255))
    glyph.putdata(cleaned)

    icon_box = int(ICON_SIZE * 0.52)
    glyph = glyph.resize((icon_box, icon_box), Image.Resampling.LANCZOS)
    ox = (ICON_SIZE - icon_box) // 2
    oy = (ICON_SIZE - icon_box) // 2
    canvas.alpha_composite(glyph, (ox, oy))
    canvas.save(ASSETS / f"icon-{name}.png", "PNG")
    print(f"wrote icon-{name}.png")


def make_arrow() -> None:
    size = 48
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Chevron / right arrow in teal.
    stroke = 5
    d.line([(14, 10), (34, 24), (14, 38)], fill=TEAL, width=stroke, joint="curve")
    img.save(ASSETS / "icon-arrow.png", "PNG")
    print("wrote icon-arrow.png")


def make_texture() -> None:
    """Subtle paper grain for the preview page only (Gmail uses solid fill)."""
    w, h = 600, 280
    rng = Image.new("L", (w, h))
    pixels = []
    seed = 12345
    for y in range(h):
        for x in range(w):
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            n = seed % 18
            pixels.append(242 + n)  # 242–259 clamped later
    rng.putdata([min(255, p) for p in pixels])
    rng = rng.filter(ImageFilter.GaussianBlur(0.4))
    rgb = Image.merge("RGB", (rng, rng, ImageEnhance.Brightness(rng).enhance(0.99)))
    rgb.save(ASSETS / "paper-texture.png", "PNG")
    print("wrote paper-texture.png")


def main() -> None:
    make_portrait()
    make_linkedin_in().save(ASSETS / "icon-linkedin.png", "PNG")
    print("wrote icon-linkedin.png")
    for name, url in ICON_URLS.items():
        if name == "linkedin":
            continue
        make_icon(name, fetch(url))
    make_arrow()
    make_texture()


if __name__ == "__main__":
    main()
