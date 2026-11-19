#!/usr/bin/env python3
"""The site's pictures, from the App Store pictures' raw screens (made by tools/store-shots.sh in the Tipbit repo).

Usage: python3 tools/images.py            (from the site's folder; reads ~/Desktop/Tipbit App Store, writes img/)

Each picture is written as AVIF, WebP and a JPEG or PNG fallback at a few widths, for <picture> with srcset. The screens
are the app's own screens, flat, square-cornered here (the page rounds them); a "piece" is a card lifted off a screen
with its own rounded corners baked in (alpha), as the store pictures lift them; the watch's pages are cut to the watch
screen's own shape; a "tile" (img/t) is a screen cut for the front page's grid, under the status bar or at a sheet's own
top, with rounded top corners in alpha. The strip (img/strip.jpg, the eight store pictures as one scene) is only re-encoded smaller.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageCms

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
STORE = os.path.expanduser("~/Desktop/Tipbit App Store")
RAW, RAW_IPAD, WATCH = (os.path.join(STORE, d) for d in ("raw", "raw-ipad", "Watch"))
IMG = os.path.join(SITE, "img")
POINT = 3  # the 6.9" iPhone's pixels per point

SRGB = ImageCms.createProfile("sRGB")


def load(path):
    """A raw screen as sRGB (the simulator's screenshots carry Display P3)."""
    im = Image.open(path)
    icc = im.info.get("icc_profile")
    im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(__import__("io").BytesIO(icc))
            mode = "RGBA" if im.mode == "RGBA" else "RGB"
            im = ImageCms.profileToProfile(im, src, SRGB, outputMode=mode)
        except Exception as e:  # noqa: BLE001
            print(f"  (icc left as is: {e})", file=sys.stderr)
    return im


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def save_all(im, stem, widths, alpha=False, avif_q=58, webp_q=80, jpg_q=82):
    """stem-W.avif / .webp / .jpg (or .png with alpha) at each width; prints what each weighs."""
    out = []
    for w in widths:
        if w >= im.width:
            w = im.width
        h = round(im.height * w / im.width)
        small = im.resize((w, h), Image.LANCZOS)
        base = f"{stem}-{w}"
        small.save(base + ".avif", quality=avif_q, speed=4)
        small.save(base + ".webp", quality=webp_q, method=6)
        if alpha:
            small.save(base + ".png", optimize=True)
        else:
            small.convert("RGB").save(base + ".jpg", quality=jpg_q, optimize=True, progressive=True)
        sizes = {ext: os.path.getsize(f"{base}.{ext}") // 1024 for ext in ("avif", "webp", "png" if alpha else "jpg")}
        out.append((w, h, sizes))
        print(f"  {os.path.relpath(base, SITE)}  {w}x{h}  " + "  ".join(f"{k} {v} KB" for k, v in sizes.items()))
    return out


def screens():
    os.makedirs(os.path.join(IMG, "s"), exist_ok=True)
    for name in ("home", "entry", "calendar", "insights", "schedule", "trip", "year", "home-dark"):
        print(name)
        im = load(os.path.join(RAW, f"{name}.png"))
        assert im.size == (1320, 2868), im.size
        save_all(im, os.path.join(IMG, "s", name), (440, 660, 990), avif_q=56)
    print("ipad-home")
    im = load(os.path.join(RAW_IPAD, "home.png"))
    save_all(im, os.path.join(IMG, "s", "ipad-home"), (820, 1240, 1860), avif_q=54)


PIECES = {
    # name: (shot, box in points (x, y, w, h), corner radius in points, snap to the card's own edges, display widths)
    "perhour": ("home", (16, 552, 129, 74), 20, True, (260, 390)),
    "dinner": ("home", (302.7, 430, 115.3, 52), 16, True, (230, 346)),
    "chart": ("home-chart", (16, 452, 408, 255), 24, True, (640, 960)),
    "day": ("calendar", (16, 640, 408, 177), 24, True, (640, 960)),
    "bestdays": ("insights-more", (16, 567, 408, 225), 24, True, (640, 960)),
    "days": ("plan", (16, 202, 408, 154), 24, False, (640, 960)),
    "tripbanner": ("home-trip", (16, 399.7, 408, 56), 22, False, (640, 960)),
    "map": ("trip", (16, 684, 408, 146), 22, False, (640, 960)),
    "icloud": ("settings-dark", (16, 525, 408, 130), 24, False, (640, 960)),
}


def snap(img, box):
    """A card's own edges near `box` (pixels): the card's color against the page's, along the middle of each side.
    (As tools/store-compose.py in the Tipbit repo does.)"""
    x0, y0, x1, y1 = box
    img = img.convert("RGB")
    card = img.getpixel((x0 + 24, (y0 + y1) // 2))
    near = lambda c: max(abs(a - b) for a, b in zip(c, card)) <= 3  # noqa: E731

    def edge(fixed_range, moving, along_x):
        for v in moving:
            if sum(near(img.getpixel((v, u) if along_x else (u, v))) for u in fixed_range) >= 0.9 * len(fixed_range):
                return v
        return None

    mid_y = range((y0 + y1) // 2 - 20, (y0 + y1) // 2 + 20, 2)
    mid_x = range((x0 + x1) // 2 - 60, (x0 + x1) // 2 + 60, 4)
    left = edge(mid_y, range(max(x0 - 30, 0), x0 + 30), True)
    right = edge(mid_y, range(min(x1 + 30, img.width - 1), x1 - 30, -1), True)
    top = edge(mid_x, range(max(y0 - 30, 0), y0 + 30), False)
    bottom = edge(mid_x, range(min(y1 + 30, img.height - 1), y1 - 30, -1), False)
    if None in (left, right, top, bottom):
        return box
    return (left, top, right + 1, bottom + 1)


def pieces():
    os.makedirs(os.path.join(IMG, "p"), exist_ok=True)
    for name, (shot, (x, y, w, h), radius, do_snap, widths) in PIECES.items():
        print(name)
        im = load(os.path.join(RAW, f"{shot}.png"))
        box = tuple(round(v * POINT) for v in (x, y, x + w, y + h))
        if do_snap:
            box = snap(im, box)
        cut = im.crop(box).convert("RGBA")
        cut.putalpha(rounded_mask(cut.size, radius * POINT))
        save_all(cut, os.path.join(IMG, "p", name), widths, alpha=True, avif_q=60)
    # The year summary's first page, as the app makes it: a sheet of paper (its margins transparent in the raw).
    print("paper")
    im = load(os.path.join(RAW, "year-summary-page1.png"))
    bbox = im.getchannel("A").getbbox() if im.mode == "RGBA" else None
    if bbox:
        im = im.crop(bbox)
    if im.mode == "RGBA":
        im = im.convert("RGB")
    save_all(im, os.path.join(IMG, "p", "paper"), (480, 720), avif_q=62, webp_q=84)


# The front page's six-screen grid: each screen cut to a tidy tile. A plain screen starts just under the status bar
# (its glyphs end at 40 pt on the 6.9" iPhone); a sheet (New entry, the trip's page) starts at the sheet's own top edge
# (62 pt), so the screen behind it never shows. Every tile gets the same rounded top corners (a sheet's own 40 pt, in
# alpha), so the six read as one set; the page fades each tile's bottom out, so they're cut at 800 pt.
TILES = {
    # name: (top in points, the raw screen it's cut from)
    "entry": (62, "entry"),
    "calendar": (46, "calendar"),
    "insights": (46, "insights"),
    "schedule": (46, "schedule"),
    "trip": (62, "trip"),
    "year": (46, "year"),
}
TILE_RADIUS = 40  # points, a sheet's own top corners
TILE_HEIGHT = 800  # points kept under the cut


def tiles():
    os.makedirs(os.path.join(IMG, "t"), exist_ok=True)
    for name, (top, shot) in TILES.items():
        print(name)
        im = load(os.path.join(RAW, f"{shot}.png")).convert("RGB")
        assert im.size == (1320, 2868), im.size
        y0 = top * POINT
        px = im.load()
        # The cut must fall between the status bar's glyphs and the first thing drawn under them.
        dark = [y for y in range(0, 110 * POINT) if any((sum(px[x, y]) / 3) < 110 for x in range(0, im.width, 3))]
        above = max((y for y in dark if y < y0), default=None)
        below = min((y for y in dark if y >= y0), default=None)
        print(f"  cut at {top} pt: dark above ends {above and above / POINT:.0f} pt, next dark row {below and below / POINT:.0f} pt")
        cut = im.crop((0, y0, im.width, min(im.height, y0 + TILE_HEIGHT * POINT))).convert("RGBA")
        r = TILE_RADIUS * POINT
        mask = Image.new("L", cut.size, 255)
        draw = ImageDraw.Draw(mask)
        # Only the top corners are rounded: a rounded rectangle taller than the tile, so its bottom corners fall outside.
        draw.rectangle((0, 0, cut.width - 1, cut.height - 1), fill=0)
        draw.rounded_rectangle((0, 0, cut.width - 1, cut.height - 1 + r), radius=r, fill=255)
        cut.putalpha(mask)
        save_all(cut, os.path.join(IMG, "t", name), (360, 520), alpha=True, avif_q=58)


WATCH_RADIUS = 0.26  # the watch screen's corners as a share of its width (measured on the Ultra 3's own screen shape)


def watch():
    """The watch's pages, each cut to the watch screen's own rounded shape (alpha): the app's background is black like
    the screen's surround, so the whole picture is the screen."""
    os.makedirs(os.path.join(IMG, "w"), exist_ok=True)
    for n in (1, 2, 3, 4, 5, 6):
        print(f"watch-{n}")
        im = load(os.path.join(WATCH, f"Tipbit Watch {n}.png")).convert("RGBA")
        im.putalpha(rounded_mask(im.size, round(im.width * WATCH_RADIUS)))
        save_all(im, os.path.join(IMG, "w", f"watch-{n}"), (im.width,), alpha=True, avif_q=60)


def strip():
    im = load(os.path.join(IMG, "strip.jpg"))
    print("strip", im.size)
    for w in (2640, 3960):
        small = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        small.save(os.path.join(IMG, f"strip-{w}.avif"), quality=56, speed=4)
        small.save(os.path.join(IMG, f"strip-{w}.webp"), quality=78, method=6)
        small.save(os.path.join(IMG, f"strip-{w}.jpg"), quality=80, optimize=True, progressive=True)
    im.save(os.path.join(IMG, "strip-5280.avif"), quality=54, speed=4)
    im.save(os.path.join(IMG, "strip-5280.webp"), quality=76, method=6)
    for f in sorted(os.listdir(IMG)):
        if f.startswith("strip"):
            print(f"  {f}  {os.path.getsize(os.path.join(IMG, f)) // 1024} KB")


def icon():
    im = Image.open(os.path.join(IMG, "icon.png")).convert("RGBA")
    for size in (96, 180):
        im.resize((size, size), Image.LANCZOS).save(os.path.join(IMG, f"icon-{size}.png"), optimize=True)
        print(f"  icon-{size}.png  {os.path.getsize(os.path.join(IMG, f'icon-{size}.png')) // 1024} KB")


if __name__ == "__main__":
    which = sys.argv[1:] or ["screens", "tiles", "pieces", "watch", "strip", "icon"]
    for step in which:
        globals()[step]()
