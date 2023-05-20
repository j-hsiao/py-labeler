"""Color picker."""
from __future__ import division
import base64

import cv2
import numpy as np

from jhsiao.tkutil import tk, add_bindtags
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

def make_sv_palette(hue, out=None, width=256, height=256):
    """Make saturation/value image for a particular hue.

    x axis is saturation.
    y axis is value. top is 255, bottom is 0

    hue: 0-6
    out should be square if given.  Otherwise a new array is allocated
    with shape (dim, dim, 3)
    """
    if out is None:
        out = np.empty((height, width, 3), np.uint8)
    else:
        height, width = out.shape[:2]
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
    s = np.divide(
        np.arange(width, dtype=np.uint16), width-1, dtype=np.float32)
    v = np.divide(
        np.arange(height, dtype=np.uint16)[::-1], height-1, dtype=np.float32)
    v *= 255
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
    """Create virtual hue selection image.

    out: output array, takes priority over dim.
    dim: output height.
    """
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

fstr = '{:.3f}'.format


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

class RGB(tk.Frame, object):
    def __init__(self, color, *args, **kwargs):
        """Create a toplevel to select a color via rgb.

        color: str: The starting color. 
        """
        self.change_origin = kwargs.pop('change_origin', self)
        super(RGB, self).__init__(*args, **kwargs)
        r, g, b = parse_color(self, color)
        self.orig = color
        self.configure(background=color)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1, minsize=100)
        self.red = tk.StringVar(self, value=str(r))
        self.green = tk.StringVar(self, value=str(g))
        self.blue = tk.StringVar(self, value=str(b))
        kwargs = {'orient': 'horizontal', 'from': 0, 'to': 255}
        self.r = tk.Scale(self, variable=self.red, **kwargs)
        self.g = tk.Scale(self, variable=self.green, **kwargs)
        self.b = tk.Scale(self, variable=self.blue, **kwargs)
        valcmd = self.intvalidate.str(data=(255, int))
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
        self.rl.grid(row=1, column=0, sticky='nsew')
        self.gl.grid(row=2, column=0, sticky='nsew')
        self.bl.grid(row=3, column=0, sticky='nsew')
        self.r.grid(row=1, column=1, sticky='nsew')
        self.g.grid(row=2, column=1, sticky='nsew')
        self.b.grid(row=3, column=1, sticky='nsew')
        self.re.grid(row=1, column=2, sticky='nsew')
        self.ge.grid(row=2, column=2, sticky='nsew')
        self.be.grid(row=3, column=2, sticky='nsew')
        changed = self.onchange.update(widget=self)
        changed.trace(self, self.red, 'write')
        changed.trace(self, self.green, 'write')
        changed.trace(self, self.blue, 'write')

    def color(self):
        """Return tk string var"""
        return self.cget('background')

    def set_color(self, color):
        r, g, b = parse_color(self, color)
        self.red.set(str(r))
        self.green.set(str(g))
        self.blue.set(str(b))

    @bindings('', scope=scopes.Trace)
    def onchange(widget, var, index, op):
        r = widget.red.get()
        g = widget.green.get()
        b = widget.blue.get()
        r = clip(int(r) if r else 0, 0, 255)
        g = clip(int(g) if g else 0, 0, 255)
        b = clip(int(b) if b else 0, 0, 255)
        color=format_color(r,g,b)
        widget.configure(background=color)
        widget.change_origin.event_generate(
            '<<ColorChange>>', when='head', data=color)

    @bindings('', scope=scopes.Validation, data=(None, int))
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
            elif pending.startswith('0') and len(pending) > 1:
                for end in range(len(pending)):
                    if pending[end] != '0':
                        break
                widget.after_idle(widget.delete, 0, end)
        else:
            # force variable to 0 when cleared. Using entry.delete
            # causes an exception, but backspace seems to be fine.
            if current != '0':
                widget.event_generate('<BackSpace>', when='head')
                widget.event_generate('<0>', when='head')
        return True

class HSV(tk.Frame, object):
    def __init__(self, color, *args, **kwargs):
        """Create a toplevel to select color via hsv.

        color: str: the starting color
        """
        self.change_origin = kwargs.pop('change_origin', self)
        super(HSV, self).__init__(*args, **kwargs)
        self.grid_rowconfigure(0, minsize=100, weight=1)
        self.grid_columnconfigure(0, minsize=2, weight=1)
        self.configure(background=color)
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
        add_bindtags(svl, 'HSV.sv')
        add_bindtags(hl, 'HSV.h')
        hlabel = tk.Label(self, text='h:')
        slabel = tk.Label(self, text='s:')
        vlabel = tk.Label(self, text='v:')
        self.hentry = tk.Entry(self, validate='key')
        self.sentry = tk.Entry(self, validate='key')
        self.ventry = tk.Entry(self, validate='key')
        self.hentry.insert(0, fstr(h*60))
        self.sentry.insert(0, fstr(s))
        self.ventry.insert(0, fstr(v/255))
        svl.grid(row=0, column=0, sticky='nsew', rowspan=4)
        hl.grid(row=0, column=1, sticky='nsew', rowspan=4)
        hlabel.grid(row=1, column=2, sticky='nsew')
        slabel.grid(row=2, column=2, sticky='nsew')
        vlabel.grid(row=3, column=2, sticky='nsew')
        self.hentry.grid(row=1, column=3, sticky='nsew')
        self.sentry.grid(row=2, column=3, sticky='nsew')
        self.ventry.grid(row=3, column=3, sticky='nsew')
        svl.configure(width=200, height=200)

        self.hentry.configure(
            validatecommand=self.floatvalidate.str(
                widget=self.hentry, data=(360,float)))
        self.sentry.configure(
            validatecommand=self.floatvalidate.str(
                widget=self.sentry, data=(1.0,float)))
        self.ventry.configure(
            validatecommand=self.floatvalidate.str(
                widget=self.ventry, data=(1.0,float)))

    def color(self):
        """Return tk string var"""
        return self.cget('background')

    def set_color(self, color):
        h, s, v = rgb2hsv(*parse_color(self, color))
        self.hentry.delete(0, 'end')
        self.hentry.insert(0, str(h))
        self.sentry.delete(0, 'end')
        self.sentry.insert(0, str(s))
        self.ventry.delete(0, 'end')
        self.ventry.insert(0, str(v))
        self._sync_to_entry(True)

    def rgb(self):
        """Return r,g,b int tuple (0-255)."""
        return parse_color(self, self.cget('background'))

    def hsv(self):
        """Return hsv tuple in range of 0-1, 0-1, 0-1."""
        try:
            h = float(self.hentry.get())
        except ValueError:
            h = 0
        try:
            s = float(self.sentry.get())
        except ValueError:
            s = 0
        try:
            v = float(self.ventry.get())
        except ValueError:
            v = 0
        return (h/360, s, v)

    @staticmethod
    @bindings['HSV.sv'].bind('<Configure>')
    def _resize_sv(widget, width, height):
        picker = widget.master
        iheight, iwidth = picker.svpalette.shape[:2]
        if iheight != height or iwidth != width:
            h, s, v = picker.hsv()
            picker.svpalette = make_sv_palette(h*6, None, width, height)
            picker.svim.configure(
                data=draw_sv_selection(
                    picker.svpalette,
                    int(s * (width-1)),
                    int((1-v)*(height-1))))

    @staticmethod
    @bindings['HSV.sv'].bind('<B1-Motion>', '<Button-1>')
    def _pick_sv(widget, x, y):
        picker = widget.master
        height, width = picker.svpalette.shape[:2]
        x = min(max(x, 0), width-1)
        y = min(max(y, 0), height-1)
        picker.svim.configure(
            data=draw_sv_selection(picker.svpalette, x, y))
        s = x/(width-1)
        v = 1 - y/(height-1)
        picker.sentry.configure(validate='none')
        picker.ventry.configure(validate='none')
        picker.sentry.delete(0, 'end')
        picker.sentry.insert(0, fstr(s))
        picker.ventry.delete(0, 'end')
        picker.ventry.insert(0, fstr(v))
        picker.sentry.configure(validate='key')
        picker.ventry.configure(validate='key')
        color = format_color(*picker.svpalette[y, x, ::-1])
        picker.configure(background=color)
        picker.change_origin.event_generate('<<ColorChange>>', when='head', data=color)


    @bindings['HSV.h'].bind('<Configure>')
    def _resize_h(widget, height):
        picker = widget.master
        if picker.hpalette.shape[0] != height:
            h = picker.hsv()[0]
            picker.hpalette = make_hue_palette(dim=height)
            picker.him.configure(
                data=draw_h_selection(
                    picker.hpalette, int((1 - h)*(height-1))))

    @bindings['HSV.h'].bind('<B1-Motion>', '<Button-1>')
    def _pick_h(widget, y):
        picker = widget.master
        height = picker.hpalette.shape[0]
        y = min(max(y, 0), height-1)
        picker.him.configure(
            data=draw_h_selection(picker.hpalette, y))
        s, v = picker.hsv()[1:]
        h = (1 - y/(height-1))
        picker.hentry.configure(validate='none')
        picker.hentry.delete(0, 'end')
        picker.hentry.insert(0, fstr(h*360))
        picker.hentry.configure(validate='key')
        make_sv_palette(h*6, picker.svpalette)
        svh, svw = picker.svpalette.shape[:2]
        svx, svy = int(s*(svw-1)), int((1-v)*(svh-1))
        picker.svim.configure(
            data=draw_sv_selection(picker.svpalette, svx, svy))
        color = format_color(*picker.svpalette[svy, svx,::-1])
        picker.configure(background=color)
        picker.change_origin.event_generate('<<ColorChange>>', when='head', data=color)

    @bindings('', scope=scopes.Validation, data=(None, float))
    def floatvalidate(widget, current, pending, data):
        if pending:
            try:
                fval = float(pending)
            except ValueError:
                if pending != '.':
                    return False
            else:
                if fval > data:
                    widget.delete(0, 'end')
                    widget.insert(0, fstr(data))
                    widget.after_idle(
                        lambda: widget.configure(validate='key'))
                elif pending.startswith('0') and len(pending) > 1:
                    for end in range(len(pending)):
                        if pending[end] != '0':
                            break
                    if pending[end] != '.':
                        widget.after_idle(widget.delete, 0, end)
        widget.after_idle(widget.master._sync_to_entry, data>2)
        return True

    def _sync_to_entry(self, huechange):
        h, s, v = self.hsv()
        if huechange:
            hh = self.hpalette.shape[0]
            hy = round((hh-1) * (1-h))
            self.him.configure(
                data=draw_h_selection(self.hpalette, hy))
            make_sv_palette(h*6, self.svpalette)
        svh, svw = self.svpalette.shape[:2]
        svx, svy = round(s*(svw-1)), round((1-v)*(svh-1))
        self.svim.configure(
            data=draw_sv_selection(self.svpalette, svx, svy))
        color = format_color(*self.svpalette[svy, svx,::-1])
        self.configure(background=color)
        self.change_origin.event_generate('<<ColorChange>>', when='head', data=color)


class ColorPicker(tk.Label, object):
    binds = bindings['ColorPicker']
    def __init__(self, master, *args, **kwargs):
        cls = kwargs.pop('picker', HSV)
        kwargs.setdefault('background', 'black')
        super(ColorPicker, self).__init__(master, *args, **kwargs)
        r, g, b = parse_color(self, self.cget('background'))
        self.configure(
            foreground=format_color(
                (r+127)%256, (g+127)%256, (b+127)%256),
            text='Pick a color')
        add_bindtags(self, 'ColorPicker')
        self.pickercls = cls

    @staticmethod
    @binds.bind('<Button-1>')
    def _select_color(widget):
        """Wait for a color to be submitted or canceled."""
        orig = widget.cget('background')

        window = tk.Toplevel(widget)
        window.title('Pick a color')
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)
        picker = widget.pickercls(orig, window, change_origin=widget)
        submit = tk.Button(
            window, text='submit',
            command=widget.submitted.str(widget=picker))
        cancel = tk.Button(
            window, text='cancel',
            command=widget.canceled.str(widget=picker))
        picker.grid(row=0, column=0, columnspan=2, sticky='nsew')
        submit.grid(row=1, column=0, sticky='nsew')
        cancel.grid(row=1, column=1, sticky='nsew')
        window.grab_set()
        window.wait_window()
        result = getattr(window, 'result', None)
        if result:
            widget.set_color(result)
            widget.event_generate('<<ColorSelected>>')

    def set_color(self, color):
        self.configure(background=color)
        r, g, b = parse_color(self, color)
        self.configure(
            foreground=format_color(
                (r+127)%256, (g+127)%256, (b+127)%256))

    def color(self):
        return self.cget('background')

    @bindings('')
    def submitted(widget):
        widget.master.result = widget.color()
        widget.master.grab_release()
        widget.master.destroy()

    @bindings('')
    def canceled(widget):
        widget.master.grab_release()
        widget.master.destroy()
