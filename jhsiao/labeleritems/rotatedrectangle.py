from __future__ import division

__all__ = ['RotatedRectangle']
from itertools import chain
import math

from . import Item
from .point import Point
from .. import tkutil as tku

class RotatedRectangle(Item, tku.Behavior):
    """A rotated rectangle.

    tags: Item, Item_<master>, RRect
    sidetags: Item, Item_<master>, RRectSide,
        RRectSide_<rotatedrectangle>
    arrowtags: Item, Item_<master>, Point, RRectPt,
        RRectPt_<rotatedrectangle>
    data:
        cx, cy, w, h, a(rad), offset

        cx,cy = center x,y coordinates
        w, h = width and height of rectangle
        a(rad) = angle in radians, clockwise, 0 has the arrow pointing
            up in image coordinates.
        offset: a value from [0,1] indicating offset of the arrow from
            the left of the unrotated rectangle.
    """
    LENGTH = 6
    TAGS = ['RotatedRectangle']
    ARROW = 'Arrow_'
    def __init__(self, widget, x, y, owned=False):
        color = 'black'
        idn = widget.create_polygon(
            x+30,y,x-30,y,x-30,y,x+30,y,
            fill=color, stipple='gray12', activestipple='gray50',
            outline=self.modcolor(widget, color),
            activeoutline=color, width=1, activewidth=2)
        sides = RRectSide(widget, x, y)
        points = [RRectPt(widget, x, y, owned=True) for _ in range(2)]
        arrow = widget.create_line(x,y,x,y, arrow='last', state='disabled')
        super(RotatedRectangle, self).__init__(
            widget, idn, sides, points, arrow, owned=owned)
        if not widget.tag_bind(RotatedRectangle.TAGS[0]):
            self.bind(widget, bindfunc='tag_bind')
            RRectSide.bind(widget, bindfunc='tag_bind')
            RRectPt.bind(widget, bindfunc='tag_bind')

    def addtags(self, tagdb):
        super(RotatedRectangle, self).addtags(tagdb)
        suff = self.idns[0]
        tagdb.add(self.idns[0], RotatedRectangle.TAGS)
        tagdb.add(self.idns[1:3], RRectSide.TAGS, suffix=suff)
        tagdb.add(self.idns[3:5], RRectPt.TAGS, suffix=suff)
        tagdb.add(self.idns[5], RotatedRectangle.ARROW, suffix=suff)

    @staticmethod
    def recolor_(widget, idn, color):
        subcolor = Item.modcolor(widget, color)
        sidn = str(idn)
        widget.itemconfigure(
            sidn, fill=color, activeoutline=color, outline=subcolor)
        pttag = RRectPt.TAGS[1]+sidn
        RRectPt.recolort(widget, pttag, color)
        sidetag = RRectSide.TAGS[1]+sidn
        RRectSide.recolort(widget, sidetag, subcolor)
        arrowtag = RotatedRectangle.ARROW+sidn
        widget.itemconfigure(arrowtag, fill=subcolor)

    @staticmethod
    def select(widget, idn):
        widget.itemconfigure(idn, fill='', activewidth=1)
        RRectPt.select(widget, RRectPt.TAGS[1]+str(idn))

    @staticmethod
    def unselect(widget, idn):
        color = widget.itemcget(idn, 'activeoutline')
        widget.itemconfigure(idn, fill=color, activewidth=2)
        RRectPt.unselect(widget, RRectPt.TAGS[1]+str(idn))

    @tku.Bindings('<Button-1>')
    @staticmethod
    def _pick_rrect(widget, x, y):
        """Click to pick up rectangle."""
        widget.draginfo = widget.xy(x, y)
        RotatedRectangle.select(
            widget, widget.find('withtag', 'current')[0])
        widget.crosshairs.hide(widget)

    @tku.Bindings('<ButtonRelease-1>')
    @staticmethod
    def _drop_rrect(widget, x, y):
        """Release to drop rectangle."""
        RotatedRectangle.unselect(
            widget, widget.find('withtag', 'current')[0])
        widget.crosshairs.show(widget, x, y)

    @tku.Bindings('<B1-Motion>')
    @staticmethod
    def _move_rrect(widget, x, y):
        """Drag to move rectangle."""
        ox, oy = widget.draginfo
        widget.draginfo = x, y = widget.xy(x, y)
        dx, dy = x-ox, y-oy
        widget.move(RotatedRectangle._allcurtags(widget), dx, dy)

    @staticmethod
    def _allcurtags(widget):
        suff = str(widget.find('withtag', 'current')[0])
        return '||'.join(
            [k+suff if k[-1] == '_' else k for k in 
            ('current', RRectSide.TAGS[1], RRectPt.TAGS[1], RotatedRectangle.ARROW)])

    def todict(self, widget):
        x1,y1, x2,y2, x3,y3, x4,y4 = widget.coords(self.idns[0])
        ax1,ay1, ax2,ay2 = widget.coords(self.idns[5])
        cx, cy = (x1+x2+x3+x4)/4, (y1+y2+y3+y4)/4
        # corners are in typical axis
        # but for convenience, use flipped image axes
        dx, dy = x1-x2, y1-y2
        wsq = dx**2 + dy**2
        w = math.sqrt(wsq)
        if wsq:
            offset = (dx*(ax2-x2) + dy*(ay2-y2))/wsq
        else:
            offset = 0
        h = math.sqrt((x2-x3)**2 + (y2-y3)**2)
        a = math.atan2(dy, dx)
        ret = super(RotatedRectangle, self).todict(widget)
        ret['data'] = (cx, cy, w, h, a, offset)
        return ret

    @classmethod
    def fromdict(cls, widget, dct, owned=False):
        cx, cy, w, h, a, offset = dct['data']
        s = math.sin(a)/2
        c = math.cos(a)/2
        vx, vy = s*h, c*h
        tx, ty = cx+vx, cy-vy
        bx, by = cx-vx, cy+vy
        hx, hy = c*w, s*w
        x1, y1 = tx+hx, ty+hy
        x2, y2 = tx-hx, ty-hy
        x3, y3 = bx-hx, by-hy
        x4, y4 = bx+hx, by+hy
        offset *= 2
        hx *= offset
        hy *= offset
        ax1, ay1 = x3+hx, y3+hy
        ax2, ay2 = x2+hx, y2+hy
        ret = cls(widget, ax1, ay1, owned)
        widget.coords(ret.idns[0], x1,y1, x2,y2, x3,y3, x4,y4)
        widget.coords(ret.idns[1], x4,y4, x1,y1)
        widget.coords(ret.idns[2], x3,y3, x2,y2)
        RRectPt.moveto(widget, ret.idns[3], ax1, ay1)
        RRectPt.moveto(widget, ret.idns[4], ax2, ay2)
        widget.coords(ret.idns[5], ax1,ay1, ax2,ay2)
        return ret

    @staticmethod
    def cxywha(data):
        """Convert data from todict()['data'] to cxywha format.

        a = radians.
        """
        return data[:5]

    @staticmethod
    def corners(data):
        """Convert data from todict()['data'] to corners format.

        a = radians.
        """
        cx, cy, w, h, a = data[:5]
        w /= 2
        h /= 2
        c = math.cos(a)/2
        s = math.sin(a)/2
        hx, hy = c*w, s*w
        vx, vy = s*h, c*h
        tx, ty = cx+vx, cy-vy
        bx, by = cx-vx, cy+vy
        x1, y1 = tx-hx, ty-hy
        x2, y2 = tx+hx, ty+hy
        x3, y3 = bx+hx, by+hy
        x4, y4 = bx-hx, by-hy
        return [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]

    @staticmethod
    def ltrba(data):
        """Convert data from todict()['data'] to ltrba format.

        a = radians.
        """
        cx, cy, w, h, a = data[:5]
        w /= 2
        h /= 2
        l = cx-w
        t = cy-h
        r = cx+w
        b = cy+h
        return l, t, r, b, a


    @staticmethod
    def interpolate(data1, data2, interp):
        """Interpolate, take smallest rotation angle."""
        info = [(d1, d2-d1) for d1,d2 in zip(data1, data2)]
        pi = math.pi
        pi2 = 2*pi
        dif = info[4][1]
        if abs(dif) > pi:
            dif %= pi2
            if dif > pi:
                dif -= pi2
            info[4] = (info[4][0], dif)
        data = [base + interp*dif for base, dif in info]
        data[4] %= pi2
        return data


class RRectSide(Item):
    TAGS = ['RRectSide', 'RRectSide_']

    def __init__(self, widget, x, y):
        super(RRectSide, self).__init__(
            widget,
            widget.create_line(x-30, y, x-30, y, width=2, activewidth=10),
            widget.create_line(x+30, y, x+30, y, width=2, activewidth=10),
            owned=True)

    @staticmethod
    def recolor_(widget, tagOrIdn, color):
        widget.itemconfigure(tagOrIdn, fill=color)
    recolort = recolor_

    @tku.Bindings('<Shift-Leave>', '<Shift-Motion>')
    @staticmethod
    def _snapto(widget, x, y):
        """Hold Shift to snap to rectangle side under cursor."""
        x1,y1, x2,y2 = widget.coords('current')
        nx, ny = (x1+x2)//2, (y1+y2)//2
        cx, cy = widget.xy(x,y)
        if cx!=nx or cy!=ny:
            widget.event_generate(
                '<Shift-Motion>',
                x=x+(nx-cx), y=y+(ny-cy), warp=True, when='head')

    @tku.Bindings('<Button-1>')
    @classmethod
    def _pick_side(cls, widget, x, y):
        """Click to pick a side."""
        rrectsidetag = RRectSide.tagat(widget, 'current', 1)
        rrectidn = RRectSide.getidn(rrectsidetag)
        RotatedRectangle.select(widget, rrectidn)
        widget.itemconfigure('current', activewidth=1)
        x1,y1, x2,y2 = widget.coords('current')
        widget.crosshairs.angle(x2-x1, y2-y1)
        cx, cy = (x1+x2)/2, (y1+y2)/2
        canvx, canvy = widget.xy(x, y)
        dx, dy = cx-canvx, cy-canvy
        widget.event_generate(
            '<B1-Motion>', x=x+dx, y=y+dy, warp=True, when='head')


    @tku.Bindings('<B1-Motion>')
    @classmethod
    def drag_side(cls, widget, x, y):
        """Drag to change side width."""
        x, y = widget.xy(x, y)
        rrectsidetag = RRectSide.tagat(widget, 'current', 1)
        rrectidn = RRectSide.getidn(rrectsidetag)
        x1,y1, x2,y2, x3,y3, x4,y4 = widget.coords(rrectidn)
        Lside, Rside = widget.find('withtag', rrectsidetag)
        curside = widget.find('withtag', 'current')[0]
        ax1,ay1, ax2,ay2 = widget.coords(RotatedRectangle.ARROW+rrectidn)
        vx, vy = ax2-ax1, ay2-ay1
        mag = math.sqrt(vx**2 + vy**2)
        if mag:
            vx /= mag
            vy /= mag
            if curside == Lside:
                svx, svy = -vy, vx
            else:
                svx, svy = vy, -vx
        else:
            svx, svy = (-1,0) if curside == Lside else (1,0)
        dot = max((x-ax2)*svx + (y-ay2)*svy, 0)
        svx *= dot
        svy *= dot
        nx1,ny1 = ax1+svx, ay1+svy
        nx2,ny2 = ax2+svx, ay2+svy
        widget.coords('current', nx1,ny1, nx2,ny2)
        if curside == Lside:
            widget.coords(rrectidn, nx2,ny2, x2,y2, x3,y3, nx1,ny1)
        else:
            widget.coords(rrectidn, x1,y1, nx2,ny2, nx1,ny1, x4,y4)

    @tku.Bindings('<ButtonRelease-1>')
    @classmethod
    def _drop_side(cls, widget, x, y):
        """Release to finish changing side-width."""
        rrectsidetag = RRectSide.tagat(widget, 'current', 1)
        rrectidn = RRectSide.getidn(rrectsidetag)
        RotatedRectangle.unselect(widget, rrectidn)
        widget.itemconfigure('current', activewidth=10)
        widget.crosshairs.angle(0,0)
        widget.crosshairs.draw_crosshairs(widget, x,y)


class RRectPt(Point):
    """Rotated Rectangle height points."""
    TAGS = ['RRectPt', 'RRectPt_']

    @tku.Bindings('<Button-1>')
    @classmethod
    def _pick_height(cls, widget):
        """Click to select height (points at arrow ends)."""
        rrectpttag = RRectPt.tagat(widget, 'current', 1)
        rrectidn = RRectPt.getidn(rrectpttag)
        RotatedRectangle.select(widget, rrectidn)

    @tku.Bindings('<B1-Motion>')
    @classmethod
    def _changeheight(cls, widget):
        """Drag to change height/angle."""
        rrectpttag = RRectPt.tagat(widget, 'current', 1)
        rrectidn = RRectPt.getidn(rrectpttag)
        arrowtag = RotatedRectangle.ARROW+rrectidn
        sidestag = RRectSide.TAGS[1]+rrectidn
        lside, rside = widget.find('withtag', sidestag)

        p1, p2 = widget.find('withtag', rrectpttag)
        px1, py1 = cls.xy(widget, p1)
        px2, py2 = cls.xy(widget, p2)
        ax1, ay1, ax2, ay2 = widget.coords(arrowtag)
        x1,y1, x2,y2, x3,y3, x4,y4 = widget.coords(rrectidn)
        vx, vy = px2-px1, py2-py1
        w1 = math.sqrt((x1-ax2)**2 + (y1-ay2)**2)
        w2 = math.sqrt((x2-ax2)**2 + (y2-ay2)**2)
        widget.coords(arrowtag, px1, py1, px2, py2)
        if vx or vy:
            mag = math.sqrt(vx**2 + vy**2)
            vy /= mag
            vx /= mag
            Ldx, Ldy = -vy*w1, vx*w1
            Rdx, Rdy = vy*w2, -vx*w2
            x1,y1 = px2+Ldx, py2+Ldy
            x2,y2 = px2+Rdx, py2+Rdy
            x3,y3 = px1+Rdx, py1+Rdy
            x4,y4 = px1+Ldx, py1+Ldy
            widget.coords(rrectidn, x1,y1, x2,y2, x3,y3, x4,y4)
            widget.coords(lside, x4,y4, x1,y1)
            widget.coords(rside, x3,y3, x2,y2)
        else:
            L, R = px1+w1, px1-w2
            widget.coords(rrectidn, L,py2, R,py2, R,py1, L,py1)
            widget.coords(lside, L,py1, L,py2)
            widget.coords(rside, R,py1, R,py2)
        widget.crosshairs.angle(vx, vy)

    @tku.Bindings('<ButtonRelease-1>')
    @classmethod
    def _fillrect(cls, widget, x, y):
        """Click to finish changing height/angle."""
        widget.crosshairs.angle(0, 0)
        widget.crosshairs.draw_crosshairs(widget, x, y)
        rrectpttag = RRectPt.tagat(widget, 'current', 1)
        rrectidn = RRectPt.getidn(rrectpttag)
        RotatedRectangle.unselect(widget,rrectidn)
