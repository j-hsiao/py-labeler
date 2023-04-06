"""Rotated rectangle."""
from __future__ import division
__all__ = ['RRect']
from . import Obj, bindings
from .point import Point
import math

def veclen(vx, vy):
    """Length of vector."""
    return math.sqrt((vx**2 + vy**2))

def perpleft(vx, vy):
    """With <vx,vy> as up, return the perpendicular left vector.

    This vector takes into consideration that larger y is down.
    """
    return vy, -vx

@Obj.register
class RRect(Obj):
    """A rotated rectangle."""
    HELP = ' '.join((
        'A rotated rectangle.  Unlike typical rotated rectangles, this'
        'one includes a ratio 0-1 from left to right indicating the'
        'center axis of the rotated rectangle.  This can be useful for'
        'instance, to indicate the center axis of an object such as a'
        'person (foot to head) while arms may be outstretched causing'
        'the box to be shifted.  The default format is "cxywhar" which'
        'is the center x,y coordinate, width, height, clockwise angle'
        'of rotation, and axis ratio.  Other formats are "corners"'
        '(4 x,y pairs: topleft, topright, bottomright, bottomleft'
        'followed by axis ratio), "axis" (axis bottom x,y, axis vector'
        'x,y, leftwidth, right width)'
    ))
    INFO = {'format': 'cxywha'}
    TAGS = ['RRect', 'RRect_{}']
    IDX = Obj.IDX + len(TAGS)
    binds = bindings['RRect']
    def __init__(self, master, x, y, color='black'):
        alt = Obj.altcolor(master, color)
        super(RRect, self).__init__(
            master,
            master.create_polygon(
                x,y,x,y,x,y,x,y, fill=color, outline=color,
                stipple='gray12', activestipple='gray25'),
            RRectPt(master, x, y, color),
            RRectPt(master, x, y, color),
            master.create_line(x,y,x,y, fill=alt, arrow='last', state='disabled'),
        )
        self.addtags(master, self.ids[:1], RRect.TAGS[:1])
        self.addtags(master, self.ids, RRect.TAGS[1:])


class RREctPt(Point)
    """A point on the RRect axis."""
    TAGS = ['RRectPt']
    IDX = Point.IDX + 2
    binds = bindings['RRectPt']
    def __init__(self, master, x, y, color='black'):
        super(RRectPt, self).__init__(master, x, y, color)
        self.addtags(master, self.ids, RRectPt.TAGS)
