__all__ = ['DirSet']
import os
import time

import cv2

from . import ImageSet

class DirSet(ImageSet):
    """Images that are in a directory.

    NOT recursive.
    """
    def __init__(self, dirname, check=1):
        super(DirSet, self).__init__(dirname)
        self.fnames = os.listdir(self.name)
        self.check = check
        self._check = time.time()
        self._stamp = os.stat(self.name).st_mtime

    def _check_changed(self):
        """Check if directory changed and load if so."""
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
        try:
            self.pos = self.fnames.index(curname)
        except ValueError:
            self.pos = max(min(self.pos, len(self.fnames)-1), 0)

    def __len__(self):
        return len(self.fnames)

    def __getitem__(self, idx):
        if idx < 0 or len(self.fnames) <= idx:
            return None, None
        self.pos = idx
        self._check_changed()
        fname = self.fnames[self.pos]
        return fname, cv2.imread(os.path.join(self.name, fname))
