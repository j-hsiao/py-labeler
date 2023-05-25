"""Image sets."""

import os
class ImageSet(object):
    """Image set interface."""
    def __init__(self, name):
        self.name = name
        self.pos = 0

    def __len__(self):
        raise NotImplementedError

    def __getitem__(self, idx):
        """Return name and image synchronously."""
        raise NotImplementedError

    def __call__(self, idx, callback):
        """Start loading the indexed image and call callback when done.

        idx: int
            The index of the image to load.
        callback: callable(name, image)
            name: str, the name of the image.
            image: numpy array or None if failed.
        This immediately returns the name of the image.
        Once loading is done, maybe in a thread, maybe in this
        function, callback will be called.
        """
        fname, im = self[idx]
        callback(fname, im)
        return fname

    @staticmethod
    def open(uri, *args, **kwargs):
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
