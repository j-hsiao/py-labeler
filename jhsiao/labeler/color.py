"""Color picker."""
from __future__ import division
from jhsiao.tkutil import tk
from jhsiao.tkutil.bindings import scopes
from . import bindings


def hsv2rgb(h, s, v):
    div = h / 60
    delta = s*v
    m = v - delta
    if 0 <= div < 1:
        return v, m, div*delta+m
    elif div < 2:
        return (2-div)*delta + m, v, m
    elif div < 3:
        return m, v, (div-2)*delta + m
    elif div < 4:
        return m, (4-div)*delta + m, v
    elif div < 5:
        return (div-4)*delta + m, m, v
    else:
        return v, m, (6-div)*delta + m

def rgb2hsv(r, g, b):
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
        H *= 60
        if H < 0:
            H += 360
    else:
        H = 0
    return H, S, V



@bindings(scope=scopes.Validation)
def intvalidate(widget, current, pending):
    if pending:
        try:
            int(pending)
        except ValueError:
            return False
    else:
        # force variable to 0 when cleared
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
        valcmd = str(intvalidate)
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
        self._color = self.color()
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
        r, g, b = parse_color(self, color)


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
