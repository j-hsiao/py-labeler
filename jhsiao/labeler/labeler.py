from __future__ import division
__all__ = ['Labeler']
import sys
if sys.version_info.major > 2:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import queue
else:
    import Queue as queue
    import Tkinter as tk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
import os
from collections import defaultdict
from functools import partial
import json
import pickle
from .data import Interpolator, restore_composites, extract_composites

import numpy as np

from .. import tkutil as tku

from .crosshairs import Crosshairs
from .bgim import BgIm
from ..labeleritems import ItemSelector, Item, ItemMenu
from .colorpicker import ColorPicker
from .dict import Dict
from .imset import ImageSet, filetypes

class LabelCanv(tk.Canvas, object):
    def __init__(self, *args, **kwargs):
        create = kwargs.pop('create', None)
        kwargs.setdefault('borderwidth', 0)
        kwargs.setdefault('highlightthickness', 0)
        super(LabelCanv, self).__init__(*args, **kwargs)
        self.zoom = 0
        self.zoomfactor = 2.0
        self.__create = create
        self.bgim = BgIm(self)
        self.crosshairs = Crosshairs(self)
        self.items = {}
        self.lastitem = None
        self.draginfo = None
        self.changed = False
        self._down = None
        self.menu = ItemMenu(self)
        tag = 'LabelCanv'
        tku.subclass(self, tag)
        if not self.bind_class(tag):
            tku.add_bindings(self, tag)

    def show(self, im):
        """Show an image."""
        # unzoom, then show
        antizoom = self.zoomfactor ** (-self.zoom)
        self.scale('Item', 0, 0, antizoom, antizoom)
        for item, info in self.items.values():
            item.rescale(self)
        self.zoom = 0
        self.bgim.show(self, im)
        self.master.frameinfo.zoomvar.set('100%')

    def create(self, x, y):
        """Create an item."""
        if self.__create is None:
            return
        else:
            self.changed = True
            x, y = self.xy(x, y)
            item = self.__create(self, x, y)
            color = self.master.sidepanel.colorpicker.color()
            item.recolor(self, color)
            self.tag_raise(self.crosshairs.TAG, item.idns[-1])
            self.items[item.idns[0]] = (
                item, self.master.sidepanel.new_dict())

    def syncinfo(self):
        """Sync dict info."""
        last = self.lastitem
        if last is not None:
            toup = self.items[last][1]
            self.changed = (
                self.master.sidepanel.change_dict(toup, toup)
                or self.changed)

    def unselect(self):
        """Clear lastitem."""
        self.syncinfo()
        self.lastitem = None

    def change_item(self):
        """Change the current focused item.

        Bring selected item forward. Update dict panel.
        """
        itemtag = Item.mastertag(self, 'current')
        self.tag_raise(itemtag, Item.TAGS[0])
        last = self.lastitem
        curitem = int(Item.getidn(itemtag))
        if last == curitem:
            return
        self.changed = self.master.sidepanel.change_dict(
            None if last is None else self.items[last][1],
            self.items[curitem][1]) or self.changed
        if self.master.sidepanel.dictmode.mode.get() == 'add':
            self.lastitem = None
        else:
            self.lastitem = curitem

    def delete(self, idn):
        """Remove an item (toplevel items only)."""
        thing, info = self.items.pop(idn)
        super(LabelCanv, self).delete(*thing.idns)
        if self.lastitem == idn:
            self.lastitem = None

    def data(self):
        """Return all the items currently drawn in creation order."""
        # neutralize zoom
        if self.zoom:
            antizoom = self.zoomfactor ** (-self.zoom)
            self.scale('Item', 0, 0, antizoom, antizoom)
            # Is Item.rescale necessary here?
        ret = []
        for idn, (item, info) in sorted(self.items.items()):
            d = item.todict(self)
            if info:
                d['info'] = info.copy()
            ret.append(d)
        if self.zoom:
            rezoom = self.zoomfactor ** self.zoom
            self.scale('Item', 0, 0, rezoom, rezoom)
        return ret

    def restore(self, info):
        """Restore items from info returned by data()."""
        items = self.items
        for k in list(items):
            self.delete(k)
        for iteminfo in info:
            item = Item.fromdict(self, iteminfo)
            items[item.idns[0]] = (item, iteminfo.get('info', {}))
        if info:
            self.tag_raise(self.crosshairs.TAG, 'Item')
        self.changed = False
        self.lastitem = None

    def xy(self, x, y):
        """Return canvas coords x,y."""
        return self.canvasx(x), self.canvasy(y)

    @tku.Bindings('<Enter>')
    @staticmethod
    def _mousein_autofocus(widget):
        """Focus on widget when mouse moves in."""
        widget.focus_set()

    @tku.Bindings(
        '<Control-n>', '<Control-p>',
        '<Control-N>', '<Control-P>')
    def _changeimset(widget, keysym):
        """Change to previous/next imageset."""
        #TODO: do the change in a thread?
        if keysym.lower() == 'n':
            widget.master.change_imset(1)
        else:
            widget.master.change_imset(-1)

    @tku.Bindings('<Control-space>', '<Control-Shift-space>')
    def _changeim(widget, state):
        stepsize = int(widget.master.frameinfo.stepsize.get())
        if state.Shift:
            widget.master.show(None, -stepsize)
        else:
            widget.master.show(None, stepsize)

    @tku.Bindings('<w>', '<W>', '<a>', '<A>', '<s>', '<S>', '<d>', '<D>')
    @staticmethod
    def _wasdmovemouse(widget, x, y, keysym, state):
        """WASD to move.

        With shift, move 1 pixel at a time
        Without, move scroll increments.
        When on edge, move the crosshairs/mouse instead.
        """
        if state.Control:
            # Control-s should not move canv.
            return
        k = keysym.lower()
        x1,y1, x2,y2 = map(int, widget.cget('scrollregion').split())
        if k in 'ad':
            func = widget.xview
            dim = x2-x1
            direction = -1 if k == 'a' else 1
            wdim = widget.winfo_width()
        else:
            func = widget.yview
            dim = y2-y1
            direction = -1 if k == 'w' else 1
            wdim = widget.winfo_height()
        if not state.Shift:
            direction *= max(1, wdim*.1)
        lo, hi = func()
        if (direction<0 and lo>0) or (direction>0 and hi<1):
            func('moveto', lo + direction/dim)
            widget.event_generate('<Motion>', x=x, y=y)
        else:
            if k in 'ad':
                widget.event_generate(
                    '<<ignored>>',
                    x=min(max(0, x+direction), wdim), y=y, warp=True)
            else:
                widget.event_generate(
                    '<<ignored>>',
                    x=x, y=min(max(0, y+direction), wdim), warp=True)

    @tku.Bindings('<MouseWheel>', '<Button-4>', '<Button-5>')
    def _scrollimage(widget, button, delta, x, y, state):
        """Mouse wheel to scroll up/down."""
        if delta is None:
            step = -1 if button == 4 else 1
        else:
            step = -1 if delta > 0 else 1
        if state.Shift:
            widget.xview('scroll', step, 'units')
        else:
            widget.yview('scroll', step, 'units')
        widget.event_generate('<Motion>', x=x, y=y)

    @tku.Bindings('<Control-MouseWheel>', '<Control-Button-4>', '<Control-Button-5>')
    def _zoominout(widget, button, delta, x, y):
        """Control+scroll to zoom in/out."""
        cx, cy = widget.xy(x, y)
        if delta is None:
            delta = 1 if button == 4 else -1
        else:
            delta = 1 if delta > 0 else -1
        widget.zoom += delta
        zoomfactor = widget.zoomfactor
        truezoom = zoomfactor ** widget.zoom
        if not widget.bgim.zoom(widget, truezoom):
            widget.zoom -= delta
            return
        widget.master.frameinfo.zoomvar.set('{:.2f}%'.format(truezoom*100))
        mult = zoomfactor ** delta
        widget.scale('Item', 0, 0, mult, mult)
        for item, info in widget.items.values():
            item.rescale(widget)
        x1,y1, x2,y2 = map(int, widget.cget('scrollregion').split())
        cx *= mult
        cy *= mult
        l, t = cx-x, cy-y
        widget.xview('moveto', l/(x2-x1))
        widget.yview('moveto', t/(y2-y1))
        widget.event_generate('<Motion>', x=x, y=y)

    @tku.Bindings('<Button-1>')
    @staticmethod
    def _clicked(widget, x, y):
        widget._down = x,y

    @tku.Bindings('<ButtonRelease-1>')
    @staticmethod
    def _dragged(widget, x, y):
        if widget._down is not None:
            widget.changed = ((x,y) != widget._down) or widget.changed
            widget._down = None

    @tku.Bindings('<q>')
    @staticmethod
    def _debugging(widget):
        master = widget.master
        interp = Interpolator(master.imset, master.labels)
        print('labels')
        print(master.labels)
        for i in range(len(master.imset)):
            print(i)
            print(interp.interpolate(i))


class CanvasFrame(tk.Frame, object):
    def __init__(self, master, *args, **kwargs):
        createfx = kwargs.pop('create', None)
        super(CanvasFrame, self).__init__(master, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canv = LabelCanv(master, *args, create=createfx, **kwargs)
        self.canv.grid(row=0, column=0, sticky='nsew', in_=self)

        self.scrollx = tk.Scrollbar(
            master, command=self.canv.xview, orient='horizontal')
        self.scrollx.grid(row=1, column=0, sticky='ew', in_=self)
        self.scrolly = tk.Scrollbar(
            master, command=self.canv.yview, orient='vertical')
        self.scrolly.grid(row=0, column=1, sticky='ns', in_=self)
        self.canv.configure(
            xscrollcommand=self.scrollx.set,
            yscrollcommand=self.scrolly.set)

class DictMode(tk.Frame, object):
    def __init__(self, *args, **kwargs):
        super(DictMode, self).__init__(*args, **kwargs)
        self.mode = tk.StringVar(self)
        self.label = tk.Label(self, text='dict mode:')
        self.label.grid(row=0, column=self.grid_size()[0])
        self.buttons = [
            tk.Radiobutton(self.master, variable=self.mode, value=mode, text=mode)
            for mode in ('add', 'copy', 'new')]
        self.mode.set('copy')
        for b in self.buttons:
            b.grid(row=0, column=self.grid_size()[0], in_=self)
        tag = 'DictModeBeginAdd'
        tku.subclass(self.buttons[0], tag)
        if not self.bind_class(tag):
            self._cleardict.bind(self, tag)

    # tracing the variable doesn't allow checking the original value
    @tku.Bindings('<Button-1>', '<space>')
    @staticmethod
    def _cleardict(widget):
        """Clear dict if changed to add mode.

        Do nothing if already in add mode.
        """
        sidepanel = widget.master
        if sidepanel.dictmode.mode.get() == 'add':
            return
        sidepanel.master.lcanv.unselect()
        sidepanel.dict.set({})

class SidePanel(tk.Frame, object):
    def __init__(self, *args, **kwargs):
        super(SidePanel, self).__init__(*args, **kwargs)
        self.grid_rowconfigure(0, weight=1, minsize=50)
        self.grid_columnconfigure(0, weight=1)
        self.selector = ItemSelector(self)
        self.selector.grid(row=0, column=0, sticky='nsew')
        self.colorpicker = ColorPicker(self)
        self.colorpicker.grid(row=self.grid_size()[1], column=0, sticky='nsew')
        self.dictmode = DictMode(self)
        self.dictmode.grid(row=self.grid_size()[1], column=0, sticky='nsew')
        self.dict = Dict(self)
        self.dict.grid(row=self.grid_size()[1], column=0, sticky='nsew')

    def new_dict(self):
        if self.dictmode.mode.get() == 'copy':
            return self.dict.get()
        else:
            return {}

    def change_dict(self, pre, post):
        """Change the dict when new item is selected.

        If in overwrite mode:
            ignore pre dict
            add/overwrite to post
        otherwise:
            update the pre dict
            sync with post
        """
        if self.dictmode.mode.get() == 'add':
            cur = self.dict.get()
            ret = any(k not in post or post[k] != cur[k] for k in cur)
            post.update(cur)
            return ret
        else:
            ret = False
            if pre is not None:
                cur = self.dict.get()
                ret = cur != pre
                for k in set(pre).difference(cur):
                    del pre[k]
                pre.update(cur)
            self.dict.set(post)
            return ret

class ScrollSidePanel(tku.Behavior, tk.Frame):
    """Container for a sidepanel."""
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        canv = tk.Canvas(self.master)
        canv.grid(row=0, column=0, in_ = self, sticky='nsew')
        window = tk.Frame(self.master)
        canv.create_window(0, 0, window=window, anchor='nw')
        self.panel = SidePanel(self.master)
        self.panel.grid(row=0, column=0, in_=window)
        scrolly = tk.Scrollbar(
            self.master, orient='vertical', command=canv.yview)
        scrolly.grid(row=0, column=1, in_=self, sticky='ns')
        canv.configure(yscrollcommand=scrolly.set)
        self.subs = (canv, window, scrolly)

        tag = 'ScrollSidePanelWindow'
        tku.subclass(window, tag)
        if not self.bind_class(tag):
            self.bind(self, tag)

    @tku.Bindings('<Configure>')
    @staticmethod
    def _update_scrollregion(widget):
        ssp = widget.master.scrollsidepanel
        canv = ssp.subs[0]
        canv.configure(
            scrollregion=canv.bbox('all'),
            width=ssp.panel.winfo_reqwidth(),
            height=ssp.panel.winfo_reqheight())

class InfoPanel(tk.Frame, object):
    def __init__(self, *args, **kwargs):
        super(InfoPanel, self).__init__(*args, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.frameinfo = tk.Frame(self)
        self.frameinfo.grid(row=0, column=0, sticky='nsew')
        self.frameset = tk.Label(self.frameinfo)
        self.framesep = tk.Label(self.frameinfo, text=' : ')
        self.framename = tk.Label(self.frameinfo)
        self.frameset.grid(
            row=0, column=self.frameinfo.grid_size()[0], sticky='nsew')
        self.frameinfo.grid_columnconfigure(
            self.frameinfo.grid_size()[0]-1, weight=1)
        self.framesep.grid(
            row=0, column=self.frameinfo.grid_size()[0], sticky='nsew')
        self.framename.grid(
            row=0, column=self.frameinfo.grid_size()[0], sticky='nsew')
        self.frameinfo.grid_columnconfigure(
            self.frameinfo.grid_size()[0]-1, weight=1)
        self.zoomvar = tk.StringVar(self)
        self.zoomvar.set('100%')
        self.zoomlabel = tk.Label(self.frameinfo, text='zoom: ')
        self.zoomlabel.grid(
            row=0, column=self.frameinfo.grid_size()[0], sticky='nsew')
        self.zoomtxt = tk.Label(self.frameinfo, textvariable=self.zoomvar)
        self.zoomtxt.grid(
            row=0, column=self.frameinfo.grid_size()[0], sticky='nsew')

        self.frametransition = tk.Frame(self)
        self.frametransition.grid(row=self.grid_size()[1], column=0, sticky='nsew')
        self.transitionmode = tk.StringVar(self)
        self.transitionlabel = tk.Label(
            self.frametransition, text='frame transition mode:')
        self.transitionmodes = [
            tk.Radiobutton(
                self.frametransition,
                text=mode,
                value=mode,
                variable=self.transitionmode)
            for mode in ('clear', 'copy', 'interpolate', 'extrapolate')]
        self.transitionlabel.grid(row=0, column=0)
        for button in self.transitionmodes:
            button.grid(row=0, column=self.frametransition.grid_size()[0])
        self.transitionmode.set('clear')

        self.stepframe = tk.Frame(self)
        self.stepframe.grid(row=self.grid_size()[1], column=0, sticky='nsew')
        self.steplabel = tk.Label(self.stepframe, text='frame stepsize: ')
        self.steplabel.grid(row=0, column=self.stepframe.grid_size()[0])
        self.stepsize = tk.Spinbox(self.stepframe, validate='all')
        self.stepsize.grid(row=0, column=self.stepframe.grid_size()[0])
        self.stepsize.insert(0, '1')
        self.stepsize.configure(
            {'from': 1},
            to='inf', increment=1,
            validatecommand=tku.ValSubs.make_script_(
                self.stepsize, self._validate_stepsize),
            invalidcommand=tku.ValSubs.make_script_(
                self.stepsize, self._invalid_stepsize))

    @staticmethod
    def _validate_stepsize(widget, pending, valtype):
        if pending:
            try:
                v = int(pending)
            except ValueError:
                return False
            else:
                return v>=1
        elif valtype == 'focusout':
            widget.insert(0, '1')
            widget.configure(validate='all')
        return True

    @staticmethod
    def _invalid_stepsize(widget):
        widget.bell()

class Labeler(tk.Tk, object):
    def __init__(self, *args, **kwargs):
        super(Labeler, self).__init__(*args, **kwargs)
        self.changed = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scrollsidepanel = ScrollSidePanel(self, bd=3, relief='raised')
        self.scrollsidepanel.grid(row=0, column=1, sticky='nsew', rowspan=2)
        self.sidepanel = self.scrollsidepanel.panel

        self.cframe = CanvasFrame(
            self, create=self.sidepanel.selector.create,
            bd=3, relief='raised')
        self.cframe.grid(row=0, column=0, sticky='nsew')
        self.lcanv = self.cframe.canv

        self.frameinfo = InfoPanel(self, bd=3, relief='raised')
        self.frameinfo.grid(row=1, column=0, sticky='nsew')

        tku.add_bindings(self)
        self._labelname = None
        self.imset = None

        self.labels = {}
        self._showq = queue.Queue()
        self._showname = str(id(self._show.__func__))+'_show'
        self.createcommand(self._showname, self._show)

        self.lcanv.focus_set()

    def _show_callback(self, imname, frame):
        self._showq.put((imname, frame))
        self.tk.call('after', 'idle', self._showname)

    def _show(self):
        try:
            name, im = self._showq.get()
        except Exception:
            return
        if im is None:
            messagebox.showerror(
                title='Error',
                message='Failed to load image {}.'.format(name))
            return
        self.frameinfo.framename.configure(text=name)
        self.lcanv.show(im)
        labels = self.labels.get(name, None)
        if labels is None:
            mode = self.frameinfo.transitionmode.get()
            if mode == 'clear':
                self.lcanv.restore([])
            elif mode == 'copy':
                self.lcanv.changed = True
            else:
                data = Interpolator(self.imset, self.labels).interpolate(
                    name, extrapolate=mode=='extrapolate')
                self.lcanv.restore(data)
                if data:
                    self.lcanv.changed = True
        else:
            self.lcanv.restore(labels)

    def show(self, k=None, offset=0):
        self.lcanv.unselect()
        self._update_labels()
        self.imset(k, offset, self._show_callback)

#        try:
#            name, im = self.imset(k)
#        except Exception:
#            return
#        if im is None:
#            messagebox.showerror(
#                title='Error',
#                message='Failed to load image {}.'.format(name))
#            return
#        self.frameinfo.framename.configure(text=name)
#        self.lcanv.show(im)
#        labels = self.labels.get(name, None)
#        if labels is None:
#            mode = self.frameinfo.transitionmode.get()
#            if mode == 'clear':
#                self.lcanv.restore([])
#            elif mode == 'copy':
#                self.lcanv.changed = True
#            else:
#                data = Interpolator(self.imset, self.labels).interpolate(
#                    name, extrapolate=mode=='extrapolate')
#                self.lcanv.restore(data)
#                if data:
#                    self.lcanv.changed = True
#        else:
#            self.lcanv.restore(labels)


    def change_imset(self, offset):
        self.lcanv.syncinfo()
        if self._canceled_save():
            return
        self.labels = {}
        self.imset = self.imset.next(offset)
        self.frameinfo.frameset.configure(text=self.imset.path)
        self.show()

    @tku.Bindings('<Control-o>', '<Control-O>')
    def open_file(self):
        kwargs = {}
        if self.imset is not None:
            kwargs['initialdir'] = self.imset.dir
            kwargs['initialfile'] = self.imset.name
        fnames = filedialog.askopenfilename(
            title='Open Image File.',
            filetypes=filetypes(),
            multiple=True,
            **kwargs)
        if fnames:
            if len(fnames) == 1:
                fnames = fnames[0]
            self.imset = ImageSet.open(fnames)
            self.frameinfo.frameset.configure(text=self.imset.path)
            self.show()

    @tku.Bindings('<Control-Shift-o>', '<Control-Shift-O>')
    def open_dir(self):
        kwargs = {}
        if self.imset is not None:
            kwargs['initialdir'] = self.imset.dir
        dname = filedialog.askdirectory(
            title='Open Image Directory.',
            mustexist=True, **kwargs)
        if dname:
            self.imset = ImageSet.open(dname)
            self.frameinfo.frameset.configure(text=self.imset.path)
            self.show()

    @staticmethod
    def _getoraddidx(lst, item):
        """Get index of item or add to list and return last idx."""
        try:
            return lst.index(item)
        except ValueError:
            ret = len(lst)
            lst.append(item)
            return ret

    @tku.Bindings(
        '<Control-S>', '<Control-s>',
        '<Control-Shift-S>', '<Control-Shift-s>')
    def save(self, state=None):
        """Save the labels."""
        kwargs = dict(
            title='Save as...',
            filetypes=(('json', '*.json'), ('python pickle', '*.pkl'))
        )
        if self._labelname:
            dname, bname = os.path.split(self._labelname)
            kwargs['initialdir'] = dname
            if state is None or not state.Shift:
                kwargs['title'] = 'Save...'
                kwargs['initialfile'] = bname
        fname = filedialog.asksaveasfilename(**kwargs)
        while fname:
            if self.lcanv.changed:
                curframename = self.frameinfo.framename.cget('text')
                if curframename:
                    self.labels[curframename] = self.lcanv.data()
                self.lcanv.changed = False
            base, ext = os.path.splitext(fname)
            composites = extract_composites(self.labels)
            data = dict(composites=composites, labels=self.labels)
            if ext == '.json':
                with open(fname, 'w') as f:
                    json.dump(data, f, indent=1)
            elif ext == '.pkl':
                with open(fname, 'wb') as f:
                    pickle.dump(data, f)
            else:
                messagebox.showerror(message='Unknown file type "{}"'.format(ext))
                fname = filedialog.asksaveasfilename(**kwargs)
                continue
            self.changed = False
            self._labelname = fname
            return


    @tku.Bindings('<Control-l>', '<Control-L>')
    def load(self):
        """load labels."""
        kwargs = dict(
            title='Load labels...',
            filetypes=(('json', '*.json'), ('python pickle', '*.pkl'))
        )
        if self._labelname:
            dname, bname = os.path.split(self._labelname)
            kwargs['initialdir'] = dname
        fname = filedialog.askopenfilename(**kwargs)
        if fname:
            self.lcanv.unselect()
            if self._canceled_save():
                return
            base, ext = os.path.splitext(fname)
            if ext == '.json':
                with open(fname, 'r') as f:
                    data = json.load(f)
            elif ext == '.pkl':
                with open(fname, 'rb') as f:
                    data = pickle.load(f)
            else:
                messagebox.showerror('Unknown file type "{}"'.format(ext))
                return
            self.labels = data['labels']
            restore_composites(data['composites'])
            self.sidepanel.selector.resync()
            curframe = self.frameinfo.framename.cget('text')
            data = self.labels.get(curframe)
            if data is None:
                self.lcanv.restore([])
            else:
                self.lcanv.restore(data)
            self.changed = False
            self._labelname = fname

    @tku.Bindings('<Control-r>', '<Control-R>')
    def _resync(self):
        if self.imset is not None:
            self.imset.resync()
            self.show()

    def _update_labels(self):
        """Update labels with canv changes."""
        if self.lcanv.changed:
            oldname = self.frameinfo.framename.cget('text')
            data = self.lcanv.data()
            if data and oldname:
                self.labels[oldname] = data
            else:
                self.labels.pop(oldname, None)
            self.changed = bool(oldname) or self.changed
            self.lcanv.changed = False

    def _canceled_save(self):
        """True if canceled, else False."""
        self._update_labels()
        if self.changed:
            if not messagebox.askesno(message='Save changes?'):
                # don't save, just discard
                return False
            self.save()
            if self.changed and messagebox.askyesno(
                    message='Not saved, discard changes?'):
                return False
        return self.changed


    @tku.Bindings('<Shift-Escape>')
    def destroy(self):
        self.lcanv.unselect()
        if self._canceled_save():
            return
        super(Labeler, self).destroy()

    # TODO
    # menu
    # interpolation
