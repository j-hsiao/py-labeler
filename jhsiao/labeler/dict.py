"""Widget that represents a dict."""
import ast

from . import bindings

from jhsiao.tkutil import tk

class DictItem(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super(DictItem, self).__init__(master, *args, **kwargs)
        self.key = tk.Entry(self)
        self.value = tk.Entry(self)
        self.rm = tk.Button(self, text='x')
        self.rm.bindtags(('DictItemRm',) + self.rm.bindtags())
        self.key.bindtags(('DictItemEntry',) + self.key.bindtags())
        self.value.bindtags(('DictItemEntry',) + self.value.bindtags())

    @bindings['DictItemEntry'].bind('<Return>')
    def _newitem(widget):
        cur_row = widget.master.grid_info()['row']
        dct = widget.master.get_dict()
        belows = []
        for v in dct.dframe.children.values():
            r = v.grid_info()['row']
            if r > cur_row:
                v.grid(row=r+1, column=0)

    def get_dict(self):
        """Get owning Dict instance."""
        return self.master.master

    @bindings['DictItemRm'].bind('<<Invoke>>')
    def _rm(widget):
        dct = widget.master.get_dict()
        widget.master.destroy()
        dct.rescroll()

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
        self.key.delete(0, 'end')
        self.value.delete(0, 'end')
        self.key.insert(0, repr(key))
        self.value.insert(0, repr(val))


class Dict(tk.Frame):
    binds = bindings['Dict']
    def __init__(self, master, *args, **kwargs):
        self.scrollcanv = tk.Canvas(self, highlightthickness=0, border=0)
        self.scroll = tk.Scrollbar(self, command=self.scrollcanv.yview, orient='vertical')
        self.scroll.grid(row=0, column=1)
        self.scrollcanv.configure(yscrollcommand=self.scroll.set)
        self.scrollcanv.grid(row=0, column=0)
        self.dframe = tk.Frame(self)
        self.dwindow = self.scrollcanv.create_window(0, 0, anchor='nw')

    def rescroll(self):
        self.scrollcanv.configure(
            scrollregion=self.scrollcanv.bbox(self.dwindow))

    def _items(self):
        for k, v in self.dframe.children:

    def add_item(self, idx=None):
        if idx is None:
            cols, rows = self.dframe.grid_size()
            idx = rows + 1
        d = DictItem(self.dframe)
        d.grid(column = 0, row=idx)
