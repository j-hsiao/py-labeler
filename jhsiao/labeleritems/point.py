"""Represents a single point."""
from __future__ import division
__all__ = ['Point']
from . import Obj, bindings

@Obj.register
class Point(Obj):
    HELP = 'A point. (x, y)'
    TAGS = ['Point', 'Point_{}']
    IDX = Obj.IDX  + len(TAGS)

    binds = bindings['Point']

    radius = 5
    awidth = 10
    def __init__(self, master, x, y, color='black'):
        radius = self.radius
        super(Point, self).__init__(
            master,
            master.create_oval(
                x-radius, y-radius, x+radius, y+radius,
                width=1, activewidth=Point.awidth,
                **self.colorkwargs(master, color)
            ))
        self.addtags(master, self.ids, Point.TAGS)

    @staticmethod
    def colorkwargs(master, color):
        """Generate color dict for new color."""
        return dict(
            fill=color, activeoutline=color,
            outline=Obj.altcolor(master, color))

    @staticmethod
    def color(master, idn='current'):
        return master.itemcget(idn, 'activeoutline')

    @staticmethod
    def recolor(widget, color, idn='current'):
        widget.itemconfigure(
            idn, **Point.colorkwargs(widget, color))

    @staticmethod
    def data(widget, idn, info):
        l, t, r, b = widget.coords(idn)
        return (l+r)//2, (t+b)//2

    @staticmethod
    def fromdict(widget, dct, info):
        x, y = dct['data']
        return Point(widget, x, y, dct['color'])

    @staticmethod
    def activate(widget, ids):
        widget.itemconfigure(ids[0], width=2)

    @staticmethod
    def deactivate(widget, ids):
        widget.itemconfigure(ids[0], width=1)

    @staticmethod
    def moveto(widget, x, y, idn='current'):
        """Move Point to canvas coordinates (x,y)."""
        r = Point.radius
        widget.coords(idn, x-r, y-r, x+r, y+r)

    @staticmethod
    def snapto(widget, x, y, idn='current'):
        """Snap mouse to center of point."""
        Obj.snapto(
            widget, x, y, Point.data(widget, idn))

    @staticmethod
    @binds.bind('<Shift-Motion>', '<Shift-Leave>')
    def _snapto(widget, x, y):
        Point.snapto(widget, x, y)
    binds.bind('<B1-Shift-Leave>')(' ')

    @staticmethod
    @binds.bind('<Button-1>')
    def _select(widget, x, y):
        widget.itemconfigure(
            'current', fill='', activewidth=1)
        Point.snapto(widget, x, y)

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _release(widget):
        widget.itemconfigure(
            'current',
            fill=widget.itemcget('current', 'activeoutline'),
            activewidth=Point.awidth)

    @staticmethod
    @binds.bind('<B1-Motion>', '<Shift-B1-Motion>')
    def _moveto(widget, x, y):
        nx, ny = Point.canvxy(widget, x, y)
        Point.moveto(widget, nx, ny)
