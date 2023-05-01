"""Image sets."""

import os
class ImageSet(object):
    """Image set interface."""
    def get(self, name, callback):
        """Start loading the named image and call callback when done.

        This allows for asynchronouse fetching of images if it may be
        a better choice.  (ex. via http, or if backwards seek in video.)
        callback takes 2 arguments: name and the image or None if
        loading the image failed.
        """
        raise NotImplementedError

    def __iter__(self):
        """Return names."""
        raise NotImplementedError



def open(uri):
    if os.path.isdir(uri):
        from .dirset import DirSet
        return DirSet(uri)
    else:
        if uri.endswith('.lst') or uri.endswith('.txt'):
            pass
        else:
            from .vidset import VidSet
            try:
                return VidSet(uri)
            except ValueError:
                pass
    return None
