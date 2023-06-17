__all__ = ['DirSet']
import os
import time
import re

import cv2

from . import ImageSet

_nsort_pat = re.compile(r'(\d+)')
def _nsort_key(name):
    """Convert to numerical sort structure."""
    ret = _nsort_pat.split(name)
    ret[1::2] = [int(_) for _ in ret[1::2]]
    strparts = ret[::2]
    ret[::2] = [_.lower() for _ in strparts]
    ret.extend(strparts)
    return ret

class DirSet(ImageSet):
    """Images that are in a directory.

    NOT recursive.
    """
    def __init__(self, dirname, check=1):
        super(DirSet, self).__init__(dirname)
        self.fnames = os.listdir(self.name)
        self.fnames.sort(key=_nsort_key)
        self.check = check
        self._check = time.time()
        self._stamp = os.stat(self.name).st_mtime
        self._get_thread()

    @staticmethod
    def _load(idx, dname, fname):
        """Load an image."""
        return idx, fname, cv2.imread(os.path.join(dname, fname))

    @ImageSet.lencheck
    def name(self, idx):
        return self.fnames[idx]

    def _check_changed(self):
        """Check if directory changed and reload fname list if so."""
        now = time.time()
        if now - self._check < self.check:
            return
        self._check = now
        mtime = os.stat(self.name).st_mtime
        if mtime == self._stamp:
            return
        self._stamp = mtime
        curname = self.fnames[self.pos]
        self.fnames = os.listdir(self.name)
        self.fnames.sort(key=_nsort_key)
        try:
            self.pos = self.fnames.index(curname)
        except ValueError:
            self.pos = max(min(self.pos, len(self.fnames)-1), 0)

    def __len__(self):
        return len(self.fnames)

    @ImageSet.lencheck
    def __getitem__(self, idx):
        self.pos = idx
        self._check_changed()
        return self._load(idx, self.name, self.fnames[self.pos])[1:]

    @ImageSet.lencheck
    def __call__(self, idx, callback):
        fname = self.fnames[idx]
        self.pos = idx
        with self.cond:
            self.q.append((callback, self._load, (idx, self.name, fname), {}))
            self.cond.notify()
        return fname
