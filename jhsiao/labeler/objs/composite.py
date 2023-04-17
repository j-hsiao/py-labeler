from . import Obj

class Composite(Obj):
    def __init__(self, master, x, y, color='black'):
        super(Composite, self).__init__(
            master,
            *[c(master, x, y, color) for c in self.components])
        self.addtags(master, self.ids, self.TAGS)

    @classmethod
    def color(cls, widget, idn):
        return cls.components[0].color(widget, idn)

    @classmethod
    def recolor(cls, widget, idn, newcolor):
        ids = cls.members(widget, idn)
        for idx, c in zip(cls.IDNIDXS, cls.components):
            c.recolor(widget, ids[idx], newcolor)

    @classmethod
    def data(cls, widget, idn, info):
        ids = cls.members(widget, idn)
        return {
            cls.__name__: cls.todict(
                widget, ids[idx], info[cls.__name__])
            for idx, c in zip(cls.IDNIDXS, cls.components)}

    @classmethod
    def fromdict(cls, widget, dct, info):
        data = dct['data']
        for c in cls.components:
            sub = c.fromdict(widget, data[c.__name__], info[c.__name__])
            cls.addtags(widget, sub.ids, cls.TAGS)

    @classmethod
    def activate(cls, widget, ids):
        for idx, c in enumerate(cls.components):
            c.activate(widget, ids[cls.IDNIDXS[idx]:cls.IDNIDXS[idx+1]])

    @classmethod
    def deactivate(cls, widget, ids):
        for idx, c in enumerate(cls.components):
            c.deactivate(widget, ids[cls.IDNIDXS[idx]:cls.IDNIDXS[idx+1]])

def make_composite(name, components):
    idnidxs = [0]
    for c in components:
        idnidxs.append(idnidxs[-1]+c.IDNS)
    attrs = dict(
        IDNIDXS=idnidxs,
        TAGS=['{}_{{}}'.format(name)],
        components=components,
        INFO={cls.__name__: cls.INFO for cls in components},
        IDX=components[0].IDX+1
    )
    return type(name, (Composite,), attrs)
