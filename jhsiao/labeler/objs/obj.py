from __future__ import print_function
__all__ = ['Obj']
import sys

from . import bindings

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping



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

    Subclasses should implement the following functions.  Unless
    otherwise noted, the default impl just finds the top-level Obj
    type and calls that class' corresponding method (if idn is an arg).
        color(widget, idn):
            return the color of obj
        recolor(widget, color, idn):
            change color of obj
        coords(widget, idn):
            get the coordinates (canonical)
        from_coords(coords, info):
            Convert canonical coords to alternative format.
            Default impl is do nothing, return as is.
        to_coords(coords, info):
            Convert alternative coords to canonical
            Default impl is do nothing, return as is.
        to_dict(widget, idn, info):
            Convert obj to a dict.  Default impl is to use
            dict(data=`coords(...)`, color=`color(...)`)
        parse_dict(dct, info):
            Parse dict into coordinates and color
        restore(widget, coords, color):
            Create the obj from coords and color.  Default is
            not implemented.
        activate(widget, ids):
            Activated state (selected), default is do nothing.
        deactivate(widget, ids):
            deactivate state (selected), default is do nothing.
    """
    INFO = {}
    TOP = 'top'
    HIDDEN = 'hidden'
    TAGS = ['Obj']
    IDX = 0
    SEP = ':'
    binds = bindings['', 'Obj']
    IDNS = 0

    class ObjRegistry(MutableMapping):
        def __init__(self, *args, **kwargs):
            self._registry = dict(*args, **kwargs)

        def register(self, item):
            try:
                orig = self._registry[item.__name__]
            except KeyError:
                self._registry[item.__name__] = item
            else:
                print(
                    item.__name__, 'was already added.',
                    orig, 'vs', item, file=sys.stderr)
            return item

        def __repr__(self):
            return 'ObjRegistry({})'.format(repr(self._registry))

        def update(self, other):
            self._registry.update(other)

        def items(self):
            return self._registry.items()

        def __getitem__(self, k):
            return self._registry[k]

        def __setitem__(self, k, v):
            self._registry[k] = v

        def __delitem__(self, k):
            del self._registry[k]

        def __iter__(self):
            return iter(self._registry)

        def __len__(self):
            return len(self._registry)

        def topcall(self, widget, name, idn, **kwargs):
            """Call the named method with args on the top class."""
            cls, idn = Obj.parsetag(Obj.toptag(widget, idn))
            return getattr(self._registry[cls], name)(
                widget, idn=idn, **kwargs)

        def color(self, widget, idn):
            return self.topcall(widget, 'color', idn)

        def recolor(self, widget, color, idn):
            return self.topcall(widget, 'recolor', idn, color=color)

        def coords(widget, idn):
            return Obj.topcall(widget, 'coords', idn)

    BaseObjs = ObjRegistry()
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
        return self

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
    def topitems(master):
        """Return tuples of (classname, itemid) for top-level Objs."""
        return [
            Obj.parsetag(Obj.toptag(master, idn))
            for idn in master.find('withtag', Obj.TOP)]

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
    def snapto(master, x, y, target, seq='<Motion>', when='mark'):
        """Snap mouse to target position.

        x, y: int
            x, y mouse window coordinates.  These are required because
            generating a mouse warp requires window coordinates rather
            than canvas coordinates.
        target: pair of int
            The target coordinate to warp to in canvas coordinates.
        seq: str
            The event sequence to generate.  Testing on other systems,
            it seems that only generating <Motion> can cause the
            current canvas item to lose its "current" status.
            B1-Motion is necessary to maintain the "current" status,
            especially if it changes the object to become transparent to
            improve visibility to the image underneath.
        when: str: 'mark'|'head'|'tail'
            The when argument for event_generate.
        """
        p = Obj.canvxy(master, x, y)
        if target != p:
            master.event_generate(
                seq,
                x=x+(target[0]-p[0]),
                y=y+(target[1]-p[1]),
                warp=True, when=when,
                serial=0)

    @staticmethod
    def canvxy(master, x, y):
        """Convert window x,y to canvas x,y."""
        return master.canvasx(x), master.canvasy(y)

    @staticmethod
    def altcolor(master, color):
        """Return a new color for contrast against `color`."""
        return '#{:02x}{:02x}{:02x}'.format(
            *[((x//256)+128)%256 for x in master.winfo_rgb(color)])

    @staticmethod
    def interpolate(coords1, coords2, frac):
        """Interpolate between dct1 and dct2 by frac.

        coords1, coords2:
            canonical coords to interpolate/extrapolate between
        frac is the weight of coords1.
        """
        return [(c1-c2)*w + c2 for c1, c2 in zip(coords1, coords2)]

    #------------------------------
    # General Obj interface
    #------------------------------
    @staticmethod
    def color(widget, idn):
        """Get the color of the item."""
        raise NotImplementedError

    @staticmethod
    def recolor(widget, color, idn):
        """Change color of the Obj."""
        raise NotImplementedError

    @staticmethod
    def coords(widget, idn):
        """Return a sequence of canonical data for the Obj from Canvas.

        Canonical coordinates means x,y points.  This format is most
        easily used in the Canvas and for interpolation.

        """
        raise NotImplementedError

    @staticmethod
    def from_coords(coords, info):
        """Convert coords format into some other format.

        info: the class dict INFO.
        default: assume already in coords format.
        """
        return coords

    @staticmethod
    def to_coords(coords, info):
        """Convert other format to coords format.

        info: the class dict INFO.
        default: assume already in coords format.
        """
        return coords

    @staticmethod
    def to_dict(widget, idn, info, clsname=None, zoom=1):
        """Convert data to dict.

        widget: the canvas widget.
        idn: the top-level idn
        info: class info
        """
        if clsname is None:
            clsname, idn = Obj.parsetag(Obj.toptag(widget, idn))
        cls = Obj.classes[clsname]
        canonical = [_/zoom for _ in cls.coords(widget, idn)]
        data = cls.from_coords(canonical, info)
        color = cls.color(widget, idn)
        if widget.winfo_rgb(color) != widget.winfo_rgb(info.get('color')):
            return dict(data=data, color=color)
        else:
            return dict(data=data)

    @classmethod
    def parse_dict(cls, dct, info):
        """Parse a dict to retrieve coords and color."""
        color = dct.get('color')
        if color is None:
            color = info.get('color')
            if color is None:
                color = 'black'
        return cls.to_coords(dct['data'], info), color

    @classmethod
    def convert_dict(cls, dct, info, newinfo):
        """Mutate dict from info to newinfo.
        """
        coords, color = cls.parse_dict(dct, info)
        if color == newinfo.get('color'):
            dct.pop('color', None)
        else:
            dct['color'] = color
        dct['data'] = cls.from_coords(coords, newinfo)
        return dct

    @staticmethod
    def restore(widget, coords, color):
        """Restore from coords and color.

        dct: result from `to_dict()`
        info: the class info.
        """
        raise NotImplementedError

    @staticmethod
    def activate(widget, ids):
        """Mark the Obj as active.

        This is generally called in the case when Obj is actually a
        sub Obj to indicate that it belongs to the toplevel Obj.
        """
        pass

    @staticmethod
    def deactivate(widget, ids):
        """Opposite of activate."""
        pass

    #------------------------------
    # General Obj behavior
    #------------------------------
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
        widget.master.selector.classes[cls].activate(
            widget, widget.find('withtag', tag))

    @staticmethod
    @binds.bind('<Leave>')
    def _onleave(widget):
        """Call deactivate."""
        tag = Obj.toptag(widget, 'current')
        cls, idn = Obj.parsetag(tag)
        widget.master.selector.classes[cls].deactivate(
            widget, widget.find('withtag', tag))

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

