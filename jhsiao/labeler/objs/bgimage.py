__all__ = ['BGImage']
from PIL import Image, ImageTk
import numpy as np

from . import ibinds
from .obj import Obj
from jhsiao.tkutil import tk

class BGImage(object):
    binds = ibinds['BGImage']
    def __init__(self, master):
        self.idn = master.create_image(0,0, anchor='nw')
        self.im = None
        self.raw = None
        master.addtag('BGImage', 'withtag', self.idn)
        master.tag_lower('BGImage')
        self.show(master, None)

    def show(self, master, im):
        if isinstance(im, str):
            im = Image.open(im)
        elif im is None:
            im = Image.fromarray(np.full((480,640), 127, np.uint8))
        elif isinstance(im, np.ndarray):
            if im.ndim == 3:
                im = im[...,2::-1]
            im = Image.fromarray(im)
        self.raw = im
        self.im = ImageTk.PhotoImage(im)
        master.itemconfigure(self.idn, image=self.im)
        master.configure(
            scrollregion=(0, 0, self.raw.width, self.raw.height))

    def roi(self, master):
        """Show a roi.

        Resizing the entire image can take a huge amount of memory.
        Resizing only a roi allows much better performance.
        """
        l, r = master.xview()
        t, b = master.yview()
        sw, sh = map(int, master.cget('scrollregion').split()[2:])
        if r - l == 1:
            owidth = sw
        else:
            owidth = master.winfo_width()
        if b - t == 1:
            oheight = sh
        else:
            oheight = master.winfo_height()
        height = self.raw.height
        width = self.raw.width
        l *= width
        r *= width
        t *= height
        b *= height
        self.im = ImageTk.PhotoImage(
            self.raw.resize((owidth, oheight), box=(l, t, r, b)))
        master.itemconfigure(self.idn, image=self.im)
        master.coords(
            self.idn, master.canvasx(0), master.canvasy(0))

    @staticmethod
    @binds.bind('<Button-1>')
    def _create(widget, x, y):
        cx, cy = Obj.canvxy(widget, x, y)
        lcanv = widget.master
        lcanv.selector()(
            widget, cx, cy, lcanv.created_color()).marktop(widget)
        widget.event_generate('<ButtonRelease-1>', x=x, y=y, when='tail')
        widget.event_generate('<Button-1>', x=x, y=y, when='tail')

    @staticmethod
    @binds.bind('<Button-3>')
    def _toggle_hide(widget):
        ids = widget.find('withtag', 'hidden')
        if ids:
            widget.itemconfigure('hidden&&!disabled', state='normal')
            widget.dtag('hidden')
            widget.itemconfigure('disabled', state='disabled')
        else:
            widget.itemconfigure('Obj', state='hidden')
            widget.addtag('hidden', 'withtag', 'Obj')

