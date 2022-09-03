"""Button for selecting colors."""
__all__ = ['ColorPicker']
import sys
if sys.version_info.major > 2:
    import tkinter as tk
    from tkinter import colorchooser
else:
    import Tkinter as tk
    import tkColorChooser as colorchooser

from .. import tkutil as tku

class ColorPicker(tk.Label, object):
    def __init__(self, *args, **kwargs):
        tag = 'ColorPicker'
        kwargs.setdefault('bg', 'black')
        kwargs.setdefault('relief', 'raised')
        kwargs.setdefault('bd', 2)
        kwargs.setdefault('text', 'color')
        super(ColorPicker, self).__init__(
            *args, **kwargs)
        self._color = self.cget('bg')
        self.configure(fg=self.altcolor(self._color))
        tku.subclass(self, tag)
        if not self.bind_class(tag):
            tku.add_bindings(self, tag)

    def color(self):
        return self._color

    def altcolor(self, color):
        r, g, b = self.winfo_rgb(color)
        return '#{:02x}{:02x}{:02x}'.format(
            ((r//256)+127)%256,
            ((g//256)+127)%256,
            ((b//256)+127)%256)

    @tku.Bindings('<Button-1>')
    @staticmethod
    def sinkborder(widget):
        widget.configure(relief='sunken')

    @tku.Bindings('<ButtonRelease-1>')
    @staticmethod
    def setcolor(widget):
        widget.configure(relief='raised')
        rgb, color = colorchooser.askcolor()
        if color is not None:
            widget._color = color
            widget.configure(bg=color, fg=widget.altcolor(color))

if __name__ == '__main__':
    r = tk.Tk()
    c = ColorPicker(r)
    c.grid(row=0, column=0)

    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
