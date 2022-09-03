"""Working with labeler data.

data:
    {
        imname: [
            {'type': itemtype, 'data': dataperitem, info...},
            {'type': itemtype, 'data': dataperitem, info...}
            ...
        ]
    }
the items in the list are expected to be in creation order.
"""
from __future__ import division
__all__ = [
    'extract_composites', 'restore_composites', 'Interpolator'
]
import bisect
from collections import deque, defaultdict
import sys
from itertools import count

from ..labeleritems import itemclasses, Composite, create_composite

def extract_composites(data):
    classnames = set(
        item['type'] for items in data.values() for item in items)
    composites = set(
        name for name, cls in itemclasses.items()
        if issubclass(cls, Composite))
    q = list(classnames.intersection(composites))
    targets = set()
    while q:
        cls = q.pop()
        targets.add(cls)
        for sub in itemclasses[cls].components:
            name = sub.__name__
            if name in composites and name not in targets:
                q.append(name)
    covered = set()
    targets = deque(targets)
    out = []
    while targets:
        cls = targets.popleft()
        subs = [sub.__name__ for sub in itemclasses[cls].components]
        deps = set(subs)
        deps.intersection_update(composites)
        deps.difference_update(covered)
        if deps:
            targets.append(cls)
        else:
            out.append((cls, subs))
    return out

def restore_composites(data):
    """Create composite classes from output of extract_composites."""
    toupdate = {}
    for name, subs in data:
        toupdate[name] = create_composite(name, subs)
    itemclasses.update(toupdate)

class Interpolator(object):
    """Interpolate between 2 data dicts."""
    def __init__(self, imset, labels):
        """Initialize interpolator.

        Cache pairs.
        """
        self.imset = imset
        self.labels = labels
        self.index = [imset[l] for l in labels]
        self.index.sort()

    def interpolate(self, target, extrapolate=True):
        """Interpolate labels for target imname.

        If only no images have any labels, return no labels (empty).
        If only 1 image, then return that data.
        Otherwise, interpolate if labels exist for images before and
        after according to ordering of the imset.  Else use
        extrapolation instead (2 nearest labels before or after).
        """
        if len(self.index) == 0:
            return []
        elif len(self.index) == 1:
            return self.labels[self.index[0][1]]
        tup = self.imset[target]
        targetidx, targetname = tup
        pick = bisect.bisect_left(self.index, tup)
        if pick < len(self.index):
            if self.index[pick][1] == targetname:
                # no need to interpolate/extrapolate
                return self.labels[targetname]
            elif 0 < pick:
                pre, post = self.index[pick-1], self.index[pick]
            else:
                pre, post = self.index[0], self.index[1]
        else:
            pre, post = self.index[-2], self.index[-1]
        preidx, prename = pre
        postidx, postname = post
        interp = (targetidx-preidx) / (postidx-preidx)
        if extrapolate or 0<=interp<=1:
            return self._interpolate(prename, postname, [interp])[0]
        else:
            return []

    def _interpolate(self, pre, post, interps):
        """Interpolate between given pre/post im names.

        pre/post: imname to use in labels for the respective data.
        interps: Sequence of multipliers to use.
        Return a sequence of list of items, one per interp in interps.
        Pairing algorithm:
            1. split by item type
            2. within each type match if info has matching 'id'
            3. match in order if no 'id'
        """
        predata = self._bytype(self.labels[pre])
        postdata = self._bytype(self.labels[post])
        typeinterpolated = {}
        for tp in predata:
            preinfo = predata[tp]
            postinfo = postdata[tp]
            preids = preinfo['withid']
            preitems = preinfo['items']
            postids = postinfo['withid']
            postitems = postinfo['items']
            if len(preitems) != len(postitems):
                raise Exception((
                    'Interpolation requires matching item counts'
                    'but got {} vs {} for type "{}"').format(
                        len(preitems), len(postitems), tp))
            prepairings = {
                preids[itemid]: postids[itemid]
                for itemid in set(preids).intersection(postids)}
            postidxs = iter(
                i for i in range(len(postitems))
                if i not in set(prepairings.values()))
            interpeds = []
            cls = itemclasses[tp]
            for i in range(len(preitems)):
                postidx = prepairings.get(i)
                if postidx is None:
                    postidx = next(postidxs)
                preitem = preitems[i]
                postitem = postitems[postidx]
                interped = []
                for interp in interps:
                    interitem = preitem.copy()
                    interitem['data'] = cls.interpolate(
                        preitem['data'], postitem['data'], interp)
                    interped.append(interitem)
                interpeds.append(interped)
            typeinterpolated[tp] = iter(interpeds)
        results = [[] for _ in interps]
        # match same order as pre
        for item in self.labels[pre]:
            pick = next(typeinterpolated[item['type']])
            for interitem, out in zip(pick, results):
                out.append(interitem)
        return results

    def _datastruct(self):
        """Return datastructure for each type in _bytype."""
        return dict(items=[], withid={})
    def _bytype(self, data):
        """Extract data by type.

        Return {type: {items:[items], withid={id: idx}}}
        """
        ret = defaultdict(self._datastruct)
        for idx, item in enumerate(data):
            tpdata = ret[item['type']]
            tpdata['items'].append(item)
            info = item.get('info')
            if info is not None:
                itemid = info.get('id', self)
                if itemid is not self:
                    tpdata['withid'][itemid] = idx
        return ret
