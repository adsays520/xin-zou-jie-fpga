"""Render normal warnings/errors in the application instead of modal dialogs."""
import tkinter as tk
from tkinter import messagebox as startup_messagebox


class Notices:
    @staticmethod
    def _show(title, message, parent=None, **kwargs):
        root = parent._root() if parent is not None else tk._default_root
        if root is not None and hasattr(root, 'show_notice'):
            root.show_notice(title, message)
        else:
            # Only used for startup errors before the application can be built.
            return startup_messagebox.showerror(title, message, parent=parent, **kwargs)
        return 'ok'

    showerror = _show
    showwarning = _show
    showinfo = _show


messagebox = Notices()
