"""Color picker."""
from __future__ import division
import base64

import cv2
import numpy as np

from jhsiao.tkutil import tk
from jhsiao.tkutil.bindings import scopes
from . import bindings

def hsv2rgb(h, s, v):
    """Convert hsv to rgb.

    h: [0-6)
    s: [0-1]
    v: [0-255]
    """
    delta = s*v
    m = v - delta
    if h < 1:
        return v, h*delta+m, m
    elif h < 2:
        return (2-h)*delta + m, v, m
    elif h < 3:
        return m, v, (h-2)*delta + m
    elif h < 4:
        return m, (4-h)*delta + m, v
    elif h < 5:
        return (h-4)*delta + m, m, v
    else:
        return v, m, (6-h)*delta + m


def rgb2hsv(r, g, b):
    """Convert rgb to hsv.

    r,g,b, 0-255
    h: [0-6)
    s: [0-1]
    v: [0-255]
    """
    V = max(r, g, b)
    m = min(r, g, b)
    delta = (V-m)
    S = delta/V if V else 0
    if delta:
        if V == r:
            H = (g - b)/delta
        elif V == g:
            H = 2 + (b-r)/delta
        elif V == b:
            H = 4 + (r-g)/delta
        if H < 0:
            H += 6
    else:
        H = 0
    return H, S, V

def make_sv_palette(hue, out=None, dim=256):
    """Make saturation/value image for hue.

    out should be square if given
    x axis is saturation.
    y axis is value.
    """
    if out is None:
        out = np.empty((dim, dim, 3), np.uint8)
    else:
        dim = out.shape[0]
    if hue < 1:
        hi, mid, lo = 2, 1, 0
    elif hue < 2:
        hi, mid, lo = 1, 2, 0
    elif hue < 3:
        hi, mid, lo = 1, 0, 2
    elif hue < 4:
        hi, mid, lo = 0, 1, 2
    elif hue < 5:
        hi, mid, lo = 0, 2, 1
    else:
        hi, mid, lo = 2, 0, 1
    hi = out[...,hi]
    mid = out[...,mid]
    lo = out[...,lo]
    q = int(hue)
    r = hue-q
    if q % 2:
        r = 1 - r
    s = np.divide(np.arange(dim, dtype=np.uint16), dim-1, dtype=np.float32)
    v = np.empty(dim, np.uint8)
    np.multiply(s[::-1], 255, dtype=np.float32, out=v, casting='unsafe')
    np.multiply(
        s, v[:,None], dtype=np.float32, out=mid, casting='unsafe')
    hi[:] = v[:,None]
    np.subtract(hi, mid, out=lo)
    np.multiply(r, mid, dtype=np.float32, out=mid, casting='unsafe')
    mid += lo
    return out


hueidxs = (
    (2, 0, 1, (slice(None), None)),
    (0, 2, 1, (slice(None, None, -1), None)),
    (0, 1, 2, (slice(None), None)),
    (1, 0, 2, (slice(None, None, -1), None)),
    (1, 2, 0, (slice(None), None)),
    (2, 1, 0, (slice(None, None, -1), None)),
)

def make_hue_palette(out=None, dim=360):
    if out is None:
        out = np.empty((dim, 30, 3), np.uint8)
    else:
        dim = out.shape[0]
    step = dim / 6
    segsize = int(step)
    mids = np.multiply(
        np.arange(segsize, dtype=np.uint16), 255/segsize, dtype=np.float32)
    base = lo = 0
    hi = segsize
    for i1, i2, i3, slc in hueidxs:
        s = slice(lo, hi)
        out[s, :, i1] = 255
        out[s, :, i2] = mids[slc]
        out[s, :, i3] = 0
        base += step
        if int(base) != hi:
            out[hi] = out[hi-1]
        lo = int(base)
        hi = lo+segsize
    return out

def draw_sv_selection(im, x, y):
    roi = im[max(0, y-10):y+10, max(0, x-10): x+10]
    bak = roi.copy()
    cv2.circle(im, (x, y), 5, (0,0,0), 2)
    cv2.circle(im, (x, y), 5, (255,255,255), 1)
    succ, data = cv2.imencode('.png', im)
    roi[...] = bak
    ret = base64.b64encode(data)
    return ret

def draw_h_selection(im, y):
    lo, hi = y-1, y+2
    if lo < 0:
        hi -= lo
        lo = 0
    elif hi > im.shape[0]:
        hi = im.shape[0]
        lo = hi-3
    roi = im[lo:hi]
    bak = roi.copy()
    roi[:,:5] = 255
    roi[:,-5:] = 255
    succ, data = cv2.imencode('.png', im)
    ret = base64.b64encode(data)
    roi[...] = bak
    return ret

@bindings(scope=scopes.Validation, data=(None, int))
def intvalidate(widget, current, pending, data=None):
    if pending:
        try:
            ival = int(pending)
        except ValueError:
            return False
        if data is not None and ival > data:
            widget.setvar(widget.cget('textvariable'), data)
            widget.after_idle(
                lambda: widget.configure(validate='key'))
    else:
        # force variable to 0 when cleared. Using entry.delete
        # causes an exception, but backspace seems to be fine.
        if current != '0':
            widget.event_generate('<BackSpace>', when='head')
            widget.event_generate('<0>', when='head')
    return True

def parse_color(widget, color):
    """Convert general color into r, g, b"""
    r, g, b = widget.winfo_rgb(color)
    return r//256, g//256, b//256

def clip(v, lo, hi):
    """Clip value between lo and hi inclusive."""
    return min(max(lo, v), hi)

def format_color(r, g, b):
    """Format rgb tuple into #RRGGBB color string."""
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class RGBColorPicker(tk.Toplevel, object):
    def __init__(self, color, *args, **kwargs):
        """Create a toplevel to select a color via rgb.

        color: str: The starting color. 
        """
        super(RGBColorPicker, self).__init__(*args, **kwargs)
        r, g, b = parse_color(self, color)
        self.title('Choose RGB color.')
        self.attributes('-topmost', True)
        self.configure(background=color)
        self.grid_columnconfigure(0, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.red = tk.StringVar(self, value=str(r))
        self.green = tk.StringVar(self, value=str(g))
        self.blue = tk.StringVar(self, value=str(b))
        changed = self.onchange.update(widget=(str(self), None))
        changed.trace(self, self.red, 'write')
        changed.trace(self, self.green, 'write')
        changed.trace(self, self.blue, 'write')
        kwargs = {'orient': 'horizontal', 'from': 0, 'to': 255}
        self.r = tk.Scale(self, variable=self.red, **kwargs)
        self.g = tk.Scale(self, variable=self.green, **kwargs)
        self.b = tk.Scale(self, variable=self.blue, **kwargs)
        valcmd = str(intvalidate.update(data=(str(255), int)))
        self.re = tk.Entry(
            self, textvariable=self.red,
            validate='key', validatecommand=valcmd)
        self.ge = tk.Entry(
            self, textvariable=self.green,
            validate='key', validatecommand=valcmd)
        self.be = tk.Entry(
            self, textvariable=self.blue,
            validate='key', validatecommand=valcmd)
        self.rl = tk.Label(self, text='r')
        self.gl = tk.Label(self, text='g')
        self.bl = tk.Label(self, text='b')
        self.rl.grid(row=0, column=1, sticky='nsew')
        self.gl.grid(row=1, column=1, sticky='nsew')
        self.bl.grid(row=2, column=1, sticky='nsew')
        self.r.grid(row=0, column=2, sticky='nsew')
        self.g.grid(row=1, column=2, sticky='nsew')
        self.b.grid(row=2, column=2, sticky='nsew')
        self.re.grid(row=0, column=3, sticky='nsew')
        self.ge.grid(row=1, column=3, sticky='nsew')
        self.be.grid(row=2, column=3, sticky='nsew')
        self.bindtags(('RGBColorPicker',)+self.bindtags())
        self.re.bindtags(('RGBColorPicker',)+self.re.bindtags())
        self.ge.bindtags(('RGBColorPicker',)+self.ge.bindtags())
        self.be.bindtags(('RGBColorPicker',)+self.be.bindtags())
        self.grab_set()

    def __call__(self):
        """Wait until color picked and window closed."""
        self.wait_window()
        return self._color

    def destroy(self):
        self.grab_release()
        self._color = self.cget('background')
        super(RGBColorPicker, self).destroy()

    @staticmethod
    @bindings['RGBColorPicker'].bind('<Escape>', dobreak='True')
    def _close(widget):
        widget.winfo_toplevel().destroy()
        return 'break'

    def color(self):
        r = self.red.get()
        g = self.green.get()
        b = self.blue.get()
        r = clip(int(r) if r else 0, 0, 255)
        g = clip(int(g) if g else 0, 0, 255)
        b = clip(int(b) if b else 0, 0, 255)
        return format_color(r,g,b)

    @bindings(scope=scopes.Trace)
    def onchange(widget, var, index, op):
        widget.configure(background=widget.color())

class HSVColorPicker(tk.Toplevel, object):
    def __init__(self, color, *args, **kwargs):
        """Create a toplevel to select color via hsv.

        color: str: the starting color
        """
        super(HSVColorPicker, self).__init__(*args, **kwargs)
        self.title('Choose HSV color')
        self.attributes('-topmost', True)
        self.configure(background=color)
        self.grid_rowconfigure(0, minsize=361)
        self.grid_columnconfigure(0, minsize=361)

        r, g, b = parse_color(self, color)
        h, s, v = rgb2hsv(r, g, b)
        self.svpalette = make_sv_palette(h)
        self.hpalette = make_hue_palette()
        self.svim = tk.PhotoImage(master=self, format='png')
        self.him = tk.PhotoImage(master=self, format='png')
        svl = tk.Label(
            self, image=self.svim, highlightthickness=0, borderwidth=0)
        hl = tk.Label(
            self, image=self.him, highlightthickness=0, borderwidth=0)
        svl.bindtags(('HSVColorPicker.sv',)+svl.bindtags())
        hl.bindtags(('HSVColorPicker.h',)+hl.bindtags())
        hlabel = tk.Label(self, text='h:')
        slabel = tk.Label(self, text='s:')
        vlabel = tk.Label(self, text='v:')
        self.hentry = tk.Entry(self)
        self.sentry = tk.Entry(self)
        self.ventry = tk.Entry(self)
        self.hentry.insert(0, str(int(h*60)))
        self.sentry.insert(0, str(int(s*100)))
        self.ventry.insert(0, str(int(v)))
        svl.grid(row=0, column=0, sticky='nsew', rowspan=4)
        hl.grid(row=0, column=1, sticky='nsew', rowspan=4)
        hlabel.grid(row=1, column=2, sticky='nsew')
        slabel.grid(row=2, column=2, sticky='nsew')
        vlabel.grid(row=3, column=2, sticky='nsew')
        self.hentry.grid(row=1, column=3, sticky='nsew')
        self.sentry.grid(row=2, column=3, sticky='nsew')
        self.ventry.grid(row=3, column=3, sticky='nsew')

    def __call__(self):
        self.wait_window()
        return self.color

    def destroy(self):
        self.color = parse_color(self, self.cget('background'))
        return super(HSVColorPicker, self).destroy()

    def rgb(self):
        return parse_color(self, self.cget('background'))

    def hsv(self):
        return (
            int(self.hentry.get())/60,
            int(self.sentry.get())/100,
            int(self.ventry.get()),
        )

    @staticmethod
    @bindings['HSVColorPicker.sv'].bind('<Configure>')
    def _resize_sv(widget, width, height):
        picker = widget.master
        dim = max(width, height)
        if picker.svpalette.shape[0] != dim:
            h, s, v = picker.hsv()
            picker.svpalette = make_sv_palette(h, None, dim)
            picker.svim.configure(
                data=draw_sv_selection(
                    picker.svpalette,
                    int(s * width),
                    int((1-(v/255))*height)))

    @staticmethod
    @bindings['HSVColorPicker.sv'].bind('<B1-Motion>', '<Button-1>')
    def _picksv(widget, x, y):
        picker = widget.master
        height, width = picker.svpalette.shape[:2]
        x = min(max(x, 0), width-1)
        y = min(max(y, 0), height-1)
        picker.svim.configure(
            data=draw_sv_selection(picker.svpalette, x, y))
        h = picker.hsv()[0]
        s = x/(width-1)
        v = 1 - y / (height-1)
        picker.sentry.delete(0, 'end')
        picker.sentry.insert(0, str(int(s*100)))
        picker.ventry.delete(0, 'end')
        picker.ventry.insert(0, str(int(v*255)))
        picker.configure(background=format_color(*picker.svpalette[y, x, ::-1]))


    @bindings['HSVColorPicker.h'].bind('<Configure>')
    def _resize_h(widget, height):
        picker = widget.master
        if picker.hpalette.shape[0] != height:
            h, s, v = picker.hsv()
            picker.hpalette = make_hue_palette(dim=height)
            picker.him.configure(
                data=draw_h_selection(
                    picker.hpalette, int((1 - h/6)*height)))

    @bindings['HSVColorPicker.h'].bind('<B1-Motion>', '<Button-1>')
    def _pick_h(widget, y):
        picker = widget.master
        height = picker.hpalette.shape[0]
        y = min(max(y, 0), height-1)
        picker.him.configure(
            data=draw_h_selection(picker.hpalette, y))
        s, v = picker.hsv()[1:]
        h = (1 - y/(height-1))
        picker.hentry.delete(0, 'end')
        picker.hentry.insert(0, str(int(h*360)))
        make_sv_palette(h*6, picker.svpalette)
        cv2.imshow('...', picker.svpalette)
        cv2.waitKey(50)
        svh, svw = picker.svpalette.shape[:2]
        svx, svy = int(s*(svw-1)), int((1-v/255)*(svh-1))
        picker.svim.configure(
            data=draw_sv_selection(picker.svpalette, svx, svy))
        picker.configure(
            background=format_color(*picker.svpalette[svy, svx,::-1]))


class ColorPicker(tk.Frame, object):
    binds = bindings['ColorPicker']
    def __init__(self, master, *args, **kwargs):
        super(ColorPicker, self).__init__(master, *args, **kwargs)
        self.bindtags(('ColorPicker',) + self.bindtags())
        self.configure(width=100, height=100)
        self._red = tk.StringVar(self)
        self._green = tk.StringVar(self)
        self._blue = tk.StringVar(self)
        self.configure(relief='raised', background='black')

    @staticmethod
    @binds.bind('<ButtonRelease-1>')
    def _show_picker(widget):
        pass
