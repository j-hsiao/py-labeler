from __future__ import division, print_function
import timeit
import cv2

import os

from jhsiao.labeler.color import (
    tk,
    ColorPicker,
    bindings,
    RGB,
    HSV,
    hsv2rgb,
    rgb2hsv,
)

@bindings['ColorPicker'].bind('<<ColorChange>>')
def tempcolor(widget):
    print(widget.color())

def test_rgb():
    r = tk.Tk()
    bindings.apply(r)
    picker = ColorPicker(r, picker=RGB, color='black')
    r.grid_rowconfigure(0, weight=1)
    r.grid_columnconfigure(0, weight=1)
    picker.grid(row=0, column=0, sticky='nsew')
    print(picker())
    try:
        r.destroy()
    except Exception:
        pass

def test_hsv():
    r = tk.Tk()
    bindings.apply(r)
    picker = ColorPicker(r, picker=HSV, color='black')
    r.grid_rowconfigure(0, weight=1)
    r.grid_columnconfigure(0, weight=1)
    picker.grid(row=0, column=0, sticky='nsew')
    print(picker())
    try:
        r.destroy()
    except Exception:
        pass

if os.environ.get('ALL'):
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
