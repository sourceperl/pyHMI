# -*- coding: utf-8 -*-

from tkinter import *
from .Colors import *


class ConfirmDialog(Toplevel):
    def __init__(self, parent, title, text, valid_command):
        super(ConfirmDialog, self).__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(title)
        self.valid_command = valid_command
        Label(self, text=text).grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        Button(self, text='Validation', command=self.ok).grid(row=1, column=0, padx=10, pady=10)
        Button(self, text='Annulation', command=self.cancel).grid(row=1, column=1, padx=10, pady=10)
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(45000, self.destroy)

    def ok(self):
        self.valid_command()
        self.destroy()

    def cancel(self):
        self.destroy()


class ValveOpenCloseDialog(Toplevel):
    def __init__(self, parent, title, text, open_command, close_command):
        super(ValveOpenCloseDialog, self).__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(title)
        self.open_command = open_command
        self.close_command = close_command
        Label(self, text=text).grid(row=0, column=0, columnspan=3, padx=20, pady=20)
        Button(self, text='Ouverture', command=self.open).grid(row=1, column=0, padx=10, pady=5)
        Button(self, text='Fermeture', command=self.close).grid(row=1, column=1, padx=10, pady=5)
        Button(self, text='Annulation', command=self.destroy, default=ACTIVE).grid(row=1, column=2, padx=10, pady=5)
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
        Label(self, text=text).grid(row=0, column=0, columnspan=3, padx=20, pady=20)
        Button(self, text='Fermeture', command=self.stop, background=RED).grid(row=1, column=0, padx=10, pady=5)
        Button(self, text='Test partiel', command=self.pst).grid(row=1, column=1, padx=10, pady=5)
        Button(self, text='Annulation', command=self.destroy, default=ACTIVE).grid(row=1, column=2, padx=10, pady=5)
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(45000, self.destroy)

    def stop(self):
        self.stop_command()
        self.destroy()

    def pst(self):
        self.pst_command()
        self.destroy()
