"""Handle labels for an imset."""
from .objs import Obj
class LabelSet(object):
    def __init__(self, data, imset):
        """Initialize a LabelSet.

        data: {
            imname: {
                classname:
                {
                    info: {...},
                    data: [
                        {data:..., color:..., info:...},
                        ...
                    ]
                }

            }
            ...
            info: {
                classname: {},
                ...
            }...
        }
            info keys are optional and will be replaced
            with empty dicts if absent.
            NOTE: imname is used as key instead of ImageSet index
            because while index might change (add new frames to
            ImageSet), the name should remain the same for the actual
            frame.
        imset: ImageSet
            The corresponding image set for these labels.
        """
        self.data = data
        self.imset = imset

    def _topclassinfo(self, clsname):
        """Get top class info dict."""
        info = self.data.get('info')
        if info:
            d = info.get(clsname)
            if d is not None:
                return d
        return {}

    def _add_classinfo(self, framedata):
        """Add classinfo to a frame."""
        for k, d in framedata:
            if d.get('info') is None:
                d['info'] = self._topclassinfo(k)
        return framedata


    def __getitem__(self, idx):
        """Return data for a frame."""
        name = self.imset.name(idx)
        ret = self.data.get(name)
        if ret is None:
            ret = {k: {'data': []} for k in self.data.get('info', {})}
        return self._add_classinfo(ret)

    def __setitem__(self, idx, framedata):
        """Set frame data for an idx.

        idx: the index of the frame data.
        framedata: a dict, see `jhsiao.labeler.canvas.LCanv.data()`.

        Remove _interpolated keys from object info dicts.
        Setting the dict indicates that the frame data has
        been accepted and so interpolation should not
        activate for this frame anymore.
        """
        self.data[self.imset.name(idx)] = framedata

    def normalize(self, classinfos):
        """Change all to match same class info."""
        for framename, d in self.data:
            for classname, clsdata in d.items():
                cls = Obj.classes[classname]
                clsinfo = clsdata.pop('info', None)
                if clsinfo is None:
                    info = self.data.get('info')
                    if info:
                        clsinfo = info.get(classname, cls.INFO)
                    else:
                        clsinfo = cls.INFO
                newinfo = classinfos.get(classname, cls.INFO)
                for obj in clsdata['data']:
                    cls.convert_dict(obj, clsinfo, newinfo)
        self.data['info'] = {
            k: copy.deepcopy(dict(v)) for k, v in classinfos.items()}


class InterpolatedLabelSet(LabelSet):
    def _interpolated(self, framedata):
        """Return True if any non-interpolated data."""
        empty = {}
        for k, d in framedata.items():
            objs = d.get('data')
            if objs:
                for obj in objs:
                    if not obj.get('info', empty).get('_interpolated'):
                        return False
        return True

    def _find_manual_data(self, idxs):
        """Search for data that was not interpolated.

        Return idx, data if found.
        Return None if not.
        """
        for idx in idxs:
            name = self.imset.name(idx)
            data = self.data.get(name)
            if data and not self._interpolated(data):
                return idx, data
        return None

    def interpolate(self, idx):
        """interpolate/extrapolate an index.

        Searches for data before and after.  Otherwise,
        just search for the 2 frame data closest to the
        given idx.  The created objects will be given
        info dict with _interpolated=True.  This indicates
        that the objects should be re-interpolated if
        the frame is selected again (some non-interpolated data
        may have been updated.)
        """
        name = self.imset.name(idx)
        framedata = self.data.get(name)
        empty = {}
        ret = self.data.get(name)
        if ret and not self._interpolated(ret):
            return ret
        preidxs = iter(range(idx-1, -1, -1))
        postidxs = iter(range(idx+1, len(self.imset)))
        preresult = self._find_manual_data(preidxs)
        postresult = self._find_manual_data(postidxs)
        if preresult is None and postresult is None:
            return self[idx]
        if preresult is None:
            preresult = postresult
            postresult = self._find_manual_data(postidxs)
        elif postresult is None:
            postresult = preresult
            preresult = self._find_manual_data(preidxs)
        if preresult is None:
            return self._add_classinfo(postresult[1])
        elif postresult is None:
            return self._add_classinfo(preresult[1])
        else:
            postidx - preidx
            preidx, predata = preresult
            postidx, postdata = postresult
            output = []
            # TODO

    def __setitem__(self, idx, framedata):
        """Set frame data for an idx.

        idx: the index of the frame data.
        framedata: a dict, see `jhsiao.labeler.canvas.LCanv.data()`.

        Remove _interpolated keys from object info dicts.
        Setting the dict indicates that the frame data has
        been accepted and so interpolation should not
        activate for this frame anymore.
        """
        for clsname, clsdct in framedata.items():
            for obj in clsdct['data']:
                objinfo = obj.get('info')
                if objinfo:
                    objinfo.pop('_interpolated', None)
        super(InterpolatedLabelSet).__setitem__(idx, framedata)
        # TODO: update interpolations
