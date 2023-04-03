import sys
if sys.version_info.major > 2:
    import tkinter as tk
else:
    import Tkinter as tk
from .labeler import Labeler
from jhsiao.tkutil.bindings import Bindings
bindings = Bindings()
