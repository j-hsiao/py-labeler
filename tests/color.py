from __future__ import division
from jhsiao.labeler.color import (
    tk,
    ColorPicker,
    bindings,
    RGBColorPicker,
    HSVColorPicker,
    hsv2rgb,
    rgb2hsv
)


def test_rgb():
    r = tk.Tk()
    bindings.apply(r)
    color = RGBColorPicker('black', r)()
    print(color)
    r.destroy()


def test_hsv():
    r = tk.Tk()
    bindings.apply(r)
    color = HSVColorPicker('pink', r)()
    r.destroy()

def test_colorpalette():
    for r in range(0, 255, 2):
        for g in range(0, 255, 2):
            for b in range(0, 255, 2):
                nr, ng, nb = hsv2rgb(*rgb2hsv(r, g, b))
                try:
                    assert round(nr) == r and round(ng) == g and round(nb) == b
                except Exception:
                    print(r, g, b)
                    print(nr, ng, nb)
                    raise
