from __future__ import division
import math
import sys
if sys.version_info.major > 2:
    import tkinter as tk
else:
    import Tkinter as tk

from .. import tkutil as tku

torads = math.pi / 180
def hit(x, y, tx, ty, vx, vy):
    """Calculate hit point given x, y of a corner."""
    if not vx:
        mul = (ty-y) / vy
    elif not vy:
        mul = (tx-x) / vx
    else:
        mulx = (tx-x) / vx
        muly = (ty-y) / vy
        mul = muly if abs(mulx) > abs(muly) else mulx
    return x + vx*mul, y + vy*mul

class Crosshairs(object):
    """Crosshairs on mouse."""
    TAG = '_crosshair'
    def __init__(self, master):
        self._vec = (1, 0)
        self.idns = [
            master.create_line(0, 0, 0, 0),
            master.create_line(0, 0, 0, 0),
            master.create_line(0, 0, 0, 0),
            master.create_line(0, 0, 0, 0)]
        for idn in self.idns:
            master.addtag(self.TAG, 'withtag', idn)
        for idn in self.idns[::2]:
            master.addtag('_crossh', 'withtag', idn)
        for idn in self.idns[1::2]:
            master.addtag('_crossv', 'withtag', idn)
        master.itemconfigure(self.TAG, state='disabled')
        for idn in self.idns[:2]:
            master.addtag('_crossb', 'withtag', idn)
            master.itemconfigure(idn, fill='black', width=3)
        for idn in self.idns[2:]:
            master.addtag('_crossf', 'withtag', idn)
            master.itemconfigure(idn, fill='white', width=1)
        tag = 'CanvasCrosshairs'
        if tag not in master.bindtags():
            tku.subclass(master, tag)
        if not master.bind_class(tag):
            tku.add_bindings(master, tag, tupit=tku.memberit(self))
            master.configure(cursor='none')

    def angle(self, angleorvx, vy=None, degrees=True):
        """Set the crosshairs angle.

        angleorvx: angle (if vy is None) else vector x direction
        vy: if given, then the crosshair direction is (angleorvx, vy)
        degrees: if vy is None, is angleorvx in degrees or radians.
        """
        if vy is None:
            if degrees:
                angle = (angleorvx % 90) * torads
            else:
                angle = angleorvx % (math.pi / 4)
            self._vec = (math.cos(angle), math.sin(angle))
        else:
            vx = angleorvx
            if vx * vy > 0:
                self._vec = abs(vx), abs(vy)
            else:
                if not (vx or vy):
                    self._vec = (1, 0)
                else:
                    self._vec = abs(vy), abs(vx)

    @tku.Bindings('<KeyPress-c>', '<KeyPress-C>')
    @classmethod
    def toggle(cls, widget):
        if widget.itemcget(cls.TAG, 'state') == 'disabled':
            widget.itemconfigure(cls.TAG, state='hidden')
        else:
            widget.itemconfigure(cls.TAG, state='disabled')

    @tku.Bindings('<Enter>')
    @classmethod
    def show(cls, widget, x, y):
        widget.itemconfigure(cls.TAG, state='disabled')
        Crosshairs.draw_crosshairs(widget, x, y)

    @tku.Bindings('<Leave>')
    @classmethod
    def hide(cls, widget):
        widget.itemconfigure(cls.TAG, state='hidden')

    @tku.Bindings('<Motion>')
    @staticmethod
    def draw_crosshairs(widget, x, y):
        l, t = widget.xy(0,0)
        r, b = l+widget.winfo_width(), t+widget.winfo_height()
        x, y = widget.xy(x, y)
        self = widget.crosshairs
        i1, i2, i3, i4 = self.idns
        vx, vy = self._vec
        if vy:
            x1, y1 = hit(x, y, l, t, -vx, -vy)
            x2, y2 = hit(x, y, r, b, vx, vy)
            widget.coords(i1, x1, y1, x2, y2)
            widget.coords(i3, x1, y1, x2, y2)
            x1, y1 = hit(x, y, r, t, -vy, vx)
            x2, y2 = hit(x, y, l, b, vy, -vx)
            widget.coords(i2, x1, y1, x2, y2)
            widget.coords(i4, x1, y1, x2, y2)
        else:
            widget.coords(i1, l, y, r, y)
            widget.coords(i3, l, y, r, y)
            widget.coords(i2, x, t, x, b)
            widget.coords(i4, x, t, x, b)

