#!/usr/bin/env python3

import logging
import time
from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool, ModbusInt, ModbusFloat
from pyHMI.Tag import Tag
from pyHMI.Colors import GREEN, PINK
from pyHMI.UI import UIBoolListFrame, UIButtonListFrame
import tkinter as tk
from tkinter import ttk

# global logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')


class Devices:
    plc = ModbusTCPDevice('192.168.1.99', port=502, timeout=2.0, refresh=0.5, client_args=dict(debug=True))
    plc_r_reg512 = plc.add_read_bits_request(512, size=4, run_cyclic=True)
    plc_w_reg512 = plc.add_write_bits_request(512, single_func=True, run_on_set=True)
    plc_w_reg513 = plc.add_write_bits_request(513, single_func=True, run_on_set=True)
    plc_w_reg514 = plc.add_write_bits_request(514, single_func=True, run_on_set=True)
    plc_w_reg515 = plc.add_write_bits_request(515, single_func=True, run_on_set=True)
    # immediate refresh on startup
    plc_r_reg512.run()


class Tags:
    R_REL_0 = Tag(False, src=ModbusBool(Devices.plc_r_reg512, 512))
    R_REL_1 = Tag(False, src=ModbusBool(Devices.plc_r_reg512, 513))
    R_REL_2 = Tag(False, src=ModbusBool(Devices.plc_r_reg512, 514))
    R_REL_3 = Tag(False, src=ModbusBool(Devices.plc_r_reg512, 515))
    W_REL_0 = Tag(False, src=ModbusBool(Devices.plc_w_reg512, 512))
    W_REL_1 = Tag(False, src=ModbusBool(Devices.plc_w_reg513, 513))
    W_REL_2 = Tag(False, src=ModbusBool(Devices.plc_w_reg514, 514))
    W_REL_3 = Tag(False, src=ModbusBool(Devices.plc_w_reg515, 515))

    @classmethod
    def update_tags(cls):
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
        # Relay status
        self.frmState = tk.LabelFrame(self, text='Relay status', padx=10, pady=10)
        self.frmState.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.state_list = UIBoolListFrame(self.frmState)
        self.state_list.add('PLC Bit 0', Tags.R_REL_0, alarm=False)
        self.state_list.add('PLC Bit 1', Tags.R_REL_1, alarm=False)
        self.state_list.add('PLC Bit 2', Tags.R_REL_2, alarm=False)
        self.state_list.add('PLC Bit 3', Tags.R_REL_3, alarm=False)
        # apply custom design and build
        for item in self.state_list.items:
            item.tk_lbl_value.configure(width=15)
        self.state_list.build().pack()
        self.frmCmd = tk.LabelFrame(self, text='Set/Reset', padx=10, pady=10)
        self.frmCmd.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.cmd_list = UIButtonListFrame(self.frmCmd, n_cols=2)
        self.cmd_list.add('Set All', cmd=lambda: self._set_all(True))
        self.cmd_list.add('Reset All', cmd=lambda: self._set_all(False))
        self.cmd_list.add('Set Bit 0', cmd=lambda: Tags.W_REL_0.set(True))
        self.cmd_list.add('Reset Bit 0', cmd=lambda: Tags.W_REL_0.set(False))
        self.cmd_list.add('Set Bit 1', cmd=lambda: Tags.W_REL_1.set(True))
        self.cmd_list.add('Reset Bit 1', cmd=lambda: Tags.W_REL_1.set(False))
        self.cmd_list.add('Set Bit 2', cmd=lambda: Tags.W_REL_2.set(True))
        self.cmd_list.add('Reset Bit 2', cmd=lambda: Tags.W_REL_2.set(False))
        self.cmd_list.add('Set Bit 3', cmd=lambda: Tags.W_REL_3.set(True))
        self.cmd_list.add('Reset Bit 3', cmd=lambda: Tags.W_REL_3.set(False))
        # apply custom design and build
        btn_colors_t = ('light salmon', 'OliveDrab1')
        for idx, item in enumerate(self.cmd_list.items):
            item.tk_but.configure(width=10, bg=btn_colors_t[idx % 2])
        self.cmd_list.build().pack()

    def _set_all(self, value: bool):
        Tags.W_REL_0.set(value)
        Tags.W_REL_1.set(value)
        Tags.W_REL_2.set(value)
        Tags.W_REL_3.set(value)

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
        self.butTbox.configure(background=GREEN if Devices.plc.connected else PINK)
        self.lblDate.configure(text=time.strftime('%H:%M:%S %d/%m/%Y'))


class HMIApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # configure main window
        self.wm_title('Relay control panel')
        # self.attributes('-fullscreen', True)
        self.geometry("800x600")
        # periodic tags update
        self.do_every(Tags.update_tags, every_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self)
        self.tab_misc = TabMisc(self.note)
        self.note.add(self.tab_misc, text='Relay (F1)')
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
