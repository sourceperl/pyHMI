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
    CP_COM_FAULT= Tag(0, src=Devices.redis, ref={'type': 'bool', 'key': 'cp4900:cp2redis:com_fault'})
    CP_THT = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:tht'})
    CP_STATE = Tag(0, src=Devices.redis, ref={'type': 'str', 'key': 'cp4900:state'})
    CP_RETENTION_TIME = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:retention_time'})
    CP_PEAK_AREA = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:peak_area'})
    CP_PRESSURE_GAS = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:pressure_gas'})
    CP_FLOW_GAS = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:flow_gas'})
    CP_ANALYSIS_FAULT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:analysis_fault'})
    CP_SENSOR_FAULT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:sensor_fault'})
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
        # Com state
        self.frmStateCom = tk.LabelFrame(self, text='Etat Com CP-4900 vers Redis', padx=10, pady=10)
        self.frmStateCom.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.com_l = HMIBoolList(self.frmStateCom, lbl_args={'width': 25})
        self.com_l.add('Liaison modbus ok', Tags.CP_COM_FAULT, label_1='Liaison modbus en défaut', alarm=True)
        self.com_l.build()
        self.frmInfoRedis = tk.LabelFrame(self, text='Gateway Redis', padx=10, pady=10)
        self.frmInfoRedis.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.state_list = HMIAnalogList(self.frmInfoRedis, lbl_args={'width': 15})
        self.state_list.add('Loop count', Tags.CP_LOOP_COUNT)
        self.state_list.build()
        # CP values
        self.frmValue = tk.LabelFrame(self, text='Valeurs CP-4900', padx=10, pady=10)
        self.frmValue.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.val_list = HMIAnalogList(self.frmValue, lbl_args={'width': 15})
        self.val_list.add('Etat CP-4900', Tags.CP_STATE)
        self.val_list.add('THT', Tags.CP_THT, unit='mg/nm3')
        self.val_list.add('Surface du peak', Tags.CP_PEAK_AREA)
        self.val_list.add('Temps de rétention', Tags.CP_RETENTION_TIME, unit='s')
        self.val_list.add('Pression du gaz', Tags.CP_PRESSURE_GAS, unit='mbar')
        self.val_list.add('Débit du gaz', Tags.CP_FLOW_GAS, unit='ml/h')
        self.val_list.add('Défaut analyse', Tags.CP_ANALYSIS_FAULT, unit='ok si égal à 0')
        self.val_list.add('Défaut capteur', Tags.CP_SENSOR_FAULT, unit='ok si < 10000')
        self.val_list.build()

    def tab_update(self):
        self.com_l.update()
        self.state_list.update()
        self.val_list.update()


class HMIToolbar(tk.Frame):
    def __init__(self, tk_app, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, tk_app, *args, **kwargs)
        self.tk_app = tk_app
        self.update_ms = update_ms
        # build toolbar
        self.butTbox = tk.Button(self, text='DB Redis', relief=tk.SOLID,
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
        self.wm_title('CP-4900 nano HMI')
        # self.attributes('-fullscreen', True)
        self.geometry("800x300")
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
