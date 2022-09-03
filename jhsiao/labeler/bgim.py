import sys
if sys.version_info.major > 2:
    import tkinter as tk
    from tkinter import messagebox
else:
    import Tkinter as tk
    import tkMessageBox as messagebox

from PIL import Image, ImageTk
import cv2
import numpy as np

from .. import tkutil as tku
from .crosshairs import Crosshairs

class BgIm(object):
    def __init__(self, widget):
        """Initialize background image."""
        tag = 'BgIm'
        self.idn = widget.create_image(0,0, anchor='nw')
        self.im = None
        self.raw = None
        widget.addtag(tag, 'withtag', self.idn)
        if not widget.bind_class(tag):
            tku.add_bindings(
                widget, tag, bindfunc='tag_bind',
                tupit=tku.memberit(self))
        self.show(widget, None)

    def zoom(self, widget, scale):
        """Zoom image to a scale relative to raw image.

        Return if True or not. (If too small, fail because imdim is 0.)
        """
        if scale > 5:
            return False
        newsize = (
            int(self.raw.width*scale), int(self.raw.height*scale))
        if not all(newsize):
            return False
        resized = self.raw.resize(newsize)
        self.im = ImageTk.PhotoImage(resized)
        widget.itemconfigure(self.idn, image=self.im)
        widget.configure(scrollregion=widget.bbox(self.idn))
        return True

    def show(self, widget, im):
        """Show an image.

        im: a filepath(str), blank image(None), ndarray (bgr)
            or a PIL image
        """
        if isinstance(im, str):
            im = Image.open(im)
        elif im is None:
            im = Image.fromarray(np.full((480,640), 255, np.uint8))
        elif isinstance(im, np.ndarray):
            if im.ndim == 3:
               im = im[...,2::-1]
            im = Image.fromarray(im)
        self.raw = im
        self.im = ImageTk.PhotoImage(im)
        widget.itemconfigure(self.idn, image=self.im)
        widget.configure(scrollregion=widget.bbox(self.idn))

    @tku.Bindings('<Button-1>')
    @staticmethod
    def create(widget, x, y, time, serial):
        """Create an item.

        Generates events to release/click again on same position.
        This should result in selecting the item.
        """
        if time < 0 and serial < 0:
            messagebox.showerror(
                title='Error!',
                message=(
                    'Regenerated click from bg reselected bg.'
                    ' It should have selected the newly created Item.'
                    ' Please debug the currently selected Item type.'))
            return
        else:
            if time < 0 or serial < 0:
                print('!! time or serial can actually be negative!')
            widget.create(x,y)
            widget.update_idletasks()
            widget.event_generate('<ButtonRelease-1>', x=x, y=y)
            widget.event_generate('<Button-1>', x=x, y=y, time=-1, serial=-1)

    @tku.Bindings('<Button-3>')
    @staticmethod
    def _unhide(widget):
        widget.itemconfigure('Item', state='normal')
