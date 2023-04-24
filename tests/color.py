from __future__ import division, print_function
import timeit
import cv2

import os
from jhsiao.tkutil import add_bindtags

from jhsiao.labeler.color import (
    tk,
    ColorPicker,
    bindings,
    RGB,
    HSV,
    hsv2rgb,
    rgb2hsv,
)

@bindings['TestPicker'].bind('<<ColorChange>>')
def tempcolor(widget):
    print(widget.color())
@bindings['TestPicker'].bind('<<ColorSelected>>')
def selected(widget):
    widget.master.destroy()

def test_rgb():
    r = tk.Tk()
    bindings.apply(r)
    picker = ColorPicker(r, picker=RGB, background='black')
    add_bindtags(picker, 'TestPicker')
    r.grid_rowconfigure(0, weight=1, minsize=100)
    r.grid_columnconfigure(0, weight=1, minsize=100)
    picker.grid(row=0, column=0, sticky='nsew')
    picker.wait_window()

def test_hsv():
    r = tk.Tk()
    bindings.apply(r)
    picker = ColorPicker(r, picker=HSV, background='black')
    add_bindtags(picker, 'TestPicker')
    r.grid_rowconfigure(0, weight=1, minsize=100)
    r.grid_columnconfigure(0, weight=1, minsize=100)
    picker.grid(row=0, column=0, sticky='nsew')
    picker.wait_window()

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
