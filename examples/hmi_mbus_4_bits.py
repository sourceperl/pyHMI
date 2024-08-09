#!/usr/bin/env python3

from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool
from pyHMI.Tag import Tag
from pyHMI.Colors import GREEN, PINK
from pyHMI.UI import UIBoolListFrame, UIButtonListFrame
import time
import tkinter as tk
from tkinter import ttk


class Devices:
    md = ModbusTCPDevice('localhost', port=502, timeout=2.0)
    md.add_read_bits_table(0, 4)
    md.add_write_bits_table(0, 4, default_value=False)


class Tags:
    BIT_0 = Tag(False, src=ModbusBool(Devices.md, 0))
    BIT_1 = Tag(False, src=ModbusBool(Devices.md, 1))
    BIT_2 = Tag(False, src=ModbusBool(Devices.md, 2))
    BIT_3 = Tag(False, src=ModbusBool(Devices.md, 3))
    W_BIT_0 = Tag(False, src=ModbusBool(Devices.md, 0, write=True))
    W_BIT_1 = Tag(False, src=ModbusBool(Devices.md, 1, write=True))
    W_BIT_2 = Tag(False, src=ModbusBool(Devices.md, 2, write=True))
    W_BIT_3 = Tag(False, src=ModbusBool(Devices.md, 3, write=True))

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
        # Bits
        self.frmState = tk.LabelFrame(self, text='Bits state', padx=10, pady=10)
        self.frmState.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.state_list = UIBoolListFrame(self.frmState)
        self.state_list.add('PLC Bit 0', Tags.BIT_0, alarm=False)
        self.state_list.add('PLC Bit 1', Tags.BIT_1, alarm=False)
        self.state_list.add('PLC Bit 2', Tags.BIT_2, alarm=False)
        self.state_list.add('PLC Bit 3', Tags.BIT_3, alarm=False)
        # apply custom design and build
        for item in self.state_list.items:
            item.tk_lbl_value.configure(width=15)
        self.state_list.build().pack()
        self.frmCmd = tk.LabelFrame(self, text='Set/Reset', padx=10, pady=10)
        self.frmCmd.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.cmd_list = UIButtonListFrame(self.frmCmd, n_cols=2)
        self.cmd_list.add('Set Bit 0', cmd=lambda: Tags.W_BIT_0.set(True))
        self.cmd_list.add('Reset Bit 0', cmd=lambda: Tags.W_BIT_0.set(False))
        self.cmd_list.add('Set Bit 1', cmd=lambda: Tags.W_BIT_1.set(True))
        self.cmd_list.add('Reset Bit 1', cmd=lambda: Tags.W_BIT_1.set(False))
        self.cmd_list.add('Set Bit 2', cmd=lambda: Tags.W_BIT_2.set(True))
        self.cmd_list.add('Reset Bit 2', cmd=lambda: Tags.W_BIT_2.set(False))
        self.cmd_list.add('Set Bit 3', cmd=lambda: Tags.W_BIT_3.set(True))
        self.cmd_list.add('Reset Bit 3', cmd=lambda: Tags.W_BIT_3.set(False))
        # apply custom design and build
        btn_colors_t = ('light salmon', 'OliveDrab1')
        for idx, item in enumerate(self.cmd_list.items):
            item.tk_but.configure(width=10, bg=btn_colors_t[idx%2])
        self.cmd_list.build().pack()

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
        self.butTbox.configure(background=GREEN if Devices.md.connected else PINK)
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
