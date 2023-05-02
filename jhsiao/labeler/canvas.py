from __future__ import print_function
from jhsiao.tkutil import tk, add_bindtags
from . import bindings
from .objs import Crosshairs, BGImage, Obj
from .selector import ObjSelector
from .dict import Dict
from .color import ColorPicker
import copy

class CanvInfo(tk.Frame, object):
    def __init__(self, *args, **kwargs):
        super(CanvInfo, self).__init__(*args, **kwargs)
        self.lxy = tk.Label(self, text='x, y:')
        self.lzoom = tk.Label(self, text='zoom:')
        self.xy = tk.Label(self, text='y')
        self.zoom = tk.Label(self, text='tit%')

        for col, l in enumerate((
                self.lxy, self.xy, None, self.lzoom, self.zoom)):
            if l is None:
                self.grid_columnconfigure(col, weight=1)
            else:
                l.grid(row=0, column=col, sticky='nsew')

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
        self.cinfo = CanvInfo(self)

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
        self.cinfo.grid(
            row=2, column=0, sticky='nsew',
            in_=self.cframe, columnspan=2)
        self.cframe.grid_columnconfigure(0, weight=1)
        self.cframe.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        bindings.apply(self.canv, methods=['tag_bind'], create=False)

    def info(self):
        """Get the current info."""
        canv = self.canv
        selector = self.selector
        ret = {}
        classinfo = ret['classinfo'] = {
            k: copy.deepcopy(dict(v))
            for k, v in selector.classinfo.items()}
        data = data['data'] = {}
        for idn in Obj.tops(canv):
            cls, idn2 = Obj.parsetag(Obj.toptag(canv, idn))
            if idn != idn2:
                print('Warning, object ids do not match')
            try:
                lst = data[cls]
            except KeyError:
                lst = data[cls] = []
            lst.append(
                Obj.classes[cls].todict(canv, idn, classinfo[cls]))
        return ret

    def xview(self, *args):
        ret = self.canv.xview(*args)
        self.bgim.roi(self.canv)
        return ret

    def yview(self, *args):
        ret = self.canv.yview(*args)
        self.bgim.roi(self.canv)
        return ret

    def show(self, im):
        self.cinfo.zoom.configure(text='100%')
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
    @canvbinds.bind('<C>', '<c>')
    def _recolor_obj(widget):
        self = widget.master
        if self.objid is not None:
            clsname, idn = Obj.parsetag(Obj.toptag(widget, self.objid))
            Obj.classes[clsname].recolor(
                widget, self.colorpicker.color(), self.objid)

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
        widget.master.cinfo.xy.configure(
            text='{:3d}, {:3d}'.format(
                int(widget.canvasx(x)),
                int(widget.canvasy(y))))

    @staticmethod
    @canvbinds.bind('<B1-Motion>')
    def _modified(widget, x, y):
        self = widget.master
        if not self._changed:
            self._changed = True
        self._movexhairs(widget, x, y)

    @staticmethod
    @canvbinds.bind('<Configure>')
    def _configured(widget):
        widget.master.bgim.roi(widget)

    #------------------------------
    # scrolling
    #------------------------------
    @staticmethod
    @canvbinds.bind('<Button-4>')
    def _scrollup(widget, x, y):
        widget.master._scrollupdown(widget, 1, x, y)

    @staticmethod
    @canvbinds.bind('<Button-5>')
    def _scrolldown(widget, x, y):
        widget.master._scrollupdown(widget, -1, x, y)

    @staticmethod
    @canvbinds.bind('<MouseWheel>')
    def _scrollupdown(widget, delta, x, y):
        if widget.yview() == (0,1):
            # prevent scrolling when fully visible
            return
        self = widget.master
        if delta > 0:
            self.yview('scroll', -1, 'units')
        else:
            self.yview('scroll', 1, 'units')
        self._movexhairs(widget, x, y)

    @staticmethod
    @canvbinds.bind('<Shift-Button-4>')
    def _scrollleft(widget, x, y):
        widget.master._scrollleftright(widget, 1, x, y)

    @staticmethod
    @canvbinds.bind('<Shift-Button-5>')
    def _scrollright(widget, x, y):
        widget.master._scrollleftright(widget, -1, x, y)

    @staticmethod
    @canvbinds.bind('<Shift-MouseWheel>')
    def _scrollleftright(widget, delta, x, y):
        if widget.xview() == (0,1):
            # prevent scrolling when fully visible
            return
        self = widget.master
        if delta > 0:
            self.xview('scroll', -1, 'units')
        else:
            self.xview('scroll', 1, 'units')
        self._movexhairs(widget, x, y)

    #------------------------------
    # zooming
    #------------------------------
    @staticmethod
    @canvbinds.bind('<Control-Button-4>')
    def _zoomin(widget, x, y):
        widget.master._zoominout(widget, 1, x, y)

    @staticmethod
    @canvbinds.bind('<Control-Button-5>')
    def _zoomout(widget, x, y):
        widget.master._zoominout(widget, -1, x, y)

    @staticmethod
    @canvbinds.bind('<Control-MouseWheel>')
    def _zoominout(widget, delta, x, y):
        scrollw, scrollh = map(int, widget.cget('scrollregion').split()[2:])
        self = widget.master
        rawim = self.bgim.raw
        curfx = scrollw/rawim.width
        curfy = scrollh/rawim.height
        if delta > 0:
            factor = (round(curfx*10)+1)/10
        else:
            factor = (round(curfx*10)-1)/10
        factor = max(factor, .1)
        widget.master._set_zoom(
            factor*rawim.width / scrollw,
            factor*rawim.height / scrollh, x, y)

    @staticmethod
    @canvbinds.bind('<R>', '<r>')
    def _reset_zoom(widget, x, y):
        scrollw, scrollh = map(int, widget.cget('scrollregion').split()[2:])
        self = widget.master
        rawim = self.bgim.raw
        self._set_zoom(rawim.width/scrollw, rawim.height/scrollh, x, y)

    def _set_zoom(self, factorx, factory, x, y):
        canv = self.canv
        scrollw, scrollh = map(int, canv.cget('scrollregion').split()[2:])
        cx, cy = canv.canvasx(x), canv.canvasy(y)
        fx, fy = cx/scrollw, cy/scrollh
        ww, wh = canv.winfo_width(), canv.winfo_height()

        nw = max(int(factorx * scrollw), 1)
        nh = max(int(factory * scrollh), 1)
        canv.configure(scrollregion=(0, 0, nw, nh))

        nx = fx * nw
        ny = fy * nh
        lx = max(nx - x, 0)
        ty = max(ny - y, 0)
        canv.xview('moveto', lx/nw)
        canv.yview('moveto', ty/nh)
        self.bgim.roi(canv)
        self._movexhairs(canv, x, y)
        self.cinfo.zoom.configure(
            text='{:3d}%'.format(int(100*nw/self.bgim.raw.width)))

        factors = nw/scrollw, nh/scrollh
        for idn in canv.find('withtag', 'Obj'):
            tp = canv.type(idn)
            coords = canv.coords(idn)
            if tp == 'oval' and 'Point' in canv.gettags(idn):
                l, t, r, b = coords
                cx, cy = 0.5*(l+r), 0.5*(t+b)
                ncx, ncy = factors[0]*cx, factors[1]*cy
                dx, dy = ncx-cx, ncy-cy
                canv.coords(idn, l+dx, t+dy, r+dx, b+dy)
            else:
                canv.coords(
                    idn, *[factors[i%2] * c for i, c in enumerate(coords)])

