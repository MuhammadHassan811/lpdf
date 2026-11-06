"""Small drawing helpers for the paper's figures (PIL only)."""

import sys
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

# Font resolution. Arial is preferred because the paper is set in a serif face
# and the figures in a sans one; DejaVu is the fallback where Arial is absent,
# which is the usual case on Linux.
_CANDIDATES = {
    False: [
        r"C:\Windows\Fonts\arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "DejaVuSans.ttf",
        "arial.ttf",
    ],
    True: [
        r"C:\Windows\Fonts\arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "arialbd.ttf",
    ],
}
_warned = False


@lru_cache(maxsize=None)
def font(size, bold=False):
    """Load a sans font at ``size``, falling back across platforms."""
    global _warned
    for path in _CANDIDATES[bool(bold)]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    if not _warned:
        print("warning: no TrueType font found; figures will use the bitmap "
              "default and will not match the published layout",
              file=sys.stderr)
        _warned = True
    return ImageFont.load_default()


# Muted, print-safe palette. Each tuple is (fill, border, text).
STYLES = {
    "input":  ("#EDF2F7", "#44607A", "#1D2B38"),
    "model":  ("#E4EDF6", "#2C5A82", "#16293A"),
    "filter": ("#FAF3E6", "#8A6B2F", "#3A2D13"),
    "struct": ("#E7F1EA", "#2E6B4F", "#14301F"),
    "out":    ("#F3EAF2", "#6E3A66", "#2E1A2B"),
    "refine": ("#F7ECEC", "#8C3A3A", "#3A1818"),
}

ARROW = "#3C4650"


class Canvas:
    def __init__(self, w, h, bg="white"):
        self.img = Image.new("RGB", (w, h), bg)
        self.d = ImageDraw.Draw(self.img)
        self.w, self.h = w, h

    # ---------------------------------------------------------------- boxes
    def box(self, x, y, w, h, lines, style="model", radius=14, title_bold=True,
            fs=None, fs_small=None, badge=None):
        """Draw a rounded box. ``lines`` is (title, *detail lines)."""
        fill, border, text = STYLES[style]
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                                 fill=fill, outline=border, width=3)
        fs = fs or 30
        fs_small = fs_small or 25
        title, *rest = lines
        ft = self._fit(title, w - 30, fs, title_bold)
        fr_size = min((self._fit_size(r, w - 30, fs_small) for r in rest),
                      default=fs_small)
        fr = font(fr_size)

        total = self._th(title, ft) + sum(self._th(r, fr) + 4 for r in rest)
        cy = y + (h - total) / 2
        if badge is not None:
            # Keep the text clear of the badge, which sits in the top-left
            # corner; a wide centred title would otherwise run under it.
            cy = max(cy, y + 14 + 40 + 10)
        self._centre(title, x + w / 2, cy, ft, text)
        cy += self._th(title, ft) + 6
        for r in rest:
            self._centre(r, x + w / 2, cy, fr, text)
            cy += self._th(r, fr) + 4

        if badge is not None:
            r = 20
            bx, by = x + 14, y + 14
            self.d.ellipse([bx, by, bx + 2 * r, by + 2 * r], fill=border)
            fb = font(24, True)
            self._centre(str(badge), bx + r, by + r - self._th(str(badge), fb) / 2,
                         fb, "white")
        return (x, y, x + w, y + h)

    def note(self, x, y, w, h, lines, fs=23):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=10,
                                 outline="#8A93A0", width=2)
        f = font(fs)
        total = sum(self._th(l, f) + 4 for l in lines)
        cy = y + (h - total) / 2
        for l in lines:
            self._centre(l, x + w / 2, cy, f, "#39414B")
            cy += self._th(l, f) + 4

    # -------------------------------------------------------------- helpers
    def _fit_size(self, s, max_w, start, bold=False, floor=17):
        """Largest font size at or below ``start`` whose text fits ``max_w``."""
        size = start
        while size > floor and self._tw(s, font(size, bold)) > max_w:
            size -= 1
        return size

    def _fit(self, s, max_w, start, bold=False):
        return font(self._fit_size(s, max_w, start, bold), bold)

    def _th(self, s, f):
        bb = self.d.textbbox((0, 0), s, font=f)
        return bb[3] - bb[1]

    def _tw(self, s, f):
        bb = self.d.textbbox((0, 0), s, font=f)
        return bb[2] - bb[0]

    def _centre(self, s, cx, top, f, colour):
        bb = self.d.textbbox((0, 0), s, font=f)
        self.d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], top - bb[1]), s,
                    font=f, fill=colour)

    def label(self, s, cx, cy, fs=22, colour=None, bold=False, bg="white"):
        f = font(fs, bold)
        bb = self.d.textbbox((0, 0), s, font=f)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if bg:
            self.d.rectangle([cx - w / 2 - 6, cy - h / 2 - 4,
                              cx + w / 2 + 6, cy + h / 2 + 4], fill=bg)
        self.d.text((cx - w / 2 - bb[0], cy - h / 2 - bb[1]), s, font=f,
                    fill=colour or "#39414B")

    # -------------------------------------------------------------- arrows
    def _head(self, x, y, direction, size=13, colour=None):
        c = colour or ARROW
        if direction == "r":
            pts = [(x, y), (x - size, y - size * 0.7), (x - size, y + size * 0.7)]
        elif direction == "l":
            pts = [(x, y), (x + size, y - size * 0.7), (x + size, y + size * 0.7)]
        elif direction == "d":
            pts = [(x, y), (x - size * 0.7, y - size), (x + size * 0.7, y - size)]
        else:
            pts = [(x, y), (x - size * 0.7, y + size), (x + size * 0.7, y + size)]
        self.d.polygon(pts, fill=c)

    def arrow(self, pts, colour=None, width=4, dashed=False):
        """Polyline arrow; the head is placed at the final segment's direction."""
        c = colour or ARROW
        for a, b in zip(pts, pts[1:]):
            if dashed:
                self._dashed(a, b, c, width)
            else:
                self.d.line([a, b], fill=c, width=width)
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        if abs(x1 - x0) > abs(y1 - y0):
            self._head(x1, y1, "r" if x1 > x0 else "l", colour=c)
        else:
            self._head(x1, y1, "d" if y1 > y0 else "u", colour=c)

    def _dashed(self, a, b, colour, width, dash=14, gap=10):
        (x0, y0), (x1, y1) = a, b
        dx, dy = x1 - x0, y1 - y0
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist == 0:
            return
        ux, uy = dx / dist, dy / dist
        t = 0.0
        while t < dist:
            s = min(t + dash, dist)
            self.d.line([(x0 + ux * t, y0 + uy * t), (x0 + ux * s, y0 + uy * s)],
                        fill=colour, width=width)
            t = s + gap

    def save(self, path, scale=1.0):
        img = self.img
        if scale != 1.0:
            img = img.resize((int(self.w * scale), int(self.h * scale)),
                             Image.LANCZOS)
        img.save(path, "PNG", optimize=True)
        return img.size
