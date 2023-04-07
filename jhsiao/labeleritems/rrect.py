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
        'the box to be shifted.  The default format is "cxywhal" which'
        'is the center x,y coordinate, width, height, clockwise angle'
        'of rotation, and left width.  Other formats are "corners"'
        '(4 x,y pairs: topleft, topright, bottomright, bottomleft'
        'followed by left width), "axis" (axis bottom x,y, axis vector'
        'x,y, leftwidth, right width)'
    ))
    INFO = {'format': 'cxywha', 'angle': 'radians'}
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

    @staticmethod
    def color(master, idn='current'):
        return master.itemcget(idn, 'outline')

    @staticmethod
    def recolor(master, color, idn='current'):
        ids = RRect.members(idn, 'current')
        alt = Obj.altcolor(master, color)
        master.itemconfigure(ids[0], fill=color, outline=color)
        # TODO

    @staticmethod
    def data(widget, idn, info):
        fmt = info.get('format')
        ids = RRect.members(idn, 'current')
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords(ids[0])
        ax1, ay1, ax2, ay2 = widget.coords[ids[-1]]
        left = veclen(ax2-x1, ay2-y1)
        if fmt == 'corners':
            return (x1, y1, x2, y2, x3, y3, x4, y4, left)
        elif fmt == 'axis':
            vx, vy = ax2-ax1, ay2-ay1
            return ax1, ay1, vx, vy, left, veclen(x2-ax2, y2-ay2)
        else:
            cx = (x1 + x2 + x3 + x4) / 4
            cy = (y1 + y2 + y3 + y4) / 4
            width = veclen(x2-x1, y2-y1)
            height = veclen(x3-x2, y3-y2)
            if info.get('angle') == 'degrees':
                return (
                    cx, cy, width, height,
                    math.atan2(y2-y1, x2-x1)*180/math.pi, left)
            else:
                return cx, cy, width, height, math.atan2(y2-y1, x2-x1), left

    @staticmethod
    def fromdict(widget, dct, info):
        fmt = info.get('format')
        if fmt == 'corners':
            x1, y1, x2, y2, x3, y3, x4, y4, l = info['data']
            vx, vy = x2-x1, y2-y1
            width = veclen(vx, vy)
            scale = l / width
            ax2 = x1 + vx*scale
            ay2 = y1 + vy*scale
            ax1 = x4 + vx*scale
            ay1 = y4 + vy*scale
        elif fmt == 'axis':
            ax1, ay1, vx, vy, left, right = info['data']
            ax2 = ax1 + vx
            ay2 = ay1 + vy
            ux, uy = perpleft(vx, vy)
            m = veclen(ux, uy)
            ux /= m
            uy /= m
            x1 = ax2 + ux*left
            y1 = ay2 + uy*left
            x2 = ax2 - ux*right
            y2 = ay2 - uy*right
            x3 = x2-vx
            y3 = y2-vy
            x4 = x1-vx
            y4 = y1-vy
        else:
            cx, cy, w, h, a, l = info['data']
            if info.get('angle') == 'degrees':
                a *= math.pi / 180
            ux, uy = math.cos(a)*.5, math.sin(a)*.5
            wx, wy = ux*.5, uy*.5
            hx, hy = perpleft(wx, wy)
            wx *= w
            wy *= w
            hx *= h
            hy *= h
            tx, ty = cx + hx, cy + hy
            bx, by = cx - hx, cy - hy
            x1, y1 = tx - wx, ty - wy
            x2, y2 = tx + wx, ty + wy
            x3, y3 = bx + wx, by + wy
            x4, y4 = bx - wx, by - wy
            ax2, ay2 = x1 + ux*l, y1+uy*l
            ax1, ay1 = x4 + ux*l, y4+uy*l
        # TODO

    @staticmethod
    def activate(widget, ids):
        # TODO
        pass

    @staticmethod
    def deactivate(widget, ids):
        # TODO
        pass

    @staticmethod
    def selected(widget, idns):
        # TODO
        pass

    @staticmethod
    def unselected(widget, idns):
        # TODO
        pass

    @staticmethod
    @binds.bind('<Button-1>')
    def _selected(widget, x, y):
        ids = RRect.members(widget, 'current')
        RRect.selected(widget, ids)
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords(ids[0])
        cx = (x1 + x2 + x3 + x4) / 4
        cy = (y1 + y2 + y3 + y4) / 4
        Obj.snapto(widget, x, y, cx, cy)

    @staticmethod
    @binds.bind('<B1-Motion>')
    def _move(widget, x, y):
        nx, ny = Obj.canvxy(x, y)
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords('current')
        cx = (x1 + x2 + x3 + x4) / 4
        cy = (y1 + y2 + y3 + y4) / 4
        dx = nx-cx
        dy = ny-cy
        widget.move(widget.gettags('current')[RRect.IDX], dx, dy)








