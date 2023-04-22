"""A namespace package for adding items for the labeler to use."""
from __future__ import print_function
__all__ = ['Obj', 'BGImage', 'Crosshairs']
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import sys
import math

import numpy as np
from PIL import Image, ImageTk

from jhsiao.tkutil import tk
from .. import bindings as wbindings
bindings = wbindings('tag_bind')

class Obj(object):
    """An object on a tk.Canvas.

    Objs represent an object on a canvas and can be made up of multiple
    tk.Canvas items.  The items that make an Obj should always have a
    fixed relative stacking order.  This allows selecting particular
    items by searching for the object idtag.  The Obj's idtag is the
    name of the Obj class joined to the item id of its first item by an
    underscore.  All constituent items should have this object tag.
    For instance, a Rectangle may have a Point as a corner.
    This particular Point should also contain Rectangle_<topid> in its
    list of tags.

    Class attributes:
        TAGS: list of str
            These are tags that all Objs of this type have, including
            sub-Objs.  It is expected that the last tag is the idtag
            for the class.
        IDX: int
            The index of the idtag for the particular class.
        HELP: a help message.
        INFO: class-wide settings info.
    Subclasses should generally have an __init__ signature of
    __init__(self, master, x, y, color) where x, y have already been
    converted to canvas coordinates.

    Regarding coordinates, there are window coordinates and canvas
    coordinates.  Window coordinates are the coordinates directly
    received from a callback.  Canvas coordinates convert the window
    coordinates into coordinates in the canvas and differ when the
    tk.Canvas is not scrolled to the top left.
    """
    INFO = {}
    TOP = 'top'
    TAGS = ['Obj']
    IDX = 0
    binds = bindings['Obj']
    classes = dict()
    IDNS = 0

    @staticmethod
    def register(item):
        """Register `item` as a top-level Obj."""
        orig = Obj.classes.get(item.__name__)
        if orig is None:
            Obj.classes[item.__name__] = item
        else:
            print(
                item.__name__, 'was already added.',
                orig, 'vs', item, file=sys.stderr)
        return item

    def __init__(self, master, *ids):
        self.ids = []
        for idn in ids:
            if isinstance(idn, Obj):
                self.ids.extend(idn.ids)
            else:
                self.ids.append(idn)
        self.addtags(master, self.ids, Obj.TAGS)
        master.tag_raise('Crosshairs')

    def marktop(self, master):
        """Mark this Obj as a top-level object."""
        master.addtag(Obj.TOP, 'withtag', self.ids[0])

    @staticmethod
    def tops(master):
        """Get all top-level ids."""
        return master.find('withtag', Obj.TOP)

    @staticmethod
    def parsetag(tag):
        """Parse an Obj tag into class and index."""
        cls, idn = tag.rsplit('_', 1)
        return cls, int(idn)

    @staticmethod
    def parseid(tag):
        return int(tag.rsplit('_', 1)[-1])

    @staticmethod
    def toptag(master, idn):
        """Get the toplevel Obj's idtag."""
        tags = master.gettags(idn)
        idx = len(tags) - 1
        tag = tags[idx]
        while tag == 'current' or tag == Obj.TOP:
            idx -= 1
            tag = tags[idx]
        return tag

    @staticmethod
    def topid(master, idn):
        """Get the toplevel Obj's item id."""
        return int(Obj.toptag(master, idn).rsplit('_', 1)[-1])

    @staticmethod
    def topitems(master):
        """Return tuples of (classname, itemid) for top-level Objs."""
        return [
            Obj.parsetag(Obj.toptag(master, idn))
            for idn in master.find('withtag', Obj.TOP)]

    @classmethod
    def idtag(cls, master, idn):
        """Extract the class id tag."""
        return master.gettags(idn)[cls.IDX]

    @classmethod
    def members(cls, widget, idn, idx=None):
        """Find the member idns of this Obj class."""
        if idx is None:
            idx = cls.IDX
        return widget.find('withtag', widget.gettags(idn)[idx])


    @staticmethod
    def addtags(master, ids, tags):
        """Add tags.

        ids: list of int
            The ids to add tags to.
        tags: str or list of str
            The tags to add.  If a tag contains "{}", then it will
            be replaced with the first idn in `ids`
        """
        for name in tags:
            tag = name.format(ids[0])
            for idn in ids:
                master.addtag(tag, 'withtag', idn)

    @staticmethod
    def snapto(master, x, y, target, when='head'):
        """Snap mouse to target position.

        x, y: int
            x, y mouse window coordinates.  These are required because
            generating a mouse warp requires window coordinates rather
            than canvas coordinates.
        target: pair of int
            The target coordinate to warp to in canvas coordinates.
        """
        p = Obj.canvxy(master, x, y)
        if target != p:
            master.event_generate(
                '<Motion>',
                x=x+(target[0]-p[0]),
                y=y+(target[1]-p[1]),
                warp=True, when=when)

    @staticmethod
    def canvxy(master, x, y):
        """Convert window x,y to canvas x,y."""
        return master.canvasx(x), master.canvasy(y)

    @staticmethod
    def altcolor(master, color):
        """Return a new color for contrast against `color`."""
        return '#{:02x}{:02x}{:02x}'.format(
            *[((x//256)+128)%256 for x in master.winfo_rgb(color)])

    # General Obj interface
    @staticmethod
    def color(widget, idn):
        """Get the color for this Obj."""
        raise NotImplementedError

    @staticmethod
    def recolor(widget, color, idn):
        """Change color of the Obj."""
        raise NotImplementedError

    @staticmethod
    def data(widget, idn, info):
        """Return a sequence of data represented by the Obj.

        info: the corresponding info instance.
        """
        raise NotImplementedError

    @classmethod
    def todict(cls, widget, idn, info):
        """Convert data to dict."""
        return dict(
            data=cls.data(widget, idn, fmt),
            color=cls.color(widget, idn))

    @staticmethod
    def fromdict(widget, dct, info):
        """Restore from a dict."""
        raise NotImplementedError

    @staticmethod
    def activate(widget, ids):
        """Mark the Obj as active.

        This is generally called in the case when Obj is actually a
        sub Obj to indicate that it belongs to the toplevel Obj.
        """
        raise NotImplementedError

    @staticmethod
    def deactivate(widget, ids):
        """Opposite of activate."""
        raise NotImplemented

    # General Obj behavior
    @staticmethod
    @binds.bind('<Button-1>')
    def _onclick(widget):
        """When clicked, set the current tag."""
        tag = Obj.toptag(widget, 'current')
        cls, idn = Obj.parsetag(tag)
        widget.objid = idn
        widget.tag_raise(tag, 'Obj')

    # Leave/enter can cause an infinite loop mouse button because the
    # new Item changes shape causing infinite enter/leave, so only
    # fire (de)activate when no buttons are pressed
    binds.bind(
        '<B1-Leave>', '<B1-Enter>',
        '<B2-Leave>', '<B2-Enter>',
        '<B3-Leave>', '<B3-Enter>',
        '<B4-Leave>', '<B4-Enter>',
        '<B5-Leave>', '<B5-Enter>',
    )(' ')

    @staticmethod
    @binds.bind('<Enter>')
    def _onenter(widget):
        """Call activate."""
        tag = Obj.toptag(widget, 'current')
        cls, idn = Obj.parsetag(tag)
        Obj.classes[cls].activate(widget, widget.find('withtag', tag))

    @staticmethod
    @binds.bind('<Leave>')
    def _onleave(widget):
        """Call deactivate."""
        tag = Obj.toptag(widget, 'current')
        cls, idn = Obj.parsetag(tag)
        Obj.classes[cls].deactivate(widget, widget.find('withtag', tag))

    @staticmethod
    @binds.bind('<Button-3>')
    def _hide(widget):
        """Hide current Obj (or component if part of a composite)."""
        tags = widget.gettags('current')
        for tag in reversed(tags):
            if (
                    tag == 'current'
                    or tag == Obj.TOP
                    or tag.startswith('Composite')):
                continue
            widget.itemconfigure(tag, state='hidden')
            widget.addtag('hidden', 'withtag', tag)
            return
        else:
            raise Exception('Failed to find topbase tag.')


class BGImage(object):
    binds = bindings['BGImage']
    def __init__(self, master):
        self.idn = master.create_image(0,0, anchor='nw')
        self.im = None
        self.raw = None
        master.addtag('BGImage', 'withtag', self.idn)
        master.tag_lower('BGImage')
        self.show(master, None)

    def show(self, master, im):
        if isinstance(im, str):
            im = Image.open(im)
        elif im is None:
            im = Image.fromarray(np.full((480,640), 127, np.uint8))
        elif isinstance(im, np.ndarray):
            if im.ndim == 3:
                im = im[...,2::-1]
            im = Image.fromarray(im)
        self.raw = im
        self.im = ImageTk.PhotoImage(im)
        master.itemconfigure(self.idn, image=self.im)
        master.configure(
            scrollregion=(0, 0, self.raw.width, self.raw.height))

    def roi(self, master):
        """Show a roi.

        Resizing the entire image can take a huge amount of memory.
        Resizing only a roi allows much better performance.
        """
        l, r = master.xview()
        t, b = master.yview()
        if r - l == 1:
            owidth = self.im.width
        else:
            owidth = master.winfo_width()
        if b - t == 1:
            oheight = self.im.height
        else:
            oheight = master.winfo_height()
        height, width = self.raw.shape[:2]
        l *= width
        r *= width
        t *= height
        b *= height
        self.im = ImageTk.PhotoImage(
            self.raw.resize((owidth, oheight), box=(l, t, r, b)))
        master.itemconfigure(self.idn, image=self.im)
        master.coords(
            self.idn, master.canvasx(0), master.canvasy(0))

    @staticmethod
    @binds.bind('<Button-1>')
    def _create(widget, x, y):
        x, y = Obj.canvxy(widget, x, y)
        return
        # TODO
        # select item class and instantiate
        #widget.event_generate('<ButtonRelease-1>', x, y)
        #widget.event_generate('<Button-1>', x, y)

    @staticmethod
    @binds.bind('<Button-3>')
    def _toggle_hide(widget):
        ids = widget.find('withtag', 'hidden')
        if ids:
            widget.itemconfigure('hidden&&!disabled', state='normal')
            widget.dtag('hidden')
            widget.itemconfigure('disabled', state='disabled')
        else:
            widget.itemconfigure('Obj', state='hidden')
            widget.addtag('hidden', 'withtag', 'Obj')

class ObjSelector(tk.Frame, object):
    def __init__(self, master, *args, **kwargs):
        super(ObjSelector, self).__init__(master, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.lbl = tk.Label(self, text='Object type')
        self.lst = tk.Listbox(self, exportselection=False)
        self.scroll = tk.Scrollbar(
            self, orient='vertical', command=self.lst.yview)
        self.lst.configure(yscrollcommand=self.scroll.set)
        self.clbl = tk.Label(self, text='Composite components')
        self.clst = tk.Listbox(self, exportselection=False)
        self.cscroll = tk.Scrollbar(
            self, orient='vertical', command=self.clst.yview)
        self.clst.configure(yscrollcommand=self.cscroll.set)
        self.lbl.grid(row=0, column=0, columnspan=2, sticky='ew')
        self.lst.grid(row=1, column=0, sticky='nsew')
        self.scroll.grid(row=1, column=1, sticky='nsew')
        self.clbl.grid(row=0, column=2, columnspan=2, sticky='ew')
        self.clst.grid(row=1, column=2, sticky='nsew')
        self.cscroll.grid(row=1, column=3, sticky='nsew')

    def reload(self):
        self.lst.insert(0, delete(0, 'end'))
        toadd = []
        for name in sorted(Obj.classes):
            if name.startswith('Composite'):
                toadd.append(
            else:
                toadd.append(name)
        self.lst.insert('end', *toadd)







class Crosshairs(object):
    """Canvas crosshairs."""
    TAG = 'Crosshairs'
    UP = (0,1)
    def __init__(self, master):
        k = dict(
            state='disabled',
            tags=('Crosshairs',))
        # add thicker black to back for contrast.
        self.idns = (
            master.create_line(0, 0, 1, 1, fill='black', width=3, **k),
            master.create_line(0, 0, 1, 1, fill='black', width=3, **k),
            master.create_line(0, 0, 1, 1, fill='white', width=1, **k),
            master.create_line(0, 0, 1, 1, fill='white', width=1, **k))
        master.tag_raise('Crosshairs')
        master.configure(cursor='None')
        self._up = (0, 1)

    def up(self, x, y):
        if x or y:
            self._up = (x, y)
        else:
            self._up = (0,1)

    @staticmethod
    def hide(master):
        master.itemconfigure('Crosshairs', state='hidden')

    @staticmethod
    def show(master):
        master.itemconfigure('Crosshairs', state='disabled')

    @staticmethod
    def _edgepts(dx1, dx2, dy1, dy2, vx, vy, cx, cy):
        """Return vectors to reach the edges of the canvas.

        dx/dy: int
            Signed distance to an edge.
        vx, vy: vector direction.
        cx, cy: int
            canvas coordinates of mouse.
        """
        if vx:
            mx = (dx1 / vx, dx2 / vx)
            if mx[0] > mx[1]:
                mx = mx[::-1]
        else:
            mx = [-math.inf, math.inf]
        if vy :
            my = (dy1 / vy, dy2 / vy)
            if my[0] > my[1]:
                my = my[::-1]
        else:
            my = [-math.inf, math.inf]
        m1 = max(mx[0], my[0])
        m2 = min(mx[1], my[1])
        return (
            (int(vx*m1)+cx, int(vy*m1)+cy),
            (int(vx*m2)+cx, int(vy*m2)+cy))

    def moveto(self, master, x, y):
        """Place crosshairs at location.

        master: tk.Canvas
        x,y: int, the widget mouse x,y coords (not canvasxy)
        """
        w = master.winfo_width()
        h = master.winfo_height()
        cx, cy = Obj.canvxy(master, x, y)
        vx, vy = self._up
        (x1,y1), (x2,y2) = self._edgepts(
            -x, w-x, -y, h-y, vx, vy, cx, cy)
        idns = self.idns
        master.coords(idns[0], x1, y1, x2, y2)
        master.coords(idns[2], x1, y1, x2, y2)
        (x1,y1), (x2,y2) = self._edgepts(
            -x, w-x, -y, h-y, vy, -vx, cx, cy)
        master.coords(idns[1], x1, y1, x2, y2)
        master.coords(idns[3], x1, y1, x2, y2)
