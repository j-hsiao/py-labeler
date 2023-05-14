"""A rectangle (axis aligned)."""
from __future__ import division
__all__ = ['Rect']
from .obj import Obj
from . import ibinds
from .point import Point

@Obj.register
class Rect(Obj):
    """A rectangle."""
    HELP = ' '.join((
        'A Rectangle.  Multiple formats are supported.  The default is'
        '"ltrb" which gives the left, top, right, bottom coordinates. '
        'Alternative values are "cxywh" which gives the center x,y'
        'coordinates and width, height', '"ltwh" which is top left x,y'
        'followed by width and height.'
    ))
    INFO = {'format': 'ltrb'}
    TAGS = ['Rect']
    TAGS.append(Obj.make_idtag(TAGS[0]))
    IDX = Obj.IDX + len(TAGS)
    IDNS = 9
    NCOORDS = 4
    binds = ibinds['Rect']
    def __init__(self, master, x, y, color='black'):
        alt = Obj.altcolor(master, color)
        super(Rect, self).__init__(
            master,
            master.create_rectangle(
                x, y, x, y, fill=color,
                outline=color,
                stipple='gray50', activestipple='gray75',
                width=3),
            RectSide(master, x, y, alt),
            RectSide(master, x, y, alt),
            RectSide(master, x, y, alt),
            RectSide(master, x, y, alt),
            RectPt(master, x, y, color),
            RectPt(master, x, y, color),
            RectPt(master, x, y, color),
            RectPt(master, x, y, color),
        )
        self.addtags(master, self.ids[:1], Rect.TAGS[:1])
        self.addtags(master, self.ids, Rect.TAGS[-1:])

    @staticmethod
    def color(master, idn='current'):
        return master.itemcget(idn, 'outline')

    @staticmethod
    def recolor(master, color, idn='current'):
        ids = Rect.members(master, idn)
        master.itemconfigure(ids[0], fill=color, outline=color)
        alt = Obj.altcolor(master, color)
        for sid in ids[1:5]:
            master.itemconfigure(sid, fill=alt)
        for pid in ids[5:]:
            RectPt.recolor(master, color, pid)

    @staticmethod
    def moveto(master, idns, l, t, r, b):
        """Move rect to coordinates."""
        master.coords(idns[0], l, t, r, b)
        master.coords(idns[1], l, t, r, t)
        master.coords(idns[2], r, t, r, b)
        master.coords(idns[3], l, b, r, b)
        master.coords(idns[4], l, t, l, b)
        RectPt.moveto(master, l, t, idns[5])
        RectPt.moveto(master, r, t, idns[6])
        RectPt.moveto(master, r, b, idns[7])
        RectPt.moveto(master, l, b, idns[8])

    @staticmethod
    def coords(widget, idn):
        return widget.coords(idn)

    @staticmethod
    def from_coords(coords, info):
        fmt = info.get('format')
        if fmt == 'cxywh':
            return (l+r)/2, (t+b)/2, r-l, b-t
        elif fmt == 'ltwh':
            l, t, r, b = coords
            return l, t, r-l, b-t
        else:
            return coords

    @staticmethod
    def to_coords(coords, info):
        fmt = info.get('format')
        if fmt == 'cxywh':
            cx, cy, w, h = coords
            hw * .5
            hh * .5
            return cx-hw, cy-hh, cx+hw, cy+hh
        elif fmt == 'ltwh':
            l, t, w, h = coords
            return l, t, l+w, t+h
        else:
            return coords

    @staticmethod
    def restore(widget, coords, color):
        l, t, r, b = coords
        ret = Rect(widget, l, t, color)
        Rect.moveto(widget, ret.idns, l, t, r, b)
        return ret

    @staticmethod
    def activate(widget, ids):
        widget.itemconfigure(ids[0], width=5)
        for sid in ids[1:5]:
            widget.itemconfigure(sid, width=3)
        for pid in ids[5:]:
            RectPt.activate(widget, [pid])

    @staticmethod
    def deactivate(widget, ids):
        widget.itemconfigure(ids[0], width=3)
        for sid in ids[1:5]:
            widget.itemconfigure(sid, width=1)
        for pid in ids[5:]:
            RectPt.deactivate(widget, [pid])

    @staticmethod
    def selected(widget, idns):
        """Change when click/drag."""
        widget.itemconfigure(idns[0], fill='')
        Rect.deactivate(widget, idns)

    @staticmethod
    def unselected(widget, idns):
        """Change when releasing click/drag."""
        widget.itemconfigure(
            idns[0], fill=widget.itemcget(idns[0], 'outline'))
        Rect.activate(widget, idns)

    @staticmethod
    @binds.bind('<Button-1>')
    def _select(widget, x, y):
        Rect.selected(widget, Rect.members(widget, 'current'))
        l, t, r, b = widget.coords('current')
        Obj.snapto(widget, x, y, ((l+r)//2, (t+b)//2))

    @staticmethod
    @binds.bind(
        '<B1-Motion>', '<B1-Shift-Motion>',
        '<B1-Leave>', '<B1-Shift-Leave>')
    def _move(widget, x, y):
        l, t, r, b = widget.coords('current')
        ox = (l+r)//2
        oy = (t+b)//2
        nx, ny = Obj.canvxy(widget, x, y)
        dx = nx-ox
        dy = ny-oy
        widget.move(
            widget.gettags('current')[Rect.IDX],
            dx, dy)

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _unselect(widget):
        Rect.unselected(widget, Rect.members(widget, 'current'))

class RectSide(Obj):
    TAGS = ['RectSide']
    binds = ibinds['RectSide']
    IDX = Obj.IDX + 2
    def __init__(self, master, x, y, color):
        super(RectSide, self).__init__(
            master, master.create_line(
                x, y, x, y,
                width=1, activewidth=4, fill=color))
        self.addtags(master, self.ids, RectSide.TAGS)

    @staticmethod
    def snapto(widget, x, y, idn='current'):
        x1, y1, x2, y2 = widget.coords('current')
        Obj.snapto(widget, x, y, ((x1+x2)//2, (y1+y2)//2))

    @staticmethod
    @binds.bind(
        '<B1-Motion>', '<Shift-B1-Motion>',
        '<B1-Leave>', '<Shift-B1-Leave>')
    def _moved(widget, x, y):
        ids = RectSide.members(widget, 'current')
        idx = ids.index(widget.find('withtag', 'current')[0], 1)
        x, y = Obj.canvxy(widget, x, y)
        x1, y1, x2, y2 = widget.coords(ids[1 + (idx+1)%4])
        if idx == 1:
            Rect.moveto(widget, ids, x1, y, x2, y2)
        elif idx == 2:
            Rect.moveto(widget, ids, x1, y1, x, y2)
        elif idx == 3:
            Rect.moveto(widget, ids, x1, y1, x2, y)
        elif idx == 4:
            Rect.moveto(widget, ids, x, y1, x2, y2)

    @staticmethod
    @binds.bind('<Button-1>')
    def _select(widget, x, y):
        Rect.selected(widget, RectSide.members(widget, 'current'))
        RectSide.snapto(widget, x, y)
        widget.itemconfigure('current', activewidth=1)

    @staticmethod
    @binds.bind('<Shift-Motion>', '<Shift-Leave>')
    def _snapto(widget, x, y):
        RectSide.snapto(widget, x, y)

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _normalize(widget, x, y):
        widget.itemconfigure('current', activewidth=4)
        ids = RectSide.members(widget, 'current')
        Rect.unselected(widget, ids)
        idx = ids.index(widget.find('withtag', 'current')[0], 1)
        x, y = Obj.canvxy(widget, x, y)
        x1, y1, x2, y2 = widget.coords(ids[1 + (idx+1)%4])
        swap = None
        if idx == 1:
            if y > y2:
                swap = 1, 3
        elif idx == 2:
            if x < x1:
                swap = 2, 4
        elif idx == 3:
            if y < y2:
                swap = 1, 3
        elif idx == 4:
            if x > x1:
                swap = 2, 4
        if swap is not None:
            s1, s2 = swap
            widget.tag_raise(ids[s1], ids[s2-1])
            widget.tag_raise(ids[s2], ids[s1-1])
            ids = list(ids)
            ids[s1], ids[s2] = ids[s2], ids[s1]
        Rect.moveto(widget, ids, *widget.coords(ids[0]))

class RectPt(Point):
    TAGS = ['RectPt']
    binds = ibinds['RectPt']
    IDX = Point.IDX + 2
    def __init__(self, master, x, y, color):
        super(RectPt, self).__init__(master, x, y, color)
        self.addtags(master, self.ids, RectPt.TAGS)

    @staticmethod
    @binds.bind(
        '<B1-Motion>', '<Shift-B1-Motion>',
        '<B1-Leave>', '<Shift-B1-Leave>')
    def _moved(widget, x, y):
        idns = RectPt.members(widget, 'current')
        idx = idns.index(widget.find('withtag', 'current')[0], 5)
        x, y = Obj.canvxy(widget, x, y)
        x2, y2 = RectPt.coords(widget, idns[5 + (idx - 3) % 4], None)
        if idx == 5:
            x1, y1 = x, y
        elif idx == 6:
            x1, y1, x2, y2 = x2, y, x, y2
        elif idx == 7:
            x1, y1, x2, y2 = x2, y2, x, y
        elif idx == 8:
            x1, y1, x2, y2 = x, y2, x2, y
        Rect.moveto(widget, idns, x1, y1, x2, y2)

    @staticmethod
    @binds.bind('<Button-1>')
    def _select(widget):
        Rect.selected(widget, RectPt.members(widget, 'current'))

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _normalize(widget):
        """Reorder points based on current positions."""
        idns = RectPt.members(widget, 'current')
        # Rect.moveto(widget, idns, *widget.coords(idns[0]))
        l, t, r, b = widget.coords(idns[0])
        pts = [RectPt.coords(widget, idn, None) for idn in idns[5:]]
        reorder = [pts.index(p) for p in ((l, t), (r, t), (r,b), (l,b))]
        nidns = list(idns[:5])
        for nidx in reorder:
            nidn = idns[5+nidx]
            widget.tag_raise(nidn, nidns[-1])
            nidns.append(nidn)
        Rect.moveto(widget, nidns, l, t, r, b)
        l, t, r, b = widget.coords(idns[0])
        Rect.unselected(widget, idns)
