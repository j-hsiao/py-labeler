from collections import deque

from . import Obj
from ..ddict import DDict

class Composite(Obj):
    """Composite of multiple different basic objects.

    Classes are fixed
    subclasses must have attributes:
    IDNIDXS: list of indices into member idns that begin the ids for
        the component.
    COORDIDXS: list of indices into coordinates to slice the coordinates
        for the corresponding component.

    Bringing a component up would cause the returned idns to be
    reordered.  This makes it more difficult to calculate the component
    behaviors.  As a result, components within a Composite class are
    always fixed relative to eachother.  This might make some components
    harder to interact with if they are covered by other components.
    You can just hide them to access the components below.

    INFO consists of a flattened INFO dict for each component.
    Each key is the component class name, composite index, and the
    corresponding INFO key of the component class.  For example, a
    Composite consisting of 2 Rects could have an INFO dict that
    looks like:
        {'Rect:0:format': 'ltrb', 'Rect:1:format': 'cxywh'}

    To check if a class is a Composite, check whether the INFO dict
    contains a 'components' key.

    """
    def __init__(self, master, x, y, color='black', subs=None):
        if subs is None:
            super(Composite, self).__init__(
                master,
                *[c(master, x, y, color) for c in self.components])
        else:
            super(Composite, self).__init__(master, *subs)
        self.addtags(master, self.ids, self.TAGS)

    @classmethod
    def color(cls, widget, idn):
        return cls.components[0].color(widget, idn)

    @classmethod
    def recolor(cls, widget, newcolor, idn):
        ids = cls.members(widget, idn)
        for idx, c in zip(cls.IDNIDXS, cls.components):
            c.recolor(widget, newcolor, ids[idx])

    @staticmethod
    def pairwise(it):
        """Pairwise items in it.  a, b, c -> (a,b), (b,c)."""
        it = iter(it)
        first = next(it)
        for second in it:
            yield first, second
            first = second

    @classmethod
    def coords(cls, widget, idn):
        ids = cls.members(widget, idn)
        ret = []
        for first, c in zip(cls.IDNIDXS, cls.components):
            ret.extend(c.coords(widget, ids[first]))
        return ret

    @classmethod
    def from_coords(cls, coords, info):
        ret = []
        cidxs = cls.COORDIDXS
        for idx, (c, cinfo) in enumerate(zip(
                cls.components, cls.sepinfo(info))):
            ret.append(c.from_coords(coords[cidxs[idx]:cidxs[idx+1], cinfo))
        return ret

    @classmethod
    def to_coords(cls, coords, info):
        ret = []
        for coor, c, cinfo in zip(coords, cls.components, cls.sepinfo(info)):
            ret.extend(c.to_coords(coor, cinfo))
        return ret

    @classmethod
    def restore(cls, widget, coords, color):
        subs = []
        cidxs = cls.COORDIDXS
        for idx, c in enumerate(cls.components):
            subs.append(
                c.restore(widget, coords[cidxs[idx]:cidxs[idx+1]], color))
        return cls(widget, 0, 0, color, subs)

    @classmethod
    def sepinfo(cls, info):
        """Separate keys into separate dicts per class."""
        dcts = [DDict({}, c.INFO) for c in cls.components]
        for k, v in info.items():
            name, idx, key = k.split(':', 2)
            dcts[int(idx)][key] = v
        return dcts

    @classmethod
    def activate(cls, widget, ids):
        for idx, c in enumerate(cls.components):
            c.activate(widget, ids[cls.IDNIDXS[idx]:cls.IDNIDXS[idx+1]])

    @classmethod
    def deactivate(cls, widget, ids):
        for idx, c in enumerate(cls.components):
            c.deactivate(widget, ids[cls.IDNIDXS[idx]:cls.IDNIDXS[idx+1]])

def make_composite(components, name=None):
    """Create a composite Obj.

    components: classes to use as comonents.
        Composites will be flattened into their components.
    name: the name of the resulting class.
        If None, use a concatenation of the components.
        No underscores, they will be removed.
    """
    q = deque(components)
    idnidxs = [0]
    coordidxs = [0]
    components = []
    while q:
        c = q.popleft()
        if issubclass(c, Composite):
            q.extendleft(reversed(c.components))
        else:
            components.append(c)
            idnidxs.append(idnidxs[-1] + c.IDNS)
            coordidxs.append(coordidxs[-1] + c.NCOORDS)
    if not name:
        name = ''.join([cls.__name__ for cls in components])
    info = {
        Obj.SEP.join((cls.__name__, str(idx), key)): value
        for idx, cls in zip(components)
        for key, value in cls.INFO.items() if key != 'color'}
    info['components'] = [c.__name__ for c in components]
    attrs = dict(
        IDNIDXS=idnidxs,
        TAGS=[Obj.make_idtag(name)],
        INFO=info,
        components=components,
        IDX=components[0].IDX+1,
        IDNS=idnidxs[-1],
        NCOORDS=coordidxs[-1],
        COORDIDXS=coordidxs,
    )
    return Obj.register(type(name, (Composite,), attrs))
