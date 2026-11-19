#!/usr/bin/env python3
"""The site's art: the app's real screens on phones in perspective, with pieces of them lifted onto glass, drawn by the
App Store pictures' own composer (~/Documents/Tipbit/tools/store-compose.py, imported and never changed), on a clear
ground so the page's own colors show through. Out: img/a/<name>-<width>.{avif,webp,png}.

    python3 tools/art.py            every scene
    python3 tools/art.py hero trip  some of them
"""
import importlib.util
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HOME = os.path.expanduser("~")
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SITE, "img", "a")
RAW = os.path.join(HOME, "Desktop", "Tipbit App Store", "raw")
RAW_IPAD = os.path.join(HOME, "Desktop", "Tipbit App Store", "raw-ipad")
WATCH = os.path.join(SITE, "img", "w")

_spec = importlib.util.spec_from_file_location("sc", os.path.join(HOME, "Documents", "Tipbit", "tools", "store-compose.py"))
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)

# Pieces of Home used more than once: the hourly rate's tile and the Dinner macro's chip.
PER_HOUR = dict(shot="home", box=(16, 552, 129, 74), snap=True, radius=20)
DINNER = dict(shot="home", box=(302.7, 430, 115.3, 52), snap=True, radius=16)


def phone(canvas, shot, x, y, w, ry=0, rx=3, rz=0, pieces=(), raw=RAW, screen=None):
    unit = w / 0.80
    screen = screen or sc.Screen(os.path.join(raw, "mask.png"))
    p = sc.Phone(canvas, raw, screen, shot, (x, y), w, dict(rx=rx, ry=ry, rz=rz), unit)
    for piece in pieces:
        sc.lift_piece(canvas, raw, p, piece, unit)
    return p


def watch(canvas, n, x, y, w, spin=0):
    """A watch from the front: its screen (the store's own picture, already in the screen's shape) in a black body with a
    thin metal edge and the crown, a soft shadow under it."""
    face = Image.open(os.path.join(WATCH, f"watch-{n}-422.png")).convert("RGBA")
    k = w / face.width
    face = face.resize((round(face.width * k), round(face.height * k)), Image.LANCZOS)
    pad = round(w * 0.075)
    bw, bh = face.width + 2 * pad, face.height + 2 * pad
    body = Image.new("RGBA", (bw + round(w * 0.06), bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    r = round(bw * 0.27)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), r, fill=(150, 154, 160, 255))
    e = max(2, round(w * 0.012))
    d.rounded_rectangle((e, e, bw - 1 - e, bh - 1 - e), r - e, fill=(10, 11, 12, 255))
    cw, ch = round(w * 0.06), round(bh * 0.2)
    d.rounded_rectangle((bw - 2, bh * 0.3, bw - 2 + cw, bh * 0.3 + ch), cw // 2, fill=(120, 124, 130, 255))
    body.alpha_composite(face, (pad, pad))
    if spin:
        body = body.rotate(spin, resample=Image.BICUBIC, expand=True)
    x0, y0 = round(x - body.width / 2), round(y - body.height / 2)
    unit = w / 0.8 * 0.6
    sc.drop_shadow(canvas, body.getchannel("A"), (x0, y0), unit, sc.PHONE_SHADOW)
    sc.paste(canvas, body, x0, y0)


def hero():
    c = Image.new("RGBA", (3000, 2050), (0, 0, 0, 0))
    phone(c, "entry", 830, 1330, 680, ry=12, rz=-7)
    phone(c, "calendar", 2170, 1330, 680, ry=-12, rz=7)
    phone(c, "home", 1500, 1180, 800, ry=0, rz=0,
          pieces=[dict(PER_HOUR, at=(-24, 600), scale=1.45, lift=0.05),
                  dict(DINNER, at=(468, 455), scale=1.4, lift=0.05)])
    return c


TILE = (1400, 1240)


def tile(shot, ry, rz, pieces, x=700, y=1085, w=980):
    """A feature's tile: its phone straight on (Jay, Nov 19: "don't tilt them just have them flat"; ry and rz are kept
    in the scenes below only as they were), the pieces still lifted off it on glass."""
    c = Image.new("RGBA", TILE, (0, 0, 0, 0))
    phone(c, shot, x, y, w, ry=0, rx=0, rz=0, pieces=pieces)
    return c


SCENES = {
    "hero": (hero, (1000, 1600, 2400)),
    "entry": (lambda: tile("entry", 9, -3, [dict(DINNER, at=(-6, 330), scale=1.3),
                                            dict(PER_HOUR, at=(446, 168), scale=1.3)]), (560, 840, 1120)),
    "calendar": (lambda: tile("calendar", -9, 3, [dict(shot="calendar", box=(16, 236, 408, 55), radius=24, at=(262, 252),
                                                       scale=1.14),
                                                  dict(shot="calendar", box=(16, 640, 408, 177), snap=True, radius=24,
                                                       at=(196, 462), scale=1.0)]), (560, 840, 1120)),
    "insights": (lambda: tile("insights", 9, -3, [dict(shot="insights-more", box=(16, 567, 408, 225), snap=True,
                                                       radius=24, at=(226, 400), scale=1.0)]), (560, 840, 1120)),
    "schedule": (lambda: tile("schedule", -9, 3, [dict(shot="plan", box=(16, 202, 408, 154), radius=24, at=(222, 392),
                                                       scale=1.0)]), (560, 840, 1120)),
    "trip": (lambda: tile("triplog", 9, -3, [dict(shot="home-trip", box=(16, 399.7, 408, 56), radius=22, at=(214, 38),
                                                  scale=1.1),
                                             dict(shot="trip", box=(16, 684, 408, 146), radius=22, at=(246, 506),
                                                  scale=1.04)]), (560, 840, 1120)),
    "year": (lambda: tile("year", -5, 1, [dict(shot="year-summary-page1", box=(0, 0, 612, 792), radius=0, at=(222, 572),
                                               scale=0.62, spin=0, paper=True)]), (560, 840, 1120)),
    "home": (lambda: tile("home", 9, -3, [dict(shot="home-chart", box=(16, 452, 408, 255), snap=True, radius=24,
                                               at=(222, 420), scale=1.0)]), (560, 840, 1120)),
    "private": (lambda: tile("home-dark", -9, 3, [dict(shot="settings-dark", box=(16, 525, 408, 130), radius=24,
                                                       at=(206, 410), scale=1.0)]), (560, 840, 1120)),
}


def devices():
    c = Image.new("RGBA", (3000, 1900), (0, 0, 0, 0))
    sc.use("ipad")
    phone(c, "home", 1330, 930, 2050, ry=7, rx=3, rz=0, raw=RAW_IPAD)
    sc.use("iphone")
    phone(c, "home", 2420, 1120, 640, ry=-9, rz=3)
    watch(c, 1, 520, 1420, 360, spin=4)
    return c


SCENES["devices"] = (devices, (1000, 1600, 2400))


def save(im, name, widths):
    for w in widths:
        h = round(im.height * w / im.width)
        small = im.resize((w, h), Image.LANCZOS)
        base = os.path.join(OUT, f"{name}-{w}")
        small.save(base + ".avif", quality=60, speed=4)
        small.save(base + ".webp", quality=82, method=6)
        if w == widths[len(widths) // 2]:
            small.save(base + ".png", optimize=True)   # the <img>'s own src, for a browser with neither format
        kb = {e: os.path.getsize(f"{base}.{e}") // 1024 for e in ("avif", "webp")}
        print(f"{name}-{w}: {w}x{h}  avif {kb['avif']} KB, webp {kb['webp']} KB")


def main():
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(SCENES)
    for name in names:
        make, widths = SCENES[name]
        im = make()
        save(im, name, widths)


if __name__ == "__main__":
    main()
