#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from HMI_Canvas import HMICanvas
from HMI_Colors import *
from HMI_Dialog import ValveOpenCloseDialog, ValveESDDialog
from HMI_Modbus import ModbusDevice
from HMI_Misc import Relay
from HMI_Tags import Tags
import time
import tkinter as tk
from tkinter import ttk
from threading import Timer


class HMIApp(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        # create modbus client
        self.master.wm_title('Poste de Chilly')
        # self.master.attributes('-fullscreen', True)
        self.master.geometry("800x600")
        # networks tasks
        self.init_net_task()
        # manage tags
        self.init_tags()
        self.do_every(self.update_tags, every_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self.master)
        self.tab_int = tk.Frame(self.note)
        self.tab_gny_dn900 = tk.Frame(self.note)
        self.tab_reg = tk.Frame(self.note)
        self.tab_info = tk.Frame(self.note)
        self.tab_sim = tk.Frame(self.note)
        self.note.add(self.tab_int, text='Interconnexion (F1)')
        self.note.add(self.tab_gny_dn900, text='Gournay DN900 (F2)')
        self.note.add(self.tab_reg, text='Régulation (F3)')
        self.note.add(self.tab_info, text='Informations (F4)')
        self.note.add(self.tab_sim, text='I/O simul (F5)')
        self.note.select(self.tab_int)
        self.note.pack(fill=tk.BOTH, expand=True)
        # refresh display when tab come above
        self.tab_int.bind('<Visibility>', lambda evt: self.update_tab_interco())
        self.tab_gny_dn900.bind('<Visibility>', lambda evt: self.update_tab_gny_dn900())
        self.tab_reg.bind('<Visibility>', lambda evt: self.update_tab_reg())
        self.tab_info.bind('<Visibility>', lambda evt: self.update_tab_info())
        self.tab_sim.bind('<Visibility>', lambda evt: self.update_tab_simul())
        # bind function keys to tabs
        self.master.bind('<F1>', lambda evt: self.note.select(self.tab_int))
        self.master.bind('<F2>', lambda evt: self.note.select(self.tab_gny_dn900))
        self.master.bind('<F3>', lambda evt: self.note.select(self.tab_reg))
        self.master.bind('<F4>', lambda evt: self.note.select(self.tab_info))
        self.master.bind('<F5>', lambda evt: self.note.select(self.tab_sim))
        # build tabs
        self.init_tab_interco()
        self.init_tab_gny_dn900()
        self.init_tab_info()
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
        self.tbx.add_bits_table(3050, 55)
        self.tbx.add_bits_table(1536, 8)
        self.tbx.add_words_table(4000, 4)
        self.tbx.add_floats_table(5030, 8)
        # Reg. T640
        self.reg = ModbusDevice('163.111.181.84', port=502, timeout=2.0)
        self.reg.add_bits_table(240, 9)
        self.reg.add_words_table(201, 6)
        # Aconcagua supervisor
        self.acon = ModbusDevice('163.111.181.83', port=502, timeout=2.0)
        self.acon.add_words_table(12288, 11)

    def init_tags(self):
        # null tag
        self.NULL_TAG = Tags(False)
        # Tbox PLC
        self.DEF_EDF = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3050})
        self.DEF_CHG = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3051})
        self.DEF_OND = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3052})
        self.DEF_ATD1 = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3053})
        self.DEF_ATD2 = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3054})
        self.DEF_FEU = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3055})
        self.DEF_CENT = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3056})
        self.TC_AUTO = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3057})
        self.TRA_EN_COURS = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3058})
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
        self.MV2_EV_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3072})
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
        self.DEF_SEQ_MV1130 = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3099})
        self.DEF_SEQ_MV1135 = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3100})
        self.DEF_SEQ_MV1136 = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3101})
        self.SEQ_MV1130_EN_COURS = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3102})
        self.SEQ_MV1135_EN_COURS = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3103})
        self.SEQ_MV1136_EN_COURS = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3104})
        self.TRA_REG_V_NEU = Tags(False, src=self.tbx, ref={'type': 'word', 'addr': 4000})
        self.TRA_REG_V_SEC = Tags(False, src=self.tbx, ref={'type': 'word', 'addr': 4001})
        self.TRA_NEU_V_REG = Tags(False, src=self.tbx, ref={'type': 'word', 'addr': 4002})
        self.TRA_NEU_V_SEC = Tags(False, src=self.tbx, ref={'type': 'word', 'addr': 4003})
        self.P_GNY_DN900 = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5030})
        self.P_GNY_DN800 = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5032})
        self.P_ARL = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5034})
        self.P_AV_VL = Tags(90.0, src=self.tbx, ref={'type': 'float', 'addr': 5036})
        self.Q_ANTENNES = Tags(0.0, src=self.tbx, ref={'type': 'float', 'addr': 5038})
        self.POS_VL = Tags(0.0, src=self.tbx, ref={'type': 'float', 'addr': 5040})
        self.POS_MV7 = Tags(0.0, src=self.tbx, ref={'type': 'float', 'addr': 5042})
        self.P_CPTGE = Tags(0.0, src=self.tbx, ref={'type': 'float', 'addr': 5044})
        # Reg T640
        self.REG_AUTO_D = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 240})
        self.REG_AUTO_L = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 241})
        self.REG_MANU = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 242})
        self.REG_MARCHE = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 243})
        self.REG_ARRET = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 244})
        self.REG_EN_ETL = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 245})
        self.REG_HORS_ETL = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 246})
        self.REG_DEF_MES_P = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 247})
        self.REG_ERR_CONS = Tags(False, src=self.reg, ref={'type': 'bit', 'addr': 248})
        self.REG_P_AM_VL = Tags(False, src=self.reg, ref={'type': 'word', 'addr': 201})
        self.REG_P_AV_VL = Tags(False, src=self.reg, ref={'type': 'word', 'addr': 202})
        self.REG_C_ACTIVE = Tags(False, src=self.reg, ref={'type': 'word', 'addr': 203})
        self.REG_C_CSR = Tags(False, src=self.reg, ref={'type': 'word', 'addr': 204})
        self.REG_SORTIE = Tags(False, src=self.reg, ref={'type': 'word', 'addr': 205})
        # Aconcagua
        self.ACON_MDV = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12288})
        self.ACON_PCS = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12289})
        self.ACON_DENS = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12290})
        self.ACON_PCS_ANC = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12291})
        self.ACON_N2 = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12292})
        self.ACON_CO2 = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12293})
        self.ACON_THT = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12294})
        self.ACON_THT_ANC = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12295})
        self.ACON_H2O = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12296})
        self.ACON_P_HE = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12297})
        self.ACON_P_AIR = Tags(0, src=self.acon, ref={'type': 'word', 'addr': 12298})
        # self.API_MDV = Tags(0, src=self.reg, ref={'type': 'word', 'addr': 4000})
        # virtual (a tag from tag(s))
        self.GET_TAG_TEST = Tags(False, get_cmd=lambda: self.V1130_FDC_FER.val and self.V1133_FDC_FER.val)
        # local (no external source)
        self.HMI_WORD = Tags(0)
        self.HMI_WORD2 = Tags(0)
        # write tags
        self.V1130_CMD_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6017})
        self.V1130_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6018})
        self.V1135_CMD_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6019})
        self.V1135_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6020})
        self.V1136_CMD_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6021})
        self.V1136_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6022})
        self.MV2_CMD_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6023})
        self.MV2_CMD_PST = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 6025})
        self.REG_MARCHE = Tags(False, src=self.reg, ref={'type': 'w_bit', 'addr': 220})
        self.REG_ARRET = Tags(False, src=self.reg, ref={'type': 'w_bit', 'addr': 221})
        self.ETL_MARCHE = Tags(False, src=self.reg, ref={'type': 'w_bit', 'addr': 222})
        self.ETL_ARRET = Tags(False, src=self.reg, ref={'type': 'w_bit', 'addr': 223})
        # TODO remove this after test
        self.r1 = Relay()
        self.r2 = Relay()
        self.r3 = Relay()
        self.r4 = Relay()
        self.r5 = Relay()
        self.r6 = Relay()

    def update_tags(self):
        # update tags
        self.HMI_WORD.set(self.HMI_WORD.val + 1)
        self.HMI_WORD2.set(self.HMI_WORD2.val + 3)
        # TODO debug remove this after test
        self.r1.state = self.V1130_EV_OUV.val
        self.r2.state = self.V1130_EV_FER.val
        self.r3.state = self.V1135_EV_OUV.val
        self.r4.state = self.V1135_EV_FER.val
        self.r5.state = self.V1136_EV_OUV.val
        self.r6.state = self.V1136_EV_FER.val

        # V1130
        if self.r1.trigger_pos():
            self.tbx.write_bit(525, False)
            Timer(5, lambda: self.tbx.write_bit(524, True)).start()
        if self.r2.trigger_pos():
            self.tbx.write_bit(524, False)
            Timer(5, lambda: self.tbx.write_bit(525, True)).start()

        # V1135
        if self.r3.trigger_pos():
            self.tbx.write_bit(531, False)
            Timer(5, lambda: self.tbx.write_bit(530, True)).start()
        if self.r4.trigger_pos():
            self.tbx.write_bit(530, False)
            Timer(5, lambda: self.tbx.write_bit(531, True)).start()

        # V1136
        if self.r5.trigger_pos():
            self.tbx.write_bit(533, False)
            Timer(5, lambda: self.tbx.write_bit(532, True)).start()
        if self.r6.trigger_pos():
            self.tbx.write_bit(532, False)
            Timer(5, lambda: self.tbx.write_bit(533, True)).start()


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
        self.map_int.add_button('MANAGE_V1130', 480, 370, text='V1130', command=self.confirm_v1130, state='disabled')
        self.map_int.add_button('MANAGE_V1135', 660, 140, text='V1135', command=self.confirm_v1135, state='disabled')
        self.map_int.add_button('MANAGE_V1136', 480, 200, text='V1136', command=self.confirm_v1136, state='disabled')
        self.map_int.add_button('MANAGE_MV2', 480, 470, text='MV2', command=self.confirm_mv2, state='disabled')
        # add simple valve
        self.map_int.add_s_valve('V1133', 570, 340, label='V1133', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1134', 230, 340, label='V1134', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1137', 230, 260, label='V1137', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1138', 230, 120, label='V1138', zoom=0.8, align='v')
        # add simple valve
        self.map_int.add_m_valve('V1130', 400, 400, label='V1130', zoom=1)
        self.map_int.add_m_valve('V1135', 570, 140, label='V1135', zoom=0.8, align='v')
        self.map_int.add_m_valve('V1136', 400, 230, label='V1136', zoom=0.8)
        self.map_int.add_m_valve('MV2', 400, 500, label='MV2', zoom=1)
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
        self.frmConf = tk.Frame(self.map_int.can)
        tk.Label(self.frmConf, text='Pilot. poste').pack(fill=tk.X)
        self.cnfDist = tk.Label(self.frmConf, text='DISTANT', background=WHITE)
        self.cnfDist.pack(fill=tk.X)
        self.cnfLoc = tk.Label(self.frmConf, text='LOCAL', background=WHITE)
        self.cnfLoc.pack(fill=tk.X)
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        # Configuration poste
        tk.Label(self.frmConf, text='TC Auto.').pack(fill=tk.X)
        self.cnfAuto = tk.Label(self.frmConf, text='AUTO', background=WHITE)
        self.cnfAuto.pack(fill=tk.X)
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        # Configuration poste
        tk.Label(self.frmConf, text='Config. poste').pack(fill=tk.X)
        self.cnfReg = tk.Label(self.frmConf, text='REGIONAL', background=WHITE)
        self.cnfReg.pack(fill=tk.X)
        self.cnfNeu = tk.Label(self.frmConf, text='NEUTRE', background=WHITE)
        self.cnfNeu.pack(fill=tk.X)
        self.cnfSec = tk.Label(self.frmConf, text='SECURITE', background=WHITE)
        self.cnfSec.pack(fill=tk.X)
        self.cnfNop = tk.Label(self.frmConf, text='NON OP.', background=WHITE)
        self.cnfNop.pack(fill=tk.X)
        self.frmConf.pack()
        self.map_int.can.create_window(55, 120, window=self.frmConf)
        # self.map_int.can.create_oval(50, 50, 150, 150, fill=HMI_Canvas.RED, outline=HMI_Canvas.RED, tag='CUST_LOCAL')
        # self.map_int.can.create_text(100, 100, text='LOCAL MODE', tag='CUST_LOCAL')
        # build all
        self.map_int.build()

    def update_tab_interco(self):
        # update value box
        self.map_int.update_vbox()
        # update simple valves
        self.map_int.simple_valve.tag_anim('V1133', self.V1133_FDC_OUV, self.V1133_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1134', self.V1134_FDC_OUV, self.V1134_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1137', self.V1137_FDC_OUV, self.V1137_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1138', self.V1138_FDC_OUV, self.V1138_FDC_FER)
        self.map_int.flow_valve.tag_anim('VL1', self.VL_FDC_OUV, self.VL_FDC_FER)
        self.map_int.flow_valve.pos_tag_anim('VL1', self.POS_VL)
        # update motor valves
        self.map_int.motor_valve.tag_anim('V1130', self.V1130_FDC_OUV, self.V1130_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1130', self.V1130_EV_OUV, self.V1130_EV_FER, self.DEF_SEQ_MV1130)
        self.map_int.motor_valve.tag_anim('V1135', self.V1135_FDC_OUV, self.V1135_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1135', self.V1135_EV_OUV, self.V1135_EV_FER, self.DEF_SEQ_MV1135)
        self.map_int.motor_valve.tag_anim('V1136', self.V1136_FDC_OUV, self.V1136_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1136', self.V1136_EV_OUV, self.V1136_EV_FER, self.DEF_SEQ_MV1136)
        self.map_int.motor_valve.tag_anim('MV2', self.MV2_FDC_OUV, self.MV2_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('MV2', self.NULL_TAG, self.MV2_EV_FER)
        # update config.
        self.cnfDist.configure(background=color_tag_state(self.PIL_TELE))
        self.cnfLoc.configure(background=color_tag_state(self.PIL_LOCAL))
        self.cnfAuto.configure(background=color_tag_state(self.TC_AUTO))
        self.cnfReg.configure(background=color_tag_state(self.CONF_REG))
        self.cnfNeu.configure(background=color_tag_state(self.CONF_NEU))
        self.cnfSec.configure(background=color_tag_state(self.CONF_SEC))
        self.cnfNop.configure(background=color_tag_state(self.CONF_NOP))
        # validate command when local mode active
        if self.PIL_LOCAL.val:
            self.map_int.d_widget['MANAGE_V1130']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_V1135']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_V1136']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_MV2']['obj'].configure(state='normal')
        else:
            self.map_int.d_widget['MANAGE_V1130']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_V1135']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_V1136']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_MV2']['obj'].configure(state='disabled')

    def init_tab_gny_dn900(self):
        # tab "Gournay DN900"
        self.map_gny_dn900 = HMICanvas(self.tab_gny_dn900, width=800, height=550, debug=False)
        # add valves
        self.map_gny_dn900.add_m_valve('MV2', 300, 200, label='MV2', zoom=1, align='v')
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
        self.map_gny_dn900.add_button('MANAGE_MV2', 220, 200, text='MV2',
                                      command=self.confirm_mv2, state='disabled')
        # add pipes
        self.map_gny_dn900.add_pipe('t1', from_name='GNY', to_name='p2')
        self.map_gny_dn900.add_pipe('t2', from_name='p2', to_name='p3')
        self.map_gny_dn900.add_pipe('t3', from_name='p3', to_name='MV10')
        self.map_gny_dn900.add_pipe('t4', from_name='p3', to_name='MV7')
        self.map_gny_dn900.add_pipe('t5', from_name='p2', to_name='MV2')
        self.map_gny_dn900.add_pipe('t6', from_name='MV7', to_name='EVENT')
        self.map_gny_dn900.add_pipe('t7', from_name='MV10', to_name='GARE')
        self.map_gny_dn900.add_pipe('t8', from_name='MV2', to_name='ARL')
        # add vbox
        self.map_gny_dn900.add_vbox('POS_MV7', 430, 200, get_value=lambda: self.POS_MV7, prefix='', suffix='%')

        # MV7 info panel
        self.frmMV7 = tk.Frame(self.map_gny_dn900.can)
        self.frmMV7.pack()
        self.mv7_list = HMIBoolList(self.frmMV7, head_str='Etat MV7')
        self.mv7_list.add('Distant', self.MV7_DIST, width=10)
        self.mv7_list.add('Hors-Service', self.MV7_HS, width=10)
        self.mv7_list.add('Défaut élec.', self.MV7_DEF_ELEC, width=10)
        self.mv7_list.build()
        self.map_gny_dn900.can.create_window(600, 160, window=self.frmMV7)
        self.map_gny_dn900.build()

    def update_tab_gny_dn900(self):
        # update vbox
        self.map_gny_dn900.update_vbox()
        # update valves on canvas
        self.map_gny_dn900.motor_valve.tag_anim('MV2', self.MV2_FDC_OUV, self.MV2_FDC_FER)
        self.map_gny_dn900.motor_valve.motor_tag_anim('MV2', self.NULL_TAG, self.MV2_EV_FER)
        self.map_gny_dn900.simple_valve.tag_anim('MV7', self.MV7_FDC_OUV, self.MV7_FDC_FER)
        self.map_gny_dn900.simple_valve.tag_anim('MV10', self.MV10_FDC_OUV, self.MV10_FDC_FER)
        # validate command when local mode active
        if self.PIL_LOCAL.val:
            self.map_gny_dn900.d_widget['MANAGE_MV2']['obj'].configure(state='normal')
        else:
            self.map_gny_dn900.d_widget['MANAGE_MV2']['obj'].configure(state='disabled')
        # update MV7 info panel
        self.mv7_list.update()

    def init_tab_reg(self):
        pass

    def update_tab_reg(self):
        pass

    def init_tab_info(self):
        # Energie
        self.tab_info.frmEnergie = tk.LabelFrame(self.tab_info, text='Energie', padx=10, pady=10)
        self.tab_info.frmEnergie.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NS)
        self.tab_info.energie_list = HMIBoolList(self.tab_info.frmEnergie)
        self.tab_info.energie_list.add('Absence EDF', self.DEF_EDF, alarm=True, width=15)
        self.tab_info.energie_list.add('Défaut chargeur', self.DEF_CHG, alarm=True, width=15)
        self.tab_info.energie_list.add('Défaut onduleur', self.DEF_OND, alarm=True, width=15)
        self.tab_info.energie_list.build()
        # ATD/Feu
        self.tab_info.frmCentrale = tk.LabelFrame(self.tab_info, text='ATD/Feu', padx=10, pady=10)
        self.tab_info.frmCentrale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NS)
        self.tab_info.centrale_list = HMIBoolList(self.tab_info.frmCentrale)
        self.tab_info.centrale_list.add('Défaut centrale', self.DEF_CENT, alarm=True, width=15)
        self.tab_info.centrale_list.add('ATD stade 1', self.DEF_ATD1, alarm=True, width=15)
        self.tab_info.centrale_list.add('ATD stade 2', self.DEF_ATD2, alarm=True, width=15)
        self.tab_info.centrale_list.add('Feu', self.DEF_FEU, alarm=True, width=15)
        self.tab_info.centrale_list.build()
        # Pilotage
        self.tab_info.lblPil = tk.LabelFrame(self.tab_info, text='Pilotage', padx=10, pady=10)
        self.tab_info.lblPil.grid(row=0, column=2, padx=5, pady=5,  sticky=tk.NS)
        self.tab_info.pilotage_list = HMIBoolList(self.tab_info.lblPil)
        self.tab_info.pilotage_list.add('Distant', self.PIL_TELE, width=10)
        self.tab_info.pilotage_list.add('Local', self.PIL_LOCAL, width=10)
        self.tab_info.pilotage_list.add('TC Auto', self.TC_AUTO, width=10)
        self.tab_info.pilotage_list.build()
        # Configuration
        self.tab_info.lblConf = tk.LabelFrame(self.tab_info, text='Configuration', padx=10, pady=10)
        self.tab_info.lblConf.grid(row=0, column=3, padx=5, pady=5, sticky=tk.NS)
        self.tab_info.conf_list = HMIBoolList(self.tab_info.lblConf)
        self.tab_info.conf_list.add('En Transition', self.TRA_EN_COURS, width=10)
        self.tab_info.conf_list.add('Régional', self.CONF_REG, width=10)
        self.tab_info.conf_list.add('Neutre', self.CONF_NEU, width=10)
        self.tab_info.conf_list.add('Sécurité', self.CONF_SEC, width=10)
        self.tab_info.conf_list.add('Non Op.', self.CONF_NOP, width=10)
        self.tab_info.conf_list.build()
        # Transitions
        self.tab_info.lblTrans = tk.LabelFrame(self.tab_info, text='Transitions', padx=0, pady=5)
        self.tab_info.lblTrans.grid(row=0, column=4, padx=5, pady=5, sticky=tk.NS)
        self.tab_info.tran = HMIAnalogList(self.tab_info.lblTrans)
        self.tab_info.tran.add('Neutre vers régionale', self.TRA_NEU_V_REG, unit='niv')
        self.tab_info.tran.add('Régionale vers neutre', self.TRA_REG_V_NEU, unit='niv')
        self.tab_info.tran.add('Neutre vers sécurité', self.TRA_NEU_V_SEC, unit='niv')
        self.tab_info.tran.add('Régionale vers sécurité', self.TRA_REG_V_SEC, unit='niv')
        self.tab_info.tran.build()
        # Laboratoire
        self.tab_info.frmLabo = tk.LabelFrame(self.tab_info, text='Laboratoire', padx=5, pady=5)
        self.tab_info.frmLabo.grid(row=1, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.tab_info.labo_list = HMIAnalogList(self.tab_info.frmLabo)
        self.tab_info.labo_list.add('PCS', self.ACON_PCS, 'w/nm3', width=10)
        self.tab_info.labo_list.add('Densité', self.ACON_DENS, width=10)
        self.tab_info.labo_list.add('Azote', self.ACON_N2, '%', width=10)
        self.tab_info.labo_list.add('CO2', self.ACON_CO2, '%', width=10)
        self.tab_info.labo_list.add('PCS Ancienneté', self.ACON_PCS_ANC, 'min', width=10)
        self.tab_info.labo_list.add('THT', self.ACON_THT, 'mg/Nm3', width=10)
        self.tab_info.labo_list.add('THT Ancienneté', self.ACON_THT_ANC, 'min', width=10)
        self.tab_info.labo_list.add('Taux H2O', self.ACON_H2O, 'mg/Nm3', width=10)
        self.tab_info.labo_list.add('P Air', self.ACON_P_AIR, 'bars rel.', width=10)
        self.tab_info.labo_list.add('P Hélium', self.ACON_P_HE, 'bars rel.', width=10)
        self.tab_info.labo_list.add('Mot de vie Acon.', self.ACON_MDV, '', width=10)
        self.tab_info.labo_list.build()
        #  Poste
        self.tab_info.frmPoste = tk.LabelFrame(self.tab_info, text='Poste', padx=5, pady=5)
        self.tab_info.frmPoste.grid(row=1, column=2, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        self.tab_info.poste_list = HMIAnalogList(self.tab_info.frmPoste)
        self.tab_info.poste_list.add('Q vers antennes régionales', self.Q_ANTENNES, 'Nm3/h', fmt='%d', width=10)
        self.tab_info.poste_list.add('P comptage (aval VL)', self.NULL_TAG, 'Nm3/h', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('P Gournay DN900 (amt MV2)', self.P_GNY_DN900, 'bars rel.', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('P Arleux', self.P_ARL, 'bars rel.', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('P amont VL', self.P_GNY_DN800, 'bars rel.', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('P aval VL', self.P_AV_VL, 'bars rel.', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('Position MV7', self.POS_MV7, '%', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('Position VL', self.POS_VL, '%', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('Sortie régulateur VL', self.REG_SORTIE, '%', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('Consigne active REG P aval', self.REG_C_ACTIVE, 'bars rel.', fmt='%.02f', width=10)
        self.tab_info.poste_list.add('Consigne CSR REG P aval', self.REG_C_CSR, 'bars rel.', fmt='%.02f', width=10)
        self.tab_info.poste_list.build()

    def update_tab_info(self):
        # Energie
        self.tab_info.energie_list.update()
        # ATD/Feu
        self.tab_info.centrale_list.update()
        # Pilotage
        self.tab_info.pilotage_list.update()
        # Configuration
        self.tab_info.conf_list.update()
        # Transition
        self.tab_info.tran.update()
        # Laboratoire
        self.tab_info.labo_list.update()
        # Poste
        self.tab_info.poste_list.update()

    def init_tab_io_simul(self):
        # TODO remove IO simul at end of project
        # tab "I/O simul"
        # self.tab_sim.resizable(width=FALSE, height=FALSE)
        # Vanne 1130
        self.lblVal = tk.LabelFrame(self.tab_sim, text='Etat vannes', padx=5, pady=5)
        self.lblVal.grid(padx=5, pady=5, row=0, columnspan=4, sticky=tk.NSEW)
        self.frame1130 = tk.LabelFrame(self.lblVal, borderwidth=2, text='V.1130', relief=tk.GROOVE, padx=10, pady=10)
        self.open1130But = tk.Button(self.frame1130, text="Open", padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(525, False),
                                                   Timer(10, lambda: self.tbx.write_bit(524, True)).start()])
        self.open1130But.pack(fill=tk.X)
        self.close1130But = tk.Button(self.frame1130, text="Close", padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(524, False),
                                                    Timer(10, lambda: self.tbx.write_bit(525, True)).start()])
        self.close1130But.pack(fill=tk.X)
        self.frame1130.grid(padx=10, pady=10, row=0, column=0)
        # Vanne 1133
        self.frame1133 = tk.LabelFrame(self.lblVal, borderwidth=2, text='V.1133', relief=tk.GROOVE, padx=10, pady=10)
        self.open1133But = tk.Button(self.frame1133, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(527, False),
                                                   Timer(3, lambda: self.tbx.write_bit(526, True)).start()])
        self.open1133But.pack(fill=tk.X)
        self.close1133But = tk.Button(self.frame1133, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(526, False),
                                                    Timer(3, lambda: self.tbx.write_bit(527, True)).start()])
        self.close1133But.pack(fill=tk.X)
        self.frame1133.grid(padx=10, pady=10, row=0, column=1)
        # Vanne 1134
        self.frame1134 = tk.LabelFrame(self.lblVal, borderwidth=2, text='V.1134', relief=tk.GROOVE, padx=10, pady=10)
        self.open1134But = tk.Button(self.frame1134, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(529, False),
                                                   Timer(3, lambda: self.tbx.write_bit(528, True)).start()])
        self.open1134But.pack(fill=tk.X)
        self.close1134But = tk.Button(self.frame1134, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(528, False),
                                                    Timer(3, lambda: self.tbx.write_bit(529, True)).start()])
        self.close1134But.pack(fill=tk.X)
        self.frame1134.grid(padx=10, pady=10, row=0, column=2)
        # Vanne 1135
        self.frame1135 = tk.LabelFrame(self.lblVal, borderwidth=2, text='V.1135', relief=tk.GROOVE, padx=10, pady=10)
        self.open1135But = tk.Button(self.frame1135, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(531, False),
                                                   Timer(3, lambda: self.tbx.write_bit(530, True)).start()])
        self.open1135But.pack(fill=tk.X)
        self.close1135But = tk.Button(self.frame1135, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(530, False),
                                                    Timer(3, lambda: self.tbx.write_bit(531, True)).start()])
        self.close1135But.pack(fill=tk.X)
        self.frame1135.grid(padx=10, pady=10, row=0, column=3)
        # Vanne 1136
        self.frame1136 = tk.LabelFrame(self.lblVal, borderwidth=2, text='V.1136', relief=tk.GROOVE, padx=10, pady=10)
        self.open1136But = tk.Button(self.frame1136, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(533, False),
                                                   Timer(3, lambda: self.tbx.write_bit(532, True)).start()])
        self.open1136But.pack(fill=tk.X)
        self.close1136But = tk.Button(self.frame1136, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(532, False),
                                                    Timer(3, lambda: self.tbx.write_bit(533, True)).start()])
        self.close1136But.pack(fill=tk.X)
        self.frame1136.grid(padx=10, pady=10, row=1, column=0)
        # Vanne 1137
        self.frame1137 = tk.LabelFrame(self.lblVal, borderwidth=2, text='V.1137', relief=tk.GROOVE, padx=10, pady=10)
        self.open1137But = tk.Button(self.frame1137, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(535, False),
                                                   Timer(3, lambda: self.tbx.write_bit(534, True)).start()])
        self.open1137But.pack(fill=tk.X)
        self.close1137But = tk.Button(self.frame1137, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(534, False),
                                                    Timer(3, lambda: self.tbx.write_bit(535, True)).start()])
        self.close1137But.pack(fill=tk.X)
        self.frame1137.grid(padx=10, pady=10, row=1, column=1)
        # Vanne 1138
        self.frame1138 = tk.LabelFrame(self.lblVal, borderwidth=2, text='V.1138', relief=tk.GROOVE, padx=10, pady=10)
        self.open1138But = tk.Button(self.frame1138, text='Open', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(537, False),
                                                   Timer(3, lambda: self.tbx.write_bit(536, True)).start()])
        self.open1138But.pack(fill=tk.X)
        self.close1138But = tk.Button(self.frame1138, text='Close', padx=20, pady=15,
                                   command=lambda: [self.tbx.write_bit(536, False),
                                                    Timer(3, lambda: self.tbx.write_bit(537, True)).start()])
        self.close1138But.pack(fill=tk.X)
        self.frame1138.grid(padx=10, pady=10, row=1, column=2)
        # Vanne 1138
        self.frameMV2 = tk.LabelFrame(self.lblVal, borderwidth=2, text='MV2', relief=tk.GROOVE, padx=10, pady=10)
        self.openMV2But = tk.Button(self.frameMV2, text='Open', padx=20, pady=15,
                                 command=lambda: [self.tbx.write_bit(548, False),
                                                  Timer(3, lambda: self.tbx.write_bit(547, True)).start()])
        self.openMV2But.pack(fill=tk.X)
        self.closeMV2But = tk.Button(self.frameMV2, text='Close', padx=20, pady=15,
                                  command=lambda: [self.tbx.write_bit(547, False),
                                                   Timer(3, lambda: self.tbx.write_bit(548, True)).start()])
        self.closeMV2But.pack(fill=tk.X)
        self.frameMV2.grid(padx=10, pady=10, row=1, column=3)
        # Configuration poste
        self.lblConf = tk.LabelFrame(self.tab_sim, text='Configuration', padx=10, pady=10)
        self.lblConf.grid(padx=5, pady=5, row=1, column=0, sticky=tk.NSEW)
        self.conf_list = HMIBoolList(self.lblConf)
        self.conf_list.add('Régional', self.CONF_REG, width=10)
        self.conf_list.add('Neutre', self.CONF_NEU, width=10)
        self.conf_list.add('Sécurité', self.CONF_SEC, width=10)
        self.conf_list.add('Non Op.', self.CONF_NOP, width=10)
        self.conf_list.build()
        # Etat automate
        self.lblPlc = tk.LabelFrame(self.tab_sim, text='Etat de l\'automate', padx=10, pady=10)
        self.lblPlc.grid(padx=5, pady=5, row=1, column=1, sticky=tk.NSEW)
        self.plc_list = HMIBoolList(self.lblPlc)
        self.plc_list.add('TC AUTO', self.TC_AUTO, width=15)
        self.plc_list.add('TRAN. EN COURS', self.TRA_EN_COURS, width=15)
        self.plc_list.add('SEQ ACT MV1130 ', self.SEQ_MV1130_EN_COURS, width=15)
        self.plc_list.add('DEF SEQ MV1130', self.DEF_SEQ_MV1130, width=15, alarm=True)
        self.plc_list.add('SEQ ACT MV1135', self.SEQ_MV1135_EN_COURS, width=15)
        self.plc_list.add('DEF SEQ MV1135', self.DEF_SEQ_MV1135, width=15, alarm=True)
        self.plc_list.add('SEQ ACT MV1136', self.SEQ_MV1136_EN_COURS, width=15)
        self.plc_list.add('DEF SEQ MV1136', self.DEF_SEQ_MV1136, width=15, alarm=True)
        self.plc_list.build()
        # Pilotage
        self.lblPil = tk.LabelFrame(self.tab_sim, text='Pilotage', padx=10, pady=10)
        self.lblPil.grid(padx=5, pady=5, row=1, column=2, sticky=tk.NSEW)
        self.pilotage_list = HMIBoolList(self.lblPil)
        self.pilotage_list.add('DISTANT', self.PIL_TELE, width=10)
        self.pilotage_list.add('LOCAL', self.PIL_LOCAL, width=10)
        self.pilotage_list.build()
        # Commandes
        self.lblCmd = tk.LabelFrame(self.tab_sim, text='Commandes', padx=10, pady=10)
        # Local button
        tk.Button(self.lblCmd, text='Distant', command=lambda: self.tbx.write_bit(520, False)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='Local', command=lambda: self.tbx.write_bit(520, True)).pack(fill=tk.X)
        # Ack button
        tk.Button(self.lblCmd, text='Acquit défaut', command=self.ack_default).pack(fill=tk.X)
        self.lblCmd.grid(padx=5, pady=5, row=1, column=3, sticky=tk.NSEW)

    def update_tab_simul(self):
        # update valve status
        # vanne 1130
        self.frame1130.configure(background=color_tags_valve(self.V1130_FDC_OUV, self.V1130_FDC_FER))
        # vanne 1133
        self.frame1133.configure(background=color_tags_valve(self.V1133_FDC_OUV, self.V1133_FDC_FER))
        # vanne 1134
        self.frame1134.configure(background=color_tags_valve(self.V1134_FDC_OUV, self.V1134_FDC_FER))
        # vanne 1135
        self.frame1135.configure(background=color_tags_valve(self.V1135_FDC_OUV, self.V1135_FDC_FER))
        # vanne 1136
        self.frame1136.configure(background=color_tags_valve(self.V1136_FDC_OUV, self.V1136_FDC_FER))
        # vanne 1137
        self.frame1137.configure(background=color_tags_valve(self.V1137_FDC_OUV, self.V1137_FDC_FER))
        # vanne 1138
        self.frame1138.configure(background=color_tags_valve(self.V1138_FDC_OUV, self.V1138_FDC_FER))
        # vanne MV1
        self.frameMV2.configure(background=color_tags_valve(self.MV2_FDC_OUV, self.MV2_FDC_FER))
        # update PLC
        self.plc_list.update()
        # update config.
        self.conf_list.update()
        # update pilotage
        self.pilotage_list.update()

    def update_tabs(self):
        # current ID of notebook select tab
        cur_tab = self.note.index(self.note.select())
        # run current update handler
        if cur_tab == self.note.index(self.tab_int):
            self.update_tab_interco()
        elif cur_tab == self.note.index(self.tab_gny_dn900):
            self.update_tab_gny_dn900()
        elif cur_tab == self.note.index(self.tab_info):
            self.update_tab_info()
        elif cur_tab == self.note.index(self.tab_sim):
            self.update_tab_simul()

    def init_toolbar(self):
        self.tbarFm = tk.Frame(self.master)
        self.butTbox = tk.Button(self.tbarFm, text='API T-Box', relief=tk.SUNKEN)
        self.butTbox.pack(side=tk.LEFT)
        self.butReg = tk.Button(self.tbarFm, text='REG T640', relief=tk.SUNKEN)
        self.butReg.pack(side=tk.LEFT)
        self.butAcon = tk.Button(self.tbarFm, text='Aconcagua', relief=tk.SUNKEN)
        self.butAcon.pack(side=tk.LEFT)
        self.lblDate = tk.Label(self.tbarFm, text='', font=('TkDefaultFont', 12))
        self.lblDate.pack(side=tk.RIGHT)
        self.tbarFm.pack(side=tk.BOTTOM, fill=tk.X)

    def update_toolbar(self):
        self.butTbox.configure(background=GREEN if self.tbx.connected else PINK)
        self.butReg.configure(background=GREEN if self.reg.connected else PINK)
        self.butAcon.configure(background=GREEN if self.acon.connected else PINK)
        self.lblDate.configure(text=time.strftime('%H:%M:%S %d/%m/%Y'))

    def ack_default(self):
        self.tbx.write_bit(522, True)
        time.sleep(.1)
        self.tbx.write_bit(522, False)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))

    def confirm_mv2(self):
        ValveESDDialog(self, title='MV2', text='Action sur vanne de sécurité MV2 ?',
                       stop_command=lambda: self.MV2_CMD_CLOSE.set(True),
                       pst_command=lambda: self.MV2_CMD_PST.set(True))

    def confirm_v1130(self):
        ValveOpenCloseDialog(self, title='V1130', text='Mouvement V1130 ?',
                             open_command=lambda: self.V1130_CMD_OPEN.set(True),
                             close_command=lambda: self.V1130_CMD_CLOSE.set(True))

    def confirm_v1135(self):
        ValveOpenCloseDialog(self, title='V1135', text='Mouvement V1135 ?',
                             open_command=lambda: self.V1135_CMD_OPEN.set(True),
                             close_command=lambda: self.V1135_CMD_CLOSE.set(True))

    def confirm_v1136(self):
        ValveOpenCloseDialog(self, title='V1136', text='Mouvement V1136 ?',
                             open_command=lambda: self.V1136_CMD_OPEN.set(True),
                             close_command=lambda: self.V1136_CMD_CLOSE.set(True))


if __name__ == '__main__':
    # main Tk App
    root = tk.Tk()
    app = HMIApp(master=root)
    app.mainloop()
