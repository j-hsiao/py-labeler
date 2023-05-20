__all__ = ['ObjSelector']
import copy
import importlib
import pkgutil

from . import bindings
from .objs import Obj, __path__
from jhsiao.tkutil import tk, add_bindtags
from .objs.composite import make_composite
from .dict import Dict
from .ddict import DDict

class ObjSelector(tk.Frame, object):
    def __init__(self, master, *args, **kwargs):
        super(ObjSelector, self).__init__(master, *args, **kwargs)
        self.creating = False
        self.classinfo = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.lbl = tk.Label(self, text='Object type')
        self.lst = tk.Listbox(self, exportselection=False)
        self.scroll = tk.Scrollbar(
            self, orient='vertical', command=self.lst.yview)
        self.lst.configure(yscrollcommand=self.scroll.set)
        self.clbl = tk.Label(self, text='Composite components')
        self.clst = tk.Listbox(self, exportselection=False, state='disabled')
        self.cscroll = tk.Scrollbar(
            self, orient='vertical', command=self.clst.yview)
        self.clst.configure(yscrollcommand=self.cscroll.set)
        self.lbl.grid(row=0, column=0, columnspan=2, sticky='ew')
        self.lst.grid(row=1, column=0, sticky='nsew')
        self.scroll.grid(row=1, column=1, sticky='nsew')
        self.clbl.grid(row=0, column=2, columnspan=2, sticky='ew')
        self.clst.grid(row=1, column=2, sticky='nsew')
        self.cscroll.grid(row=1, column=3, sticky='nsew')
        self.addpath(__path__, 'jhsiao.labeler.objs.')
        add_bindtags(self.lst, 'ObjSelector.lst')
        add_bindtags(self.clst, 'ObjSelector.clst')

        self.createbutton = tk.Button(
            self, text='create', state='disabled',
            command=self._create.str(widget=self))
        self.createbutton.grid(row=2, column=2, columnspan=2, sticky='nsew')
        self.togglebutton = tk.Button(
            self, text='start creation',
            command=self._toggle_creation.str(widget=self))
        self.togglebutton.grid(row=2, column=0, columnspan=2, sticky='nsew')

        self.nframe = tk.Frame(self)
        self.nframe.grid_columnconfigure(1, weight=1)
        self.namelbl = tk.Label(self.nframe, text='Composite name:')
        self.compositename = tk.Entry(self.nframe, state='disabled')
        self.nframe.grid(row=3, column=0, columnspan=4, sticky='nsew')
        self.namelbl.grid(row=0, column=0, sticky='nsew')
        self.compositename.grid(row=0, column=1, sticky='nsew')

    def __call__(self):
        """Retrieve the currently selected class."""
        return self._cls

    def select(self, cls_or_name):
        if not isinstance(cls_or_name, str):
            cls_or_name = cls_or_name.__name__
        try:
            idx = self.lst.get(0, 'end').index(self.displayname(cls_or_name))
        except ValueError:
            pass
        else:
            try:
                self._cls = Obj.classes[cls_or_name]
            except KeyError:
                pass
            else:
                self.lst.selection_clear(0, 'end')
                self.lst.selection_set(idx)

    @staticmethod
    @bindings['ObjSelector.lst'].bind('<ButtonRelease-1>')
    def _add_component(widget):
        """Add a component to list for composite."""
        self = widget.master
        if self.creating:
            self.clst.insert(
                'end',
                widget.get(widget.curselection()[0]))

    @staticmethod
    @bindings['ObjSelector.lst'].bind('<<ListboxSelect>>')
    def _sel_changed(widget):
        """Change the current selected class."""
        self = widget.master
        curname = self.classname(widget.get(widget.curselection()[0]))
        self._cls = Obj.classes.get(curname)
        color = self.classinfo[curname].get('color')
        if color is not None:
            self.master.colorpicker.set_color(color)

    @staticmethod
    @bindings['ObjSelector.lst'].bind('<Double-ButtonRelease-1>')
    def _edit_classinfo(widget):
        """Change class info dict."""
        self = widget.master
        if self.creating:
            self._add_component(widget)
        else:
            curname = self.classname(widget.get(widget.curselection()[0]))
            top = tk.Toplevel(widget)
            top.title('Edit settings for {}'.format(curname))
            d = Dict(top)
            d.set(self.classinfo[curname])
            submit = tk.Button(
                top, text='submit',
                command=self._submit_classedit.str(widget=d))
            cancel = tk.Button(
                top, text='cancel',
                command=self._cancel_classedit.str(widget=d))
            top.grid_rowconfigure(0, weight=1)
            top.grid_columnconfigure(0, weight=1)
            top.grid_columnconfigure(1, weight=1)
            d.grid(row=0, column=0, sticky='nsew', columnspan=2)
            submit.grid(row=1, column=0, sticky='nsew')
            cancel.grid(row=1, column=1, sticky='nsew')
            top.grab_set()
            top.wait_window()
            response = getattr(top, 'response', None)
            if response:
                self.classinfo[curname][...] = response

    @bindings('')
    def _submit_classedit(widget):
        t = widget.master
        t.response = widget.dict()
        t.grab_release()
        t.destroy()

    @bindings('')
    def _cancel_classedit(widget):
        t = widget.master
        t.grab_release()
        t.destroy()

    @staticmethod
    @bindings['ObjSelector.clst'].bind('<ButtonRelease-1>')
    def _rm_component(widget, y):
        """Remove a component from composite list."""
        self = widget.master
        if self.creating:
            pick = widget.nearest(y)
            if pick >= 0:
                self.clst.delete(pick)

    @staticmethod
    def displayname(classname):
        """Calculate the name to display from class name."""
        if classname.startswith('Composite'):
            return classname[len('Composite'):] + '(Composite)'
        return classname

    @staticmethod
    def classname(displayname):
        """Calculate the class name from display name."""
        if displayname.endswith('(Composite)'):
            displayname = 'Composite' + displayname[:-len('(Composite)')]
        return displayname

    @bindings('')
    def _toggle_creation(widget):
        """Toggle composite creation mode."""
        if widget.creating:
            widget.creating = False
            widget.togglebutton.configure(text='start creation')
            widget.createbutton.configure(state='disabled')
            widget.clst.configure(state='disabled')
            widget.compositename.configure(state='disabled')
        else:
            widget.creating = True
            widget.togglebutton.configure(text='stop creation')
            widget.createbutton.configure(state='normal')
            widget.clst.configure(state='normal')
            widget.compositename.configure(state='normal')

    @bindings('')
    def _create(widget):
        """Create the composite class.

        If no components have een selected, cancel.
        Otherwise, create a composite class and add to list of classes.
        """
        names = widget.clst.get(0, 'end')
        tname = widget.compositename.get()
        if names:
            make_composite(
                [Obj.classes[widget.classname(name)] for name in names],
                tname)
            widget.reload()
        widget.clst.delete(0, 'end')
        widget.compositename.delete(0, 'end')
        widget._toggle_creation.func(widget)
        widget.lst.focus_set()

    def reload(self):
        """Reload the list of classes (sorted order."""
        self.lst.delete(0, 'end')
        for name, cls in Obj.classes.items():
            try:
                self.classinfo[name]
            except KeyError:
                self.classinfo[name] = DDict(cls.INFO)
        toadd = [self.displayname(name) for name in Obj.classes]
        toadd.sort(key=str.lower)
        self.lst.insert('end', *toadd)
        self.lst.selection_clear(0, 'end')
        self.lst.selection_set(0)
        self._sel_changed(self.lst)

    def addpath(self, paths, prefix):
        """Import submodules in path under prefix.

        Any additional Objs should be `register`ed.
        """
        if isinstance(paths, str):
            paths = [paths]
        for finder, name, ispkg in pkgutil.walk_packages(paths, prefix):
            importlib.import_module(name)
        self.reload()

