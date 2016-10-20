#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.Colors import *
from pyHMI.DS_Redis import RedisDevice
from pyHMI.Tag import Tag
import time
import tkinter as tk
from tkinter import ttk


class Devices(object):
    # init datasource
    # PLC TBox
    redis = RedisDevice()


class Tags(object):
    # tags list
    # from PLC
    CP_LOOP_COUNT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:cp2redis:loop_count'})
    CP_THT = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:tht'})
    CP_STATE = Tag(0, src=Devices.redis, ref={'type': 'str', 'key': 'cp4900:state'})

    @classmethod
    def update_tags(cls):
        # update tags
        pass


class HMITab(tk.Frame):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, notebook, *args, **kwargs)
        # global tk app shortcut
        self.notebook = notebook
        self.app = notebook.master
        # frame auto-refresh delay (in ms)
        self.update_ms = update_ms
        # setup auto-refresh of notebook tab (on-visibility and every update_ms)
        self.bind('<Visibility>', lambda evt: self.tab_update())
        self._tab_update()

    def _tab_update(self):
        if self.winfo_ismapped():
            self.tab_update()
        self.master.after(self.update_ms, self._tab_update)

    def tab_update(self):
        pass


class TabMisc(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Long
        self.frmStateCom = tk.LabelFrame(self, text='Etat Com avec CP-4900', padx=10, pady=10)
        self.frmStateCom.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.state_list = HMIAnalogList(self.frmStateCom, lbl_args={'width': 15})
        self.state_list.add('Loop count', Tags.CP_LOOP_COUNT)
        self.state_list.build()

        self.frmValue = tk.LabelFrame(self, text='Valeurs CP-4900', padx=10, pady=10)
        self.frmValue.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.val_list = HMIAnalogList(self.frmValue, lbl_args={'width': 15})
        self.val_list.add('Etat CP-4900', Tags.CP_STATE)
        self.val_list.add('THT', Tags.CP_THT)
        self.val_list.build()

    def tab_update(self):
        self.state_list.update()
        self.val_list.update()


class HMIToolbar(tk.Frame):
    def __init__(self, tk_app, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, tk_app, *args, **kwargs)
        self.tk_app = tk_app
        self.update_ms = update_ms
        # build toolbar
        self.butTbox = tk.Button(self, text='PLC', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butTbox.pack(side=tk.LEFT)
        self.lblDate = tk.Label(self, text='', font=('TkDefaultFont', 12))
        self.lblDate.pack(side=tk.RIGHT)
        self.pack(side=tk.BOTTOM, fill=tk.X)
        # setup auto-refresh of notebook tab (on-visibility and every update_ms)
        self.bind('<Visibility>', lambda evt: self.tab_update())
        self._tab_update()

    def _tab_update(self):
        self.tab_update()
        self.master.after(self.update_ms, self._tab_update)

    def tab_update(self):
        self.butTbox.configure(background=GREEN if Devices.redis.connected else PINK)
        self.lblDate.configure(text=time.strftime('%H:%M:%S %d/%m/%Y'))


class HMIApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # configure main window
        self.wm_title('HMI nano test')
        # self.attributes('-fullscreen', True)
        self.geometry("800x600")
        # periodic tags update
        self.do_every(Tags.update_tags, every_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self)
        self.tab_misc = TabMisc(self.note)
        self.note.add(self.tab_misc, text='CP-4900 (F1)')
        # defaut selected tab
        self.note.select(self.tab_misc)
        self.note.pack(fill=tk.BOTH, expand=True)
        # bind function keys to tabs
        self.bind('<F1>', lambda evt: self.note.select(self.tab_misc))
        # build toolbar
        self.toolbar = HMIToolbar(self, update_ms=500)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))


if __name__ == '__main__':
    # main Tk App
    app = HMIApp()
    app.mainloop()
