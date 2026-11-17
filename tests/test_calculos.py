"""Validación contra ejemplos del cap. 6 de Shigley y contra la Sesión 2 del curso."""
import math
import pytest
from fatiga import calculos as c


def test_limite_probeta():
    assert c.limite_probeta(590) == 295
    assert c.limite_probeta(1600) == 700


def test_ka_ejemplo_shigley():
    # Acero con Sut = 520 MPa, maquinado -> ka = 0.860
    assert c.factor_ka(520, "Maquinado o laminado en frío") == pytest.approx(0.860, abs=0.002)


def test_kb_ejemplo_shigley():
    # Eje de 32 mm: giratorio kb = 0.858; no giratorio de = 11.84 mm, kb = 0.954.
    # El libro usa (d/7.62)^-0.107; la forma redondeada 1.24 d^-0.107 difiere en ~0.3 %.
    assert c.factor_kb("Flexión", 32) == pytest.approx(0.858, abs=0.003)
    de = c.diametro_equivalente("Redonda no giratoria", d=32)
    assert de == pytest.approx(11.84, abs=0.01)
    assert c.factor_kb("Flexión", de) == pytest.approx(0.954, abs=0.003)
    assert c.factor_kb("Axial", 32) == 1.0


def test_kd():
    assert c.factor_kd(20) == 1.0
    assert c.factor_kd(21.2) == pytest.approx(1.0, abs=0.001)
    # 450 °F (232 °C): kd ~ 1.007 según el polinomio
    assert c.factor_kd((450 - 32) * 5 / 9) == pytest.approx(1.007, abs=0.003)


def test_neuber_ejemplo_shigley():
    # Sut = 690 MPa, r = 3 mm, Kt = 1.65 -> q ~ 0.84, Kf ~ 1.55
    q = c.sensibilidad_q(690, 3)
    assert q == pytest.approx(0.84, abs=0.01)
    assert c.factor_Kf(1.65, q) == pytest.approx(1.55, abs=0.01)


def test_sesion2_1040cd():
    Sut = 590
    f = c.fraccion_f(Sut)
    assert f == pytest.approx(0.866, abs=0.001)
    a, b = c.coef_a_b(f, Sut, 295)
    assert a == pytest.approx(885, abs=1)
    assert b == pytest.approx(-0.0795, abs=0.0002)
    assert c.resistencia(a, b, 1e5) == pytest.approx(354, abs=1)
    assert c.vida(a, b, 400) == pytest.approx(2.2e4, rel=0.03)


def test_f_baja_resistencia():
    assert c.fraccion_f(400) == 0.9


def test_resolver_coherente():
    p = dict(Sut=590, Sy=490, acabado="Maquinado o laminado en frío", carga="Flexión",
             forma="Redonda giratoria", d=32, T=20, conf="50 %", kf_misc=1.0,
             Kt=1.0, r=1, sigma0=150, f_manual=None)
    r = c.resolver(p)
    assert r["Se"] == pytest.approx(r["ka"] * r["kb"] * 295)
    assert r["infinita"] and r["N"] is None and r["nf"] > 1
    p["sigma0"] = 300
    r = c.resolver(p)
    assert not r["infinita"]
    assert c.resistencia(r["a"], r["b"], r["N"]) == pytest.approx(300)


def test_ejercicio_reproducible():
    assert c.generar_ejercicio(7) == c.generar_ejercicio(7)
    for n in range(200):
        p = c.generar_ejercicio(n)
        r = c.resolver(p)
        assert r["sigma"] <= p["Sy"] * 1.02 and r["kb_ok"]
        assert r["N"] is None or r["N"] > 1e3


def test_probeta_ejercicio_de_clase():
    R = c.resolver_probeta(c.EJEMPLOS_PROBETA["Ejercicio de clase: AISI 1050 HR"])
    assert R["Se_p"] == 310 and R["Sf"] == pytest.approx(392, abs=1)
    assert R["casos"][0]["N"] == pytest.approx(4.5e5, rel=0.02)
    assert R["casos"][1]["fluye"] and R["casos"][1]["N"] is None


def test_probeta_reproducible():
    assert c.generar_ejercicio_probeta(3) == c.generar_ejercicio_probeta(3)
    for n in range(300):
        P = c.generar_ejercicio_probeta(n)
        R = c.resolver_probeta(P)
        assert not R["casos"][0]["fluye"]
        assert all(k["N"] is None or 1e3 < k["N"] < 1e6 for k in R["casos"])


def test_sesion3_eje_con_hombro():
    # Eje 1040 CD, d = 32 mm, maquinado, 99 %, hombro r = 3 mm con Kt = 1.65, M = 400 N·m
    s0 = 32 * 400e3 / (math.pi * 32 ** 3)
    r = c.resolver(dict(Sut=590, Sy=490, acabado="Maquinado o laminado en frío", carga="Flexión",
                        forma="Redonda giratoria", d=32, T=20, conf="99 %", kf_misc=1.0,
                        Kt=1.65, r=3, sigma0=s0, f_manual=None))
    assert s0 == pytest.approx(124.3, abs=0.1)
    assert r["Se"] == pytest.approx(171, abs=0.5)
    assert r["Kf"] == pytest.approx(1.53, abs=0.005)
    assert r["nf"] == pytest.approx(0.90, abs=0.005)
    assert r["N"] == pytest.approx(5.0e5, rel=0.02)
