#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.Canvas import HMICanvas
from pyHMI.Colors import *
from pyHMI.Dialog import ValveOpenCloseDialog, ValveESDDialog
from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag, tag_equal
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox


class Devices(object):
    def __init__(self):
        # init datasource
        # PLC TBox
        self.tbx = ModbusTCPDevice('163.111.181.85', port=502, timeout=2.0, refresh=1.0)
        # init modbus tables
        self.tbx.add_bits_table(3050, 61)
        self.tbx.add_bits_table(1536, 8)
        self.tbx.add_words_table(4000, 5)
        self.tbx.add_floats_table(5030, 8)
        # Reg. T640
        self.reg = ModbusTCPDevice('163.111.181.84', port=502, unit_id=2, timeout=5.0, refresh=1.0)
        self.reg.add_bits_table(240, 9)
        self.reg.add_words_table(201, 6)
        # Aconcagua supervisor
        self.acon = ModbusTCPDevice('163.111.181.83', port=502, timeout=2.0, refresh=1.0)
        self.acon.add_words_table(12288, 11)
        # PSLS
        self.psls = ModbusTCPDevice('163.111.181.80', port=502, timeout=2.0, refresh=1.0)


class Tags(object):
    def __init__(self, tk_app, update_ms=500):
        self.tk_app = tk_app
        self.update_ms = update_ms
        # Devices
        self.d = self.tk_app.d
        # tags list
        self.NULL_TAG = Tag(False)
        # Tbox PLC
        self.DEF_EDF = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3050})
        self.DEF_CHG = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3051})
        self.DEF_OND = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3052})
        self.DEF_ATD1 = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3053})
        self.DEF_ATD2 = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3054})
        self.DEF_FEU = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3055})
        self.DEF_CENT = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3056})
        self.TC_AUTO = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3057})
        self.TRA_EN_COURS = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3058})
        self.CONF_NOP = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3059})
        self.CMD_PST_ACT = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3060})
        self.CONF_REG = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3061})
        self.CONF_NEU = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3062})
        self.CONF_SEC = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3063})
        self.PIL_TELE = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3064, 'not': True})
        self.PIL_LOCAL = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3064})
        self.V1130_EV_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3066})
        self.V1130_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3067})
        self.V1135_EV_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3068})
        self.V1135_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3069})
        self.V1136_EV_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3070})
        self.V1136_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3071})
        self.MV2_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3072})
        self.V1130_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3074})
        self.V1130_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3075})
        self.V1133_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3076})
        self.V1133_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3077})
        self.V1134_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3078})
        self.V1134_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3079})
        self.V1135_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3080})
        self.V1135_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3081})
        self.V1136_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3082})
        self.V1136_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3083})
        self.V1137_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3084})
        self.V1137_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3085})
        self.V1138_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3086})
        self.V1138_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3087})
        self.VL_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3088})
        self.VL_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3089})
        self.MV10_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3090})
        self.MV10_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3091})
        self.MV7_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3092})
        self.MV7_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3093})
        self.MV7_DEF_ELEC = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3094})
        self.MV7_DIST = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3095})
        self.MV7_HS = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3096})
        self.MV2_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3097})
        self.MV2_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3098})
        self.DEF_SEQ_MV1130 = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3099})
        self.DEF_SEQ_MV1135 = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3100})
        self.DEF_SEQ_MV1136 = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3101})
        self.SEQ_MV1130_EN_COURS = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3102})
        self.SEQ_MV1135_EN_COURS = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3103})
        self.SEQ_MV1136_EN_COURS = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3104})
        self.DELTA_P_INF_1_5 = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3105})
        self.DELTA_P_INF_0_5 = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3106})
        self.MV2_PST_EN_COURS = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3107})
        self.MV2_DEF_PST = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3108})
        self.DEF_DJ_220V = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3109})
        self.DEF_DJ_24V = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3110})
        self.TRA_REG_V_NEU = Tag(False, src=self.d.tbx, ref={'type': 'word', 'addr': 4000})
        self.TRA_REG_V_SEC = Tag(False, src=self.d.tbx, ref={'type': 'word', 'addr': 4001})
        self.TRA_NEU_V_REG = Tag(False, src=self.d.tbx, ref={'type': 'word', 'addr': 4002})
        self.TRA_NEU_V_SEC = Tag(False, src=self.d.tbx, ref={'type': 'word', 'addr': 4003})
        self.API_TBX_MDV = Tag(False, src=self.d.tbx, ref={'type': 'word', 'addr': 4004})
        self.P_GNY_DN900 = Tag(0.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5030})
        # self.P_GNY_DN800 = Tags(90.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5032})
        self.P_ARL = Tag(90.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5034})
        # self.P_AV_VL = Tags(90.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5036})
        self.Q_ANTENNES = Tag(0.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5038})
        self.POS_VL = Tag(0.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5040})
        self.POS_MV7 = Tag(0.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5042})
        self.P_CPTGE = Tag(0.0, src=self.d.tbx, ref={'type': 'float', 'addr': 5044})
        # Reg T640
        self.REG_AUTO_D = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 240})
        self.REG_AUTO_L = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 241})
        self.REG_MANU = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 242})
        self.REG_MARCHE = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 243})
        self.REG_ARRET = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 244})
        self.REG_EN_ETL = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 245})
        self.REG_HORS_ETL = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 246})
        self.REG_DEF_MES_P = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 247})
        self.REG_ERR_CONS = Tag(False, src=self.d.reg, ref={'type': 'bit', 'addr': 248})
        self.REG_P_AM_VL = Tag(False, src=self.d.reg, ref={'type': 'word', 'addr': 201})
        self.REG_P_AV_VL = Tag(False, src=self.d.reg, ref={'type': 'word', 'addr': 202})
        self.REG_C_ACTIVE = Tag(False, src=self.d.reg, ref={'type': 'word', 'addr': 203})
        self.REG_C_CSR = Tag(False, src=self.d.reg, ref={'type': 'word', 'addr': 204})
        self.REG_SORTIE = Tag(False, src=self.d.reg, ref={'type': 'word', 'addr': 205})
        self.REG_MDV = Tag(False, src=self.d.reg, ref={'type': 'word', 'addr': 206})
        # Aconcagua
        self.ACON_MDV = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12288})
        self.ACON_PCS = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12289})
        self.ACON_DENS = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12290})
        self.ACON_PCS_ANC = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12291})
        self.ACON_N2 = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12292})
        self.ACON_CO2 = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12293})
        self.ACON_THT = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12294})
        self.ACON_THT_ANC = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12295})
        self.ACON_H2O = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12296})
        self.ACON_P_HE = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12297})
        self.ACON_P_AIR = Tag(0, src=self.d.acon, ref={'type': 'word', 'addr': 12298})
        # virtual (a tag from tag(s))
        self.GET_TAG_TEST = Tag(False, get_cmd=lambda: self.V1130_FDC_FER.val and self.V1133_FDC_FER.val)
        self.DELTA_P_VL = Tag(0, get_cmd=lambda: self.REG_P_AM_VL.e_val - self.REG_P_AV_VL.e_val)
        self.TRA_NVR_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_NEU_V_REG, 1))
        self.TRA_RVN_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_NEU, 1))
        self.TRA_RVN_STEP_2 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_NEU, 2))
        self.TRA_RVN_STEP_3 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_NEU, 3))
        self.TRA_RVN_STEP_4 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_NEU, 4))
        self.TRA_RVN_STEP_5 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_NEU, 5))
        self.TRA_RVN_STEP_6 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_NEU, 6))
        self.TRA_NVS_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_NEU_V_SEC, 1))
        self.TRA_NVS_STEP_2 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_NEU_V_SEC, 2))
        self.TRA_RVS_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_SEC, 1))
        self.TRA_RVS_STEP_2 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_SEC, 2))
        self.TRA_RVS_STEP_3 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_SEC, 3))
        self.TRA_RVS_STEP_4 = Tag(0, get_cmd=lambda: tag_equal(self.TRA_REG_V_SEC, 4))
        # local (no external source)
        self.HMI_WORD = Tag(0)
        self.HMI_WORD2 = Tag(0)
        # WRITE TAGS
        # API
        self.CMD_V1130_OPEN = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6017})
        self.CMD_V1130_CLOSE = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6018})
        self.CMD_V1135_OPEN = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6019})
        self.CMD_V1135_CLOSE = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6020})
        self.CMD_V1136_OPEN = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6021})
        self.CMD_V1136_CLOSE = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6022})
        self.CMD_MV2_CLOSE = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6023})
        self.CMD_MV2_PST = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6025})
        self.CMD_CONF_REGION = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6026})
        self.CMD_CONF_NEUTRE = Tag(False, src=self.d.tbx, ref={'type': 'w_bit', 'addr': 6027})
        # REG
        self.CMD_REG_MARCHE = Tag(False, src=self.d.reg, ref={'type': 'w_bit', 'addr': 220})
        self.CMD_REG_ARRET = Tag(False, src=self.d.reg, ref={'type': 'w_bit', 'addr': 221})
        self.CMD_ETL_MARCHE = Tag(False, src=self.d.reg, ref={'type': 'w_bit', 'addr': 222})
        self.CMD_ETL_ARRET = Tag(False, src=self.d.reg, ref={'type': 'w_bit', 'addr': 223})
        # launch update loop
        self.tk_app.do_every(self.update_tags, every_ms=self.update_ms)

    def update_tags(self):
        # update tags
        self.HMI_WORD.set(self.HMI_WORD.val + 1)
        self.HMI_WORD2.set(self.HMI_WORD2.val + 3)


class HMITab(tk.Frame):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, notebook, *args, **kwargs)
        self.notebook = notebook
        self.update_ms = update_ms
        # from main app
        self.app = notebook.master
        self.t = notebook.master.t
        self.d = notebook.master.d
        # setup auto-refresh of notebook tab (on-visibility and every update_ms)
        self.bind('<Visibility>', lambda evt: self.tab_update())
        self._tab_update()

    def _tab_update(self):
        if self.winfo_ismapped():
            self.tab_update()
        self.master.after(self.update_ms, self._tab_update)

    def tab_update(self):
        pass


class TabInterco(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # tab "interconnexion"
        self.map_int = HMICanvas(self, width=800, height=550, debug=False)
        # add button
        self.map_int.add_button('GNY_800', 100, 400, text='Gournay DN800', state='disabled',
                                disabledforeground=BLACK, borderwidth=0)
        self.map_int.add_button('GNY_900', 100, 500, text='Gournay DN900',
                                command=lambda: self.notebook.select(self.app.tab_gny_dn900))
        self.map_int.add_button('ARL', 700, 400, text='Arleux DN800', state='disabled',
                                disabledforeground=BLACK, borderwidth=0)
        self.map_int.add_button('ANT_REG', 700, 50, text='Antennes REG', state='disabled',
                                disabledforeground=BLACK, borderwidth=0)
        self.map_int.add_button('MANAGE_V1130', 480, 370, text='V1130',
                                command=self.app.confirm_v1130, state='disabled')
        self.map_int.add_button('MANAGE_V1135', 660, 140, text='V1135',
                                command=self.app.confirm_v1135, state='disabled')
        self.map_int.add_button('MANAGE_V1136', 480, 200, text='V1136',
                                command=self.app.confirm_v1136, state='disabled')
        self.map_int.add_button('MANAGE_MV2', 480, 470, text='MV2',
                                command=self.app.confirm_mv2, state='disabled')
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
        self.map_int.add_vbox('P_GNY_DN900', 230, 475, get_value=lambda: self.t.P_GNY_DN900, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_GNY_DN800', 160, 300, get_value=lambda: self.t.REG_P_AM_VL, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_ARL', 640, 300, get_value=lambda: self.t.P_ARL, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_AV_VL', 160, 80, get_value=lambda: self.t.REG_P_AV_VL, prefix='P', suffix='bars')
        self.map_int.add_vbox('POS_VL', 160, 190, get_value=lambda: self.t.POS_VL, prefix='', suffix='%')
        self.map_int.add_vbox('Q_ANTENNES', 400, 50, get_value=lambda: self.t.Q_ANTENNES, prefix='Q', suffix='Nm3/h',
                              tk_fmt='{:.0f}')
        # custom widget
        # Pilotage poste
        self.frmConf = tk.Frame(self.map_int.can)
        tk.Label(self.frmConf, text='Pilot. poste').pack(fill=tk.X)
        self.cnfDist = tk.Label(self.frmConf, text='Distant', background=WHITE)
        self.cnfDist.pack(fill=tk.X)
        self.cnfLoc = tk.Label(self.frmConf, text='Local', background=WHITE)
        self.cnfLoc.pack(fill=tk.X)
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        # Configuration poste
        tk.Label(self.frmConf, text='TC Auto.').pack(fill=tk.X)
        self.cnfAuto = tk.Label(self.frmConf, text='Auto', background=WHITE)
        self.cnfAuto.pack(fill=tk.X)
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        # Configuration poste
        tk.Label(self.frmConf, text='Config. poste').pack(fill=tk.X)
        self.cnfReg = tk.Label(self.frmConf, text='Régionale', background=WHITE)
        self.cnfReg.pack(fill=tk.X)
        self.cnfNeu = tk.Label(self.frmConf, text='Neutre', background=WHITE)
        self.cnfNeu.pack(fill=tk.X)
        self.cnfSec = tk.Label(self.frmConf, text='Sécurité', background=WHITE)
        self.cnfSec.pack(fill=tk.X)
        self.cnfNop = tk.Label(self.frmConf, text='Non op.', background=WHITE)
        self.cnfNop.pack(fill=tk.X)
        self.frmConf.pack()
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        self.map_int.can.create_window(55, 130, window=self.frmConf)
        # build all
        self.map_int.build()

    def tab_update(self):
        # update value box
        self.map_int.update_vbox()
        # update simple valves
        self.map_int.simple_valve.tag_anim('V1133', self.t.V1133_FDC_OUV, self.t.V1133_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1134', self.t.V1134_FDC_OUV, self.t.V1134_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1137', self.t.V1137_FDC_OUV, self.t.V1137_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1138', self.t.V1138_FDC_OUV, self.t.V1138_FDC_FER)
        self.map_int.flow_valve.tag_anim('VL1', self.t.VL_FDC_OUV, self.t.VL_FDC_FER)
        self.map_int.flow_valve.pos_tag_anim('VL1', self.t.POS_VL)
        # update motor valves
        self.map_int.motor_valve.tag_anim('V1130', self.t.V1130_FDC_OUV, self.t.V1130_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1130', self.t.V1130_EV_OUV, self.t.V1130_EV_FER,
                                                self.t.DEF_SEQ_MV1130)
        self.map_int.motor_valve.tag_anim('V1135', self.t.V1135_FDC_OUV, self.t.V1135_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1135', self.t.V1135_EV_OUV, self.t.V1135_EV_FER,
                                                self.t.DEF_SEQ_MV1135)
        self.map_int.motor_valve.tag_anim('V1136', self.t.V1136_FDC_OUV, self.t.V1136_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1136', self.t.V1136_EV_OUV, self.t.V1136_EV_FER,
                                                self.t.DEF_SEQ_MV1136)
        self.map_int.motor_valve.tag_anim('MV2', self.t.MV2_FDC_OUV, self.t.MV2_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('MV2', self.t.NULL_TAG, self.t.MV2_EV_FER)
        # update config.
        self.cnfDist.configure(background=color_tag_state(self.t.PIL_TELE))
        self.cnfLoc.configure(background=color_tag_state(self.t.PIL_LOCAL))
        self.cnfAuto.configure(background=color_tag_state(self.t.TC_AUTO))
        self.cnfReg.configure(background=color_tag_state(self.t.CONF_REG))
        self.cnfNeu.configure(background=color_tag_state(self.t.CONF_NEU))
        self.cnfSec.configure(background=color_tag_state(self.t.CONF_SEC))
        self.cnfNop.configure(background=color_tag_state(self.t.CONF_NOP))
        # validate command when local mode active
        if self.t.PIL_LOCAL.val:
            self.map_int.d_widget['MANAGE_V1130']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_V1135']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_V1136']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_MV2']['obj'].configure(state='normal')
        else:
            self.map_int.d_widget['MANAGE_V1130']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_V1135']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_V1136']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_MV2']['obj'].configure(state='disabled')


class TabGnyDN900(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # tab "Gournay DN900"
        self.map_gny_dn900 = HMICanvas(self, width=800, height=550, debug=False)
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
                                      command=self.app.confirm_mv2, state='disabled')
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
        self.map_gny_dn900.add_vbox('POS_MV7', 430, 200, get_value=lambda: self.t.POS_MV7, prefix='', suffix='%')

        # MV7 info panel
        self.frmMV7 = tk.Frame(self.map_gny_dn900.can)
        self.frmMV7.pack()
        self.mv7_list = HMIBoolList(self.frmMV7, head_str='Etat MV7', lbl_args={'width': 10})
        self.mv7_list.add('Distant', self.t.MV7_DIST)
        self.mv7_list.add('Hors-Service', self.t.MV7_HS)
        self.mv7_list.add('Défaut élec.', self.t.MV7_DEF_ELEC)
        self.mv7_list.build()
        self.map_gny_dn900.can.create_window(600, 160, window=self.frmMV7)
        # MV2 info panel
        self.frmMV2 = tk.Frame(self.map_gny_dn900.can, padx=0, pady=0)
        self.frmMV2.pack()
        self.mv2_list = HMIBoolList(self.frmMV2, head_str='Etat MV2', lbl_args={'width': 10})
        self.mv2_list.add('PST actif', self.t.MV2_PST_EN_COURS)
        self.mv2_list.add('Défaut PST', self.t.MV2_DEF_PST, alarm=True)
        self.mv2_list.build()
        self.map_gny_dn900.can.create_window(380, 150, window=self.frmMV2)
        # build panel
        self.map_gny_dn900.build()

    def tab_update(self):
        # update vbox
        self.map_gny_dn900.update_vbox()
        # update valves on canvas
        self.map_gny_dn900.motor_valve.tag_anim('MV2', self.t.MV2_FDC_OUV, self.t.MV2_FDC_FER)
        self.map_gny_dn900.motor_valve.motor_tag_anim('MV2', self.t.NULL_TAG, self.t.MV2_EV_FER)
        self.map_gny_dn900.simple_valve.tag_anim('MV7', self.t.MV7_FDC_OUV, self.t.MV7_FDC_FER)
        self.map_gny_dn900.simple_valve.tag_anim('MV10', self.t.MV10_FDC_OUV, self.t.MV10_FDC_FER)
        # validate command when local mode active
        if self.t.PIL_LOCAL.val:
            self.map_gny_dn900.d_widget['MANAGE_MV2']['obj'].configure(state='normal')
        else:
            self.map_gny_dn900.d_widget['MANAGE_MV2']['obj'].configure(state='disabled')
        # update MV7 info panel
        self.mv7_list.update()
        # update MV2 info panel
        self.mv2_list.update()


class TabReg(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Etats régulateur
        self.frmEtatReg = tk.LabelFrame(self, text='Etats régulateur', padx=10, pady=10)
        self.frmEtatReg.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.etat_l = HMIBoolList(self.frmEtatReg, lbl_args={'width': 15}, grid_args={'padx': 15})
        self.etat_l.add('Marche', self.t.REG_MARCHE)
        self.etat_l.add('Arrêt', self.t.REG_ARRET)
        self.etat_l.add('Auto Distant', self.t.REG_AUTO_D)
        self.etat_l.add('Auto Local', self.t.REG_AUTO_L)
        self.etat_l.add('Manuel', self.t.REG_MANU)
        self.etat_l.add('En etalonnage', self.t.REG_EN_ETL)
        self.etat_l.add('Hors etalonnage', self.t.REG_HORS_ETL)
        self.etat_l.add('Défaut mesure P', self.t.REG_DEF_MES_P)
        self.etat_l.add('Erreur consigne', self.t.REG_ERR_CONS)
        self.etat_l.build()
        # Mesures régulateur
        self.frmMesReg = tk.LabelFrame(self, text='Mesures régulateur', padx=10, pady=10)
        self.frmMesReg.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.mes_l = HMIAnalogList(self.frmMesReg, lbl_args={'width': 10})
        self.mes_l.add('Pression amont VL', self.t.REG_P_AM_VL, unit='bars rel.')
        self.mes_l.add('Pression aval VL', self.t.REG_P_AV_VL, unit='bars rel.')
        self.mes_l.add('Retour consigne active', self.t.REG_C_ACTIVE, unit='bars rel.')
        self.mes_l.add('Retour consigne CSR', self.t.REG_C_CSR, unit='bars rel.')
        self.mes_l.add('Sortie régulateur', self.t.REG_C_CSR, unit='%')
        self.mes_l.add('Calcul Delta P VL', self.t.DELTA_P_VL, unit='bars rel.')
        self.mes_l.build()
        # Commande du régulateur
        self.frmCmdReg = tk.LabelFrame(self, text='Commandes', padx=10, pady=10)
        self.frmCmdReg.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.cmd_l = HMIButtonList(self.frmCmdReg, btn_args={'width': 15}, grid_args={'pady': 5})
        self.cmd_l.add('Marche régulateur', tag_valid=self.t.PIL_LOCAL, cmd=lambda: self.t.CMD_REG_MARCHE.set(True),
                       btn_args={'bg': GREEN})
        self.cmd_l.add('Arrêt régulateur', tag_valid=self.t.PIL_LOCAL, cmd=lambda: self.t.CMD_REG_ARRET.set(True),
                       btn_args={'bg': RED})
        self.cmd_l.add('En étalonnage', tag_valid=self.t.PIL_LOCAL, cmd=lambda: self.t.CMD_ETL_MARCHE.set(True),
                       btn_args={'bg': ORANGE})
        self.cmd_l.add('Hors étalonnage', tag_valid=self.t.PIL_LOCAL, cmd=lambda: self.t.CMD_ETL_ARRET.set(True),
                       btn_args={'bg': ORANGE})
        self.cmd_l.build()

    def tab_update(self):
        self.etat_l.update()
        self.mes_l.update()
        self.cmd_l.update()


class TabInfo(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Energie
        self.frmEnergie = tk.LabelFrame(self, text='Energie', padx=10, pady=10)
        self.frmEnergie.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.energie_list = HMIBoolList(self.frmEnergie, lbl_args={'width': 15})
        self.energie_list.add('Absence EDF', self.t.DEF_EDF, alarm=True)
        self.energie_list.add('Défaut chargeur', self.t.DEF_CHG, alarm=True)
        self.energie_list.add('Défaut onduleur', self.t.DEF_OND, alarm=True)
        self.energie_list.add('Défaut disj. 220V', self.t.DEF_DJ_220V, alarm=True)
        self.energie_list.add('Défaut disj. 24V', self.t.DEF_DJ_24V, alarm=True)
        self.energie_list.build()
        # ATD/Feu
        self.frmCentrale = tk.LabelFrame(self, text='ATD/Feu', padx=10, pady=10)
        self.frmCentrale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.centrale_list = HMIBoolList(self.frmCentrale, lbl_args={'width': 15})
        self.centrale_list.add('Défaut centrale', self.t.DEF_CENT, alarm=True)
        self.centrale_list.add('ATD stade 1', self.t.DEF_ATD1, alarm=True)
        self.centrale_list.add('ATD stade 2', self.t.DEF_ATD2, alarm=True)
        self.centrale_list.add('Feu', self.t.DEF_FEU, alarm=True)
        self.centrale_list.build()
        # Pilotage
        self.lblPil = tk.LabelFrame(self, text='Pilotage', padx=10, pady=10)
        self.lblPil.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        self.pilotage_list = HMIBoolList(self.lblPil, lbl_args={'width': 10})
        self.pilotage_list.add('Distant', self.t.PIL_TELE)
        self.pilotage_list.add('Local', self.t.PIL_LOCAL)
        self.pilotage_list.add('TC Auto', self.t.TC_AUTO)
        self.pilotage_list.build()
        # Configuration
        self.lblConf = tk.LabelFrame(self, text='Configuration', padx=10, pady=10)
        self.lblConf.grid(row=0, column=3, padx=5, pady=5, sticky=tk.NSEW)
        self.conf_list = HMIBoolList(self.lblConf, lbl_args={'width': 10})
        self.conf_list.add('En Transition', self.t.TRA_EN_COURS)
        self.conf_list.add('Régional', self.t.CONF_REG)
        self.conf_list.add('Neutre', self.t.CONF_NEU)
        self.conf_list.add('Sécurité', self.t.CONF_SEC)
        self.conf_list.add('Non Op.', self.t.CONF_NOP)
        self.conf_list.build()
        # Transitions
        self.lblTrans = tk.LabelFrame(self, text='Transitions', padx=0, pady=10)
        self.lblTrans.grid(row=0, column=4, padx=5, pady=5, sticky=tk.NSEW)
        self.tran = HMIAnalogList(self.lblTrans)
        self.tran.add('Neutre vers régionale', self.t.TRA_NEU_V_REG, unit='niv')
        self.tran.add('Régionale vers neutre', self.t.TRA_REG_V_NEU, unit='niv')
        self.tran.add('Neutre vers sécurité', self.t.TRA_NEU_V_SEC, unit='niv')
        self.tran.add('Régionale vers sécurité', self.t.TRA_REG_V_SEC, unit='niv')
        self.tran.build()
        # Laboratoire
        self.frmLabo = tk.LabelFrame(self, text='Laboratoire', padx=5, pady=5)
        self.frmLabo.grid(row=1, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.labo_list = HMIAnalogList(self.frmLabo, lbl_args={'width': 10})
        self.labo_list.add('PCS', self.t.ACON_PCS, 'w/nm3')
        self.labo_list.add('Densité', self.t.ACON_DENS)
        self.labo_list.add('Azote', self.t.ACON_N2, '%')
        self.labo_list.add('CO2', self.t.ACON_CO2, '%')
        self.labo_list.add('PCS Ancienneté', self.t.ACON_PCS_ANC, 'min')
        self.labo_list.add('THT', self.t.ACON_THT, 'mg/Nm3')
        self.labo_list.add('THT Ancienneté', self.t.ACON_THT_ANC, 'min')
        self.labo_list.add('Taux H2O', self.t.ACON_H2O, 'mg/Nm3')
        self.labo_list.add('P Air', self.t.ACON_P_AIR, 'bars rel.')
        self.labo_list.add('P Hélium', self.t.ACON_P_HE, 'bars rel.')
        self.labo_list.build()
        #  Poste
        self.frmPoste = tk.LabelFrame(self, text='Poste', padx=5, pady=5)
        self.frmPoste.grid(row=1, column=2, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        self.poste_list = HMIAnalogList(self.frmPoste, lbl_args={'width': 10})
        self.poste_list.add('Q vers antennes régionales', self.t.Q_ANTENNES, 'Nm3/h', fmt='%d')
        self.poste_list.add('P comptage (aval VL)', self.t.P_CPTGE, 'bars abs.', fmt='%.02f')
        self.poste_list.add('P Gournay DN900 (amt MV2)', self.t.P_GNY_DN900, 'bars rel.', fmt='%.02f')
        self.poste_list.add('P Arleux', self.t.P_ARL, 'bars rel.', fmt='%.02f')
        self.poste_list.add('P amont VL', self.t.REG_P_AM_VL, 'bars rel.', fmt='%.02f')
        self.poste_list.add('P aval VL', self.t.REG_P_AV_VL, 'bars rel.', fmt='%.02f')
        self.poste_list.add('Position MV7', self.t.POS_MV7, '%', fmt='%.02f')
        self.poste_list.add('Position VL', self.t.POS_VL, '%', fmt='%.02f')
        self.poste_list.add('Sortie régulateur VL', self.t.REG_SORTIE, '%', fmt='%.02f')
        self.poste_list.add('Consigne active REG P aval', self.t.REG_C_ACTIVE, 'bars rel.', fmt='%.02f')
        self.poste_list.add('Consigne CSR REG P aval', self.t.REG_C_CSR, 'bars rel.', fmt='%.02f')
        self.poste_list.build()
        # Vannes
        self.frmValves = tk.LabelFrame(self, text='Vannes configuration', padx=5, pady=5)
        self.frmValves.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        # V1130
        self.frmV1130 = tk.Frame(self.frmValves, padx=0, pady=0)
        self.frmV1130.grid(row=0, column=0, padx=6, pady=5, sticky=tk.NSEW)
        self.v1130_l = HMIBoolList(self.frmV1130, head_str='V1130', lbl_args={'width': 10})
        self.v1130_l.add('Ouv', self.t.V1130_FDC_OUV)
        self.v1130_l.add('Fer', self.t.V1130_FDC_FER)
        self.v1130_l.add('Def. seq.', self.t.DEF_SEQ_MV1130, alarm=True)
        self.v1130_l.add('Seq. act.', self.t.SEQ_MV1130_EN_COURS)
        self.v1130_l.build()
        # V1135
        self.frmV1135 = tk.Frame(self.frmValves, padx=0, pady=0)
        self.frmV1135.grid(row=0, column=1, padx=6, pady=5, sticky=tk.NSEW)
        self.v1135_l = HMIBoolList(self.frmV1135, head_str='V1135', lbl_args={'width': 10})
        self.v1135_l.add('Ouv', self.t.V1135_FDC_OUV)
        self.v1135_l.add('Fer', self.t.V1135_FDC_FER)
        self.v1135_l.add('Def. seq.', self.t.DEF_SEQ_MV1135, alarm=True)
        self.v1135_l.add('Seq. act.', self.t.SEQ_MV1135_EN_COURS)
        self.v1135_l.build()
        # V1136
        self.frmV1136 = tk.Frame(self.frmValves, padx=0, pady=0)
        self.frmV1136.grid(row=0, column=2, padx=6, pady=5, sticky=tk.NSEW)
        self.v1136_l = HMIBoolList(self.frmV1136, head_str='V1136', lbl_args={'width': 10})
        self.v1136_l.add('Ouv', self.t.V1136_FDC_OUV)
        self.v1136_l.add('Fer', self.t.V1136_FDC_FER)
        self.v1136_l.add('Def. seq.', self.t.DEF_SEQ_MV1136, alarm=True)
        self.v1136_l.add('Seq. act.', self.t.SEQ_MV1136_EN_COURS)
        self.v1136_l.build()
        # Vanne ESD
        self.frmESDValves = tk.LabelFrame(self, text='Vanne ESD', padx=5, pady=5)
        self.frmESDValves.grid(row=2, column=2, padx=5, pady=5, sticky=tk.NSEW)
        # MV2
        self.frmMV2 = tk.Frame(self.frmESDValves, padx=0, pady=0)
        self.frmMV2.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.mv2_l = HMIBoolList(self.frmMV2, head_str='MV2', lbl_args={'width': 10})
        self.mv2_l.add('Ouv', self.t.MV2_FDC_OUV)
        self.mv2_l.add('Fer', self.t.MV2_FDC_FER)
        self.mv2_l.add('PST actif', self.t.MV2_PST_EN_COURS)
        self.mv2_l.add('Défaut PST', self.t.MV2_DEF_PST, alarm=True)
        self.mv2_l.build()
        # Système
        self.frmSys = tk.LabelFrame(self, text='Système', padx=5, pady=5)
        self.frmSys.grid(row=2, column=3, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.sys_l = HMIAnalogList(self.frmSys, lbl_args={'width': 10})
        self.sys_l.add('Mot de vie API', self.t.API_TBX_MDV)
        self.sys_l.add('Mot de vie REG', self.t.REG_MDV)
        self.sys_l.add('Mot de vie Acon.', self.t.ACON_MDV)
        self.sys_l.build()

    def tab_update(self):
        self.energie_list.update()
        self.centrale_list.update()
        self.pilotage_list.update()
        self.conf_list.update()
        self.tran.update()
        self.labo_list.update()
        self.poste_list.update()
        self.v1130_l.update()
        self.v1135_l.update()
        self.v1136_l.update()
        self.mv2_l.update()
        self.sys_l.update()


class TabTran(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Transitions
        self.lblTrans = tk.LabelFrame(self, text='Transitions', padx=0, pady=10)
        self.lblTrans.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.tran = HMIAnalogList(self.lblTrans)
        self.tran.add('Neutre vers régionale', self.t.TRA_NEU_V_REG, unit='niv')
        self.tran.add('Régionale vers neutre', self.t.TRA_REG_V_NEU, unit='niv')
        self.tran.add('Neutre vers sécurité', self.t.TRA_NEU_V_SEC, unit='niv')
        self.tran.add('Régionale vers sécurité', self.t.TRA_REG_V_SEC, unit='niv')
        self.tran.build()
        # Configuration
        self.lblConf = tk.LabelFrame(self, text='Configuration', padx=10, pady=10)
        self.lblConf.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.conf_list = HMIBoolList(self.lblConf, lbl_args={'width': 20})
        self.conf_list.add('En Transition', self.t.TRA_EN_COURS)
        self.conf_list.add('Régional', self.t.CONF_REG)
        self.conf_list.add('Neutre', self.t.CONF_NEU)
        self.conf_list.add('Sécurité', self.t.CONF_SEC)
        self.conf_list.add('Non Op.', self.t.CONF_NOP)
        self.conf_list.build()
        # Lancement des transitions
        self.frmCmdTra = tk.LabelFrame(self, text='Commandes transitions', padx=10, pady=10)
        self.frmCmdTra.grid(row=2, column=0, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.cmd_l = HMIButtonList(self.frmCmdTra, btn_args={'width': 10}, grid_args={'pady': 40})
        self.cmd_l.add('Vers régionale', tag_valid=self.t.PIL_LOCAL, cmd=self.app.confirm_region,
                       btn_args={'bg': GREEN})
        self.cmd_l.add('Vers neutre', tag_valid=self.t.PIL_LOCAL, cmd=self.app.confirm_neutre,
                       btn_args={'bg': GREEN})
        self.cmd_l.build()
        # Neutre vers régionale
        self.frmCmdNVR = tk.LabelFrame(self, text='Neutre vers régionale', padx=10, pady=10)
        self.frmCmdNVR.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.nvr_list = HMIBoolList(self.frmCmdNVR, lbl_args={'width': 60})
        self.nvr_list.add('1. Fermeture vanne 1136', self.t.TRA_NVR_STEP_1)
        self.nvr_list.build()
        # Réginale vers neutre
        self.frmCmdRVN = tk.LabelFrame(self, text='Régionale vers neutre', padx=10, pady=10)
        self.frmCmdRVN.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.rvn_list = HMIBoolList(self.frmCmdRVN, lbl_args={'width': 60})
        self.rvn_list.add('1. Arrêt régulation (ouv. VL à 100% en pente douce)', self.t.TRA_RVN_STEP_1)
        self.rvn_list.add('2. Attente delta P VL < 1.5 bar', self.t.TRA_RVN_STEP_2)
        self.rvn_list.add('3. Ouverture V1135 (mise en bipasse comptage)', self.t.TRA_RVN_STEP_3)
        self.rvn_list.add('4. Attente delta P VL < 0.5 bar', self.t.TRA_RVN_STEP_4)
        self.rvn_list.add('5. Ouverture V1136', self.t.TRA_RVN_STEP_5)
        self.rvn_list.add('6. Fermeture V1135 (arrêt du bipasse comptage)', self.t.TRA_RVN_STEP_6)
        self.rvn_list.build()
        # Neutre vers sécurité
        self.frmCmdNVS = tk.LabelFrame(self, text='Neutre vers sécurité', padx=10, pady=10)
        self.frmCmdNVS.grid(row=2, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.nvs_list = HMIBoolList(self.frmCmdNVS, lbl_args={'width': 60})
        self.nvs_list.add('1. Ouverture V1135', self.t.TRA_NVS_STEP_1)
        self.nvs_list.add('2. Arrêt régulation (ouv. VL à 100% en pente douce)', self.t.TRA_NVS_STEP_2)
        self.nvs_list.build()
        # Régionale vers sécurité
        self.frmCmdRVS = tk.LabelFrame(self, text='Régionale vers sécurité', padx=10, pady=10)
        self.frmCmdRVS.grid(row=3, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.rvs_list = HMIBoolList(self.frmCmdRVS, lbl_args={'width': 60})
        self.rvs_list.add('1. Ouverture V1135', self.t.TRA_RVS_STEP_1)
        self.rvs_list.add('2. Arrêt régulation (ouv. VL à 100% en pente douce)', self.t.TRA_RVS_STEP_2)
        self.rvs_list.add('3. Attente delta P VL < 0.5 bar ou attente 3 min', self.t.TRA_RVS_STEP_3)
        self.rvs_list.add('4. Ouverture V1136', self.t.TRA_RVS_STEP_4)
        self.rvs_list.build()

    def tab_update(self):
        self.tran.update()
        self.cmd_l.update()
        self.conf_list.update()
        self.nvr_list.update()
        self.rvn_list.update()
        self.nvs_list.update()
        self.rvs_list.update()


# TODO remove IO simul at end of project
class TabSim(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # tab "I/O simul"
        # self.tab_sim.resizable(width=FALSE, height=FALSE)
        # Vanne 1130
        self.lblVal = tk.LabelFrame(self, text='Etat des vannes', padx=5, pady=5)
        self.lblVal.grid(padx=5, pady=5, row=0, columnspan=4, sticky=tk.NSEW)
        self.btn_v_l = HMIButtonList(self.lblVal, dim=4, btn_args={'width': 12},
                                     grid_args={'padx': 5, 'pady': 5})
        c = ({'background': GREEN}, {'background': RED})
        self.btn_v_l.add('Ouverture V1130', cmd=lambda: self.d.tbx.write_bits(524, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture V1130', cmd=lambda: self.d.tbx.write_bits(524, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture V1133', cmd=lambda: self.d.tbx.write_bits(526, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture V1133', cmd=lambda: self.d.tbx.write_bits(526, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture V1134', cmd=lambda: self.d.tbx.write_bits(528, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture V1134', cmd=lambda: self.d.tbx.write_bits(528, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture V1135', cmd=lambda: self.d.tbx.write_bits(530, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture V1135', cmd=lambda: self.d.tbx.write_bits(530, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture V1136', cmd=lambda: self.d.tbx.write_bits(532, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture V1136', cmd=lambda: self.d.tbx.write_bits(532, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture V1137', cmd=lambda: self.d.tbx.write_bits(534, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture V1137', cmd=lambda: self.d.tbx.write_bits(534, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture V1138', cmd=lambda: self.d.tbx.write_bits(536, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture V1138', cmd=lambda: self.d.tbx.write_bits(536, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture MV2', cmd=lambda: self.d.tbx.write_bits(547, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture MV2', cmd=lambda: self.d.tbx.write_bits(547, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture MV7', cmd=lambda: self.d.tbx.write_bits(542, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture MV7', cmd=lambda: self.d.tbx.write_bits(542, [False, True]), btn_args=c[1])
        self.btn_v_l.add('Ouverture MV10', cmd=lambda: self.d.tbx.write_bits(540, [True, False]), btn_args=c[0])
        self.btn_v_l.add('Fermeture MV10', cmd=lambda: self.d.tbx.write_bits(540, [False, True]), btn_args=c[1])
        self.btn_v_l.build()
        # Configuration poste
        self.lblConf = tk.LabelFrame(self, text='Configuration', padx=10, pady=10)
        self.lblConf.grid(padx=5, pady=5, row=1, column=0, sticky=tk.NSEW)
        self.conf_list = HMIBoolList(self.lblConf, lbl_args={'width': 10})
        self.conf_list.add('Régional', self.t.CONF_REG)
        self.conf_list.add('Neutre', self.t.CONF_NEU)
        self.conf_list.add('Sécurité', self.t.CONF_SEC)
        self.conf_list.add('Non Op.', self.t.CONF_NOP)
        self.conf_list.build()
        # Etat automate
        self.lblPlc = tk.LabelFrame(self, text='Etat de l\'automate', padx=10, pady=10)
        self.lblPlc.grid(padx=5, pady=5, row=1, column=1, sticky=tk.NSEW)
        self.plc_list = HMIBoolList(self.lblPlc, lbl_args={'width': 15})
        self.plc_list.add('TC Auto', self.t.TC_AUTO)
        self.plc_list.add('Tran. en cours', self.t.TRA_EN_COURS)
        self.plc_list.add('Seq. act. MV1130 ', self.t.SEQ_MV1130_EN_COURS)
        self.plc_list.add('Def.seq. MV1130', self.t.DEF_SEQ_MV1130, alarm=True)
        self.plc_list.add('Seq. act. MV1135', self.t.SEQ_MV1135_EN_COURS)
        self.plc_list.add('Def.seq. MV1135', self.t.DEF_SEQ_MV1135, alarm=True)
        self.plc_list.add('Seq. act. MV1136', self.t.SEQ_MV1136_EN_COURS)
        self.plc_list.add('Def.seq. MV1136', self.t.DEF_SEQ_MV1136, alarm=True)
        self.plc_list.build()
        # Pilotage
        self.lblPil = tk.LabelFrame(self, text='Pilotage', padx=10, pady=10)
        self.lblPil.grid(padx=5, pady=5, row=1, column=2, sticky=tk.NSEW)
        self.pilotage_list = HMIBoolList(self.lblPil, lbl_args={'width': 10})
        self.pilotage_list.add('Distant', self.t.PIL_TELE)
        self.pilotage_list.add('Local', self.t.PIL_LOCAL)
        self.pilotage_list.build()
        # Commandes
        self.lblCmd = tk.LabelFrame(self, text='Commandes', padx=10, pady=10)
        tk.Button(self.lblCmd, text='Login PSLS', background=BLUE,
                  command=lambda: os.system('write_rtu_id.py 163.111.181.80 ')).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR TC Acquittement défaut', background=GREEN,
                  command=lambda: self.d.psls.write_word(20706, 1)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR TC Autorisation', background=GREEN,
                  command=lambda: self.d.psls.write_word(20709, 1)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR TC conf. Région', background=ORANGE,
                  command=lambda: self.d.psls.write_word(20701, 1)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR TC conf. Neutre', background=ORANGE,
                  command=lambda: self.d.psls.write_word(20702, 1)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR TC conf. Sécurité', background=ORANGE,
                  command=lambda: self.d.psls.write_word(20703, 1)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR Ouv. V1135', background=BLUE,
                  command=lambda: self.d.psls.write_word(20707, 1)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR Fer. V1135', background=BLUE,
                  command=lambda: self.d.psls.write_word(20708, 1)).pack(fill=tk.X)
        tk.Button(self.lblCmd, text='CSR isol. MV2', background=RED,
                  command=lambda: self.d.psls.write_word(20710, 1)).pack(fill=tk.X)
        self.lblCmd.grid(padx=5, pady=5, row=1, column=3, sticky=tk.NSEW)

    def tab_update(self):
        # update valve status
        # update PLC
        self.plc_list.update()
        # update config.
        self.conf_list.update()
        # update pilotage
        self.pilotage_list.update()


class HMIToolbar(tk.Frame):
    def __init__(self, tk_app, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, tk_app, *args, **kwargs)
        self.tk_app = tk_app
        self.update_ms = update_ms
        # build toolbar
        self.butTbox = tk.Button(self, text='API T-Box', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butTbox.pack(side=tk.LEFT)
        self.butReg = tk.Button(self, text='REG T640', relief=tk.SUNKEN,
                                state='disabled', disabledforeground='black')
        self.butReg.pack(side=tk.LEFT)
        self.butAcon = tk.Button(self, text='Aconcagua', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butAcon.pack(side=tk.LEFT)
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
        self.butTbox.configure(background=GREEN if self.tk_app.d.tbx.connected else PINK)
        self.butReg.configure(background=GREEN if self.tk_app.d.reg.connected else PINK)
        self.butAcon.configure(background=GREEN if self.tk_app.d.acon.connected else PINK)
        self.lblDate.configure(text=time.strftime('%H:%M:%S %d/%m/%Y'))


class HMIApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # configure main window
        self.wm_title('Poste de Chilly')
        # self.attributes('-fullscreen', True)
        self.geometry("800x600")
        # create devices
        self.d = Devices()
        # create tags
        self.t = Tags(self, update_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self)
        self.tab_int = TabInterco(self.note)
        self.tab_gny_dn900 = TabGnyDN900(self.note)
        self.tab_reg = TabReg(self.note)
        self.tab_info = TabInfo(self.note)
        self.tab_tran = TabTran(self.note)
        self.tab_sim = TabSim(self.note)
        self.note.add(self.tab_int, text='Interconnexion (F1)')
        self.note.add(self.tab_gny_dn900, text='Gournay DN900 (F2)')
        self.note.add(self.tab_reg, text='Régulation (F3)')
        self.note.add(self.tab_info, text='Informations (F4)')
        self.note.add(self.tab_tran, text='Transitions (F5)')
        self.note.add(self.tab_sim, text='I/O simul (F6)')
        # defaut selected tab
        self.note.select(self.tab_int)
        self.note.pack(fill=tk.BOTH, expand=True)
        # bind function keys to tabs
        self.bind('<F1>', lambda evt: self.note.select(self.tab_int))
        self.bind('<F2>', lambda evt: self.note.select(self.tab_gny_dn900))
        self.bind('<F3>', lambda evt: self.note.select(self.tab_reg))
        self.bind('<F4>', lambda evt: self.note.select(self.tab_info))
        self.bind('<F5>', lambda evt: self.note.select(self.tab_tran))
        self.bind('<F6>', lambda evt: self.note.select(self.tab_sim))
        # build toolbar
        self.toolbar = HMIToolbar(self, update_ms=500)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))

    def ack_default(self):
        self.d.tbx.write_bit(522, True)
        time.sleep(.1)
        self.d.tbx.write_bit(522, False)

    def confirm_region(self):
        if messagebox.askokcancel('Confirmation', message='Passage en régionale ?', default='cancel'):
            self.t.CMD_CONF_REGION.set(True)

    def confirm_neutre(self):
        if messagebox.askokcancel('Confirmation', message='Passage en neutre ?', default='cancel'):
            self.t.CMD_CONF_NEUTRE.set(True)

    def confirm_mv2(self):
        ValveESDDialog(self, title='MV2', text='Action sur vanne de sécurité MV2 ?',
                       stop_command=lambda: self.t.CMD_MV2_CLOSE.set(True),
                       pst_command=lambda: self.t.CMD_MV2_PST.set(True))

    def confirm_v1130(self):
        ValveOpenCloseDialog(self, title='V1130', text='Mouvement V1130 ?',
                             open_command=lambda: self.t.CMD_V1130_OPEN.set(True),
                             close_command=lambda: self.t.CMD_V1130_CLOSE.set(True))

    def confirm_v1135(self):
        ValveOpenCloseDialog(self, title='V1135', text='Mouvement V1135 ?',
                             open_command=lambda: self.t.CMD_V1135_OPEN.set(True),
                             close_command=lambda: self.t.CMD_V1135_CLOSE.set(True))

    def confirm_v1136(self):
        ValveOpenCloseDialog(self, title='V1136', text='Mouvement V1136 ?',
                             open_command=lambda: self.t.CMD_V1136_OPEN.set(True),
                             close_command=lambda: self.t.CMD_V1136_CLOSE.set(True))


if __name__ == '__main__':
    # main Tk App
    app = HMIApp()
    app.mainloop()
