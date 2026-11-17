"""Cálculos de fatiga (método esfuerzo-vida) según Shigley, cap. 6.

Unidades: esfuerzos en MPa, longitudes en mm, temperatura en °C.
Fase 1: carga completamente invertida en flexión o axial.
"""
from __future__ import annotations

import math
import random

MPA_POR_KPSI = 6.894757
MM_POR_IN = 25.4

# Aceros al carbono (valores típicos tipo tabla A-20 de Shigley): Sut, Sy en MPa
ACEROS = {
    "AISI 1006 HR": (300, 170), "AISI 1006 CD": (330, 280),
    "AISI 1010 HR": (320, 180), "AISI 1010 CD": (370, 300),
    "AISI 1015 HR": (340, 190), "AISI 1015 CD": (390, 320),
    "AISI 1018 HR": (400, 220), "AISI 1018 CD": (440, 370),
    "AISI 1020 HR": (380, 210), "AISI 1020 CD": (470, 390),
    "AISI 1030 HR": (470, 260), "AISI 1030 CD": (520, 440),
    "AISI 1035 HR": (500, 270), "AISI 1035 CD": (550, 460),
    "AISI 1040 HR": (520, 290), "AISI 1040 CD": (590, 490),
    "AISI 1045 HR": (570, 310), "AISI 1045 CD": (630, 530),
    "AISI 1050 HR": (620, 340), "AISI 1050 CD": (690, 580),
    "AISI 1060 HR": (680, 370),
    "AISI 1080 HR": (770, 420),
    "AISI 1095 HR": (830, 460),
}

# Factor de superficie ka = a * Sut^b  (Sut en MPa)
ACABADOS = {
    "Esmerilado": (1.58, -0.085),
    "Maquinado o laminado en frío": (4.51, -0.265),
    "Laminado en caliente": (57.7, -0.718),
    "Como sale de la forja": (272.0, -0.995),
}

CARGAS = {"Flexión": 1.0, "Axial": 0.85}

FORMAS = ["Redonda giratoria", "Redonda no giratoria", "Rectangular no giratoria"]

# Factor de confiabilidad ke
CONFIABILIDAD = {
    "50 %": 1.000, "90 %": 0.897, "95 %": 0.868, "99 %": 0.814,
    "99.9 %": 0.753, "99.99 %": 0.702, "99.999 %": 0.659, "99.9999 %": 0.620,
}

F_UMBRAL = 70 * MPA_POR_KPSI  # por debajo de 70 kpsi (~483 MPa) se usa f = 0.9


def limite_probeta(Sut: float) -> float:
    """S'e de la probeta de viga rotatoria (aceros)."""
    return 0.5 * Sut if Sut <= 1400 else 700.0


def factor_ka(Sut: float, acabado: str) -> float:
    a, b = ACABADOS[acabado]
    return a * Sut ** b


def diametro_equivalente(forma: str, d: float = 0.0, b: float = 0.0, h: float = 0.0) -> float:
    if forma == "Redonda giratoria":
        return d
    if forma == "Redonda no giratoria":
        return 0.370 * d
    return 0.808 * math.sqrt(b * h)


def factor_kb(carga: str, de: float) -> float:
    """Factor de tamaño. En carga axial no hay efecto de tamaño."""
    if carga == "Axial":
        return 1.0
    if de <= 51:
        return 1.24 * de ** -0.107      # válido desde 2.79 mm
    return 1.51 * de ** -0.157          # válido hasta 254 mm


def kb_en_rango(carga: str, de: float) -> bool:
    return carga == "Axial" or 2.79 <= de <= 254


def factor_kc(carga: str) -> float:
    return CARGAS[carga]


def factor_kd(T_C: float) -> float:
    """Factor de temperatura (polinomio de Shigley en °F, 20 a 540 °C)."""
    if T_C <= 21:
        return 1.0
    TF = T_C * 9 / 5 + 32
    return (0.975 + 0.432e-3 * TF - 0.115e-5 * TF ** 2
            + 0.104e-8 * TF ** 3 - 0.595e-12 * TF ** 4)


def raiz_a_neuber(Sut: float) -> float:
    """Constante de Neuber sqrt(a) en sqrt(in), para flexión o axial."""
    s = Sut / MPA_POR_KPSI
    return 0.246 - 3.08e-3 * s + 1.51e-5 * s ** 2 - 2.67e-8 * s ** 3


def sensibilidad_q(Sut: float, r_mm: float) -> float:
    return 1.0 / (1.0 + raiz_a_neuber(Sut) / math.sqrt(r_mm / MM_POR_IN))


def factor_Kf(Kt: float, q: float) -> float:
    return 1.0 + q * (Kt - 1.0)


def fraccion_f(Sut: float) -> float:
    """Fracción de resistencia a la fatiga a 10^3 ciclos."""
    if Sut < F_UMBRAL:
        return 0.9
    Se_p = limite_probeta(Sut)
    sF = Sut + 345.0
    bp = -math.log10(sF / Se_p) / math.log10(2e6)
    return sF / Sut * (2e3) ** bp


def coef_a_b(f: float, Sut: float, Se: float) -> tuple[float, float]:
    a = (f * Sut) ** 2 / Se
    b = -math.log10(f * Sut / Se) / 3.0
    return a, b


def resistencia(a: float, b: float, N: float) -> float:
    return a * N ** b


def vida(a: float, b: float, sigma: float) -> float:
    return (sigma / a) ** (1.0 / b)


def resolver(p: dict) -> dict:
    """Resuelve un caso completo. `p` contiene:
    Sut, Sy, acabado, carga, forma, d, b, h, T, conf, kf_misc, Kt, r, sigma0, f_manual (o None)
    """
    Sut, Sy = p["Sut"], p["Sy"]
    r = {}
    r["Se_p"] = limite_probeta(Sut)
    r["ka"] = factor_ka(Sut, p["acabado"])
    r["de"] = diametro_equivalente(p["forma"], p.get("d", 0), p.get("b", 0), p.get("h", 0))
    r["kb"] = factor_kb(p["carga"], r["de"])
    r["kb_ok"] = kb_en_rango(p["carga"], r["de"])
    r["kc"] = factor_kc(p["carga"])
    r["kd"] = factor_kd(p.get("T", 20))
    r["ke"] = CONFIABILIDAD[p.get("conf", "50 %")]
    r["kf_misc"] = p.get("kf_misc", 1.0)
    r["Se"] = r["ka"] * r["kb"] * r["kc"] * r["kd"] * r["ke"] * r["kf_misc"] * r["Se_p"]

    Kt = p.get("Kt", 1.0)
    if Kt > 1.0:
        r["raiz_a"] = raiz_a_neuber(Sut)
        r["q"] = sensibilidad_q(Sut, p["r"])
        r["Kf"] = factor_Kf(Kt, r["q"])
    else:
        r["raiz_a"], r["q"], r["Kf"] = None, None, 1.0
    r["sigma"] = r["Kf"] * p["sigma0"]

    r["f"] = p["f_manual"] if p.get("f_manual") else fraccion_f(Sut)
    r["a"], r["b"] = coef_a_b(r["f"], Sut, r["Se"])
    r["nf"] = r["Se"] / r["sigma"] if r["sigma"] > 0 else math.inf
    r["ny"] = Sy / r["sigma"] if r["sigma"] > 0 else math.inf
    r["infinita"] = r["sigma"] <= r["Se"]
    r["N"] = None if r["infinita"] else vida(r["a"], r["b"], r["sigma"])
    r["bajo_ciclaje"] = (r["N"] is not None) and r["N"] < 1e3
    r["fluye"] = r["sigma"] > Sy
    return r


def generar_ejercicio(numero: int) -> dict:
    """Ejercicio reproducible: el mismo número genera siempre los mismos datos."""
    rng = random.Random(numero)
    material = rng.choice(list(ACEROS))
    Sut, Sy = ACEROS[material]
    carga = rng.choice(["Flexión", "Flexión", "Axial"])
    forma = "Redonda giratoria" if carga == "Flexión" else "Redonda no giratoria"
    acabado = "Laminado en caliente" if material.endswith("HR") and rng.random() < 0.4 \
        else rng.choice(["Maquinado o laminado en frío", "Esmerilado"])
    p = dict(material=material, Sut=float(Sut), Sy=float(Sy), acabado=acabado, carga=carga,
             forma=forma, d=float(rng.choice([20, 25, 30, 32, 40, 45, 50, 60])), b=0.0, h=0.0,
             T=20.0, conf=rng.choice(["50 %", "90 %", "99 %"]), kf_misc=1.0,
             Kt=rng.choice([1.0, 1.5, 1.7, 2.0, 2.2]), r=float(rng.choice([1, 1.5, 2, 3, 4])),
             sigma0=100.0, f_manual=None)
    base = resolver(p)
    objetivo = base["Se"] * rng.uniform(0.75, 1.6)          # mezcla de vida finita e infinita
    objetivo = min(objetivo, 0.95 * Sy)
    p["sigma0"] = max(5.0, 5.0 * round(objetivo / base["Kf"] / 5.0))
    return p


# ───────────── Sesión 2: probeta de laboratorio (Se = S'e) ─────────────
EJEMPLOS_PROBETA = {
    "Ejemplo de clase: AISI 1040 CD": dict(material="AISI 1040 CD", Sut=590.0, Sy=490.0,
                                            N_obj=1e5, sigmas=[400.0], f_manual=None),
    "Ejercicio de clase: AISI 1050 HR": dict(material="AISI 1050 HR", Sut=620.0, Sy=340.0,
                                              N_obj=5e4, sigmas=[330.0, 380.0], f_manual=None),
}


def resolver_probeta(p: dict) -> dict:
    """Probeta de viga rotatoria. `p`: Sut, Sy, N_obj, sigmas (lista), f_manual (o None)."""
    Sut, Sy = p["Sut"], p["Sy"]
    r = {"Se_p": limite_probeta(Sut)}
    r["f"] = p["f_manual"] if p.get("f_manual") else fraccion_f(Sut)
    r["a"], r["b"] = coef_a_b(r["f"], Sut, r["Se_p"])
    r["Sf"] = resistencia(r["a"], r["b"], p["N_obj"])
    r["casos"] = []
    for s in p["sigmas"]:
        caso = {"sigma": s, "ny": Sy / s, "fluye": s > Sy, "infinita": s <= r["Se_p"], "N": None}
        if not caso["fluye"] and not caso["infinita"]:
            caso["N"] = vida(r["a"], r["b"], s)
        r["casos"].append(caso)
    return r


def generar_ejercicio_probeta(numero: int) -> dict:
    """Ejercicio reproducible de probeta. Uno de cada cuatro incluye un esfuerzo que supera Sy."""
    rng = random.Random(10_000 + numero)
    material = rng.choice(list(ACEROS))
    Sut, Sy = ACEROS[material]
    Se_p = limite_probeta(Sut)
    f = fraccion_f(Sut)
    N_obj = rng.choice([2e3, 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5])
    tope = min(0.95 * f * Sut, 0.97 * Sy)
    if tope > 1.06 * Se_p:
        s1 = 5.0 * round(rng.uniform(1.06 * Se_p, tope) / 5.0)
        s1 = min(max(s1, 5.0 * math.ceil(1.03 * Se_p / 5.0)), 5.0 * math.floor(Sy / 5.0))
    else:                      # aceros con Sy muy baja: el esfuerzo queda bajo el límite de resistencia
        s1 = 5.0 * round(0.9 * Se_p / 5.0)
    sigmas = [float(s1)]
    if rng.random() < 0.25 and Sy < 0.9 * f * Sut:
        sigmas.append(float(5.0 * math.ceil(rng.uniform(1.05, 1.15) * Sy / 5.0)))
    return dict(material=material, Sut=float(Sut), Sy=float(Sy), N_obj=N_obj, sigmas=sigmas, f_manual=None)
