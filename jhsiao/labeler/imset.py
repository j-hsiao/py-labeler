"""Structures for organizing data.

ImDirs should contain only image files, no subdirs
"""
from __future__ import print_function, division
__all__ = ['ImageSet', 'image_exts', 'loop']
from collections import defaultdict
from itertools import chain
import mimetypes
import os
import re
import sys
import threading
import traceback
import zipfile
if sys.version_info.major > 2:
    import queue
else:
    import Queue as queue

import cv2
import numpy as np

# missing mimetypes
mimetypes.add_type('image/webp', '.webp')

def filetypes(tps=[]):
    """Return filetypes tuples suitable for tkinter filedialog."""
    if not tps:
        tpdct = defaultdict(list)
        for ext, tp in mimetypes.types_map.items():
            if tp.startswith('image') or tp.startswith('video'):
                tpdct[tp].append(ext)
        for k, v in sorted(tpdct.items()):
            v[0] = '*'+v[0]
            tps.append((k, ' *'.join(v)))
        tps.append(('all', '*.*'))
    return tps


def findfkey(target, items, key=None, pick=None):
    """Find key.

    Keys are expected to be path-like.
    Priority is:
        exact match
        exact basename match
        startswith basename match
    attr: getattr on the items if given.
    pick: If multiple matches, then select the pickth
        candidate.
    """
    if key is None:
        try:
            return items.index(target)
        except ValueError:
            pass
    else:
        for idx, item in enumerate(map(key, items)):
            if item == target:
                return idx
        else:
            items = list(map(key, items))
    tbase = os.path.basename(target)
    candidates = []
    for i, base in map(os.path.basename, items):
        if base == tbase:
            return i
        elif base.startswith(tbase):
            candidates.append(i)
    if candidates:
        if len(candidates) == 1:
            return candidates[0]
        elif pick is not None:
            return candidates[pick]
        else:
            raise KeyError(
                'ambiguous key {}: {}'.format(
                    repr(target),
                    list(map(items.__getitem__, candidates))))
    else:
        raise KeyError('bad key {}'.format(target))

class Loop(object):
    """Threaded loop to call functions asynchronously."""
    class LoopProxy(object):
        def __init__(self, loop):
            self.loop = loop
            self.lock = loop.lock
            with loop.lock:
                loop.users += 1

        def put(self, func, arg):
            loop = self.loop
            with loop.lock:
                if loop.thread is None:
                    loop._start()
                loop.item[0] = (func, arg)
                loop.has.set()

        def release(self):
            loop = self.loop
            if loop is None:
                return
            with loop.lock:
                loop.users -= 1
                if loop.users == 0 and loop.thread is not None:
                    loop._stop()
            self.loop = None

        def __del__(self):
            self.release()

    def __init__(self):
        self.lock = threading.Lock()
        self.item = None
        self.has = None
        self.users = 0
        self.thread = None

    def __call__(self):
        """Return a proxy/reference for auto-thread management."""
        return self.LoopProxy(self)

    def _start(self):
        """Start thread.  Assume not started."""
        self.item = [None]
        self.has = threading.Event()
        self.thread = threading.Thread(
            target=self._async_loop, args=[self.lock, self.has, self.item])
        self.thread.daemon = True
        self.thread.start()

    def _stop(self):
        """Stop thread.  Assume started."""
        self.item[0] = self.item = None
        self.has.set()
        self.has = None
        self.thread = None

    @staticmethod
    def _async_loop(lock, has, item):
        """Async loop for image loading.

        q: a queue, should take a pair:
            callable and an arg.
        """
        while 1:
            has.wait()
            with lock:
                thing = item[0]
                if thing is None:
                    sys.stdout.flush()
                    return
                func, arg = thing
                thing = item[0] = None
                has.clear()
            try:
                func(arg)
            except Exception:
                traceback.print_exc()
            # If func is a bound method of something
            # with reference to a LoopProxy,
            # reassignment may cause __del__ to be fired
            # resulting in a deadlock, so clear the refs.
            func = arg = None

class ImageSet(object):
    LOOP = Loop()
    def __init__(self, name):
        self.path = os.path.normpath(name)
        self.dir, self.name = os.path.split(self.path)
        if not self.dir:
            self.dir = '.'
        normed = os.path.normcase(self.name)
        # get actual case.
        for n in os.listdir(self.dir):
            if os.path.normcase(n) == normed:
                self.name = n
                self.path = os.path.join(self.dir, self.path)
        self.loop = ImageSet.LOOP()
        self.index = 0

    @staticmethod
    def _numsort_key(
        string, pattern=re.compile(r'(?P<num>\d+)|(?P<alpha>\D+)')):
        """Split string into int/non-int list.

        Suitable for use as a key for numeric sorting.
        Prefer case insensitive sort first.
        """
        ret1 = []
        ret2 = []
        match = pattern.search(string)
        while match is not None:
            start, stop = match.span()
            nstr = match.group('num')
            if nstr:
                v = int(nstr)
                ret1.append(v)
                ret2.append(v)
            else:
                ret1.append(match.group('alpha').lower())
                ret2.append(match.group('alpha'))
            match = pattern.search(string, stop)
        ret1.extend(ret2)
        return ret1

    @staticmethod
    def open(name):
        if isinstance(name, (list, tuple)):
            return ImList(name)
        elif os.path.isdir(name):
            return ImDir(name)
        else:
            if name.endswith('.zip'):
                return ZipSet(name)
            tp, enc = mimetypes.guess_type(name)
            if tp is None:
                raise Exception('unknown mimetype for {}'.format(name))
            else:
                basetype = tp.split('/', 1)[0]
                if basetype == 'video':
                    return Vid(name)
                elif basetype == 'image':
                    return ImDir(name)
                else:
                    raise Exception(
                        'No handling for detected mimetype {} of "{}"'.format(
                            tp, name))

    def next(self, offset=1):
        """Return next image set."""
        dirname = self.dir
        fnames = os.listdir(dirname)
        fnames.sort(key=self._numsort_key)
        pick = min(max(fnames.index(self.name)+offset, 0), len(fnames)-1)
        if offset > 0:
            order = chain(range(pick, len(fnames)), range(pick))
        else:
            order = chain(range(pick, -1, -1), range(len(fnames)-1, pick, -1))
        for candidate in order:
            fullpath = os.path.join(dirname, fnames[candidate])
            if os.path.normpath(fullpath) != self.path:
                try:
                    return self.open(fullpath)
                except Exception as e:
                    print(e, file=sys.stderr)
        return None

    def __getitem__(self, key):
        """Return int idx and name without updating position."""
        if isinstance(key, tuple):
            key, offset = key
        else:
            offset = 0
        return self._getitem(
            self._normkey(self.index if key is None else key, offset))

    def __call__(self, key, offset=0, callback=None):
        """Return (imname, np.ndarray) of image.

        key: index or (index, offset).
            int: index into the list
            str: index of str
            None: current index
        Retrieving an item also changes the current index to the
        index of the returned item.
        Failture to decode an image will result in None for the image.
        Indices will be clipped to 0 to number of images.
        """
        if key is None:
            key = self.index
        index = self.index = self._normkey(key, offset)
        if callback is None:
            return self._getframe(index)
        else:
            self.loop.put(self._async, (index, callback))

    def _async(self, info):
        idx, callback = info
        callback(*self._getframe(idx))

    def _normkey(self, key, offset):
        raise NotImplementedError
    def _getframe(self, idx):
        raise NotImplementedError
    def _getitem(self, idx):
        raise NotImplementedError
    def __len__(self):
        raise NotImplementedError

    def resync(self):
        """Resync image source."""
        pass

class ImList(ImageSet):
    """Represent custom selection of images.

    (For example, from multi-select files)
    """
    def __init__(self, uri):
        """uri: a list of file paths.

        relative paths should be relative to cwd.
        """
        super(ImList, self).__init__('custom set')
        self.filenames = sorted(uri, key=self._numsort_key)

    def _normkey(self, key, offset):
        if isinstance(k, str):
            key = findfkey(key, self.filenames)
        return min(max(key+offset, 0), len(self.filenames)-1)

    def _getframe(self, idx):
        fname = self.filenames[idx]
        try:
            with open(fname, 'rb') as f:
                im = cv2.imdecode(np.frombuffer(f.read(), np.uint8), -1)
        except IOError:
            im = None
        return fname, im

    def _getitem(self, idx):
        return idx, self.filenames[idx]

    def __len__(self):
        return len(self.filenames)

    def resync(self):
        """Custom set of images does not change."""
        pass

class ImDir(ImageSet):
    """Represent a dir containing images.

    Does not check subdirectories.
    """
    def __init__(self, uri):
        """If uri is a file, use its containing dir."""
        if os.path.isdir(uri):
            name = uri
            start = None
        else:
            name, start = os.path.split(uri)
            if not name:
                name = '.'
        super(ImDir, self).__init__(name)
        self.basenames = [start]
        self.resync()

    def __len__(self):
        return len(self.basenames)

    def _normkey(self, key, offset):
        if isinstance(key, str):
            key = findfkey(key, self.basenames)
        return min(max(key+offset, 0), len(self.basenames)-1)

    def _getframe(self, idx):
        imname = self.basenames[idx]
        fullpath = os.path.join(self.path, imname)
        try:
            with open(fullpath, 'rb') as f:
                im = cv2.imdecode(np.frombuffer(f.read(), np.uint8), -1)
        except IOError:
            im = None
        return imname, im

    def _getitem(self, index):
        return index, self.basenames[index]

    def resync(self):
        """Reload the directory."""
        try:
            curname = self.basenames[self.index]
        except Exception:
            curname = None
        self.basenames = sorted(os.listdir(self.path), key=self._numsort_key)
        if curname:
            try:
                self.index = self.basenames.index(curname)
            except ValueError:
                self.index = 0
        else:
            self.index = 0

class ZipSet(ImageSet):
    """Zipped archive of images."""
    def __init__(self, uri):
        super(ZipSet, self).__init__(uri)
        self.f = self.infos = None
        self.idx = {}
        self.resync()

    @classmethod
    def _sortkey(cls, thing):
        """Key for sorting zip infos."""
        return cls._numsort_key(thing.filename)

    @staticmethod
    def _fnamekey(info):
        """Key for using filename of infos."""
        return info.filename

    def resync(self):
        """Reopen the zip."""
        try:
            curname = self.infos[self.index].filename
        except Exception:
            curname = None
        if self.f is not None:
            self.f.close()
        self.f = zipfile.ZipFile(self.path)
        self.infos = [
            info for info in self.f.infolist() if not info.is_dir()]
        self.infos.sort(key=self._sortkey)
        if curname is not None:
            try:
                self.index = findfkey(
                    curname, self.infos, self._fnamekey, pick=0)
                return
            except KeyError:
                pass
        self.index = 0

    def _normkey(self, key, offset):
        if isinstance(key, str):
            key = findfkey(key, self.infos, self._fnamekey)
        return min(max(key+offset, 0), len(self.infos)-1)

    def _getframe(self, idx):
        info = self.infos[idx]
        try:
            with self.f.open(info) as imf:
                im = cv2.imdecode(np.frombuffer(imf.read(), np.uint8), -1)
        except Exception:
            im = None
        return info.filename, im

    def _getitem(self, index):
        return index, self.infos[index].filename

    def __len__(self):
        return len(self.infos)


class Vid(ImageSet):
    def __init__(self, vid):
        super(Vid, self).__init__(vid)
        self.cap = cv2.VideoCapture(self.path)
        self.cap.grab()
        if not self.cap.isOpened():
            raise Exception('Failed to open "{}"'.format(self.path))
        self._len = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)

    def _normkey(self, key, offset):
        with self.loop.lock:
            l = self._len
        return min(max(0, int(key)+offset), l-1)

    def _getitem(self, idx):
        return idx, str(idx)

    def _getframe(self, idx):
        cap = self.cap
        target = idx+1
        cur = cap.get(cv2.CAP_PROP_POS_FRAMES)
        if cur > target:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            cap.grab()
        else:
            while cur < target:
                if not cap.grab():
                    break
                cur += 1
        success, frame = cap.retrieve()
        if not success:
            l = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            with self.loop.lock:
                self._len = l
            cap.set(cv2.CAP_PROP_POS_FRAMES, l-1)
            success, frame = cap.read()
        return str(int(cap.get(cv2.CAP_PROP_POS_FRAMES)-1)), frame

    def __len__(self):
        if self._len < max(0, cap.get(cv2.CAP_PROP_POS_FRAMES)):
            while cap.grab():
                pass
            self._len = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        return self._len

    def resync(self):
        """Resync the video.

        If this is needed, then that implies that the video has some
        kind of error.  Frame seeking will be inaccurate so this will
        seek to the beginning and step back to the current frame number.
        """
        cap = self.cap
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        for i in range(self.index):
            if not cap.grab():
                print(
                    'warning, index/length differs from metadata',
                    file=sys.stderr)
                self._len = i
                self.index = i-1
                return

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('uri', help='uri to some image set')
    args = p.parse_args()
    imset = ImageSet.open(args.uri)
    cv2.namedWindow(imset.name)
    imname, im = imset(None)
    scale = min(720/im.shape[0], 1280/im.shape[1])
    im = cv2.resize(im, (0,0), fx=scale, fy=scale)
    cv2.putText(
        im, imname, (0, im.shape[0]-10),
        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
    cv2.imshow(imset.name, im)
    key = cv2.waitKey(0) & 0xFF

    q = [None]
    def callback(imname, frame):
        print('finished loading', imname)
        q[0] = (imname, frame)

    step = 1
    while key != ord('q'):
        if key == ord('a'):
            imname, im = imset(None,-step)
            scale = min(720/im.shape[0], 1280/im.shape[1])
            im = cv2.resize(im, (0,0), fx=scale, fy=scale)
            cv2.putText(
                im, imname, (0, im.shape[0]-10),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
        elif key == ord('d'):
            imname, im = imset(None,step)
            scale = min(720/im.shape[0], 1280/im.shape[1])
            im = cv2.resize(im, (0,0), fx=scale, fy=scale)
            cv2.putText(
                im, imname, (0, im.shape[0]-10),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
        elif key == ord('i'):
            step += 1
            print(step)
        elif key == ord('k'):
            step = max(1, step-1)
            print(step)
        elif key == ord('A'):
            imset(None,-step, callback)
        elif key == ord('D'):
            imset(None,step, callback)
        elif key == ord('N'):
            nxt = imset.next(1)
            if nxt is not None:
                cv2.destroyWindow(imset.name)
                imset = nxt
                imname, im = imset(None)
                scale = min(720/im.shape[0], 1280/im.shape[1])
                im = cv2.resize(im, (0,0), fx=scale, fy=scale)
                cv2.putText(
                    im, imname, (0, im.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
        elif key == ord('P'):
            nxt = imset.next(-1)
            if nxt is not None:
                cv2.destroyWindow(imset.name)
                imset = nxt
                imname, im = imset(None)
                scale = min(720/im.shape[0], 1280/im.shape[1])
                im = cv2.resize(im, (0,0), fx=scale, fy=scale)
                cv2.putText(
                    im, imname, (0, im.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
        elif q[0]:
            imname, im = q[0]
            q[0] = None
            scale = min(720/im.shape[0], 1280/im.shape[1])
            im = cv2.resize(im, (0,0), fx=scale, fy=scale)
            cv2.putText(
                im, imname, (0, im.shape[0]-10),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
        cv2.imshow(imset.name, im)
        key = cv2.waitKey(0) & 0xFF
