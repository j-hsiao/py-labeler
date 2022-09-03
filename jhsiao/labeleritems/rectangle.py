__all__ = ['Rectangle']
from . import Item
from .point import Point
from .. import tkutil as tku

class Rectangle(Item):
    """A rectangle.

    rectangle tags: Item, Item_<master>, Rectangle
    corner tags: Item, Item_<master>, Point, RectPt, RectPt_<rect>
    data: x1, y1, x2, y2
        topleft, bottomright
    """
    LENGTH = 4
    TAGS = ['Rectangle']
    def __init__(self, widget, x, y, owned=False):
        """Create a rectangle.

        Rectangle and 4 points
        """
        color = 'black'
        idn = widget.create_rectangle(
            x, y, x, y, fill=color,
            stipple='gray12', activestipple='gray50',
            activeoutline=color,
            width=1, activewidth=1)
        self.points = [RectPt(widget, x, y, owned=True) for _ in range(4)]
        super(Rectangle, self).__init__(widget, idn, self.points, owned=owned)
        if not widget.tag_bind(Rectangle.TAGS[0]):
            Rectangle.bind(widget, bindfunc='tag_bind')
            RectPt.bind(widget, bindfunc='tag_bind')


    def addtags(self, tagdb):
        super(Rectangle, self).addtags(tagdb)
        tagdb.add(self.idns[0], Rectangle.TAGS)
        tagdb.add(self.points, RectPt.TAGS, suffix=self.idns[0])

    @staticmethod
    def select(widget, idn):
        """Select rectangle."""
        widget.itemconfigure(idn, fill='', activewidth=1)
        RectPt.select(widget, RectPt.TAGS[1]+str(idn))

    @staticmethod
    def unselect(widget, idn):
        """Unselect rectangle."""
        color = widget.itemcget(idn, 'activeoutline')
        widget.itemconfigure(idn, fill=color, activewidth=2)
        RectPt.unselect(widget, RectPt.TAGS[1]+str(idn))

    @staticmethod
    def recolor_(widget, idn, color):
        """Recolor the rectangle and its corner points."""
        subcolor = Item.modcolor(widget, color)
        widget.itemconfigure(
            idn, fill=color, outline=subcolor,
            activeoutline=color)
        RectPt.recolor_(widget, RectPt.TAGS[1]+str(idn), color)

    @tku.Bindings('<Button-1>')
    @staticmethod
    def _pickrect(widget, x, y):
        """Click to pick up rectangle."""
        Rectangle.select(widget, widget.find('withtag', 'current')[0])
        widget.draginfo = widget.xy(x, y)
        widget.crosshairs.hide(widget)

    @tku.Bindings('<B1-Motion>')
    @staticmethod
    def _move_rect(widget, x, y):
        """Drag to move the rectangle."""
        ox, oy = widget.draginfo
        widget.draginfo = x, y = widget.xy(x, y)
        dx, dy = x-ox, y-oy
        idn = widget.find('withtag', 'current')[0]
        widget.move(idn, dx, dy)
        widget.move(RectPt.TAGS[1]+str(idn), dx, dy)

    @tku.Bindings('<ButtonRelease-1>')
    @staticmethod
    def _place_rect(widget, x, y):
        """Release to place the rectangle."""
        widget.crosshairs.show(widget, x, y)
        Rectangle.unselect(widget, widget.find('withtag', 'current')[0])

    def todict(self, widget):
        d = super(Rectangle, self).todict(widget)
        d['data'] = widget.coords(self.idns[0])
        return d

    @classmethod
    def fromdict(cls, widget, dct, owned=False):
        l, t, r, b = dct['data']
        rect = cls(widget, l, t, owned)
        widget.coords(rect.idns[0], l, t, r, b)
        lt, rt, rb, lb = rect.points
        RectPt.moveto(widget, lt, l, t)
        RectPt.moveto(widget, rt, r, t)
        RectPt.moveto(widget, rb, r, b)
        RectPt.moveto(widget, lb, l, b)
        return rect

class RectPt(Point):
    TAGS = ['RectPt', 'RectPt_']
    @tku.Bindings('<Button-1>')
    @staticmethod
    def _select_corner(widget):
        """Click to pick corner."""
        pttag = RectPt.tagat(widget, 'current')
        rectid = RectPt.getidn(pttag)
        Rectangle.select(widget, rectid)

    @tku.Bindings('<B1-Motion>')
    @staticmethod
    def _move_corner(widget):
        """Drag to move corner/resize rectangle."""
        idn = widget.find('withtag', 'current')[0]
        pttag = RectPt.tagat(widget, idn, 1)
        corners = widget.find('withtag', pttag)
        rectid = RectPt.getidn(pttag)
        cur = corners.index(idn)
        cpt, xpt, opt, ypt = [corners[(cur+i)%4] for i in range(4)]
        ox, oy = Point.xy(widget, opt)
        cx, cy = Point.xy(widget, cpt)
        Point.moveto(widget, xpt, cx, oy)
        Point.moveto(widget, ypt, ox, cy)
        widget.coords(rectid, cx, cy, ox, oy)

    @tku.Bindings('<ButtonRelease-1>')
    @staticmethod
    def _unselect_corner(widget):
        """Release to finish changing corner location."""
        pttag = RectPt.tagat(widget, 'current')
        lt, rt, rb, lb = widget.find('withtag', pttag)
        rectid = RectPt.getidn(pttag)
        l,t, r,b = widget.coords(rectid)
        Point.moveto(widget, lt, l, t)
        Point.moveto(widget, rt, r, t)
        Point.moveto(widget, rb, r, b)
        Point.moveto(widget, lb, l, b)
        Rectangle.unselect(widget, rectid)
