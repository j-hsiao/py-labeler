"""A namespace package for adding items for the labeler to use.

Separate packages should be sure to ensure it is a namespace package:
    Add a line to labeleritems/__init__.py:
        __path__ = __import__('pkgutil').extend_path(__path__, __name__)
    Or if python3, no labeleritems/__init__.py file.

For methods with both instance and class versions, the class version
ends with an underscore.
"""
from __future__ import print_function
__all__ = ['get_items', 'Item', 'ItemSelector', 'itemclasses', 'create_composite']
import os
from itertools import chain, islice
from pkgutil import iter_modules, extend_path
__path__ = extend_path(__path__, __name__)

from collections import defaultdict, deque
from functools import wraps
import sys
if sys.version_info.major > 2:
    import tkinter as tk
    from tkinter import messagebox
    from collections.abc import MutableMapping
else:
    import Tkinter as tk
    import tkMessageBox as messagebox
    from collections import MutableMapping
import traceback
from importlib import import_module

from .. import tkutil as tku

class TagDB(object):
    """Class for initializing desired tags per id."""
    def __init__(self, master):
        self.master = master
        self.tags = defaultdict(list)
        self.taglut = defaultdict(set)

    def __repr__(self):
        return repr(self.tags)

    def __iter__(self):
        return iter(self.tags.items())

    def _flatten_idns(self, idns):
        if isinstance(idns, str):
            idns = self.taglut[idns]
        elif isinstance(idns, int):
            yield idns
            return
        elif isinstance(idns, Item):
            idns = idns.idns
        elif not hasattr(idns, '__iter__'):
            raise ValueError('bad idn: {}'.format(repr(idns)))
        for thing in idns:
            for ret in self._flatten_idns(thing):
                yield ret

    @staticmethod
    def _normalize_at(lst, at):
        if isinstance(at, Item):
            return lst.index(at.TAGS[-1])+1
        elif isinstance(at, str):
            return lst.index(at)
        elif at is None:
            return len(lst)
        elif isinstance(at, int):
            return at
        else:
            at, offset = at
            if isinstance(at, str):
                return lst.index(at)+offset
            if offset > 0:
                return lst.index(at.TAGS[-1])+offset
            else:
                return lst.index(at.TAGS[0])+offset
        return at


    def add(self, idn, tags, at=None, suffix=None):
        """Add tags to identifiers at some value.

        idn: int, str(a tag), Item(use item.idns), or sequence of 
            above items.  idn will be parsed accordingly and all
            indicated ids will have tags added to them.
        tags: the tags to add or a single tag.
        at: int(index), None(at end), str(before this tag), a 2-tuple
            or list: a tag and an offset ('tag', 1) will mean
            at index of 'tag' + 1 (ie after 'tag').  Alternatively,
            an Item class, in which case its TAGS attribute will be
            used.
        suffix: a suffix to add after tags that end with '_'
            will be converted to str via str()
        """
        if suffix is not None:
            if isinstance(tags, str):
                if tags[-1] == '_':
                    tags += str(suffix)
            else:
                suffix = str(suffix)
                tags = [
                    tag+suffix if tag[-1]=='_' else tag
                    for tag in tags]
        for idn in set(self._flatten_idns(idn)):
            lst = self.tags[idn]
            curat = self._normalize_at(lst, at)
            if isinstance(tags, str):
                lst.insert(curat, tags)
                self.taglut[tags].add(idn)
            else:
                lst[curat:curat] = tags
                for tag in tags:
                    self.taglut[tag].add(idn)

itemclasses = {}
class Item(tku.Behavior):
    """Item baseclass.

    Items are possibly nested collections of canvas objects that
    constitute some kind of item.  For example, a rectangle may have
    a rectangle (Canvas.create_rectangle) as well as Points(create_oval)
    for each vertex.  In this example, the rectangle would be the
    'top-most item' while the Points are would be 'subitems'.  Each Item
    subclass has an attribute idns which is a list of associated
    tk.Canvas item ids for the immediate Item.  This should include ids
    for sub items.

    Every item idn should have associated tags.  Tags generally have 2
    forms.  The first form is generally the name of a class and should
    be used to bind callbacks.  The second form is the name of a class
    followed by an underscore and an item id, which is used for
    identification.  If a class has both binding and identification
    tags, then their relative order should not be broken by other
    (sub)classes' tags.  eg. The Item base class adds both 'Item' and
    'Item_<masteridn>' tags.  No tags should be inserted between these
    two tags.  This allows faster retrieval of tags while also allowing
    a more flexible tag ordering which affects callback order.
    Tags are handled in update_tags().  Subclasses should call super and
    then update the corresponding values.

    Directly instantiated Items expect arguments: (master, x, y, owned=True|False)
    """
    # LENGTH should be the length of the 'data' value in todict()
    LENGTH = 0
    TAGS = ['Item', 'Item_']

    def __init__(self, widget, *idns, **kwargs):
        """Initialize the item.

        widget: tk.Canvas item that created idns.
        idns: Pass in canvas item ids that are in the current Item or
            below.  This can contain list of ids, Items(will use its
            idns attribute), or ids.
        kwargs:
        """
        self.subitems = []
        self.rawidns = []
        self.idns = []
        self.parse_idns(idns)
        if not kwargs.get('owned', False):
            if not widget.tag_bind(Item.TAGS[0]):
                Item.bind(widget, bindfunc='tag_bind')
            tagdb = TagDB(self.idns[0])
            self.addtags(tagdb)
            for idn, tags in tagdb:
                for tag in tags:
                    widget.addtag(tag, 'withtag', idn)

    def rescale(self, widget):
        """Rescale fixed-sized items."""
        for item in self.subitems:
            item.rescale(widget)


    def addtags(self, tagdb):
        """Add new tags to db.

        tagdb: a TagDB.
        """
        for subitem in self.subitems:
            subitem.addtags(tagdb)
        tagdb.add(self.rawidns, Item.TAGS, at=0, suffix=tagdb.master)

    def parse_idns(self, idns):
        """Parse idns into self.idns and self.subitems.

        idns: Some data structure of id numbers.
            Acceptable items:
                an int: an id
                an Item: use Item.idns
                a sequence (has __iter__) of any of the above
                    (including other sequences).

        self.subitems: contains all subitems contained in idns
        self.idns: all idns (ints)
        """
        if isinstance(idns, (int, Item)):
            idns = (idns,)
        idns = deque(idns)
        while idns:
            thing = idns.popleft()
            if isinstance(thing, int):
                self.idns.append(thing)
                self.rawidns.append(thing)
            elif isinstance(thing, Item):
                self.idns.extend(thing.idns)
                self.subitems.append(thing)
            elif hasattr(thing, '__iter__'):
                idns.extendleft(reversed(thing))
            else:
                raise ValueError(
                    'Bad value in idns: {}'.format(repr(thing)))

    @classmethod
    def tagat(cls, widget, tagOrId, offset=1):
        """Find the tag in <tags> relative to <tag> by <offset>."""
        tags = widget.gettags(tagOrId)
        return tags[tags.index(cls.TAGS[0])+offset]

    @staticmethod
    def mastertag(widget, idn):
        """Return the master tag: 'Item_<masteridn>'."""
        return Item.tagat(widget, idn, 1)

    @classmethod
    def getidn(cls, tag):
        """Return a str: the idn used as master item of item.

        Generally a str is fine.  Be aware, ints are required for
        LabelCanv.items though
        """
        return tag[len(cls.TAGS[-1]):]

    @staticmethod
    def modcolor(master, color):
        """Return a similar but different color.

        Brighten/darkens the color. Might help in making things
        more visible against similarly colored background.
        """
        return '#{:02x}{:02x}{:02x}'.format(
            *(((x//256)+128)%256 for x in master.winfo_rgb(color)))

    @staticmethod
    def pertag(func):
        """Wrap function to be performed per idn.

        func should have signature func(widget, idn, *args).
        Return a function wrapped(widget, tagOrId, *args) that calls
        func for each idn tagged with tagOrId.  If tagOrId is not str,
        then just call func with tagOrId as is.

        Can also decorate staticmethod/classmethod
        """
        if isinstance(func, (staticmethod, classmethod)):
            tp = type(func)
            func = func.__func__
        else:
            tp = lambda x:x

        @wraps(func)
        def wrapped(widget, tag, *args):
            for idn in widget.find('withtag', tag):
                func(widget, idn, *args)
        return tp(wrapped)

    @classmethod
    def recolort(cls, widget, tag, color):
        for idn in widget.find('withtag', tag):
            cls.recolor_(widget, idn, color)

    @staticmethod
    def recolor_(master, idn, color):
        """Change the color given idn."""
        raise NotImplementedError

    # mainly for composite for better visual indication
    # of which items compose the composite
    @staticmethod
    def entered(master, idn):
        """Act as if mouse entered."""
        pass

    @staticmethod
    def left(master, idn):
        """Act as if mouse left."""
        pass

    def recolor(self, widget, color):
        """Change the color given idn."""
        self.recolor_(widget, self.idns[0], color)

    def __str__(self):
        """Allow using instance as the first idn."""
        return str(self.idns[0])


    def color(self, widget):
        """Return current color.

        Assume activeoutline for all parts is the current color.
        """
        return widget.itemcget(self.idns[0], 'activeoutline')

    @tku.Bindings('<Button-1>')
    @staticmethod
    def _item_selected(widget):
        widget.change_item()

    @tku.Bindings('<Button-3>')
    @staticmethod
    def _item_menu(widget, rootx, rooty):
        widget.menu.itemtag = Item.mastertag(widget, 'current')
        widget.menu.post(rootx, rooty)

    @tku.Bindings('<ButtonRelease-1>')
    @staticmethod
    def _dragdelete(widget):
        """Delete item if dragged completely out of image."""
        itag = Item.mastertag(widget, 'current')
        l, t, r, b = widget.bbox(itag)
        x1,y1, x2,y2 = map(int, widget.cget('scrollregion').split())
        if max(l,x1)>=min(r, x2) or max(t, y1)>=min(b, y2):
            widget.delete(int(itag[5:]))
            return 'break'

    @staticmethod
    def interpolate(data1, data2, interp):
        """Return interpolated data.

        data1/2: todict()
        interp:
            float: interpolation multiplier.
                0-1 for interpolation
                <0 or >1 for extrapolation.
                0 = data1, 1 = data2
        """
        return [d1 + interp*(d2-d1) for d1,d2 in zip(data1, data2)]

    def todict(self, widget):
        """Return self as a dict."""
        return dict(
            type=type(self).__name__,
            color=self.color(widget))

    @staticmethod
    def fromdict(widget, dct, owned=False):
        """Create self from return value of todict."""
        try:
            cls = itemclasses[dct['type']]
        except KeyError:
            itemclasses.update(get_items())
            cls = itemclasses[dct['type']]
        # Calling fromdict from Item, owned should be False
        # because otherwise just use the class directly.
        ret = cls.fromdict(widget, dct)
        ret.recolor(widget, dct['color'])
        return ret

class ItemMenu(tku.Behavior, tk.Menu, object):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('tearoff', False)
        super(ItemMenu, self).__init__(*args, **kwargs)
        subs = dict(widget=self)
        _, delname = tku.Subber.createcommand(self, self._delete, subs=subs)
        _, bakname = tku.Subber.createcommand(self, self._toback, subs=subs)
        _, hidname = tku.Subber.createcommand(self, self._hide, subs=subs)
        self.add(
            'command', label='delete', underline=0,
            command='{} {}'.format(delname, self))
        self.add(
            'command', label='send to back', underline=8,
            command='{} {}'.format(bakname, self))
        self.add(
            'command', label='hide', underline=0,
            command='{} {}'.format(hidname, self))
        self.itemtag = None

    @staticmethod
    def _hide(widget):
        canv = widget.master
        canv.itemconfigure(widget.itemtag, state='hidden')

    @staticmethod
    def _toback(widget):
        canv = widget.master
        canv.tag_lower(widget.itemtag, 'Item')

    @staticmethod
    def _delete(widget):
        canv = widget.master
        canv.delete(int(Item.getidn(widget.itemtag)))

class ItemSelector(tk.Frame, object):
    def __init__(self, *args, **kwargs):
        """Initialize ItemSelector.

        kwargs:
            classes: a dict of {name: class}
        """
        classes = kwargs.pop('classes', None)
        kwargs.setdefault('border', 2)
        kwargs.setdefault('relief', 'raised')
        super(ItemSelector, self).__init__(*args, **kwargs)
        self._title = tk.Label(self, text='Items')
        self._title.grid(row=0, column=0, sticky='ew', columnspan=2)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._bx = tk.Listbox(self, exportselection=False)
        self._bx.grid(row=1, column=0, sticky='nsew')

        self._scrollbar = tk.Scrollbar(
            self, orient='vertical', command=self._bx.yview)
        self._scrollbar.grid(row=1, column=1, sticky='ns')
        self._bx.configure(yscrollcommand=self._scrollbar.set)

        self._compose = tk.Button(self, text='Create a composite class')
        self._compose.grid(row=2, column=0, sticky='nsew', columnspan=2)
        self._launch_creator.bind(self)
        self._compose.configure(
            command=' '.join((self._launch_creator.name(), str(self))))

        self.classes = itemclasses if classes is None else classes
        self.resync()

    def resync(self, classes=None):
        if classes is None:
            classes = self.classes
        else:
            self.classes = classes
        if not self.classes:
            self.classes.update(get_items())
        cursel = self._bx.curselection()
        if cursel:
            cursel = self._bx.get(cursel[0])
        else:
            cursel = None
        self._bx.delete(0, 'end')
        for k in sorted(self.classes):
            self._bx.insert('end', k)
            if k == cursel:
                self._bx.selection_set('end')
        if not self._bx.curselection():
            self._bx.selection_set(0)

    @tku.Bindings()
    @staticmethod
    def _launch_creator(widget):
        CompositeCreator(widget)

    def create(self, widget, x, y):
        """Create an item.

        widget: the canvas
        x, y: the x, y from the event
        """
        return self.get()(widget, x, y)

    def get(self):
        """Return selected class."""
        return self.classes[self._bx.get(self._bx.curselection()[0])]

class Composite(Item):
    """Composite baseclass.

    Derived classes should set the class attributes:
        components: a list of Item classes.
        TAGS: ['<name of class>_']
    """
    def __init__(self, widget, x, y, owned=False):
        """Create multiple items as 1."""
        if y is None:
            super(Composite, self).__init__(widget, *x, owned=owned)
        else:
            super(Composite, self).__init__(
                widget,
                *[
                    sub(widget, x, y, True) for (x,y), sub in
                    zip(self.__initxy(x,y), self.components)],
                owned=owned)
        if not widget.tag_bind('Composite'):
            Composite.bind(widget, bindfunc='tag_bind')

    @tku.Bindings('<Enter>')
    @staticmethod
    def _entered(widget):
        for sub in Composite.bases(widget):
            sub.entered(widget, sub.idns[0])

    @tku.Bindings('<Leave>')
    @staticmethod
    def _left(widget):
        for sub in Composite.bases(widget):
            sub.left(widget, sub.idns[0])

    @staticmethod
    def bases(widget):
        """Generate all non-composite items."""
        tag = Item.tagat(widget, 'current', 1)
        self = widget.items[int(Item.getidn(tag))][0]
        q = deque(self.subitems)
        while q:
            item = q.popleft()
            if isinstance(item, Composite):
                q.extendleft(reversed(item.subitems))
            else:
                yield item

    @classmethod
    def __initxy(cls, x,y):
        """Return modified x,y for any besides primary subclass.

        Points are the smallest and most likely to be occluded by other
        subclass items so generally, they should be last to be on top.
        However, being on top means when the item is created, the point
        becomes the selected subitem for modification which is generally
        less useful.
        """
        subxy = tuple([k-10 if k>20 else k+10 for k in (x,y)])
        xys = [subxy] * len(cls.components)
        xys[cls.PRIMARY] = (x,y)
        return xys

    def addtags(self, tagdb):
        super(Composite, self).addtags(tagdb)
        tagdb.add(
            [sub.idns[0] for sub in self.subitems],
            self.TAGS, suffix=self.idns[0])
        if tagdb.master == self.idns[0]:
            tagdb.add(self.idns, ('Composite',))

    @classmethod
    def recolor_(cls, widget, idn, color):
        subidns = widget.find('withtag', cls.TAGS[0]+str(idn))
        for cls, subidn in zip(cls.components, subidns):
            cls.recolor_(widget, subidn, color)

    def recolor(self, widget, color):
        for thing in self.subitems:
            thing.recolor(widget, color)

    def color(self, widget):
        return self.subitems[0].color(widget)

    def todict(self, widget):
        d = super(Composite, self).todict(widget)
        it = iter(self.subitems)
        data = list(next(it).todict(widget)['data'])
        for sub in it:
            data.extend(sub.todict(widget)['data'])
        d['data'] = data
        return d

    @classmethod
    def interpolate(cls, data1, data2, interp):
        it1 = iter(data1)
        it2 = iter(data2)
        result = []
        for sub in cls.components:
            result.extend(
                sub.interpolate(
                    list(islice(it1, sub.LENGTH)),
                    list(islice(it2, sub.LENGTH)),
                    interp))
        return result

    @classmethod
    def fromdict(cls, widget, dct, owned=False):
        """Create self from return value of todict."""
        it = iter(dct['data'])
        subitems = [
            sub.fromdict(
                widget,
                dict(
                    data=list(islice(it, sub.LENGTH)),
                    type=sub.__name__,
                    color=dct['color']),
                owned=True)
            for sub in cls.components]
        return cls(widget, subitems, None, owned)

def create_composite(name, components):
    """Create a composite class of of a list of Items."""
    if not len(components):
        raise Exception('Composite class needs non-empty sequence of components')
    try:
        component_classes = [
            itemclasses[item] if isinstance(item, str) else item
            for item in components]
    except KeyError:
        itemclasses.update(get_items())
        component_classes = [
            itemclasses[item] if isinstance(item, str) else item
            for item in components]
    for primary, subcls in enumerate(component_classes):
        if subcls.__name__ != 'Point':
            if issubclass(subcls, Composite):
                q = deque(subcls.components)
                while q:
                    subsub = q.popleft()
                    if subsub.__name__ != 'Point':
                        if issubclass(subsub, Composite):
                            q.extendleft(reversed(subsub.components))
                        else:
                            q.append(None)
                            break
                if q:
                    break
            else:
                break
    return type(
        name,
        (Composite,),
        dict(
            components=component_classes,
            PRIMARY=primary,
            TAGS=[name+'_'],
            LENGTH=sum(sub.LENGTH for sub in component_classes))
    )


class CompositeCreator(tk.Toplevel, object):
    def __init__(self, *args, **kwargs):
        super(CompositeCreator, self).__init__(*args, **kwargs)
        self.title('Create new composite item.')
        self.boxframe = tk.Frame(self)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.boxframe.grid(row=0, column=0, sticky='nsew', columnspan=3)

        self.boxframe.grid_rowconfigure(0, weight=1)
        self.boxframe.grid_columnconfigure(0, weight=1)
        self.boxframe.grid_columnconfigure(2, weight=1)
        self.choicesbox = tk.Listbox(self, exportselection=False)
        try:
            classes = self.master.classes
        except AttributeError:
            classes = itemclasses
        if not classes:
            classes.update(get_items())
        for cls in sorted(classes):
            self.choicesbox.insert('end', cls)
        self.targetsbox = tk.Listbox(self, exportselection=False)
        self.choicesbox.selection_set(0)
        tku.subclass(self.targetsbox, 'CompositeTarget')
        tku.subclass(self.choicesbox, 'CompositeChoice')
        self.choicesscroll = tk.Scrollbar(
            self.boxframe, orient='vertical', command=self.choicesbox.yview)
        self.targetsscroll = tk.Scrollbar(
            self.boxframe, orient='vertical', command=self.targetsbox.yview)
        self.choicesbox.configure(yscrollcommand=self.choicesscroll.set)
        self.targetsbox.configure(yscrollcommand=self.targetsscroll.set)
        self.choicesbox.grid(row=0, column=0, sticky='nsew', in_=self.boxframe)
        self.choicesscroll.grid(row=0, column=1, sticky='ns')
        self.targetsbox.grid(row=0, column=2, sticky='nsew', in_=self.boxframe)
        self.targetsscroll.grid(row=0, column=3, sticky='ns')

        self.clsname = tk.Entry(self)
        self.create = tk.Button(self, text='create')
        self.cancel = tk.Button(self, text='cancel')
        self.clsname.grid(row=1, column=0, sticky='nsew')
        self.create.grid(row=1, column=1, sticky='nsew')
        self.cancel.grid(row=1, column=2, sticky='nsew')
        tku.subclass(self.cancel, 'CompositeCancel')
        tku.subclass(self.create, 'CompositeCreate')
        tku.subclass(self.clsname, 'CompositeEntry')

        self.grab_set()
        self.lift(self.master)

        if not self.bind_class('CompositeChoice'):
            self._create.bind(self, tag='CompositeCreate')
            self._add_itemtype.bind(self, tag='CompositeChoice')
            self._remove_itemtype.bind(self, tag='CompositeTarget')
            self._cancel.bind(self, tag='CompositeCancel')
            self.bind(
                '<Escape>',
                ' '.join((self._cancel.name(), str(self.cancel))))
            self.bind_class(
                'CompositeEntry',
                '<Return>',
                ' '.join((self._create.name(), tku.EvSubs.subs['widget'][0])))


    @tku.Bindings('<ButtonRelease-1>', '<Return>', '<space>')
    @staticmethod
    def _add_itemtype(widget):
        creator = widget.master
        choices = creator.choicesbox
        targets = creator.targetsbox
        try:
            pick = choices.get(choices.curselection()[0])
        except IndexError:
            return
        targets.insert('end', pick)
        targets.selection_clear(0, 'end')
        targets.selection_set('end')

    @tku.Bindings('<ButtonRelease-1>', '<Return>', '<space>')
    @staticmethod
    def _remove_itemtype(widget):
        creator = widget.master
        targets = creator.targetsbox
        try:
            toremove = targets.curselection()[0]
        except IndexError:
            return
        targets.delete(toremove)
        targets.selection_clear(0, 'end')
        if toremove < targets.index('end'):
            targets.selection_set(toremove)
        else:
            targets.selection_set('end')

    @tku.Bindings('<ButtonRelease-1>', '<Return>', '<space>')
    @staticmethod
    def _create(widget):
        self = widget.master
        name = self.clsname.get()
        msg = None
        if not name:
            msg = 'pleace choose a name'
        elif name in itemclasses:
            msg = 'Class name already exists.'
        if msg:
            messagebox.showerror(title='Bad class name', message=msg)
            return
        newclass = create_composite(name, self.targetsbox.get(0, 'end'))
        itemclasses[name] = newclass
        self.master._bx.insert('end', name)
        self.master._bx.selection_clear(0, 'end')
        self.master._bx.selection_set('end')
        self.destroy()

    def destroy(self):
        self.grab_release()
        self.master.focus_set()
        super(CompositeCreator, self).destroy()

    @tku.Bindings('<ButtonRelease-1>', '<Return>', '<space>')
    @staticmethod
    def _cancel(widget):
        widget.master.destroy()

def _find_module_candidates(paths, prefix):
    try:
        # try pkgutil iter_modules
        # pkgutil implementation
        # pkgutil documentation says something about
        # finder must implement iter_modules, but is non-standard?
        # Does that mean iter_modules is not always available?
        for _, name, ispkg in iter_modules(paths, prefix):
            yield name
    except Exception:
        # fallback to listdir
        for path in set(map(os.path.abspath, map(os.path.normcase, paths))):
            for fname in os.listdir(path):
                name, ext = os.path.splitext(fname)
                fullpath = os.path.join(path, fname)
                if (
                        fname.startswith('_')
                        or (
                            os.path.isfile(fullpath)
                            and ext not in ('.py', '.pyc'))
                        or (
                            sys.version_info < (3,3)
                            and not os.path.exists(
                                os.path.join(fullpath, '__init__.py')))):
                    continue
                yield prefix+name

def get_items(paths=None, prefix=None, cls=None):
    """Search for cls subclasses inside <prefix> namespace.

    paths, prefix: same as pkgutil.iter_modules
    paths defaults to {}
    prefix defaults to '{}.'
    """
    if paths is None:
        paths = __path__
    if prefix is None:
        prefix = __name__+'.'
    if cls is None:
        cls = Item
    ret = {}
    for name in _find_module_candidates(paths, prefix):
        try:
            module = import_module(name)
        except Exception:
            traceback.print_exc()
            continue
        try:
            keys = module.__all__
        except AttributeError:
            keys = dir(module)
        for k in keys:
            try:
                cand = getattr(module, k)
                if isinstance(cand, type) and issubclass(cand, cls):
                    if ret.setdefault(cand.__name__, cand) is not cand:
                        orig = ret[cand.__name__]
                        print('found multiple classes:', cand.__name__, file=sys.stderr)
                        print(
                            'keeping original: {}.{} vs new: {}.{}'.format(
                                orig.__module__, orig.__name__,
                                cand.__module__, cand.__name__), file=sys.stderr)
            except Exception:
                traceback.print_exc()
    return ret
try:
    get_items.__doc__ = get_items.__doc__.format(__path__, __name__)
except Exception:
    pass
