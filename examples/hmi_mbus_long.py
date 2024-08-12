#!/usr/bin/env python3

from pyHMI.Colors import GREEN, PINK
from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusInt
from pyHMI.Tag import Tag
from pyHMI.Dialog import SetIntValueDialog
from pyHMI.UI import UIAnalogListFrame, UIButtonListFrame
import time
import tkinter as tk
from tkinter import ttk


class Devices(object):
    # init datasource
    # PLC TBox
    plc = ModbusTCPDevice('localhost', port=502, timeout=2.0, refresh=1.0)
    plc_r_reg0_req = plc.add_read_regs_request(0, size=2, is_schedule=True)
    plc_w_reg0_req = plc.add_write_regs_request(0)
    plc_w_reg1_req = plc.add_write_regs_request(1)


class Tags(object):
    # tags list
    # from PLC
    R_LONG_0 = Tag(0, src=ModbusInt(Devices.plc_r_reg0_req, 0, bit_length=32))
    # to PLC
    W_WORD_0 = Tag(0, src=ModbusInt(Devices.plc_w_reg0_req, 0, sched_on_write=True))
    W_WORD_1 = Tag(0, src=ModbusInt(Devices.plc_w_reg1_req, 1, sched_on_write=True))

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
        self.frmState = tk.LabelFrame(self, text='Long value', padx=10, pady=10)
        self.frmState.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.longs_list = UIAnalogListFrame(self.frmState)
        self.longs_list.add('Long @0', Tags.R_LONG_0)
        # apply custom design and build
        for idx, item in enumerate(self.longs_list.items):
            item.tk_lbl_value.configure(width=15)
        self.longs_list.build().pack()
        self.frmCmd = tk.LabelFrame(self, text='Set/Reset', padx=10, pady=10)
        self.frmCmd.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.cmd_list = UIButtonListFrame(self.frmCmd, n_cols=2)
        self.cmd_list.add('Word @0 = 0xffff', cmd=lambda: Tags.W_WORD_0.set(0xffff))
        self.cmd_list.add('Word @0 = 0x0000', cmd=lambda: Tags.W_WORD_0.set(0x0))
        self.cmd_list.add('Word @1= 0xffff', cmd=lambda: Tags.W_WORD_1.set(0xffff))
        self.cmd_list.add('Word @1 = 0x0000', cmd=lambda: Tags.W_WORD_1.set(0x0),)
        # apply custom design and build
        btn_colors_t = ('light salmon', 'OliveDrab1')
        for idx, item in enumerate(self.cmd_list.items):
            item.tk_but.configure(width=15, bg=btn_colors_t[idx % 2])
        self.cmd_list.build().pack()
        # frame "set value of word"
        self.frmEntry = tk.LabelFrame(self, text='Set value of words', padx=10, pady=10)
        self.frmEntry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.button1 = tk.Button(self.frmEntry, text='Write @0',
                                 command=lambda: SetIntValueDialog(self, title='Saisie de valeur',
                                                                   text='Valeur du mot @0',
                                                                   valid_command=Tags.W_WORD_0.set))
        self.button1.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.button2 = tk.Button(self.frmEntry, text='Write @1',
                                 command=lambda: SetIntValueDialog(self, title='Saisie de valeur',
                                                                   text='Valeur du mot @1',
                                                                   valid_command=Tags.W_WORD_1.set))
        self.button2.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)

    def tab_update(self):
        self.longs_list.update()


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
        self.butTbox.configure(background=GREEN if Devices.plc.connected else PINK)
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
