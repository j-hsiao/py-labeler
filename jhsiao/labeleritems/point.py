from __future__ import division
__all__ = ['Point']
from .. import tkutil as tku
from . import Item

class Point(Item):
    """A point.

    tags: Item, Item_<master> Point
    data: x, y
    """
    LENGTH = 2
    TAGS = ['Point']
    radius = 3
    awidth = 10
    def __init__(self, master, x, y, owned=False):
        """Create a point, represented by a circle."""
        color = 'black'
        radius = self.radius
        idn = master.create_oval(
            x-radius, y-radius, x+radius, y+radius,
            fill=color, activeoutline=color,
            outline=self.modcolor(master, color),
            width=1, activewidth=self.awidth)
        super(Point, self).__init__(master, idn, owned=owned)
        if not master.tag_bind(Point.TAGS[0]):
            Point.bind(master, bindfunc='tag_bind')

    @staticmethod
    def entered(widget, idn):
        color = widget.itemcget(idn, 'activeoutline')
        widget.itemconfigure(
            idn, fill=Item.modcolor(widget, color),
            outline=color)

    @staticmethod
    def left(widget, idn):
        color = widget.itemcget(idn, 'activeoutline')
        widget.itemconfigure(
            idn, fill=color,
            outline=Item.modcolor(widget, color))

    def rescale(self, widget):
        idn = self.idns[0]
        x, y = self.xy(widget, idn)
        self.moveto(widget, idn, x, y)

    def addtags(self, tagdb):
        super(Point, self).addtags(tagdb)
        tagdb.add(self.idns[0], Point.TAGS)

    @staticmethod
    def xy(widget, idn):
        """Return the x, y coordinate of the point."""
        l, t, r, b = widget.coords(idn)
        return (l+r)/2, (t+b)/2

    @classmethod
    def moveto(cls, widget, idn, x, y):
        """Move the point to x, y."""
        radius = cls.radius
        widget.coords(
            idn, x-radius, y-radius, x+radius, y+radius)

    @staticmethod
    def recolor_(widget, tagOrId, color):
        """Change colors."""
        widget.itemconfigure(
            tagOrId,
            fill=color,
            activeoutline=color,
            outline=Item.modcolor(widget, color))
    recolort = recolor_

    @staticmethod
    def select(widget, tagOrId):
        """Change to hollow when selected."""
        widget.itemconfigure(tagOrId, fill='', activewidth=1)

    @classmethod
    def unselect(cls, widget, tagOrId):
        """Restore fill."""
        color = widget.itemcget(tagOrId, 'activeoutline')
        widget.itemconfigure(tagOrId, fill=color, activewidth=cls.awidth)

    @tku.Bindings('<Shift-Motion>', '<Shift-Leave>')
    @classmethod
    def _snapto(cls, widget, x, y):
        """Hold Shift to snap mouse to current point."""
        cx, cy = widget.xy(x, y)
        nx, ny = map(int, cls.xy(widget, 'current'))
        if cx!=nx or cy!=ny:
            widget.event_generate(
                '<Shift-Motion>',
                x=x+(nx-cx), y=y+(ny-cy), warp=True, when='head')

    @tku.Bindings('<Button-1>')
    @classmethod
    def _pick(cls, widget, x, y):
        """Click to pick up a point."""
        cx, cy = widget.xy(x, y)
        px, py = cls.xy(widget, 'current')
        cls.moveto(widget, 'current', cx, cy)
        dx, dy = px-cx, py-cy
        widget.event_generate('<<ignored>>', x=x+dx, y=y+dy, warp=True)
        cls.select(widget, 'current')

    @tku.Bindings('<B1-Motion>')
    @classmethod
    def _move(cls, widget, x, y):
        """Drag to move the point."""
        x, y = widget.xy(x, y)
        cls.moveto(widget, 'current', x, y)

    @tku.Bindings('<ButtonRelease-1>')
    @classmethod
    def _drop(cls, widget):
        """Release to place the point."""
        cls.unselect(widget, 'current')

    def todict(self, widget):
        """Return dict.

        {"type": "Point", data: (x, y)}
        """
        d = super(Point, self).todict(widget)
        d['data'] = self.xy(widget, self.idns[0])
        return d

    @classmethod
    def fromdict(cls, widget, dct, owned=False):
        x, y = dct['data']
        return cls(widget, x, y, owned)
