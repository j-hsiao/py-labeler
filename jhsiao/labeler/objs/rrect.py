"""Rotated rectangle.

x1,y1----ax2,ay2---x2,y2
|           ^      |
|           |      |
x4,y4----ax1,ay1---x3,y3
"""
from __future__ import division
__all__ = ['RRect']
from .obj import Obj
from . import ibinds
from .point import Point
import math

def veclen(vx, vy):
    """Length of vector."""
    return math.sqrt((vx**2 + vy**2))

def perpleft(vx, vy):
    """With <vx,vy> as up, return the perpendicular left vector.

    This vector takes into consideration that larger y is down.
    """
    if vx or vy:
        return vy, -vx
    else:
        return -1, 0

def norm(vec):
    m = veclen(*vec)
    if m:
        return vec[0]/m, vec[1]/m
    return (0,0)


@Obj.register
class RRect(Obj):
    """A rotated rectangle."""
    HELP = (
        'A rotated rectangle.  Unlike typical rotated rectangles, this'
        ' one includes a ratio 0-1 from left to right indicating the'
        ' center axis of the rotated rectangle.  This can be useful for'
        ' instance, to indicate the center axis of an object such as a'
        ' person (foot to head) while arms may be outstretched causing'
        ' the box to be shifted.  The default format is "cxywhal" which'
        ' is the center x,y coordinate, width, height, clockwise angle'
        ' of rotation, and left width.  Other formats are "corners"'
        ' (4 x,y pairs: topleft, topright, bottomright, bottomleft'
        ' followed by left width), "axis" (axis bottom x,y, up vector'
        ' x,y, leftwidth, right width)'
    )
    INFO = {'format': 'cxywha', 'angle': 'radians'}
    TAGS = ['RRect']
    TAGS.append(Obj.make_idtag(TAGS[0]))
    IDX = Obj.IDX + len(TAGS)
    IDNS = 6
    binds = ibinds['RRect']
    NCOORDS = 12
    def __init__(self, master, x, y, color='black'):
        alt = Obj.altcolor(master, color)
        super(RRect, self).__init__(
            master,
            master.create_polygon(
                x-50,y,x+50,y,x+50,y,x-50,y, fill=color, outline=color,
                stipple='gray50', activestipple='gray75', width=3),
            RRectHSide(master, x, y, alt),
            RRectHSide(master, x, y, alt),
            RRectVSide(master, x, y, alt),
            RRectVSide(master, x, y, alt),
            master.create_line(
                x,y,x,y, fill=alt, arrow='last', state='disabled',
                arrowshape=(12, 15, 4)),
        )
        self.addtags(master, self.ids[:1], RRect.TAGS[:1])
        self.addtags(master, self.ids[-1:], ['disabled'])
        self.addtags(master, self.ids, RRect.TAGS[1:])

    @staticmethod
    def color(master, idn='current'):
        return master.itemcget(idn, 'outline')

    @staticmethod
    def recolor(master, color, idn='current'):
        ids = RRect.members(master, idn)
        alt = Obj.altcolor(master, color)
        master.itemconfigure(ids[0], fill=color, outline=color)
        master.itemconfigure(ids[1], fill=alt)
        master.itemconfigure(ids[2], fill=alt)
        master.itemconfigure(ids[3], fill=alt)
        master.itemconfigure(ids[4], fill=alt)
        master.itemconfigure(ids[5], fill=alt)

    @staticmethod
    def parse_axis(ax1, ay1, vx, vy, left, right):
        """Calculate xy coordinates from axis data."""
        ax2, ay2 = ax1 + vx, ay1 + vy
        ux, uy = norm(perpleft(vx, vy))
        x1, y1 = ax2 + ux*left, ay2 + uy*left
        x2, y2 = ax2 - ux*right, ay2 - uy*right
        x3, y3 = x2 - vx, y2 - vy
        x4, y4 = x1 - vx, y1 - vy
        return x1, y1, x2, y2, x3, y3, x4, y4, ax1, ay1, ax2, ay2

    @staticmethod
    def parse_corners(x1, y1, x2, y2, x3, y3, x4, y4, left):
        """Calculate xy coordinates from corners data."""
        ux, uy = norm(x2-x1, y2-y1)
        ux *= left
        uy *= left
        return (
            x1, y1, x2, y2, x3, y3, x4, y4,
            x4 + ux, y4 + uy, x1 + ux, y1 + uy)

    @staticmethod
    def parse_cxywhal(cx, cy, w, h, a, l, **info):
        """Parse xy coordinates from cxywhal.

        info: class info: used for angle degrees or radians
        """
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
        return x1, y1, x2, y2, x3, y3, x4, y4, ax1, ay1, ax2, ay2

    @staticmethod
    def draw(
        widget, ids, x1, y1, x2, y2, x3, y3, x4, y4, ax1, ay1, ax2, ay2):
        """Draw rrect based on coordinates."""
        widget.coords(ids[0], x1, y1, x2, y2, x3, y3, x4, y4)
        widget.coords(ids[1], x4, y4, x1, y1)
        widget.coords(ids[2], x2, y2, x3, y3)
        widget.coords(ids[3], x3, y3, x4, y4)
        widget.coords(ids[4], x1, y1, x2, y2)
        widget.coords(ids[5], ax1, ay1, ax2, ay2)

    @staticmethod
    def coords(widget, idn):
        ids = RRect.members(widget, idn)
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords(ids[0])
        ax1, ay1, ax2, ay2 = widget.coords(ids[-1])
        return x1, y1, x2, y2, x3, y3, x4, y4, ax1, ay1, ax2, ay2

    @staticmethod
    def from_coords(coords, info):
        fmt = info.get('format')
        x1, y1, x2, y2, x3, y3, x4, y4, ax1, ay1, ax2, ay2 = coords
        left = veclen(ax2-x1, ay2-y1)
        if fmt == 'corners':
            return x1, y1, x2, y2, x3, y3, x4, y4, left
        elif fmt == 'axis':
            right = veclen(ax2-x2, ay2-y2)
            vx, vy = ax2-ax1, ay2-ay1
            return ax1, ay1, vx, vy, left, right
        else:
            cx = (x1 + x2 + x3 + x4)*.25
            cy = (y1 + y2 + y3 + y4)*.25
            rx, ry = x2-x1, y2-y1
            width = veclen(rx, ry)
            height = veclen(x2-x3, y2-y3)
            angle = math.atan2(ry, rx)
            if info.get('angle') == 'degrees':
                angle *= 180/math.pi
            return cx, cy, width, height, angle, left

    @staticmethod
    def to_coords(coords, info):
        fmt = info.get('format')
        if fmt == 'corners':
            x1,y1, x2,y2, x3,y3, x4,y4, left = coords
            rx, ry = x2-x1, y2-y1
            scale = left / veclen(rx, ry)
            rx *= scale
            ry *= scale
            return (
                x1,y1, x2,y2, x3,y3, x4,y4,
                x4+rx, y4+ry, x1+rx, y1+ry)
        elif fmt == 'axis':
            ax1,ay1, vx,vy, left, right = coords
            lx, ly = norm(perpleft(vx, vy))
            ax2, ay2 = ax1+vx, ay2+vy
            x1, y1 = ax2 + lx*left, ay2 + ly*left
            x2, y2 = ax2 - lx*right, ay2 - ly*right
            x3, y3 = x2-vx, y2-vy
            x4, y4 = x1-vx, y1-vy
            return x1,y1, x2,y2, x3,y3, x4,y4, ax1,ay1, ax2,ay2
        else:
            cx,cy, w,h, a, l = coords
            if info.get('angle') == 'degrees':
                a *= math.pi / 360
            ox, oy = math.cos(a), math.sin(a)
            rx, ry = ox * .5, oy * .5
            ox, oy = ox * l, oy * l
            ux, uy = perpleft(rx, ry)
            ux *= h
            uy *= h
            rx *= w
            ry *= w
            bx, by = cx - ux, cy - uy
            tx, ty = cx + ux, cy + uy
            x1, y1 = tx - rx, ty - ry
            x2, y2 = tx + rx, ty + ry
            x3, y3 = bx + rx, by + ry
            x4, y4 = bx - rx, by - ry
            ax1, ay1 = x4 + ox, y4 + oy
            ax2, ay2 = x1 + ox, y1 + oy
            return x1,y1, x2,y2, x3,y3, x4,y4, ax1,ay1, ax2,ay2

    @staticmethod
    def restore(widget, coords, color):
        ret = RRect(widget, 0, 0, color)
        RRect.draw(widget, ret.ids, *coords)
        return ret

    @staticmethod
    def activate(widget, ids):
        widget.itemconfigure(ids[0], width=5)
        for idn in ids[1:5]:
            widget.itemconfigure(idn, width=3)

    @staticmethod
    def deactivate(widget, ids):
        widget.itemconfigure(ids[0], width=3)
        for idn in ids[1:5]:
            widget.itemconfigure(idn, width=1)

    @staticmethod
    def selected(widget, ids):
        widget.itemconfigure(ids[0], fill='')
        RRect.deactivate(widget, ids)


    @staticmethod
    def unselected(widget, ids):
        widget.itemconfigure(
            ids[0], fill=widget.itemcget(ids[0], 'outline'))
        RRect.activate(widget, ids)

    @staticmethod
    @binds.bind('<Button-1>')
    def _select(widget, x, y):
        ids = RRect.members(widget, 'current')
        RRect.selected(widget, ids)
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords(ids[0])
        cx = (x1 + x2 + x3 + x4) / 4
        cy = (y1 + y2 + y3 + y4) / 4
        Obj.snapto(widget, x, y, (cx, cy))
        ax1, ay1, ax2, ay2 = widget.coords(ids[-1])
        widget.master.xhairs.up(ax2-ax1, ay2-ay1)
        widget.master.xhairs.moveto(widget, x, y)

    @staticmethod
    @binds.bind('<B1-Motion>')
    def _move(widget, x, y):
        nx, ny = Obj.canvxy(widget, x, y)
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords('current')
        cx = (x1 + x2 + x3 + x4) / 4
        cy = (y1 + y2 + y3 + y4) / 4
        dx = nx-cx
        dy = ny-cy
        widget.move(widget.gettags('current')[RRect.IDX], dx, dy)

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _unselect(widget, x, y):
        RRect.unselected(widget, RRect.members(widget, 'current'))
        widget.master.xhairs.up(0, 1)
        widget.master.xhairs.moveto(widget, x, y)


class RRectVSide(Obj):
    TAGS = ['RRectVSide']
    IDX = Obj.IDX + 2
    binds = ibinds['RRectVSide']
    def __init__(self, master, x, y, color='black'):
        super(RRectVSide, self).__init__(
            master,
            master.create_line(
                x-50, y, x+50, y,
                fill=color, width=1, activewidth=4))
        self.addtags(master, self.ids, RRectVSide.TAGS)

    @staticmethod
    def snapto(widget, x, y, idn='current'):
        ids = RRectVSide.members(widget, idn)
        idn = widget.find('withtag', idn)[0]
        ax1, ay1, ax2, ay2 = widget.coords(ids[-1])
        if ids.index(idn) == 3:
            Obj.snapto(widget, x, y, (ax1, ay1))
        else:
            Obj.snapto(widget, x, y, (ax2, ay2))

    @staticmethod
    @binds.bind('<Shift-Motion>', '<Shift-Leave>')
    def _snapto(widget, x, y):
        RRectVSide.snapto(widget, x, y)

    @staticmethod
    @binds.bind('<Button-1>')
    def _select(widget, x, y):
        widget.itemconfigure('current', activewidth=1)
        ids = RRectVSide.members(widget, 'current')
        RRect.selected(widget, ids)
        RRectVSide.snapto(widget, x, y)
        x1, y1, x2, y2 = widget.coords(ids[-1])
        widget.master.xhairs.up(x2-x1, y2-y1)
        widget.master.xhairs.moveto(widget, x, y)

    @staticmethod
    @binds.bind(
        '<B1-Motion>','<Shift-B1-Motion>',
        '<B1-Leave>', '<Shift-B1-Leave>')
    def _moved(widget, x, y):
        x, y = Obj.canvxy(widget, x, y)
        ids = RRectVSide.members(widget, 'current')
        idn = widget.find('withtag', 'current')[0]
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords(ids[0])
        ax1, ay1, ax2, ay2 = widget.coords(ids[-1])
        left = veclen(x1-ax2, y1-ay2)
        right = veclen(x2-ax2, y2-ay2)
        if ids.index(idn) == 3:
            ax1, ay1 = x, y
        else:
            ax2, ay2 = x, y
        vx, vy = ax2-ax1, ay2-ay1
        RRect.draw(widget, ids, 
            *RRect.parse_axis(ax1, ay1, vx, vy, left, right))
        widget.master.xhairs.up(vx, vy)

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _deselect(widget, x, y):
        widget.itemconfigure('current', activewidth=4)
        ids = RRectVSide.members(widget, 'current')
        RRect.unselected(widget, ids)
        widget.master.xhairs.up(0, 1)
        widget.master.xhairs.moveto(widget, x, y)

class RRectHSide(Obj):
    TAGS = ['RRectHSide']
    IDX = Obj.IDX + 2
    binds = ibinds['RRectHSide']
    def __init__(self, master, x, y, color='black'):
        super(RRectHSide, self).__init__(
            master,
            master.create_line(
                x, y, x, y,
                fill=color, width=1, activewidth=4))
        self.addtags(master, self.ids, RRectHSide.TAGS)

    @staticmethod
    def snapto(widget, x, y, idn='current'):
        x1, y1, x2, y2 = widget.coords(idn)
        Obj.snapto(widget, x, y, ((x1+x2)/2, (y1+y2)/2))

    @staticmethod
    @binds.bind('<Shift-Motion>', '<Shift-Leave>')
    def _snapto(widget, x, y):
        RRectHSide.snapto(widget, x, y)

    @staticmethod
    @binds.bind('<Button-1>')
    def _select(widget, x, y):
        widget.itemconfigure('current', activewidth=1)
        ids = RRectHSide.members(widget, 'current')
        RRect.selected(widget, ids)
        RRectHSide.snapto(widget, x, y)
        x1, y1, x2, y2 = widget.coords('current')
        widget.master.xhairs.up(x2-x1, y2-y1)
        widget.master.xhairs.moveto(widget, x, y)

    @staticmethod
    @binds.bind(
        '<B1-Motion>','<Shift-B1-Motion>',
        '<B1-Leave>', '<Shift-B1-Leave>')
    def _moved(widget, x, y):
        cx, cy = Obj.canvxy(widget, x, y)
        ids = RRectHSide.members(widget, 'current')
        x1, y1, x2, y2, x3, y3, x4, y4 = widget.coords(ids[0])
        ax1, ay1, ax2, ay2 = widget.coords(ids[-1])
        idn = widget.find('withtag', 'current')[0]
        vx, vy = ax2-ax1, ay2-ay1
        ux, uy = norm(perpleft(vx, vy))
        if ids.index(idn) == 1:
            left = (cx-ax1)*ux + (cy-ay1)*uy
            right = veclen(x2-ax2, y2-ay2)
            if left < 0:
                dx, dy = ux*left, uy*left
                if abs(dx) >= 1 or abs(dy) >= 1:
                    Obj.snapto(widget, x, y, (cx-dx, cy-dy))
                left = 0
        else:
            ux, uy = norm(perpleft(vx, vy))
            right = (cx-ax1)*ux + (cy-ay1)*uy
            right *= -1
            left = veclen(x1-ax2, y1-ay2)
            if right < 0:
                dx, dy = ux*right, uy*right
                if abs(dx) >= 1 or abs(dy) >= 1:
                    Obj.snapto(widget, x, y, (cx+dx, cy+dy))
                right = 0
        RRect.draw(widget, ids,
            *RRect.parse_axis(ax1, ay1, vx, vy, left, right))

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _deselect(widget, x, y):
        widget.itemconfigure('current', activewidth=4)
        ids = RRectHSide.members(widget, 'current')
        RRect.unselected(widget, ids)
        widget.master.xhairs.up(0, 1)
        widget.master.xhairs.moveto(widget, x, y)
