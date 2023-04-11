from __future__ import division
from jhsiao.labeler.color import (
    tk,
    ColorPicker,
    bindings,
    RGBColorPicker,
    hsv2rgb,
    rgb2hsv
)


def test_rgb():
    r = tk.Tk()
    bindings.apply(r)
    color = RGBColorPicker('black')()
    print(color)
    r.destroy()


def test_rgb2hsv():
    for r in range(0, 101, 10):
        for g in range(0, 101, 10):
            for b in range(0, 101, 10):
                r /= 100
                g /= 100
                b /= 100
                nr, ng, nb = hsv2rgb(*rgb2hsv(r, g, b))
                assert abs(r-nr) < 1e-3
                assert abs(g-ng) < 1e-3
                assert abs(b-nb) < 1e-3
    print('pass')
