from __future__ import print_function
__all__ = ['Obj']
import sys

from . import ibinds

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
    HIDDEN = 'hidden'
    TAGS = ['Obj']
    IDX = 0
    SEP = ':'
    binds = ibinds['Obj']
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
        cls, idn = tag.rsplit(Obj.SEP, 1)
        return cls, int(idn)

    @staticmethod
    def parseid(tag):
        return int(tag.rsplit(Obj.SEP, 1)[-1])

    @staticmethod
    def toptag(master, idn):
        """Get the toplevel Obj's idtag."""
        tags = master.gettags(idn)
        idx = len(tags) - 1
        tag = tags[idx]
        while tag == 'current' or tag == Obj.TOP or tag == Obj.HIDDEN:
            idx -= 1
            tag = tags[idx]
        return tag

    @staticmethod
    def topid(master, idn):
        """Get the toplevel Obj's item id."""
        return int(Obj.toptag(master, idn).rsplit(Obj.SEP, 1)[-1])

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

    @staticmethod
    def make_idtag(maintag):
        return Obj.SEP.join((maintag, '{}'))

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

        info: the class info
        """
        raise NotImplementedError

    @classmethod
    def todict(cls, widget, idn, info):
        """Convert data to dict.

        widget: the canvas widget.
        idn: the top-level idn
        info: class info
        """
        return dict(
            data=cls.data(widget, idn, fmt),
            color=cls.color(widget, idn))

    @staticmethod
    def fromdict(widget, dct, info):
        """Restore from a dict.

        dct: result from `todict()`
        info: the class info.
        """
        raise NotImplementedError

    @staticmethod
    def interpolate(dct1, dct2, info, frac):
        """Interpolate between dct1 and dct2 by frac.

        dct1, dct2: dicts from todict()
        info: class info
        frac is the weight of dct1.
        """
        raise NotImplementedError

    @staticmethod
    def interp(w, data1, data2):
        """Interpolate values between data1 and data2.

        data[1|2]: tuple of floats
        frac: weight for data1
        """
        return [(d1-d2)*w + d2 for d1, d2 in zip(data1, data2)]

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
        widget.master.set_obj(idn)
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
            widget.itemconfigure(tag, state=Obj.HIDDEN)
            widget.addtag(Obj.HIDDEN, 'withtag', tag)
            return
        else:
            raise Exception('Failed to find topbase tag.')


