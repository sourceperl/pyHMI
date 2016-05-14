# -*- coding: utf-8 -*-

from tkinter import *
from .Colors import *


class ValveOpenCloseDialog(Toplevel):
    def __init__(self, parent, title, text, open_command, close_command):
        super(ValveOpenCloseDialog, self).__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(title)
        self.open_command = open_command
        self.close_command = close_command
        Label(self, text=text).pack(padx=20, pady=20)
        Button(self, text='Ouverture', command=self.open).pack(padx=15, side=LEFT)
        Button(self, text='Fermeture', command=self.close).pack(padx=15, side=LEFT)
        Button(self, text='Annulation', command=self.destroy, default=ACTIVE).pack(padx=15, side=LEFT)
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(45000, self.destroy)

    def open(self):
        self.open_command()
        self.destroy()

    def close(self):
        self.close_command()
        self.destroy()


class ValveESDDialog(Toplevel):
    def __init__(self, parent, title, text, stop_command, pst_command):
        super(ValveESDDialog, self).__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(title)
        self.stop_command = stop_command
        self.pst_command = pst_command
        Label(self, text=text).pack(padx=20, pady=20)
        Button(self, text='Fermeture', command=self.stop, background=RED).pack(padx=15, side=LEFT)
        Button(self, text='Test partiel', command=self.pst).pack(padx=15, side=LEFT)
        Button(self, text='Annulation', command=self.destroy, default=ACTIVE).pack(padx=15, side=LEFT)
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(45000, self.destroy)

    def stop(self):
        self.stop_command()
        self.destroy()

    def pst(self):
        self.pst_command()
        self.destroy()
