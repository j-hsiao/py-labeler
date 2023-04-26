"""Widget that represents a dict."""
from __future__ import division
import ast

from . import bindings

from jhsiao.tkutil import tk, add_bindtags

class DictItem(tk.Frame):
    ebinds = bindings['DictItemEntry']
    def __init__(self, master, *args, **kwargs):
        super(DictItem, self).__init__(master, *args, **kwargs)
        self.key = tk.Entry(self)
        self.value = tk.Entry(self)
        self.rm = tk.Button(self, text='x')
        add_bindtags(self.rm, 'DictItemSub', 'DictItemRm')
        add_bindtags(self.key, 'DictItemSub', 'DictItemEntry')
        add_bindtags(self.value, 'DictItemSub', 'DictItemEntry')
        self.key.grid(row=0, column=0, sticky='nsew')
        self.value.grid(row=0, column=1, sticky='nsew')
        self.rm.grid(row=0, column=2)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def clear(self):
        self.key.delete(0, 'end')
        self.value.delete(0, 'end')

    def get(self):
        """Get key,value of DictItem.

        None if all empty.
        """
        key = self.key.get()
        val = self.value.get()
        if not key and not val:
            return None
        try:
            key = ast.literal_eval(key)
        except Exception:
            pass
        try:
            val = ast.literal_eval(val)
        except Exception:
            pass
        return key, val

    def set(self, key, val):
        """Set key,val of DictItem."""
        self.clear()
        self.key.insert(0, repr(key))
        self.value.insert(0, repr(val))

    @staticmethod
    @bindings['DictItemSub'].bind('<MouseWheel>')
    def _escrolled(widget, delta):
        canv = widget.master.master.master
        if delta > 0:
            if canv.yview()[0] != 0:
                canv.yview('scroll', -1, 'u')
        else:
            if canv.yview()[1] != 1:
                canv.yview('scroll', 1, 'u')

    @staticmethod
    @bindings['DictItemSub'].bind('<Button-4>')
    def _escrollup(widget):
        canv = widget.master.master.master
        if canv.yview()[0] != 0:
            canv.yview('scroll', -1, 'u')

    @staticmethod
    @bindings['DictItemSub'].bind('<Button-5>')
    def _escrolldown(widget):
        canv = widget.master.master.master
        if canv.yview()[1] != 1:
            canv.yview('scroll', 1, 'u')

    @staticmethod
    @ebinds.bind('<Return>')
    def _newitem(widget):
        cur_row = widget.master.grid_info()['row']
        dct = widget.master.master.master.master
        dct.add_item(cur_row+1)

    @staticmethod
    @ebinds.bind('<Control-BackSpace>', '<Shift-BackSpace>')
    def _krm(widget):
        row = widget.master.grid_info()['row']
        dct = widget.master.master.master.master
        dct.rm_item(row)

    @staticmethod
    @ebinds.bind('<Control-n>', '<Control-N>', '<Down>')
    def _nxtline(widget):
        row = widget.master.grid_info()['row']
        dframe = widget.master.master
        rows = dframe.grid_size()[1]
        newrow = row+1
        if newrow == rows:
            newrow = 0
        dframe.grid_slaves(row=newrow)[0].key.focus_set()
        dframe.master.master.show(newrow)

    @staticmethod
    @ebinds.bind('<Control-p>', '<Control-P>', '<Up>')
    def _prevline(widget):
        row = widget.master.grid_info()['row']
        dframe = widget.master.master
        newrow = row-1
        if newrow < 0:
            newrow = dframe.grid_size()[1]-1
        dframe.grid_slaves(row=newrow)[0].key.focus_set()
        dframe.master.master.show(newrow)

    @staticmethod
    @ebinds.bind('<Tab>', dobreak=True)
    def _nxt(widget):
        if widget.grid_info()['column'] == 0:
            widget.master.value.focus_set()
        else:
            row = widget.master.grid_info()['row']
            dframe = widget.master.master
            rows = dframe.grid_size()[1]
            nxt = row+1
            if nxt == rows:
                dframe.grid_slaves(row=0)[0].key.focus_set()
            else:
                dframe.grid_slaves(row=nxt)[0].key.focus_set()
        return 'break'

    @staticmethod
    @ebinds.bind('<Shift-Tab>', dobreak=True)
    def _prev(widget):
        if widget.grid_info()['column'] == 0:
            row = widget.master.grid_info()['row']
            dframe = widget.master.master
            if row:
                dframe.grid_slaves(row=row-1)[0].value.focus_set()
            else:
                dframe.grid_slaves(row=dframe.grid_size()[1]-1)[0].value.focus_set()
        else:
            widget.master.key.focus_set()
        return 'break'

    @staticmethod
    @bindings['DictItemRm'].bind('<ButtonRelease-1>', '<space>', '<Return>')
    def _rm(widget):
        item = widget.master
        row = item.grid_info()['row']
        dct = item.master.master.master
        dct.rm_item(row)

class Dict(tk.Frame):
    binds = bindings['Dict']
    def __init__(self, master, *args, **kwargs):
        super(Dict, self).__init__(master, *args, **kwargs)
        self.scrollcanv = tk.Canvas(self, highlightthickness=0, border=0)
        self.scroll = tk.Scrollbar(self, command=self.scrollcanv.yview, orient='vertical')
        self.scrollcanv.configure(yscrollcommand=self.scroll.set)
        self.dframe = tk.Frame(self.scrollcanv, background='purple')
        self.dwindow = self.scrollcanv.create_window(
            0, 0, anchor='nw', window=self.dframe)
        self.add_item()
        add_bindtags(self.dframe, 'DictFrame')
        add_bindtags(self.scrollcanv, 'DictCanv')
        self.addbutton = tk.Button(self, text='+')
        self.klabel = tk.Label(self, text='keys')
        self.vlabel = tk.Label(self, text='values')
        add_bindtags(self.addbutton, 'DictPlus')

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.klabel.grid(row=0, column=0, sticky='nsew')
        self.vlabel.grid(row=0, column=1, sticky='nsew')
        self.scrollcanv.grid(row=1, column=0, sticky='nsew', columnspan=2)
        self.scroll.grid(row=0, column=2, sticky='ns', rowspan=2)
        self.addbutton.grid(row=2, column=0, sticky='ew', columnspan=2)

    def dict(self):
        ret = {}
        for item in self.dframe.children.values():
            i = item.get()
            if i is not None:
                ret[i[0]] = i[1]
        return ret

    def set(self, dct):
        """Set the DictItem entries to the values of the `dct`."""
        nitems = len(dct)
        cur = self.dframe.grid_size()[1]
        if nitems > cur:
            for i in range(nitems-cur):
                self.add_item()
        else:
            for i in range(cur-nitems):
                self.rm_item()
        for i, (k, v) in enumerate(dct.items()):
            self.dframe.grid_slaves(row=i)[0].set(k, v)

    def add_item(self, idx=None):
        """Add a new dict item and set focus."""
        rows = self.dframe.grid_size()[1]
        if idx is None:
            idx = rows
        d = DictItem(self.dframe)
        for row in range(rows, idx, -1):
            self.dframe.grid_slaves(row=row-1)[0].grid(
                row=row, column=0, sticky='ew')
        d.grid(column=0, row=idx, sticky='ew')
        d.key.focus_set()
        if rows:
            self.update_idletasks()
            self.show(idx)

    def rm_item(self, idx=None):
        """Remove an item."""
        rows = self.dframe.grid_size()[1]
        if rows == 1:
            item = self.dframe.grid_slaves(row=0)[0]
            item.clear()
            item.key.focus_set()
            return
        if idx is None:
            idx = rows-1
        self.dframe.grid_slaves(row=idx)[0].destroy()
        for r in range(idx+1, rows):
            self.dframe.grid_slaves(row=r)[0].grid(
                row=r-1, column=0, sticky='ew')
        self.dframe.grid_slaves(row=max(0, idx-1))[0].key.focus_set()

    def show(self, idx):
        """Scroll to show idxth item."""
        lo, hi = self.scrollcanv.yview()
        nrows = self.dframe.grid_size()[1]
        if idx / nrows < lo:
            self.scrollcanv.yview('moveto', idx / nrows)
        elif hi < (idx+1)/nrows:
            self.scrollcanv.yview('moveto', lo + ((idx+1) / nrows - hi))

    @staticmethod
    @bindings['DictFrame'].bind('<Configure>')
    def _rescroll(widget, width, height):
        widget.master.configure(scrollregion=(0, 0, width, height))

    @staticmethod
    @bindings['DictCanv'].bind('<Configure>')
    def _resized(widget, width):
        widget.master.dframe.grid_columnconfigure(0, minsize=width)

    @staticmethod
    @bindings['DictPlus'].bind('<ButtonRelease-1>', '<Return>', '<space>')
    def _dplus(widget):
        widget.master.add_item()
