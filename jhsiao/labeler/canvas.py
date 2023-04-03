from . import tk

from jhsiao.tkutil import bindings
from ..labeleritems import bindings as itembindings


binds = Bindings['LabelerCanv']


class LabelerCanvas(tk.Canvas, object):
    def __init__(self, master, *args, **kwargs):
        super(Canvas, self).__init__(master, *args, **kwargs)
        self.bindtags(self.bindtags() + ('LabelerCanv',))
        itembindings.apply(self)
