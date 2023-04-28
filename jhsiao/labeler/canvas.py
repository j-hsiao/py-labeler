from jhsiao.tkutil import tk, add_bindtags
from . import bindings
from .objs import Crosshairs, BGImage, Obj
from .selector import ObjSelector
from .dict import Dict
from .color import ColorPicker

class LCanv(tk.Frame, object):
    canvbinds = bindings['LCanv.canv']
    def __init__(self, master, *args, **kwargs):
        super(LCanv, self).__init__(master, *args, **kwargs)
        self._changed = False
        self.objid = None
        self.info = {}
        self.cframe = tk.Frame(self)
        self.canv = tk.Canvas(self, border=0, highlightthickness=0)
        self.yscroll = tk.Scrollbar(orient='vertical', command=self.yview)
        self.xscroll = tk.Scrollbar(orient='horizontal', command=self.xview)
        self.canv.configure(
            xscrollcommand=self.xscroll.set, yscrollcommand=self.yscroll.set)
        add_bindtags(self.canv, 'LCanv.canv')
        self.bgim = BGImage(self.canv)
        self.xhairs = Crosshairs(self.canv)
        self.selector = ObjSelector(self, border=2, relief='sunken')
        self.colorpicker = ColorPicker(self, border=2, relief='raised')
        self.infoframe = tk.Frame(self, border=2, relief='sunken')
        self._dict = Dict(self.infoframe)
        self.iteminfolabel = tk.Label(self.infoframe, text='Object info')

        self.selector.grid(row=0, column=1, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.colorpicker.grid(row=1, column=1, sticky='nsew')
        self.grid_rowconfigure(1, minsize=50)
        self.infoframe.grid(row=2, column=1, sticky='nsew')
        self.grid_rowconfigure(2, weight=1)
        self.infoframe.grid_rowconfigure(1, weight=1)
        self.infoframe.grid_columnconfigure(0, weight=1)
        self.iteminfolabel.grid(row=0, column=0, sticky='nsew')
        self._dict.grid(row=1, column=0, sticky='nsew')
        self.cframe.grid(row=0, column=0, sticky='nsew', rowspan=self.grid_size()[1])
        self.canv.grid(row=0, column=0, sticky='nsew', in_=self.cframe)
        self.xscroll.grid(row=1, column=0, sticky='nsew', in_=self.cframe)
        self.yscroll.grid(row=0, column=1, sticky='nsew', in_=self.cframe)
        self.cframe.grid_columnconfigure(0, weight=1)
        self.cframe.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        bindings.apply(self.canv, methods=['tag_bind'], create=False)

    def xview(self, *args):
        ret = self.canv.xview(*args)
        self.bgim.roi(self.canv)
        return ret

    def yview(self, *args):
        ret = self.canv.yview(*args)
        self.bgim.roi(self.canv)
        return ret

    def show(self, im):
        return self.bgim.show(self.canv, im)

    def set_obj(self, idn):
        if idn != self.objid:
            if self.objid is not None:
                self.info[self.objid] = self._dict.dict()
            self.objid = idn
            self._dict.set(self.info.get(self.objid, {}))
            self.canv.focus_set()

    canvbinds.bind('<B1-Leave>', '<B1-Enter>')(' ')

    @staticmethod
    @canvbinds.bind('<Enter>')
    def _entered(widget):
        Crosshairs.show(widget)
        widget.focus_set()

    @staticmethod
    @canvbinds.bind('<Delete>')
    def _remove(widget):
        self = widget.master
        if self.objid is not None:
            self._dict.set({})
            self.canv.focus_set()
            self.info.pop(self.objid, None)
            widget.delete(Obj.toptag(widget, self.objid))
            self.objid = None

    @staticmethod
    @canvbinds.bind('<h>', '<H>')
    def _toggle_crosshairs(widget):
        if widget.itemcget('Crosshairs', 'state') == 'hidden':
            Crosshairs.show(widget)
        else:
            Crosshairs.hide(widget)

    @staticmethod
    @canvbinds.bind('<B>', '<b>')
    def _sendtoback(widget):
        self = widget.master
        if self.objid is not None:
            widget.tag_lower(Obj.toptag(widget, self.objid), 'Obj')

    @staticmethod
    @canvbinds.bind('<W>', '<w>', '<A>', '<a>', '<S>', '<s>', '<D>', '<d>')
    def _moveleft(widget, x, y, keysym):
        dif = dict(w=(0,-1), a=(-1,0), s=(0,1), d=(1,0))
        dx, dy = dif[keysym.lower()]
        widget.event_generate('<Motion>', x=x+dx, y=y+dy, when='tail', warp=True)

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

    @staticmethod
    @canvbinds.bind('<Configure>')
    def _configured(widget):
        widget.master.bgim.roi(widget)
