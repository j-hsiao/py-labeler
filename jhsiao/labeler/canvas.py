from jhsiao.tkutil import tk
from . import bindings
from jhsiao.labeleritems import bindings as itembindings
from jhsiao.labeleritems import Crosshairs, BGImage

class LCanv(tk.Frame, object):
    canvbinds = bindings['LCanv.canv']
    def __init__(self, master, *args, **kwargs):
        super(LCanv, self).__init__(master, *args, **kwargs)
        self.canv = tk.Canvas(self)
        self.canv.bindtags(self.canv.bindtags() + ('LCanv.canv',))
        itembindings.apply(self.canv)
        self.bgim = BGImage(self.canv)
        self.xhairs = Crosshairs(self.canv)

        self.canv.grid(row=0, column=0)
        self.canv.configure(background='blue')

    @staticmethod
    @canvbinds.bind('<Enter>')
    def _entered(widget):
        Crosshairs.show(widget)
        widget.focus_set()

    @staticmethod
    @canvbinds.bind('<Leave>')
    def _left(widget):
        Crosshairs.show(widget)

    @staticmethod
    @canvbinds.bind('<Motion>')
    def _movexhairs(widget, x, y):
        widget.master.xhairs.moveto(widget, x, y)
