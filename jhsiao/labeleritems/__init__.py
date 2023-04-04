"""A namespace package for adding items for the labeler to use."""
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

from jhsiao.tkutil.bindings import Bindings

import numpy as np
from PIL import Image, ImageTk

bindings = Bindings('tag_bind')

class Obj(object):
    """An object on a tk.Canvas.

    Objs represent an object on a canvas and can be made up of multiple
    tk.Canvas items.  The items that make an Obj should always have a
    fixed relative stacking order.  This allows selecting particular
    items by searching for the object idtag.  The Obj's idtag is the
    name of the Obj joined to the item id of its first item by an
    underscore.  All constituent items should have this object tag.

    Class attributes:
        TAGS: list of str
            These are tags that all Objs of this type have, including
            sub-Objs.  It is expected that the last tag is a tag that
            would indicate the top-level object and so should contain
            {}.
        IDX: int
            The index in the list of all tags for that idn.  This takes
            All tags from base Objs into account.
    """
    TOP = 'top'
    TAGS = ['Obj', 'Obj_{}']
    IDX = 1
    binds = bindings['Obj']

    def __init__(self, master, *ids):
        self.ids = []
        for idn in ids:
            if isinstance(idn, Obj):
                self.ids.extend(idn.ids)
            else:
                self.ids.append(idn)
        self.addtags(master, self.ids, Obj.TAGS)

    def marktop(self, master):
        """Mark this Obj as a top-level object."""
        master.addtag(Obj.TOP, 'withtag', self.ids[0])

    @staticmethod
    def tops(master):
        """Get all top-level ids."""
        return master.find('withtag', Obj.TOP)

    @staticmethod
    def topitems(master):
        """Return tuples of (classname, itemid) for top-level Objs."""
        return [
            Obj.parsetag(Obj.toptag(master, idn))
            for idn in master.find('withtag', Obj.TOP)]

    @staticmethod
    def toptag(master, idn):
        """Get the toplevel Obj's tag."""
        tags = master.gettags(idn)
        idx = len(tags) - 1
        tag = tags[idx]
        while tag == 'current' or tag == 'top':
            idx -= 1
            tag = tags[idx]
        return tag

    @staticmethod
    def parsetag(tag):
        """Parse an Obj tag into class and index."""
        cls, idn = tag.split('_', 1)
        return cls, int(idn)

    @staticmethod
    def topid(master, idn):
        """Get the toplevel Obj's item id."""
        return int(Obj.toptag(master, idn).split('_', 1)[-1])

    @staticmethod
    def addtags(master, ids, tags):
        """Add tags.

        ids: list of int
            The ids to add tags to.
        tags: list of str
            The tags to add.  If a tag contains "{}", then it will
            be replaced with the first idn in `ids`
        """
        for name in tags:
            tag = name.format(ids[0])
            for idn in ids:
                master.addtag(tag, 'withtag', idn)

    @staticmethod
    def snapto(master, x, y, target):
        """Snap mouse to target position."""
        p = Obj.canvxy(master, x, y)
        if target != p:
            master.event_generate(
                '<Shift-Motion>',
                x=x+(target[0]-p[0]),
                y=y+(target[1]-p[1]),
                warp=True, when='head')

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
    def data(widget, idn):
        """Return a sequence of data represented by the Obj."""
        raise NotImplementedError

    @classmethod
    def todict(cls, widget, idn):
        """Convert data to dict."""
        return dict(
            data=cls.data(widget, idn),
            color=cls.color(widget, idn))

    @staticmethod
    def fromdict(widget, dct):
        """Restore from a dict."""
        raise NotImplementedError

    @staticmethod
    def activate(widget, idn):
        """Mark the Obj as active.

        This is generally called in the case when Obj is actually a
        sub Obj to indicate that it belongs to the toplevel Obj.
        """
        raise NotImplementedError

    @staticmethod
    def deactivate(widget, idn):
        """Opposite of activate."""
        raise NotImplemented

    @classmethod
    def members(cls, widget, idn):
        """Find the member idns of this Obj class."""
        return widget.find('withtag', widget.gettags(idn)[cls.IDX])

    # General Obj behavior
    @staticmethod
    @binds.bind('<Button-1>')
    def onclick(widget):
        """When clicked, set the current tag."""
        tag = Obj.toptag(widget, 'current')
        cls, idn = Obj.parsetag(tag)
        widget.objid = idn
        widget.tag_raise(tag)

class BGImage(object):
    binds = bindings['BGImage']
    def __init__(self, master, **kwargs):
        self.idn = master.create_image(0,0, anchor='nw')
        self.im = None
        self.raw = None
        master.addtag('BGImage', 'withtag', self.idn)

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
        """Show a roi."""
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
