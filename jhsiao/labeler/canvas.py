from jhsiao.tkutil import tk, add_bindtags
from . import bindings
from .objs import Crosshairs, BGImage, ObjSelector
from .dict import Dict
from .color import ColorPicker

class LCanv(tk.Frame, object):
    canvbinds = bindings['LCanv.canv']
    def __init__(self, master, *args, **kwargs):
        super(LCanv, self).__init__(master, *args, **kwargs)
        self._changed = False
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, minsize=50)
        self.canv = tk.Canvas(self)
        add_bindtags(self.canv, 'LCanv.canv')
        self.bgim = BGImage(self.canv)
        self.xhairs = Crosshairs(self.canv)
        self.selector = ObjSelector(self)
        self._dict = Dict(self)
        self.colorpicker = ColorPicker(self, border=2, relief='raised')

        self.canv.grid(row=0, column=0, sticky='nsew', rowspan=3)
        self.selector.grid(row=0, column=1, sticky='nsew')
        self.colorpicker.grid(row=1, column=1, sticky='nsew')
        self._dict.grid(row=2, column=1, sticky='nsew')
        bindings.apply(self.canv, methods=['tag_bind'], create=False)

    canvbinds.bind('<B1-Leave>', '<B1-Enter>')(' ')

    @staticmethod
    @canvbinds.bind('<Enter>')
    def _entered(widget):
        Crosshairs.show(widget)
        widget.focus_set()

    @staticmethod
    @canvbinds.bind('<h>', '<H>')
    def _toggle_crosshairs(widget):
        if widget.itemcget('Crosshairs', 'state') == 'hidden':
            Crosshairs.show(widget)
        else:
            Crosshairs.hide(widget)

    @staticmethod
    @canvbinds.bind('<Leave>')
    def _left(widget):
        Crosshairs.hide(widget)

    @staticmethod
    @canvbinds.bind('<Motion>')
    def _movexhairs(widget, x, y):
        widget.master.xhairs.moveto(widget, x, y)

    @staticmethod
    @canvbinds.bind('<B1-Motion>')
    def _modified(widget, x, y):
        self = widget.master
        if not self._changed:
            self._changed = True
        self.xhairs.moveto(widget, x, y)
