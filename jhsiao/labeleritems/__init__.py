"""A namespace package for adding items for the labeler to use."""
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

from jhsiao.tkutil.bindings import Bindings

import numpy as np
from PIL import Image, ImageTk

bindings = Bindings('tag_bind')

class Obj(object):
    """An object on a tk.Canvas.

    Objs represent an object on a canvas and can be made up of multiple
    tk.Canvas items.  The items that make an Obj should always have a
    fixed relative stacking order.  This allows selecting particular
    items by searching for the object idtag.  The Obj's idtag is the
    name of the Obj joined to the item id of its first item by an
    underscore.  All constituent items should have this object tag.

    """
    TAGS = ['Obj', 'Obj_{}']
    binds = bindings['Obj']

    def __init__(self, master, *ids):
        self.ids = []
        for idn in ids:
            if isinstance(idn, Obj):
                self.ids.extend(idn.ids)
            else:
                self.ids.append(idn)
        self.addtag(master, self.ids, Obj.TAGS)

    @staticmethod
    def addtag(master, ids, names):
        for name in names:
            tag = name.format(ids[0])
            for idn in ids:
                master.addtag(tag, 'withtag', idn)

    @staticmethod
    def _snapto(master, x, y, target):
        p = Obj.canvxy(master, x, y)
        if target != p:
            master.event_generate(
                '<Shift-Motion>',
                x=x+(target[0]-p[0]),
                y=y+(target[1]-p[1]),
                warp=True, when='head')

    @staticmethod
    def canvxy(master, x, y):
        return master.canvasx(x), master.canvasy(y)

    @staticmethod
    def altcolor(master, color):
        """Return a color for contrast against color."""
        return '#{:02x}{:02x}{02x}'.format(
            *[((x//256)+128)%256 for x in master.winfo_rgb(color))

    @staticmethod
    @binds.bind('<Button-1>')
    def onclick(widget):
        idn = widget.find('withtag', 'current')
        widget.obj = widget.gettags('current')[-1]



class BGImage(object):
    binds = bindings['BGImage']
    def __init__(self, master, x, y, **kwargs):
        self.idn = master.create_image(0,0, anchor='nw')
        self.im = None
        self.raw = None
        master.addtag('BGImage', 'withtag', self.idn)

    def show(self, master, im):
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
        master.itemconfigure(self.idn, image=self.im)
        master.configure(
            scrollregion=(0, 0, self.raw.shape[1], self.raw.shape[0]))

    def roi(self, master):
        """Show a roi."""
        l, r = master.xview()
        t, b = master.yview()
        if r - l == 1:
            owidth = self.im.width
        else:
            owidth = master.winfo_width()
        if b - t == 1:
            oheight = self.im.height
        else:
            oheight = master.winfo_height()
        height, width = self.raw.shape[:2]
        l *= width
        r *= width
        t *= height
        b *= height
        self.im = ImageTk.PhotoImage(
            self.raw.resize((owidth, oheight), box=(l, t, r, b)))
        master.itemconfigure(self.idn, image=self.im)
        master.coords(
            self.idn, master.canvasx(0), master.canvasy(0))
