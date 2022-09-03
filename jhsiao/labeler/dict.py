"""Widget that represents key:value pairs."""
__all__ = ['Dict']
import ast
import sys
if sys.version_info.major > 2:
    import tkinter as tk
else:
    import Tkinter as tk
from .. import tkutil as tku

class DictEntry(tk.Frame, object):
    def __init__(self, *args, **kwargs):
        super(DictEntry, self).__init__(*args, **kwargs)
        self.rm = tk.Button(self, text='x', takefocus=False)
        self.keyl = tk.Label(self, text='key:')
        self.key = tk.Entry(self)
        self.valuel = tk.Label(self, text='val:')
        self.value = tk.Entry(self)

        self.rm.grid(row=0, column=self.grid_size()[0], sticky='nsew')
        self.keyl.grid(row=0, column=self.grid_size()[0], sticky='nsew')
        self.key.grid(row=0, column=self.grid_size()[0], sticky='nsew')
        self.grid_columnconfigure(self.grid_size()[0]-1, weight=1)
        self.valuel.grid(row=0, column=self.grid_size()[0], sticky='nsew')
        self.value.grid(
            row=0, column=self.grid_size()[0],
            sticky='nsew', padx=(0,5))
        self.grid_columnconfigure(self.grid_size()[0]-1, weight=1)
        script = tku.EvSubs.make_script_(
            self, self._remove, subs=dict(widget=(str(self), None)))
        self.rm.configure(command=script)
        tag = 'DictInput'
        tku.subclass(self.key, tag)
        tku.subclass(self.value, tag)
        if not self.bind_class(tag):
            tku.add_bindings(self, tag)

    def get(self):
        """Retrieve key/value pair."""
        key = self.key.get()
        val = self.value.get()
        if key or val:
            try:
                key = ast.literal_eval(key)
            except Exception:
                pass
            try:
                val = ast.literal_eval(val)
            except Exception:
                pass
            return key, val
        return None

    def set(self, k, v):
        """Set the key/value pair."""
        for item, widget in zip((k,v), (self.key, self.value)):
            widget.delete(0, 'end')
            widget.insert(0, repr(item))

    def clear(self):
        self.key.delete(0, 'end')
        self.value.delete(0, 'end')

    @staticmethod
    def _remove(widget):
        """Remove the widget for button press."""
        widget.destroy()
        canv = widget.master.entrycanv
        canv.update_idletasks()
        canv.configure(scrollregion=canv.bbox('all'))

    @tku.Bindings('<Control-a>', '<Control-A>')
    @staticmethod
    def selall(widget):
        """Control-a to select all text."""
        widget.icursor('end')
        widget.selection_range(0, 'end')
        return 'break'

    @tku.Bindings(
        '<Control-n>', '<Control-N>',
        '<Control-p>', '<Control-P>')
    @staticmethod
    def next_entry(widget, keysym):
        """Move to adjacent entry."""
        entry = widget.master
        gridinfo = entry.grid_info()
        row = gridinfo['row']
        frame = gridinfo['in']
        entries = frame.grid_slaves()
        rows = [entry.grid_info()['row'] for entry in entries]
        attr = 'key' if widget is entry.key else 'value'
        best = None
        pick = 0
        if keysym.lower() == 'p':
            for i, r in enumerate(rows):
                if r < row and (best is None or r > best):
                    best = r
                    pick = i
            if best is not None:
                target = getattr(entries[pick], attr)
                target.focus_set()
                target.icursor('end')
        else:
            for i, r in enumerate(rows):
                if r > row and (best is None or r < best):
                    best = r
                    pick = i
            if best is not None:
                target = getattr(entries[pick], attr)
                target.focus_set()
                target.icursor('end')
        return 'break'

    @tku.Bindings('<Return>')
    @staticmethod
    def addentry(widget):
        """Create a new entry."""
        dictwidget = widget.master.master
        dictwidget.addentry(dictwidget)
        dictwidget.entryframe.grid_slaves()[0].key.focus_set()

    @tku.Bindings('<Control-BackSpace>')
    @staticmethod
    def rmentry(widget):
        """Remove current dict entry.

        Switch focus to previous entry or next if no previous.
        """
        dictentry = widget.master
        currow = dictentry.grid_info()['row']
        bestlo = None
        besthi = None
        picklo = 0
        pickhi = 0
        entries = dictentry.master.entryframe.grid_slaves()
        print('current row:', currow)
        for i, entry in enumerate(entries):
            r = entry.grid_info()['row']
            if r > currow:
                if besthi is None or r < besthi:
                    besthi = r
                    pickhi = i
            elif r < currow:
                if bestlo is None or r > bestlo:
                    bestlo = r
                    picklo = i
        if bestlo is not None:
            entries[picklo].key.focus_set()
            entries[picklo].key.icursor('end')
        elif besthi is not None:
            entries[pickhi].key.focus_set()
            entries[pickhi].key.icursor('end')
        dictentry.destroy()

class Dict(tk.Frame, object):
    """Represent a sequence of DictEntries.

    DictEntries' master is self.
    """
    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__(*args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.entrycanv = tk.Canvas(self, bd=0, highlightthickness=0)
        self.entrycanv.grid(row=0, column=0, sticky='nsew')
        self.entryframe = tk.Frame(self)
        self.entryframe.grid_columnconfigure(0, weight=1)
        self.entrycanv.create_window(0,0, window=self.entryframe, anchor='nw')
        self.scrolly = tk.Scrollbar(
            self, orient='vertical', command=self.entrycanv.yview)
        self.scrolly.grid(row=0, column=1, sticky='ns', rowspan=2)
        self.scrollx = tk.Scrollbar(
            self, orient='horizontal', command=self.entrycanv.xview)
        self.scrollx.grid(row=1, column=0, sticky='ew')
        self.scrollx.grid_remove()
        self.entrycanv.configure(
            yscrollcommand=self.scrolly.set, xscrollcommand=self.scrollx.set)

        script = tku.EvSubs.make_script_(
            self, self.addentry, subs=dict(widget=(str(self), None)))
        self.add = tk.Button(self, text='+', command=script)
        self.add.grid(row=2, column=0, sticky='nsew', columnspan=2)

        self.addentry(self)
        tku.subclass(self.entryframe, 'DictInner')
        tku.subclass(self, 'Dict')
        if not self.bind_class('Dict'):
            self._inner_resized.bind(self, 'DictInner')
            self._outer_resized.bind(self, 'Dict')

    def get(self):
        """Get dict value."""
        return dict(
            filter(None, (entry.get() for entry in self.entryframe.grid_slaves())))

    def set(self, data):
        """Set the dict values."""
        entries = self.entryframe.grid_slaves()
        if len(entries) < max(len(data),1):
            for i in range(max(1, len(data)) - len(entries)):
                self.addentry(self)
            entries = self.entryframe.grid_slaves()
        entries = iter(entries)
        if data:
            for (k, v), entry in zip(data.items(), entries):
                entry.set(k,v)
        else:
            next(entries).clear()
        for remainder in entries:
            remainder.destroy()
        self.update_idletasks()
        canv = self.entrycanv 
        canv.configure(scrollregion=canv.bbox('all'))

    @staticmethod
    def addentry(widget):
        """Add a dict entry."""
        entry = DictEntry(widget)
        entry.grid(
            row=widget.entryframe.grid_size()[1], column=0, sticky='nsew',
            in_=widget.entryframe)
        canv = widget.entrycanv
        canv.update_idletasks()
        canv.configure(scrollregion=canv.bbox('all'))
        entry.lower(widget.scrolly)

    @tku.Bindings('<Configure>')
    @staticmethod
    def _inner_resized(widget):
        dct = widget.master
        canv = dct.entrycanv
        canv.configure(width=widget.winfo_reqwidth())
        if widget.winfo_reqwidth() > canv.winfo_width():
            dct.scrollx.grid()
        else:
            dct.scrollx.grid_remove()
        canv.configure(scrollregion=canv.bbox('all'))

    @tku.Bindings('<Configure>')
    @staticmethod
    def _outer_resized(widget):
        if widget.entryframe.winfo_reqwidth() > widget.winfo_width():
            widget.scrollx.grid()
        else:
            widget.scrollx.grid_remove()

if __name__ == '__main__':
    import pprint
    import traceback
    import traceback
    r = tk.Tk()
    r.grid_rowconfigure(0, weight=1)
    r.grid_rowconfigure(1, weight=1)
    r.grid_columnconfigure(0, weight=1)
    d = Dict(r)
    d.grid(row=0, column=0, sticky='nsew')


    t = tk.Text(r)
    t.grid(row=1, column=0, sticky='nsew')


    def doset():
        try:
            thing = ast.literal_eval(t.get('1.0', 'end'))
        except Exception:
            traceback.print_exc()
        else:
            d.set(thing)

    b = tk.Button(r, text='set', command=r.register(doset))
    b.grid(row=2, column=0, sticky='nsew')



    r.bind('<Return>', lambda e: print(d.get()))
    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
