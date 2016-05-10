#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from HMI_Canvas import *
from HMI_Modbus import ModbusDevice
from HMI_Tags import Tags
import time
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Timer


class HMIApp(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        # create modbus client
        self.master.wm_title('Chilly simulator')
        # self.master.attributes('-fullscreen', True)
        self.master.geometry("800x600")
        # networks tasks
        self.init_net_task()
        self.do_every(self.update_net_task, every_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self.master)
        self.tab_int = Frame(self.note)
        self.tab_gny_dn900 = Frame(self.note)
        self.tab_aux = Frame(self.note)
        self.tab_sim = Frame(self.note)
        self.note.add(self.tab_int, text='Interconnexion')
        self.note.add(self.tab_gny_dn900, text='Gournay DN900')
        self.note.add(self.tab_aux, text='Auxiliaires')
        self.note.add(self.tab_sim, text='I/O simul')
        self.note.select(self.tab_int)
        self.note.pack(fill=BOTH, expand=True)
        # build tabs
        self.init_tab_interco()
        self.init_tab_gny_dn900()
        self.init_tab_aux()
        self.init_tab_io_simul()
        # update tabs when select
        self.do_every(self.update_tabs, every_ms=500)
        # add toolbar
        self.init_toolbar()
        # update tabs when select
        self.do_every(self.update_toolbar, every_ms=500)

    def init_net_task(self):
        # PLC TBox
        self.tbx = ModbusDevice('163.111.181.85', port=502, timeout=2.0)
        # init modbus tables
        # read bit start at @3050, size is 49
        self.tbx.add_bits_table(3050, 49)
        # read bit start at @1536, size is 8
        self.tbx.add_bits_table(1536, 8)
        # read word at @22016
        self.tbx.add_words_table(22016)
        # read floats start at @5030, size is 7
        self.tbx.add_floats_table(5030, 7)
        # PLC local
        self.reg = ModbusDevice('localhost', port=502, timeout=2.0)
        # read tags
        # external (from an external source)
        # bool
        self.DEF_EDF = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3050})
        self.DEF_CHG = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3051})
        self.DEF_OND = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3052})
        self.DEF_ATD1 = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3053})
        self.DEF_ATD2 = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3054})
        self.DEF_FEU = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3055})
        self.DEF_CENT = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3056})
        self.TC_AUTO = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3057})
        self.CONF_NOP = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3059})
        self.CMD_PST_ACT = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3060})
        self.CONF_REG = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3061})
        self.CONF_NEU = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3062})
        self.CONF_SEC = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3063})
        self.PIL_TELE = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3064, 'not': True})
        self.PIL_LOCAL = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3064})
        self.V1130_EV_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3066})
        self.V1130_EV_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3067})
        self.V1135_EV_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3068})
        self.V1135_EV_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3069})
        self.V1136_EV_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3070})
        self.V1136_EV_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3071})
        self.MV2_EV_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3072})
        #  self.MV2_EV_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3073})
        self.V1130_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3074})
        self.V1130_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3075})
        self.V1133_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3076})
        self.V1133_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3077})
        self.V1134_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3078})
        self.V1134_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3079})
        self.V1135_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3080})
        self.V1135_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3081})
        self.V1136_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3082})
        self.V1136_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3083})
        self.V1137_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3084})
        self.V1137_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3085})
        self.V1138_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3086})
        self.V1138_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3087})
        self.VL_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3088})
        self.VL_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3089})
        self.MV10_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3090})
        self.MV10_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3091})
        self.MV7_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3092})
        self.MV7_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3093})
        self.MV7_DEF_ELEC = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3094})
        self.MV7_DIST = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3095})
        self.MV7_HS = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3096})
        self.MV2_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3097})
        self.MV2_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3098})
        # analog
        self.P_GNY_DN900 = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5030})
        self.P_GNY_DN800 = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5032})
        self.P_ARL = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5034})
        self.P_AV_VL = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5036})
        self.Q_ANTENNES = Tags(0.0, src=self.tbx, ref={'type': 'float', 'addr': 5038})
        self.POS_VL = Tags(0.0, src=self.tbx, ref={'type': 'float', 'addr': 5040})
        # self.API_MDV = Tags(0, src=self.reg, ref={'type': 'word', 'addr': 5042})
        # virtual (a tag from tag(s))
        self.V_BIDULE_TEST = Tags(False, get_cmd=lambda: self.V1130_FDC_FER.val and self.V1133_FDC_FER.val)
        # local (no external source)
        self.HMI_WORD = Tags(0)
        # write tags
        self.V1130_CMD_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 524})
        self.V1130_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 525})
        self.V1135_CMD_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 530})
        self.V1135_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 531})
        self.V1136_CMD_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 532})
        self.V1136_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 533})
        self.MV2_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6023})
        self.MV2_CMD_PST = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6025})

    def update_net_task(self):
        # update tags
        self.HMI_WORD.set(self.HMI_WORD.val + 1)

    def init_tab_interco(self):
        # tab "interconnexion"
        self.map_int = HMICanvas(self.tab_int, width=800, height=550, debug=False)
        # add button
        self.map_int.add_button('GNY_800', 100, 400, text='Gournay DN800', state='disabled', disabledforeground=BLACK,
                                borderwidth=0)
        self.map_int.add_button('GNY_900', 100, 500, text='Gournay DN900',
                                command=lambda: self.note.select(self.tab_gny_dn900))
        self.map_int.add_button('ARL', 700, 400, text='Arleux DN800', state='disabled', disabledforeground=BLACK,
                                borderwidth=0)
        self.map_int.add_button('ANT_REG', 700, 50, text='Antennes REG', state='disabled', disabledforeground=BLACK,
                                borderwidth=0)
        # add simple valve
        self.map_int.add_s_valve('V1130', 400, 400, label='V1130', zoom=1)
        self.map_int.add_s_valve('V1133', 570, 340, label='V1133', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1134', 230, 340, label='V1134', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1135', 570, 140, label='V1135', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1136', 400, 230, label='V1136', zoom=0.8)
        self.map_int.add_s_valve('V1137', 230, 260, label='V1137', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1138', 230, 120, label='V1138', zoom=0.8, align='v')
        self.map_int.add_s_valve('MV2', 400, 500, label='MV2', zoom=1)
        # add flow valve
        self.map_int.add_f_valve('VL1', 230, 190, label='VL', zoom=0.8, align='v')
        # add point
        self.map_int.add_point('p1', 300, 50)
        self.map_int.add_point('p2', 570, 50)
        self.map_int.add_point('p3', 230, 400)
        self.map_int.add_point('p4', 570, 400)
        self.map_int.add_point('p5', 570, 230)
        # add pipes
        self.map_int.add_pipe('t6', from_name='p3', to_name='p1')
        self.map_int.add_pipe('t8', from_name='Q_ANTENNES', to_name='p2')
        self.map_int.add_pipe('t9', from_name='p2', to_name='V1135')
        self.map_int.add_pipe('t10', from_name='p3', to_name='V1130')
        self.map_int.add_pipe('t11', from_name='V1130', to_name='p4')
        self.map_int.add_pipe('t12', from_name='p4', to_name='ARL')
        self.map_int.add_pipe('t13', from_name='GNY_800', to_name='p3')
        self.map_int.add_pipe('t14', from_name='GNY_900', to_name='MV2')
        self.map_int.add_pipe('t15', from_name='p4', to_name='MV2')
        self.map_int.add_pipe('t16', from_name='p1', to_name='V1136')
        self.map_int.add_pipe('t17', from_name='V1136', to_name='p5')
        self.map_int.add_pipe('t18', from_name='p1', to_name='Q_ANTENNES')
        self.map_int.add_pipe('t19', from_name='V1135', to_name='p5')
        self.map_int.add_pipe('t20', from_name='p5', to_name='V1133')
        self.map_int.add_pipe('t21', from_name='V1133', to_name='p4')
        self.map_int.add_pipe('t22', from_name='p4', to_name='ANT_REG')
        # add value box
        self.map_int.add_vbox('P_GNY_DN900', 230, 475, get_value=lambda: self.P_GNY_DN900, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_GNY_DN800', 160, 300, get_value=lambda: self.P_GNY_DN800, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_ARL', 640, 300, get_value=lambda: self.P_ARL, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_AV_VL', 160, 80, get_value=lambda: self.P_AV_VL, prefix='P', suffix='bars')
        self.map_int.add_vbox('POS_VL', 160, 190, get_value=lambda: self.POS_VL, prefix='', suffix='%')
        self.map_int.add_vbox('Q_ANTENNES', 400, 50, get_value=lambda: self.Q_ANTENNES, prefix='Q', suffix='Nm3/h',
                              tk_fmt='{:.0f}')
        # custom widget
        # Pilotage poste
        self.frmConf = Frame(self.map_int.can)
        Label(self.frmConf, text='Pilot. poste').pack(fill=X)
        self.cnfDist = Label(self.frmConf, text='DISTANT', background=WHITE)
        self.cnfDist.pack(fill=X)
        self.cnfLoc = Label(self.frmConf, text='LOCAL', background=WHITE)
        self.cnfLoc.pack(fill=X)
        Label(self.frmConf, text='', background=GRAY).pack(fill=X)
        # Configuration poste
        Label(self.frmConf, text='TC Auto.').pack(fill=X)
        self.cnfAuto = Label(self.frmConf, text='AUTO', background=WHITE)
        self.cnfAuto.pack(fill=X)
        Label(self.frmConf, text='', background=GRAY).pack(fill=X)
        # Configuration poste
        Label(self.frmConf, text='Config. poste').pack(fill=X)
        self.cnfReg = Label(self.frmConf, text='REGIONAL', background=WHITE)
        self.cnfReg.pack(fill=X)
        self.cnfNeu = Label(self.frmConf, text='NEUTRE', background=WHITE)
        self.cnfNeu.pack(fill=X)
        self.cnfSec = Label(self.frmConf, text='SECURITE', background=WHITE)
        self.cnfSec.pack(fill=X)
        self.cnfNop = Label(self.frmConf, text='NON OP.', background=WHITE)
        self.cnfNop.pack(fill=X)
        self.frmConf.pack()
        self.map_int.can.create_window(55, 120, window=self.frmConf)
        # self.map_int.can.create_oval(50, 50, 150, 150, fill=HMI_Canvas.RED, outline=HMI_Canvas.RED, tag='CUST_LOCAL')
        # self.map_int.can.create_text(100, 100, text='LOCAL MODE', tag='CUST_LOCAL')
        # build all
        self.map_int.build()

    def update_tab_interco(self):
        # update value box
        self.map_int.update_vbox()
        # update valves on canvas
        self.map_int.simple_valve.animate('V1130', self.V1130_FDC_OUV, self.V1130_FDC_FER)
        self.map_int.simple_valve.animate('V1133', self.V1133_FDC_OUV, self.V1133_FDC_FER)
        self.map_int.simple_valve.animate('V1134', self.V1134_FDC_OUV, self.V1134_FDC_FER)
        self.map_int.simple_valve.animate('V1135', self.V1135_FDC_OUV, self.V1135_FDC_FER)
        self.map_int.simple_valve.animate('V1136', self.V1136_FDC_OUV, self.V1136_FDC_FER)
        self.map_int.simple_valve.animate('V1137', self.V1137_FDC_OUV, self.V1137_FDC_FER)
        self.map_int.simple_valve.animate('V1138', self.V1138_FDC_OUV, self.V1138_FDC_FER)
        self.map_int.simple_valve.animate('MV2', self.MV2_FDC_OUV, self.MV2_FDC_FER)
        # update config.
        self.cnfDist.configure(background=state_color(self.PIL_TELE))
        self.cnfLoc.configure(background=state_color(self.PIL_LOCAL))
        self.cnfAuto.configure(background=state_color(self.TC_AUTO))
        self.cnfReg.configure(background=state_color(self.CONF_REG))
        self.cnfNeu.configure(background=state_color(self.CONF_NEU))
        self.cnfSec.configure(background=state_color(self.CONF_SEC))
        self.cnfNop.configure(background=state_color(self.CONF_NOP))

    def init_tab_gny_dn900(self):
        # tab "Gournay DN900"
        self.map_gny_dn900 = HMICanvas(self.tab_gny_dn900, width=800, height=550, debug=False)
        # add valves
        self.map_gny_dn900.add_s_valve('MV2', 300, 200, label='MV2', zoom=1, align='v')
        self.map_gny_dn900.add_s_valve('MV7', 500, 200, label='MV7', zoom=0.8, align='v')
        self.map_gny_dn900.add_s_valve('MV10', 600, 300, label='MV10', zoom=0.8)
        # add points
        self.map_gny_dn900.add_point('p2', 300, 300)
        self.map_gny_dn900.add_point('p3', 500, 300)
        # add buttons
        self.map_gny_dn900.add_button('EVENT', 500, 100, text='Event', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('GARE', 700, 300, text='Gare', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('GNY', 100, 300, text='Gournay DN900', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('ARL', 300, 100, text='Arleux DN800', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('PST_MV2', 175, 200, text='Test partial stroke MV2',
                                      command=self.confirm_PST_MV2, state='disabled')
        self.map_gny_dn900.add_button('FER_MV2', 300, 350, text='Ferm. MV2 (isol. DN900 GNY)',
                                      command=self.confirm_isol_MV2, background=RED, state='disabled')
        # add pipes
        self.map_gny_dn900.add_pipe('t1', from_name='GNY', to_name='p2')
        self.map_gny_dn900.add_pipe('t2', from_name='p2', to_name='p3')
        self.map_gny_dn900.add_pipe('t3', from_name='p3', to_name='MV10')
        self.map_gny_dn900.add_pipe('t4', from_name='p3', to_name='MV7')
        self.map_gny_dn900.add_pipe('t5', from_name='p2', to_name='MV2')
        self.map_gny_dn900.add_pipe('t6', from_name='MV7', to_name='EVENT')
        self.map_gny_dn900.add_pipe('t7', from_name='MV10', to_name='GARE')
        self.map_gny_dn900.add_pipe('t8', from_name='MV2', to_name='ARL')
        self.map_gny_dn900.build()

    def update_tab_gny_dn900(self):
        # update vbox
        self.map_gny_dn900.update_vbox()
        # update valves on canvas
        self.map_gny_dn900.simple_valve.animate('MV2', self.MV2_FDC_OUV, self.MV2_FDC_FER)
        self.map_gny_dn900.simple_valve.animate('MV7', self.MV7_FDC_OUV, self.MV7_FDC_FER)
        self.map_gny_dn900.simple_valve.animate('MV10', self.MV10_FDC_OUV, self.MV10_FDC_FER)
        # validate command when local mode active
        if self.PIL_LOCAL.val:
            self.map_gny_dn900.d_widget['PST_MV2']['obj'].configure(state='normal')
            self.map_gny_dn900.d_widget['FER_MV2']['obj'].configure(state='normal')
        else:
            self.map_gny_dn900.d_widget['PST_MV2']['obj'].configure(state='disabled')
            self.map_gny_dn900.d_widget['FER_MV2']['obj'].configure(state='disabled')

    def init_tab_aux(self):
        # Energie
        self.frmEnergie = LabelFrame(self.tab_aux, text='Energie', padx=5, pady=5)
        self.lblEDF = Label(self.frmEnergie, text='Défaut EDF', background=WHITE)
        self.lblEDF.pack(fill=X)
        self.lblCHG = Label(self.frmEnergie, text='Défaut chargeur', background=WHITE)
        self.lblCHG.pack(fill=X)
        self.lblUPS = Label(self.frmEnergie, text='Défaut onduleur', background=WHITE)
        self.lblUPS.pack(fill=X)
        self.frmEnergie.grid(row=0, column=0, padx=5, pady=5, sticky=N)
        # ATD/Feu
        self.frmCentrale = LabelFrame(self.tab_aux, text='ATD/Feu', padx=5, pady=5)
        self.lblCENT = Label(self.frmCentrale, text='Défaut centrale', background=WHITE)
        self.lblCENT.pack(fill=X)
        self.lblATD1 = Label(self.frmCentrale, text='ATD 1', background=WHITE)
        self.lblATD1.pack(fill=X)
        self.lblATD2 = Label(self.frmCentrale, text='ATD 2', background=WHITE)
        self.lblATD2.pack(fill=X)
        self.lblFeu = Label(self.frmCentrale, text='Feu', background=WHITE)
        self.lblFeu.pack(fill=X)
        self.frmCentrale.grid(row=0, column=1, padx=5, pady=5, sticky=N)

    def update_tab_aux(self):
        self.lblEDF.configure(background=alarm_color(self.DEF_EDF))
        self.lblCHG.configure(background=alarm_color(self.DEF_CHG))
        self.lblUPS.configure(background=alarm_color(self.DEF_OND))
        self.lblATD1.configure(background=alarm_color(self.DEF_ATD1))
        self.lblATD2.configure(background=alarm_color(self.DEF_ATD2))
        self.lblFeu.configure(background=alarm_color(self.DEF_FEU))
        self.lblCENT.configure(background=alarm_color(self.DEF_CENT))

    def init_tab_io_simul(self):
        # tab "I/O simul"
        # self.tab_sim.resizable(width=FALSE, height=FALSE)
        # Vanne 1130
        self.lblVal = LabelFrame(self.tab_sim, text='Etat vannes', padx=20, pady=20)
        self.frame1130 = LabelFrame(self.lblVal, borderwidth=2, text='V.1130', relief=GROOVE, padx=10, pady=10)
        self.open1130But = Button(self.frame1130, text="Open", padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(525, False),
                                                   Timer(10, lambda: self.tbx.write_bit(524, True)).start()])
        self.open1130But.pack(fill=X)
        self.close1130But = Button(self.frame1130, text="Close", padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(524, False),
                                                    Timer(10, lambda: self.tbx.write_bit(525, True)).start()])
        self.close1130But.pack(fill=X)
        self.frame1130.grid(padx=10, pady=10, row=0, column=0)
        # Vanne 1133
        self.frame1133 = LabelFrame(self.lblVal, borderwidth=2, text='V.1133', relief=GROOVE, padx=10, pady=10)
        self.open1133But = Button(self.frame1133, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(527, False),
                                                   Timer(3, lambda: self.tbx.write_bit(526, True)).start()])
        self.open1133But.pack(fill=X)
        self.close1133But = Button(self.frame1133, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(526, False),
                                                    Timer(3, lambda: self.tbx.write_bit(527, True)).start()])
        self.close1133But.pack(fill=X)
        self.frame1133.grid(padx=10, pady=10, row=0, column=1)
        # Vanne 1134
        self.frame1134 = LabelFrame(self.lblVal, borderwidth=2, text='V.1134', relief=GROOVE, padx=10, pady=10)
        self.open1134But = Button(self.frame1134, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(529, False),
                                                   Timer(3, lambda: self.tbx.write_bit(528, True)).start()])
        self.open1134But.pack(fill=X)
        self.close1134But = Button(self.frame1134, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(528, False),
                                                    Timer(3, lambda: self.tbx.write_bit(529, True)).start()])
        self.close1134But.pack(fill=X)
        self.frame1134.grid(padx=10, pady=10, row=0, column=2)
        # Vanne 1135
        self.frame1135 = LabelFrame(self.lblVal, borderwidth=2, text='V.1135', relief=GROOVE, padx=10, pady=10)
        self.open1135But = Button(self.frame1135, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(531, False),
                                                   Timer(3, lambda: self.tbx.write_bit(530, True)).start()])
        self.open1135But.pack(fill=X)
        self.close1135But = Button(self.frame1135, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(530, False),
                                                    Timer(3, lambda: self.tbx.write_bit(531, True)).start()])
        self.close1135But.pack(fill=X)
        self.frame1135.grid(padx=10, pady=10, row=0, column=3)
        # Vanne 1136
        self.frame1136 = LabelFrame(self.lblVal, borderwidth=2, text='V.1136', relief=GROOVE, padx=10, pady=10)
        self.open1136But = Button(self.frame1136, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(533, False),
                                                   Timer(3, lambda: self.tbx.write_bit(532, True)).start()])
        self.open1136But.pack(fill=X)
        self.close1136But = Button(self.frame1136, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(532, False),
                                                    Timer(3, lambda: self.tbx.write_bit(533, True)).start()])
        self.close1136But.pack(fill=X)
        self.frame1136.grid(padx=10, pady=10, row=1, column=0)
        # Vanne 1137
        self.frame1137 = LabelFrame(self.lblVal, borderwidth=2, text='V.1137', relief=GROOVE, padx=10, pady=10)
        self.open1137But = Button(self.frame1137, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(535, False),
                                                   Timer(3, lambda: self.tbx.write_bit(534, True)).start()])
        self.open1137But.pack(fill=X)
        self.close1137But = Button(self.frame1137, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(534, False),
                                                    Timer(3, lambda: self.tbx.write_bit(535, True)).start()])
        self.close1137But.pack(fill=X)
        self.frame1137.grid(padx=10, pady=10, row=1, column=1)
        # Vanne 1138
        self.frame1138 = LabelFrame(self.lblVal, borderwidth=2, text='V.1138', relief=GROOVE, padx=10, pady=10)
        self.open1138But = Button(self.frame1138, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(537, False),
                                                   Timer(3, lambda: self.tbx.write_bit(536, True)).start()])
        self.open1138But.pack(fill=X)
        self.close1138But = Button(self.frame1138, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(536, False),
                                                    Timer(3, lambda: self.tbx.write_bit(537, True)).start()])
        self.close1138But.pack(fill=X)
        self.frame1138.grid(padx=10, pady=10, row=1, column=2)
        # Vanne 1138
        self.frameMV2 = LabelFrame(self.lblVal, borderwidth=2, text='MV2', relief=GROOVE, padx=10, pady=10)
        self.openMV2But = Button(self.frameMV2, text='Open', padx=20, pady=15,
                                 command=lambda: [self.tbx.write_bit(548, False),
                                                  Timer(3, lambda: self.tbx.write_bit(547, True)).start()])
        self.openMV2But.pack(fill=X)
        self.closeMV2But = Button(self.frameMV2, text='Close', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(547, False),
                                                   Timer(3, lambda: self.tbx.write_bit(548, True)).start()])
        self.closeMV2But.pack(fill=X)
        self.frameMV2.grid(padx=10, pady=10, row=1, column=3)
        self.lblVal.grid(padx=5, pady=5, row=0, columnspan=4)
        # Configuration poste
        self.lblConf = LabelFrame(self.tab_sim, text='Configuration', padx=20, pady=20)
        self.lblReg = Label(self.lblConf, text='REGIONAL')
        self.lblReg.pack(fill=X)
        self.lblNeu = Label(self.lblConf, text='NEUTRE')
        self.lblNeu.pack(fill=X)
        self.lblSec = Label(self.lblConf, text='SECURITE')
        self.lblSec.pack(fill=X)
        self.lblNop = Label(self.lblConf, text='NON OP.')
        self.lblNop.pack(fill=X)
        self.lblConf.grid(padx=5, pady=5, row=1, column=0, sticky=W + E + N + S)
        # Etat automate
        self.lblPlc = LabelFrame(self.tab_sim, text='Etat de l\'automate', padx=20, pady=20)
        self.lblTcAuto = Label(self.lblPlc, text='TC AUTO')
        self.lblTcAuto.pack(fill=X)
        self.lblSeqC = Label(self.lblPlc, text='SEQ EN COURS')
        self.lblSeqC.pack(fill=X)
        self.lblPlc.grid(padx=5, pady=5, row=1, column=1, sticky=W + E + N + S)
        # Pilotage
        self.lblPil = LabelFrame(self.tab_sim, text='Pilotage', padx=20, pady=20)
        self.lblPilTele = Label(self.lblPil, text='TELE')
        self.lblPilTele.pack(fill=X)
        self.lblPil.grid(padx=5, pady=5, row=1, column=2, sticky=W + E + N + S)
        # Commandes
        self.lblCmd = LabelFrame(self.tab_sim, text='Commandes', padx=20, pady=20)
        # Ack button
        self.ackButton = Button(self.lblCmd, text='Acquit défaut', command=self.ack_default)
        self.ackButton.pack(fill=X)
        self.lblCmd.grid(padx=5, pady=5, row=1, column=3, sticky=W + E + N + S)
        # display modbus cycle
        self.cycle_mbus_str = StringVar()
        Label(self.tab_sim, textvariable=self.cycle_mbus_str).grid(padx=5, pady=5, row=7, columnspan=3)

    def update_tab_simul(self):
        # update valve status
        # vanne 1130
        self.frame1130.configure(background=valve_color(self.V1130_FDC_OUV, self.V1130_FDC_FER))
        # vanne 1133
        self.frame1133.configure(background=valve_color(self.V1133_FDC_OUV, self.V1133_FDC_FER))
        # vanne 1134
        self.frame1134.configure(background=valve_color(self.V1134_FDC_OUV, self.V1134_FDC_FER))
        # vanne 1135
        self.frame1135.configure(background=valve_color(self.V1135_FDC_OUV, self.V1135_FDC_FER))
        # vanne 1136
        self.frame1136.configure(background=valve_color(self.V1136_FDC_OUV, self.V1136_FDC_FER))
        # vanne 1137
        self.frame1137.configure(background=valve_color(self.V1137_FDC_OUV, self.V1137_FDC_FER))
        # vanne 1138
        self.frame1138.configure(background=valve_color(self.V1138_FDC_OUV, self.V1138_FDC_FER))
        # vanne MV1
        self.frameMV2.configure(background=valve_color(self.MV2_FDC_OUV, self.MV2_FDC_FER))
        # update config.
        self.lblReg.configure(background=GREEN if self.CONF_REG.val else WHITE)
        self.lblNeu.configure(background=GREEN if self.CONF_NEU.val else WHITE)
        self.lblSec.configure(background=GREEN if self.CONF_SEC.val else WHITE)
        self.lblNop.configure(background=GREEN if self.CONF_NOP.val else WHITE)
        # PLC state
        self.lblPilTele.configure(text='TELE' if self.PIL_LOCAL.val else 'LOCAL')
        # label cycle modbus
        self.cycle_mbus_str.set('mot de vie TBOX=' + str(self.HMI_WORD.val))

    def update_tabs(self):
        # current ID of notebook select tab
        cur_tab = self.note.index(self.note.select())
        # run current update handler
        if cur_tab == self.note.index(self.tab_int):
            self.update_tab_interco()
        elif cur_tab == self.note.index(self.tab_gny_dn900):
            self.update_tab_gny_dn900()
        elif cur_tab == self.note.index(self.tab_aux):
            self.update_tab_aux()
        elif cur_tab == self.note.index(self.tab_sim):
            self.update_tab_simul()

    def init_toolbar(self):
        self.tbarFm = Frame(self.master)
        self.butTbox = Button(self.tbarFm, text='API T-Box', relief=SUNKEN)
        self.butTbox.pack(side=LEFT)
        self.butReg = Button(self.tbarFm, text='REG T640', relief=SUNKEN)
        self.butReg.pack(side=LEFT)
        self.tbarFm.pack(side=BOTTOM, fill=X)

    def update_toolbar(self):
        self.butTbox.configure(background=GREEN if self.tbx.connected else PINK)
        self.butReg.configure(background=GREEN if self.reg.connected else PINK)

    def ack_default(self):
        self.tbx.write_bit(522, True)
        time.sleep(.1)
        self.tbx.write_bit(522, False)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))

    def confirm_isol_MV2(self):
        result = messagebox.askquestion('Confirmation', 'Fermeture de MV2 ?', icon='warning', default='no')
        if result == 'yes':
            self.MV2_CMD_CLOSE.set(True)

    def confirm_PST_MV2(self):
        result = messagebox.askquestion('Confirmation', 'Test PST de MV2 ?', icon='warning', default='no')
        if result == 'yes':
            self.MV2_CMD_PST.set(True)


if __name__ == '__main__':
    # main Tk App
    root = tk.Tk()
    app = HMIApp(master=root)
    app.mainloop()
