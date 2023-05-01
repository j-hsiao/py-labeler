__all__ = ['DirSet']
import os

import cv2

from . import ImageSet

class DirSet(ImageSet):
    """Images that are in a directory."""
    def __init__(self, dirname):
        self.dirname = dirname

    def get(self, name, callback):
        im = cv2.imread(os.path.join(self.dirname, name))
        callback(name, im)

    def __iter__(self):
        return iter(os.listdir(self.dirname))
