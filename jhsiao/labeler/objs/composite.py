from . import Obj

class Composite(Obj):
    def __init__(self, master, x, y, color='black'):
        super(Composite, self).__init__(
            master,
            *[c(master, x, y, color) for c in self.components])
        self.addtags(master, self.ids, self.TAGS)

    @staticmethod
    def idn_idxs(components):
        base = 0
        for c in components:
            yield base
            base += c.IDNS

    @classmethod
    def color(cls, widget, idn):
        return cls.components[0].color(widget, idn)

    @classmethod
    def recolor(cls, widget, idn, newcolor):
        ids = cls.members(widget, idn)
        for idx, c in zip(cls.IDNIDXS, cls.components):
            c.recolor(widget, ids[idx])
            base += c.IDX

    @classmethod
    def data(cls, widget, idn, info):
        ids = cls.members(widget, idn)
        data = [
            c.data(widget, ids[idx], info.get(cls.__name__, cls.INFO))
            for idx, c in zip(cls.IDNIDXS, cls.components)]
        return data

