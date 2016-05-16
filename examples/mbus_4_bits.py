#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.Colors import *
from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import time
import tkinter as tk
from tkinter import ttk


class Devices(object):
    def __init__(self):
        # init datasource
        # PLC TBox
        self.plc = ModbusTCPDevice('localhost', port=502, timeout=2.0, refresh=1.0)
        # init modbus tables
        self.plc.add_bits_table(0, 4)


class Tags(object):
    def __init__(self, tk_app, update_ms=500):
        self.tk_app = tk_app
        self.update_ms = update_ms
        # Devices
        self.d = self.tk_app.d
        # tags list
        # from PLC
        self.BIT_0 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 0})
        self.BIT_1 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 1})
        self.BIT_2 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 2})
        self.BIT_3 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 3})
        # to PLC
        self.W_BIT_0 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 0})
        self.W_BIT_1 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 1})
        self.W_BIT_2 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 2})
        self.W_BIT_3 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 3})
        # launch update loop
        self.tk_app.do_every(self.update_tags, every_ms=self.update_ms)

    def update_tags(self):
        # update tags
        pass


class HMITab(tk.Frame):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, notebook, *args, **kwargs)
        self.notebook = notebook
        self.update_ms = update_ms
        # from main app
        self.app = notebook.master
        self.t = notebook.master.t
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
        # Bits
        self.frmState = tk.LabelFrame(self, text='Bits state', padx=10, pady=10)
        self.frmState.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.state_list = HMIBoolList(self.frmState, lbl_args={'width': 15})
        self.state_list.add('PLC Bit 0', self.t.BIT_0, alarm=False)
        self.state_list.add('PLC Bit 1', self.t.BIT_1, alarm=False)
        self.state_list.add('PLC Bit 2', self.t.BIT_2, alarm=False)
        self.state_list.add('PLC Bit 3', self.t.BIT_3, alarm=False)
        self.state_list.build()
        self.frmCmd = tk.LabelFrame(self, text='Set/Reset', padx=10, pady=10)
        self.frmCmd.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.cmd_list = HMIButtonList(self.frmCmd, dim=2, btn_args={'width': 10})
        c = ('light salmon', 'OliveDrab1')
        self.cmd_list.add('Set Bit 0', cmd=lambda: self.t.W_BIT_0.set(True), btn_args={'bg': c[0]})
        self.cmd_list.add('Reset Bit 0', cmd=lambda: self.t.W_BIT_0.set(False), btn_args={'bg': c[1]})
        self.cmd_list.add('Set Bit 1', cmd=lambda: self.t.W_BIT_1.set(True), btn_args={'bg': c[0]})
        self.cmd_list.add('Reset Bit 1', cmd=lambda: self.t.W_BIT_1.set(False), btn_args={'bg': c[1]})
        self.cmd_list.add('Set Bit 2', cmd=lambda: self.t.W_BIT_2.set(True), btn_args={'bg': c[0]})
        self.cmd_list.add('Reset Bit 2', cmd=lambda: self.t.W_BIT_2.set(False), btn_args={'bg': c[1]})
        self.cmd_list.add('Set Bit 3', cmd=lambda: self.t.W_BIT_3.set(True), btn_args={'bg': c[0]})
        self.cmd_list.add('Reset Bit 3', cmd=lambda: self.t.W_BIT_3.set(False), btn_args={'bg': c[1]})
        self.cmd_list.build()

    def tab_update(self):
        self.state_list.update()


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
        self.butTbox.configure(background=GREEN if self.tk_app.d.plc.connected else PINK)
        self.lblDate.configure(text=time.strftime('%H:%M:%S %d/%m/%Y'))


class HMIApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # configure main window
        self.wm_title('HMI nano test')
        # self.attributes('-fullscreen', True)
        self.geometry("800x600")
        # create devices
        self.d = Devices()
        # create tags
        self.t = Tags(self, update_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self)
        self.tab_misc = TabMisc(self.note)
        self.note.add(self.tab_misc, text='Misc (F1)')
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
