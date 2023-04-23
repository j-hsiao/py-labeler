from jhsiao.tkutil import tk, add_bindtags
from . import bindings
from .objs import Crosshairs, BGImage

class LCanv(tk.Frame, object):
    canvbinds = bindings['LCanv.canv']
    def __init__(self, master, *args, **kwargs):
        super(LCanv, self).__init__(master, *args, **kwargs)
        self.canv = tk.Canvas(self)
        add_bindtags(self.canv, 'LCanv.canv')
        bindings.apply(self.canv, methods=['tag_bind'], create=False)
        self.bgim = BGImage(self.canv)
        self.xhairs = Crosshairs(self.canv)
        self.canv.grid(row=0, column=0)

    canvbinds.bind('<B1-Leave>', '<B1-Enter>')(' ')

    @staticmethod
    @canvbinds.bind('<Enter>')
    def _entered(widget):
        Crosshairs.show(widget)
        widget.focus_set()

    @staticmethod
    @canvbinds.bind('<Leave>')
    def _left(widget):
        Crosshairs.hide(widget)

    @staticmethod
    @canvbinds.bind('<Motion>')
    def _movexhairs(widget, x, y):
        widget.master.xhairs.moveto(widget, x, y)
