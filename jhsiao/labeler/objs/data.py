from collections import defaultdict

from .obj import Obj

class LabelSet(object):
    def __init__(self, labels, classinfo):
        self.classinfo = classinfo
        self.labels = labels

    def __getitem__(self, idx):
        """Get the framelabels at idx."""
        return self.labels[idx].canonical(self.classinfo)

class FrameLabels(object):
    """Object labels for a single frame.

    Objects are grouped in a list under the classname.  Each object is
    a length-3 list of [coordinates, color, info].
    """
    def __init__(self, data):
        self.data = data

    def iter_canonical(self, classinfos):
        """Iterate on data in canonical format.

        Each item is a pair of (classname, (coords, color, dict)) where
        `classname` is the name of the class of the Obj.  `coords` is
        the canonical coordinates of the Obj.  `color` is the color to
        use when displaying the Obj and `dict` is the extra info
        associated with the Obj.

        Assume not currently in canonical coordinates.
        """
        if self.classinfo is None:
            for clsname, objs in self.data.items():
                cls = Obj.classes[clsname]
                cinfo = classinfos[clsname]
                for obj in objs:
                    coords = cls.to_coords(obj[0])
                    if obj[1]:
                        yield clsname, (coords, obj[1], obj[2])
                    else:
                        yield clsname, (coords, cinfo['color'], obj[2])

    def to_canonical(self, classinfos):
        """Return a canonical frame labels dict.

        Assumes that not currently in canonical coordinates.
        Inputs
        ======
        classinfos: dict
            The class info dict containing formats, colors, etc.

        Outputs
        =======
        labels: {clsname: [[coords, color, info],...],...}
        """
        if self.classinfo is None:
            return self.data
        ret = {}
        for clsname, objs in self.data.items():
            ocls = Obj.classes[clsname]
            classinfo = classinfos[clsname]
            ret[clsname] = [
                [ocls.to_coords(obj[0], classinfo), obj[1], obj[2]]
                for obj in objs]
            for l in ret[clsname]:
                if not l[1]:
                    l[1] = classinfo['color']

    def from_canonical(self, classinfo):
        pass

    @classmethod
    def from_widget(cls, canv, infodict):
        """Create a FrameLabels instance from a tk Canvas widget.

        Canonical coordinates.
        """
        dats = defaultdict(list)
        for clsname, idn in Obj.topitems(canv):
            ocls = Obj.classes[clsname]
            data = ocls.coords(canv, idn)
            color = ocls.color(canv, idn)
            dats[clsname].append(
                (data, color, infodict.get(idn, None)))
        return cls(dats)
