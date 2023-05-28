"""Image sets."""
import threading
from collections import deque
import traceback
try:
    import queue
except ImportError:
    import Queue as queue

import os
class ImageSet(object):
    """Image set interface."""
    _recycle = queue.Queue()

    def __init__(self, name):
        self.name = name
        self.pos = -1
        self.thread = self.q = self.cond = None

    @staticmethod
    def lencheck(func):
        def newfunc(self, idx, *args, **kwargs):
            if idx < 0 or len(self) <= idx:
                raise IndexError(str(idx))
            return func(self, idx, *args, **kwargs)
        newfunc.__doc__ = func.__doc__
        return newfunc

    def __len__(self):
        """Number of images in the image set."""
        raise NotImplementedError

    def __getitem__(self, idx):
        """Return name and image synchronously.

        idx: int [0, len(self))
        Raise IndexError if invalid index
        """
        raise NotImplementedError

    def __call__(self, idx, callback):
        """Start loading the indexed image and call callback when done.

        idx: int, [0, len(self))
            The index of the image to load.  Invalid index raises
            IndexError
        callback: callable(idx, name, image)
            idx: idx given as argument.
            name: str, the name of the image.
            image: numpy array or None if failed.
        This immediately returns the name of the image.
        Once loading is done, maybe in a thread, maybe in this
        function, callback will be called.  The default implementation
        is synchronous.
        """
        fname, im = self[idx]
        callback(idx, fname, im)
        return fname

    def name(self, idx):
        """Return name at idx."""
        raise NotImplementedError

    @staticmethod
    def open(uri, *args, **kwargs):
        """Create a new ImageSet.

        The actual class depends on the uri.  None if no suitable
        subclasses for the given uri.
        """
        if os.path.isdir(uri):
            from .dirset import DirSet
            return DirSet(uri, *args, **kwargs)
        else:
            if uri.endswith('.lst') or uri.endswith('.txt'):
                pass
            else:
                from .vidset import VidSet
                try:
                    return VidSet(uri, *args, **kwargs)
                except ValueError:
                    pass
        return None

    def close(self):
        """Close the image set."""
        if self.q is not None:
            self._recycle_thread()

    def __del__(self):
        self.close()

    #------------------------------
    # internal methods
    #------------------------------
    def _get_thread(self):
        """Return thread, deque, and Condition tuple.

        Prefer to take from _recycle.  Create new if empty.
        """
        try:
            data = ImageSet._recycle.get(False)
        except queue.Empty:
            self.q = deque(maxlen=1)
            self.cond = threading.Condition()
            self.thread = threading.Thread(
                target=ImageSet._process, args=(self.q, self.cond))
            self.thread.daemon = True
            self.thread.start()
        else:
            self.thread, self.q, self.cond = data

    def _recycle_thread(self):
        """Put threaded resources into _recycle and set to None."""
        ImageSet._recycle.put((self.thread, self.q, self.cond))
        self.q = self.cond = self.thread = None

    @staticmethod
    def clear():
        """Explicitly clear _recycle."""
        while 1:
            try:
                thread, cond, q = ImageSet._recycle.get()
            except queue.Empty:
                return
            else:
                with cond:
                    q.append(None)
                thread.join()

    @staticmethod
    def _process(q, cond):
        """Process requests.

        Each request is a 4-tuple of:
        callback: callable(str, np.ndarray|None)
            The callback function passed to `__call__()`.
        function: callable(...)
            A callable that returns args for `callback`.
        args tuple: A tuple of args for `function`.
        kwargs dict: A dict of kwargs for `function`.
        """
        while 1:
            with cond:
                cond.wait_for(q.__len__)
                command = q.popleft()
            if command is None:
                return
            else:
                callback, func, args, kwargs = command
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    traceback.print_exc()
                    result = ('ErrorOccurred', None)
                try:
                    callback(*result)
                except Exception:
                    traceback.print_exc()

