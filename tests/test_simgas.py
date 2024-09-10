""" Test Tag and generic data sources """

import pytest

from pyHMI.SimGas import celsius_to_kelvin, pipe_water_volume_m3, valve_cv, valve_flow


def test_basic():
    assert celsius_to_kelvin(deg_c=0.0) == pytest.approx(273.15, abs=0.001)
    assert celsius_to_kelvin(deg_c=100.0) == pytest.approx(373.15, abs=0.001)
    assert pipe_water_volume_m3(d_mm=200, l_km=10.0) == pytest.approx(314.16, abs=0.001)


def test_valve_cv():
    # tested with https://www.swagelok.com/fr/toolbox/cv-calculator
    assert valve_cv(q_nm3=10_000, p1_bara=50, p2_bara=45, t_deg_c=6, sg=0.554) == pytest.approx(20.2, abs=0.1)
    assert valve_flow(cv=20.2, p1_bara=50, p2_bara=45, t_deg_c=6, sg=0.554) == pytest.approx(10_000, abs=5)
