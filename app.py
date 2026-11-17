"""Laboratorio de fatiga · Fase 1: resistencia a la fatiga (Shigley, cap. 6).

Niveles: Sesión 2 (probeta de laboratorio) y Sesión 3 (pieza real).

Ejecutar con:  streamlit run app.py
"""
import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from fatiga import calculos as c

INK, RUST, STEEL, SLATE = "#263238", "#C8553D", "#90A4AE", "#546E7A"
TOL = 0.02       # tolerancia general: 2 %
TOL_N = 0.15     # tolerancia para la vida N: 15 %

st.set_page_config(page_title="Laboratorio de fatiga", page_icon="⚙️", layout="wide")


# ───────────────────────── utilidades ─────────────────────────
def sci(x: float) -> str:
    """Notación científica en LaTeX: 2.2 \\times 10^{4}."""
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    return f"{m:.2f} \\times 10^{{{e}}}"


_SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def pot(x: float, dec: int = 1) -> str:
    """Notación científica en texto plano: 2.2 × 10⁴."""
    e = math.floor(math.log10(abs(x)))
    m = round(x / 10 ** e, dec)
    if m >= 10:
        m, e = m / 10, e + 1
    exp = "10" + str(e).translate(_SUP)
    return exp if m == 1 else f"{m:g} × {exp}"


def grafica_sn(Sut, f, Se, a, b, Se_p=None, sigma=None, N=None, alto=430, etiqueta="Pieza real (Se)",
               etiqueta_sigma="Esfuerzo aplicado (Kf·σ₀)", punto=None, extra=None):
    """Diagrama S-N. `punto` = (N, Sf) a resaltar; `extra` = lista de (sigma, N) adicionales."""
    fig = go.Figure()
    if Se_p is not None:
        a0, b0 = c.coef_a_b(f, Sut, Se_p)
        n = np.logspace(3, 6, 60)
        fig.add_trace(go.Scatter(x=np.r_[n, 1e8], y=np.r_[a0 * n ** b0, Se_p], mode="lines",
                                 line=dict(color=STEEL, width=2, dash="dash"),
                                 name="Probeta de laboratorio (S′e)",
                                 hovertemplate="N = %{x:.3g}<br>Sf = %{y:.0f} MPa<extra></extra>"))
    n = np.logspace(3, 6, 60)
    fig.add_trace(go.Scatter(x=np.r_[n, 1e8], y=np.r_[a * n ** b, Se], mode="lines",
                             line=dict(color=RUST, width=4), name=etiqueta,
                             hovertemplate="N = %{x:.3g}<br>Sf = %{y:.0f} MPa<extra></extra>"))
    if sigma:
        fig.add_trace(go.Scatter(x=[1e3, 1e8], y=[sigma, sigma], mode="lines",
                                 line=dict(color=INK, width=2, dash="dot"),
                                 name=etiqueta_sigma, hoverinfo="skip"))
        if N and 1e3 <= N <= 1e6:
            fig.add_trace(go.Scatter(x=[N], y=[sigma], mode="markers",
                                     marker=dict(color=INK, size=13, symbol="circle"),
                                     name="Falla esperada",
                                     hovertemplate="N = %{x:.3g} ciclos<br>σ = %{y:.0f} MPa<extra></extra>"))
    if punto:
        fig.add_trace(go.Scatter(x=[punto[0]], y=[punto[1]], mode="markers",
                                 marker=dict(color=RUST, size=13, symbol="diamond", line=dict(color="white", width=2)),
                                 name="Resistencia Sf a la vida pedida",
                                 hovertemplate="N = %{x:.3g} ciclos<br>Sf = %{y:.0f} MPa<extra></extra>"))
    for s_x, n_x in (extra or []):
        fig.add_trace(go.Scatter(x=[1e3, 1e8], y=[s_x, s_x], mode="lines", showlegend=False,
                                 line=dict(color=SLATE, width=2, dash="dot"), hoverinfo="skip"))
        fig.add_annotation(x=7.9, y=math.log10(s_x), text=f"{s_x:.0f} MPa", showarrow=False,
                           xanchor="right", yanchor="bottom", font=dict(color=SLATE, size=12))
    ys = [Se, f * Sut] + ([Se_p] if Se_p else []) + ([sigma] if sigma else []) + [e[0] for e in (extra or [])]
    fig.update_layout(
        height=alto, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.22, x=0), font=dict(color=INK, size=13),
        xaxis=dict(type="log", title="Número de ciclos, N", range=[3, 8], dtick=1,
                   exponentformat="power", gridcolor="#ECEFF1", linecolor=INK),
        yaxis=dict(type="log", title="Resistencia a la fatiga (MPa)", gridcolor="#ECEFF1", linecolor=INK,
                   range=[math.log10(min(ys) * 0.8), math.log10(max(ys) * 1.15)]),
    )
    return fig


def paso(num, titulo, simbolo, valor, unidad, lineas, clave, tol=TOL, fmt="%.3f", pistas=None,
         mostrar=False, ayuda=None):
    """Un paso verificable: el alumno captura su valor, se compara y se revela el procedimiento.

    Devuelve True (correcto), False (incorrecto) o None (sin intento).
    """
    estado = None
    with st.container(border=True):
        c1, c2, c3 = st.columns([3.2, 2, 2.6], vertical_alignment="center")
        c1.markdown(f"**Paso {num}. {titulo}**")
        if ayuda:
            c1.caption(ayuda)
        intento = c2.number_input(f"Tu resultado: {simbolo}" + (f" ({unidad})" if unidad else ""),
                                  value=None, format=fmt, key=clave, placeholder="Escribe tu valor")
        if intento is None:
            c3.info("Resuélvelo a mano y captura tu valor.", icon="✏️")
        else:
            err = abs(intento - valor) / abs(valor) if valor else abs(intento)
            if err <= tol:
                estado = True
                c3.success(f"Correcto (diferencia de {err * 100:.1f} %).", icon="✅")
            else:
                estado = False
                pista = ""
                for mal, texto in (pistas or []):
                    if mal and abs(intento - mal) / abs(mal) <= 0.01:
                        pista = " " + texto
                        break
                c3.error(f"No coincide (diferencia de {err * 100:.0f} %).{pista} Revisa e intenta de nuevo.", icon="❌")
        if intento is not None or mostrar:
            with st.expander("Ver procedimiento"):
                for ln in lineas:
                    if ln.startswith("$"):
                        st.latex(ln.strip("$"))
                    else:
                        st.markdown(ln)
    return estado


class Contador:
    """Numera los pasos de un problema."""
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return self.n


def cierre(res, mostrar, fig):
    """Barra de avance y gráfica final del problema."""
    hechos = [r for r in res if r is not None]
    bien = sum(1 for r in hechos if r)
    st.progress(bien / len(res), text=f"Pasos correctos: {bien} de {len(res)}")
    if len(hechos) == len(res) or mostrar:
        if bien == len(res):
            st.success("Todos los pasos coinciden con tu solución manual.")
        st.markdown("**Tu problema en el diagrama S-N**")
        st.plotly_chart(fig)
    else:
        st.caption("La gráfica S-N de tu problema aparece cuando completes todos los pasos.")


def controles_revision(pid, claves):
    o1, o2 = st.columns([3, 1], vertical_alignment="center")
    mostrar = o1.toggle("Mostrar todos los procedimientos (revisión en clase)", value=False, key=f"{pid}_mostrar")
    if o2.button("Borrar mis respuestas", key=f"{pid}_borrar"):
        for k in claves:
            st.session_state.pop(f"{pid}_{k}", None)
        st.rerun()
    return mostrar


def texto_f(Sut, f_manual):
    if f_manual:
        return "f capturada de la gráfica del libro."
    if Sut < c.F_UMBRAL:
        return "Como Sut < 483 MPa (70 kpsi), f = 0.9."
    return "De la gráfica de f contra Sut, o con la ecuación (σ′F = Sut + 345 MPa)."


def vida_txt(N):
    return pot(N)


# ═════════════════════════ SESIÓN 2: PROBETA ═════════════════════════
def explora_probeta():
    st.markdown("Aquí trabajas con la **probeta de laboratorio** (pequeña, pulida, sin muescas). "
                "Antes de mover cada control, predice qué va a pasar.")
    izq, der = st.columns([1, 2], gap="large")
    with izq:
        mat = st.selectbox("Material", list(c.ACEROS), index=list(c.ACEROS).index("AISI 1040 CD"), key="p_mat")
        Sut, Sy = c.ACEROS[mat]
        st.caption(f"Sut = {Sut} MPa · Sy = {Sy} MPa")
        N_obj = st.select_slider("Vida requerida, N (ciclos)",
                                 [1e3, 2e3, 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6], value=1e5,
                                 format_func=pot, key="p_N")
        s_max = int(0.95 * Sut)
        sig = st.slider("Esfuerzo completamente invertido, σ (MPa)", int(0.3 * Sut), s_max,
                        min(400, s_max), 5, key="p_sig")
    R = c.resolver_probeta(dict(Sut=Sut, Sy=Sy, N_obj=N_obj, sigmas=[sig], f_manual=None))
    caso = R["casos"][0]
    with der:
        m = st.columns(4)
        m[0].metric("S′e (límite)", f"{R['Se_p']:.0f} MPa"); m[0].caption("0.5 Sut")
        m[1].metric("f·Sut (a 10³ ciclos)", f"{R['f'] * Sut:.0f} MPa"); m[1].caption(f"f = {R['f']:.3f}")
        m[2].metric("Sf a la vida requerida", f"{R['Sf']:.0f} MPa"); m[2].caption(f"a = {R['a']:.0f} MPa · b = {R['b']:.4f}")
        if caso["fluye"]:
            m[3].metric("Vida con σ", "Fluye"); m[3].caption("σ > Sy: el método no aplica")
        elif caso["infinita"]:
            m[3].metric("Vida con σ", "Infinita"); m[3].caption("σ ≤ S′e")
        else:
            m[3].metric("Vida con σ", vida_txt(caso["N"])); m[3].caption(f"ciclos · σ/S′e = {sig / R['Se_p']:.2f}")
        st.plotly_chart(grafica_sn(Sut, R["f"], R["Se_p"], R["a"], R["b"], None, sig, caso["N"],
                                   etiqueta="Probeta (S′e)", etiqueta_sigma="Esfuerzo aplicado σ",
                                   punto=(N_obj, R["Sf"])))
        if caso["fluye"]:
            st.warning(f"El esfuerzo ({sig} MPa) supera Sy ({Sy} MPa): la probeta fluye en el primer ciclo "
                       "y la recta de alto ciclaje no es válida.")
    with st.expander("Retos para explorar (responde primero en tu cuaderno)"):
        st.markdown(
            "1. Compara el AISI 1020 HR con el AISI 1095 HR. ¿Cuánto vale S′e/Sut en cada uno? ¿Qué concluyes?\n"
            "2. Fija un esfuerzo con vida finita y auméntalo 10 %. ¿En qué factor cambia la vida?\n"
            "3. Duplica la vida requerida. ¿En qué porcentaje baja Sf? Compáralo con tu respuesta al reto 2.\n"
            "4. Encuentra el esfuerzo con el que la vida es exactamente 10⁶ ciclos. ¿Qué nombre recibe?\n"
            "5. Con el AISI 1050 HR, sube el esfuerzo hasta que aparezca la advertencia de fluencia. "
            "¿Ocurre antes o después de llegar a f·Sut? ¿Y con el AISI 1050 CD?")


def resuelve_probeta():
    st.markdown("Resuelve el problema **a mano**, paso a paso, y captura cada resultado. La herramienta te dice "
                "si coincide y entonces te muestra el procedimiento.")
    opciones = list(c.EJEMPLOS_PROBETA) + ["Ejercicio numerado", "Mis propios datos"]
    modo = st.radio("Problema", opciones, horizontal=True, key="p_modo")
    if modo in c.EJEMPLOS_PROBETA:
        P = c.EJEMPLOS_PROBETA[modo]
        pid = f"pc{opciones.index(modo)}"
    elif modo == "Ejercicio numerado":
        num = st.number_input("Número de ejercicio", 1, 9999, 1, step=1, key="p_num",
                              help="El mismo número genera siempre el mismo ejercicio para todos.")
        P = c.generar_ejercicio_probeta(int(num))
        pid = f"pe{int(num)}"
    else:
        pid = "pp"
        a1, a2, a3 = st.columns(3)
        with a1:
            mat = st.selectbox("Material", ["Capturar Sut y Sy"] + list(c.ACEROS), index=16, key="pp_mat")
            if mat == "Capturar Sut y Sy":
                Sut = st.number_input("Sut (MPa)", 100.0, 2500.0, 600.0, 10.0, key="pp_Sut")
                Sy = st.number_input("Sy (MPa)", 50.0, 2400.0, 400.0, 10.0, key="pp_Sy")
            else:
                Sut, Sy = map(float, c.ACEROS[mat])
                st.caption(f"Sut = {Sut:.0f} MPa · Sy = {Sy:.0f} MPa")
        with a2:
            N_obj = st.number_input("Vida requerida N (ciclos)", 1e3, 1e6, 1e5, 1e4, format="%.0f", key="pp_N")
            sig = st.number_input("Esfuerzo completamente invertido σ (MPa)", 1.0, 2500.0, 400.0, 5.0, key="pp_sig")
        with a3:
            usar_f = st.checkbox("Capturar f leída de la gráfica del libro", key="pp_usarf")
            f_manual = st.number_input("f", 0.70, 0.95, 0.87, 0.01, key="pp_f") if usar_f else None
        P = dict(material=mat if mat != "Capturar Sut y Sy" else "acero", Sut=Sut, Sy=Sy,
                 N_obj=N_obj, sigmas=[sig], f_manual=f_manual)

    R = c.resolver_probeta(P)
    Sut, Sy = P["Sut"], P["Sy"]
    letras = "abc"
    incisos = [f"**a)** la resistencia a la fatiga para una vida de {pot(P['N_obj'])} ciclos"]
    for i, s in enumerate(P["sigmas"]):
        incisos.append(f"**{letras[i + 1]})** la vida esperada con un esfuerzo completamente invertido de {s:.0f} MPa")
    with st.container(border=True):
        st.markdown(f"**Enunciado.** Una probeta de viga rotatoria (R. R. Moore) de {P['material']} tiene "
                    f"Sut = {Sut:.0f} MPa y Sy = {Sy:.0f} MPa. Estima: " + "; ".join(incisos)
                    + ". Verifica en cada caso si hay fluencia.")

    claves = ["Sep", "f", "a", "b", "Sf"] + [f"{k}{i}" for i in range(len(P["sigmas"])) for k in ("ny", "N")]
    mostrar = controles_revision(pid, claves)
    res, sig_n = [], Contador()

    res.append(paso(sig_n(), "Límite de resistencia de la probeta", "S′e", R["Se_p"], "MPa",
        [f"Como Sut = {Sut:.0f} MPa " + ("≤ 1400 MPa:" if Sut <= 1400 else "> 1400 MPa:"),
         (f"$S'_e = 0.5\\,S_{{ut}} = 0.5({Sut:.0f}) = {R['Se_p']:.1f}\\ \\text{{MPa}}$" if Sut <= 1400
          else "$S'_e = 700\\ \\text{MPa}$"),
         "En la probeta ideal todos los factores de Marin valen 1, así que $S_e = S'_e$."],
        f"{pid}_Sep", fmt="%.1f", mostrar=mostrar,
        pistas=[(0.5 * Sut if Sut > 1400 else None, "Para Sut > 1400 MPa el límite se satura en 700 MPa."),
                (Sut, "Ese valor es Sut; falta el factor 0.5."), (Sy, "Ese valor es Sy; el límite se estima con Sut.")]))
    res.append(paso(sig_n(), "Fracción de resistencia a 10³ ciclos", "f", R["f"], "",
        [texto_f(Sut, P.get("f_manual")),
         f"$f = {R['f']:.3f} \\quad\\Rightarrow\\quad f\\,S_{{ut}} = {R['f'] * Sut:.1f}\\ \\text{{MPa}}$"],
        f"{pid}_f", mostrar=mostrar, ayuda="Léela de la gráfica del libro.",
        pistas=[(0.9 if Sut >= c.F_UMBRAL else None, "f = 0.9 sólo aplica si Sut < 483 MPa (70 kpsi).")]))
    res.append(paso(sig_n(), "Coeficiente a", "a", R["a"], "MPa",
        [f"$a = \\dfrac{{(f\\,S_{{ut}})^2}}{{S_e}} = \\dfrac{{({R['f'] * Sut:.1f})^2}}{{{R['Se_p']:.1f}}} = {R['a']:.1f}\\ \\text{{MPa}}$"],
        f"{pid}_a", fmt="%.1f", tol=0.03, mostrar=mostrar,
        pistas=[(R["f"] * Sut ** 2 / R["Se_p"], "El factor f también va al cuadrado: (f·Sut)²."),
                (R["f"] * Sut, "Ese es f·Sut; falta elevar al cuadrado y dividir entre Se.")]))
    res.append(paso(sig_n(), "Exponente b", "b", R["b"], "",
        [f"$b = -\\dfrac{{1}}{{3}}\\log\\!\\left(\\dfrac{{f\\,S_{{ut}}}}{{S_e}}\\right) = -\\dfrac{{1}}{{3}}\\log\\!\\left(\\dfrac{{{R['f'] * Sut:.1f}}}{{{R['Se_p']:.1f}}}\\right) = {R['b']:.4f}$"],
        f"{pid}_b", fmt="%.4f", tol=0.03, mostrar=mostrar,
        pistas=[(-R["b"], "b es negativo: la resistencia baja al aumentar N."),
                (R["b"] * math.log(10), "Usaste logaritmo natural; va logaritmo base 10."),
                (3 * R["b"], "Falta dividir entre 3.")]))
    res.append(paso(sig_n(), f"a) Resistencia a la fatiga para N = {pot(P['N_obj'])} ciclos",
        "Sf", R["Sf"], "MPa",
        [f"$S_f = a\\,N^{{\\,b}} = {R['a']:.1f}\\,({sci(P['N_obj'])})^{{{R['b']:.4f}}} = {R['Sf']:.1f}\\ \\text{{MPa}}$",
         f"Verificación: {R['Sf']:.0f} MPa " + ("< Sy, no hay fluencia." if R["Sf"] < Sy
            else f"> Sy = {Sy:.0f} MPa: **la probeta fluiría antes** de trabajar a ese esfuerzo.")],
        f"{pid}_Sf", fmt="%.1f", mostrar=mostrar,
        pistas=[(R["a"] * P["N_obj"] ** -R["b"], "Revisa el signo del exponente b.")]))

    extra = []
    for i, caso in enumerate(R["casos"]):
        s, L = caso["sigma"], letras[i + 1]
        if caso["fluye"]:
            concl = (f"Como σ > Sy, **la probeta fluye desde el primer ciclo**. La recta de alto ciclaje supone "
                     "comportamiento elástico y no es válida: no se calcula N con ella.")
        elif caso["infinita"]:
            concl = f"No fluye. Además σ = {s:.0f} MPa ≤ S′e = {R['Se_p']:.0f} MPa: **vida infinita**; no se calcula N."
        else:
            concl = f"No fluye, y σ > S′e = {R['Se_p']:.0f} MPa: **vida finita**. Se calcula N."
        res.append(paso(sig_n(), f"{L}) Verificación de fluencia con σ = {s:.0f} MPa", "ny", caso["ny"], "",
            [f"$n_y = \\dfrac{{S_y}}{{\\sigma}} = \\dfrac{{{Sy:.0f}}}{{{s:.0f}}} = {caso['ny']:.2f}$", concl],
            f"{pid}_ny{i}", fmt="%.2f", mostrar=mostrar, ayuda="Haz esta verificación antes de calcular la vida.",
            pistas=[(1 / caso["ny"], "Está invertido: ny = Sy/σ."), (Sut / s, "Usaste Sut; la fluencia se compara con Sy.")]))
        if caso["N"]:
            lin = [f"$N = \\left(\\dfrac{{\\sigma}}{{a}}\\right)^{{1/b}} = \\left(\\dfrac{{{s:.0f}}}{{{R['a']:.1f}}}\\right)^{{1/({R['b']:.4f})}} = {sci(caso['N'])}\\ \\text{{ciclos}}$",
                   "La vida es muy sensible al redondeo de a y b; por eso aquí la tolerancia es de 15 %."]
            res.append(paso(sig_n(), f"{L}) Vida esperada con σ = {s:.0f} MPa", "N", caso["N"], "ciclos", lin,
                            f"{pid}_N{i}", fmt="%.0f", tol=TOL_N, mostrar=mostrar))
        if i > 0:
            extra.append((s, caso["N"]))

    c0 = R["casos"][0]
    cierre(res, mostrar, grafica_sn(Sut, R["f"], R["Se_p"], R["a"], R["b"], None, c0["sigma"], c0["N"], alto=380,
                                    etiqueta="Probeta (S′e)", etiqueta_sigma="Esfuerzo aplicado σ",
                                    punto=(P["N_obj"], R["Sf"]), extra=extra))


# ═════════════════════════ SESIÓN 3: PIEZA REAL ═════════════════════════
def explora_pieza():
    st.markdown("Mueve los controles y observa cómo cambia la curva de la **pieza real** respecto a la "
                "**probeta de laboratorio**. Antes de mover cada control, predice qué va a pasar.")
    izq, der = st.columns([1, 2], gap="large")
    with izq:
        e_mat = st.selectbox("Material", list(c.ACEROS), index=list(c.ACEROS).index("AISI 1040 CD"), key="e_mat")
        e_Sut, e_Sy = c.ACEROS[e_mat]
        st.caption(f"Sut = {e_Sut} MPa · Sy = {e_Sy} MPa")
        e_acab = st.selectbox("Acabado superficial", list(c.ACABADOS), index=1, key="e_acab")
        e_carga = st.radio("Tipo de carga", list(c.CARGAS), horizontal=True, key="e_carga")
        e_d = st.slider("Diámetro del eje giratorio, d (mm)", 5, 250, 30, key="e_d")
        e_conf = st.select_slider("Confiabilidad", list(c.CONFIABILIDAD), value="50 %", key="e_conf")
        e_Kt = st.slider("Concentración de esfuerzo, Kt", 1.0, 3.0, 1.0, 0.1, key="e_Kt")
        e_r = st.slider("Radio de la muesca, r (mm)", 0.5, 10.0, 2.0, 0.5, key="e_r", disabled=e_Kt == 1.0)
        e_s0 = st.slider("Esfuerzo nominal invertido, σ₀ (MPa)", 20, int(e_Sy), min(200, int(e_Sy)), 5, key="e_s0")
    R = c.resolver(dict(Sut=e_Sut, Sy=e_Sy, acabado=e_acab, carga=e_carga, forma="Redonda giratoria",
                        d=e_d, T=20, conf=e_conf, kf_misc=1.0, Kt=e_Kt, r=e_r, sigma0=e_s0, f_manual=None))
    with der:
        m = st.columns(4)

        def dato(col, titulo, valor, nota):
            col.metric(titulo, valor)
            col.caption(nota)

        dato(m[0], "S′e (probeta)", f"{R['Se_p']:.0f} MPa", "0.5 Sut")
        dato(m[1], "Se (pieza)", f"{R['Se']:.0f} MPa", f"{(1 - R['Se'] / R['Se_p']) * 100:.0f} % menos que la probeta")
        dato(m[2], "Esfuerzo Kf·σ₀", f"{R['sigma']:.0f} MPa", f"Kf = {R['Kf']:.2f}")
        if R["infinita"]:
            dato(m[3], "Vida", "Infinita", f"nf = {R['nf']:.2f}")
        elif R["bajo_ciclaje"]:
            dato(m[3], "Vida", "< 10³ ciclos", "bajo ciclaje: fuera del método")
        else:
            dato(m[3], "Vida", vida_txt(R["N"]), f"ciclos · nf = {R['nf']:.2f} (menor que 1)")
        st.plotly_chart(grafica_sn(e_Sut, R["f"], R["Se"], R["a"], R["b"], R["Se_p"], R["sigma"], R["N"]))
        fac = st.columns(5)
        for col, (nom, val) in zip(fac, [("ka", R["ka"]), ("kb", R["kb"]), ("kc", R["kc"]),
                                         ("kd", R["kd"]), ("ke", R["ke"])]):
            col.metric(nom, f"{val:.3f}")
        if R["fluye"]:
            st.warning("El esfuerzo Kf·σ₀ supera la resistencia a la fluencia: el análisis de alto ciclaje no aplica.")
        if not R["kb_ok"]:
            st.warning("El diámetro está fuera del intervalo de la ecuación de kb (2.79 a 254 mm).")
    with st.expander("Retos para explorar (responde primero en tu cuaderno)"):
        st.markdown(
            "1. Con el material y la carga fijos, cambia el acabado de *esmerilado* a *laminado en caliente*. "
            "¿En qué porcentaje baja Se? ¿Por qué el efecto es mayor en aceros de alta resistencia?\n"
            "2. Sube el diámetro de 10 a 100 mm. ¿Qué pasa con kb? ¿Y si la carga es axial?\n"
            "3. Fija un esfuerzo con vida finita y auméntalo 10 %. ¿En qué factor cambia la vida N? "
            "¿Qué te dice eso sobre la precisión que necesitas al calcular esfuerzos?\n"
            "4. Con Kt = 2, compara un radio de 0.5 mm con uno de 5 mm. ¿Cuál se acerca más a Kf = Kt?\n"
            "5. Compara el 1040 HR con el 1040 CD al mismo esfuerzo. ¿Cuál dura más y por qué?")


def resuelve_pieza():
    st.markdown("Resuelve el problema **a mano**, paso a paso, y captura cada resultado. La herramienta te dice "
                "si coincide y entonces te muestra el procedimiento.")
    modo = st.radio("Datos del problema", ["Ejercicio numerado", "Mis propios datos"], horizontal=True, key="r_modo")

    if modo == "Ejercicio numerado":
        k1, _ = st.columns([1, 3], vertical_alignment="bottom")
        num = k1.number_input("Número de ejercicio", 1, 9999, 1, step=1, key="r_num",
                              help="El mismo número genera siempre el mismo ejercicio para todos.")
        P = c.generar_ejercicio(int(num))
        pid = f"ej{int(num)}"
        nombre = P["material"]
    else:
        pid = "propio"
        a1, a2, a3 = st.columns(3)
        with a1:
            mat = st.selectbox("Material", ["Capturar Sut y Sy"] + list(c.ACEROS), index=16)
            if mat == "Capturar Sut y Sy":
                Sut = st.number_input("Sut (MPa)", 100.0, 2500.0, 600.0, 10.0)
                Sy = st.number_input("Sy (MPa)", 50.0, 2400.0, 400.0, 10.0)
            else:
                Sut, Sy = map(float, c.ACEROS[mat])
                st.caption(f"Sut = {Sut:.0f} MPa · Sy = {Sy:.0f} MPa")
            acabado = st.selectbox("Acabado superficial", list(c.ACABADOS), index=1)
            conf = st.selectbox("Confiabilidad", list(c.CONFIABILIDAD))
        with a2:
            carga = st.radio("Tipo de carga (completamente invertida)", list(c.CARGAS), horizontal=True)
            forma = st.selectbox("Sección", c.FORMAS)
            d = b_ = h_ = 0.0
            if forma.startswith("Redonda"):
                d = st.number_input("Diámetro d (mm)", 1.0, 500.0, 32.0, 1.0)
            else:
                g1, g2 = st.columns(2)
                b_ = g1.number_input("Base b (mm)", 1.0, 500.0, 40.0, 1.0)
                h_ = g2.number_input("Altura h (mm)", 1.0, 500.0, 20.0, 1.0)
            T = st.number_input("Temperatura de operación (°C)", 20.0, 540.0, 20.0, 10.0)
        with a3:
            sigma0 = st.number_input("Esfuerzo nominal invertido σ₀ (MPa)", 1.0, 2500.0, 180.0, 5.0)
            Kt = st.number_input("Kt (1 = sin muesca; léelo de las gráficas A-15)", 1.0, 6.0, 1.0, 0.05)
            r_ = st.number_input("Radio de la muesca r (mm)", 0.1, 50.0, 2.0, 0.5, disabled=Kt == 1.0)
            usar_f = st.checkbox("Capturar f leída de la gráfica del libro")
            f_manual = st.number_input("f", 0.70, 0.95, 0.87, 0.01) if usar_f else None
        P = dict(Sut=Sut, Sy=Sy, acabado=acabado, carga=carga, forma=forma, d=d, b=b_, h=h_, T=T,
                 conf=conf, kf_misc=1.0, Kt=Kt, r=r_, sigma0=sigma0, f_manual=f_manual)
        nombre = mat if mat != "Capturar Sut y Sy" else "acero"

    R = c.resolver(P)
    Sut, Sy = P["Sut"], P["Sy"]

    geo = (f"sección redonda de {P['d']:.0f} mm de diámetro" if P["forma"].startswith("Redonda")
           else f"sección rectangular de {P['b']:.0f} × {P['h']:.0f} mm")
    giro = "giratoria" if P["forma"] == "Redonda giratoria" else "no giratoria"
    muesca = (f" Tiene una muesca con Kt = {P['Kt']:.2f} y radio r = {P['r']:g} mm." if P["Kt"] > 1
              else " No tiene concentradores de esfuerzo.")
    temp = f" Opera a {P['T']:.0f} °C." if P["T"] > 21 else ""
    with st.container(border=True):
        st.markdown(
            f"**Enunciado.** Una pieza {giro} de {nombre} (Sut = {Sut:.0f} MPa, Sy = {Sy:.0f} MPa), con {geo} "
            f"y acabado *{P['acabado'].lower()}*, trabaja con carga de **{P['carga'].lower()}** completamente "
            f"invertida y un esfuerzo nominal σ₀ = **{P['sigma0']:.0f} MPa**.{muesca}{temp} "
            f"Se requiere una confiabilidad de {P['conf']}.\n\n"
            "Determina el límite de resistencia a la fatiga de la pieza, el factor de seguridad para vida "
            "infinita y, si la vida es finita, el número de ciclos esperado.")

    mostrar = controles_revision(pid, ["Sep", "ka", "kb", "Se", "q", "Kf", "sig", "f", "a", "b", "nf", "N"])
    res, sig = [], Contador()

    # 1. S'e
    res.append(paso(sig(), "Límite de resistencia de la probeta", "S′e", R["Se_p"], "MPa",
        [f"Como Sut = {Sut:.0f} MPa " + ("≤ 1400 MPa:" if Sut <= 1400 else "> 1400 MPa:"),
         (f"$S'_e = 0.5\\,S_{{ut}} = 0.5({Sut:.0f}) = {R['Se_p']:.1f}\\ \\text{{MPa}}$" if Sut <= 1400
          else "$S'_e = 700\\ \\text{MPa}$")],
        f"{pid}_Sep", fmt="%.1f", mostrar=mostrar,
        pistas=[(0.5 * Sut if Sut > 1400 else None, "Para Sut > 1400 MPa el límite se satura en 700 MPa."),
                (Sut, "Ese valor es Sut; falta el factor 0.5.")]))

    # 2. ka
    a_k, b_k = c.ACABADOS[P["acabado"]]
    otros = [(c.factor_ka(Sut, k), f"Parece que usaste los coeficientes de «{k.lower()}».")
             for k in c.ACABADOS if k != P["acabado"]]
    a_kpsi = {"Esmerilado": 1.34, "Maquinado o laminado en frío": 2.70,
              "Laminado en caliente": 14.4, "Como sale de la forja": 39.9}[P["acabado"]]
    res.append(paso(sig(), "Factor de superficie", "ka", R["ka"], "",
        [f"De la tabla 6-2, acabado *{P['acabado'].lower()}*: a = {a_k:g} (para Sut en MPa), b = {b_k:g}",
         f"$k_a = a\\,S_{{ut}}^{{\\,b}} = {a_k:g}({Sut:.0f})^{{{b_k:g}}} = {R['ka']:.3f}$"],
        f"{pid}_ka", mostrar=mostrar, ayuda="Tabla 6-2 del libro.",
        pistas=otros + [(a_kpsi * Sut ** b_k, "Usaste el coeficiente a de kpsi con Sut en MPa.")]))

    # 3. kb
    de = R["de"]
    if P["carga"] == "Axial":
        lin = ["En carga axial no hay efecto de tamaño:", "$k_b = 1$"]
        pk = [(c.factor_kb("Flexión", de), "En carga axial kb = 1, sin importar el tamaño.")]
    else:
        lin = []
        if P["forma"] == "Redonda no giratoria":
            lin += ["Sección redonda no giratoria: se usa el diámetro equivalente",
                    f"$d_e = 0.370\\,d = 0.370({P['d']:.0f}) = {de:.2f}\\ \\text{{mm}}$"]
        elif P["forma"] == "Rectangular no giratoria":
            lin += ["Sección rectangular no giratoria: se usa el diámetro equivalente",
                    f"$d_e = 0.808\\sqrt{{b\\,h}} = 0.808\\sqrt{{({P['b']:.0f})({P['h']:.0f})}} = {de:.2f}\\ \\text{{mm}}$"]
        if de <= 51:
            lin += [f"Como 2.79 ≤ {de:.2f} ≤ 51 mm:", f"$k_b = 1.24\\,d^{{-0.107}} = 1.24({de:.2f})^{{-0.107}} = {R['kb']:.3f}$"]
        else:
            lin += [f"Como 51 < {de:.2f} ≤ 254 mm:", f"$k_b = 1.51\\,d^{{-0.157}} = 1.51({de:.2f})^{{-0.157}} = {R['kb']:.3f}$"]
        pk = [(1.0, "kb = 1 sólo aplica en carga axial.")]
        if P["forma"] != "Redonda giratoria" and P["d"]:
            pk.append((c.factor_kb("Flexión", P["d"]), "Usaste d; en una pieza no giratoria va el diámetro equivalente de."))
        pk.append((1.51 * de ** -0.157 if de <= 51 else 1.24 * de ** -0.107, "Revisa el intervalo de diámetros: usaste la otra ecuación."))
    if not R["kb_ok"]:
        st.warning("El diámetro equivalente está fuera del intervalo de la ecuación de kb (2.79 a 254 mm).")
    res.append(paso(sig(), "Factor de tamaño", "kb", R["kb"], "", lin, f"{pid}_kb", mostrar=mostrar, pistas=pk))

    # 4. Se
    TF = P["T"] * 9 / 5 + 32
    lin = [f"kc = {R['kc']:g} (carga de {P['carga'].lower()}) · "
           + (f"kd = {R['kd']:.3f} (polinomio de temperatura con T = {TF:.0f} °F)" if P["T"] > 21 else "kd = 1 (temperatura ambiente)")
           + f" · ke = {R['ke']:g} (confiabilidad de {P['conf']}) · kf = 1",
           "$S_e = k_a\\,k_b\\,k_c\\,k_d\\,k_e\\,k_f\\,S'_e$",
           f"$S_e = ({R['ka']:.3f})({R['kb']:.3f})({R['kc']:g})({R['kd']:.3f})({R['ke']:g})(1)({R['Se_p']:.1f}) = {R['Se']:.1f}\\ \\text{{MPa}}$"]
    res.append(paso(sig(), "Límite de resistencia de la pieza", "Se", R["Se"], "MPa", lin, f"{pid}_Se",
        fmt="%.1f", mostrar=mostrar, ayuda="Incluye kc, kd y ke.",
        pistas=[(R["Se_p"], "Ese es S′e de la probeta; faltan los factores de Marin."),
                (R["ka"] * R["kb"] * R["Se_p"], "Faltan kc, kd o ke."),
                (R["Se"] / R["ke"], "Falta el factor de confiabilidad ke."),
                (R["Se"] / R["kc"], "Falta el factor de carga kc.")]))

    # 5-6. q y Kf
    if P["Kt"] > 1:
        r_in = P["r"] / c.MM_POR_IN
        s_k = Sut / c.MPA_POR_KPSI
        q_mm = 1 / (1 + R["raiz_a"] / math.sqrt(P["r"]))
        res.append(paso(sig(), "Sensibilidad a la muesca", "q", R["q"], "",
            [f"La constante de Neuber usa Sut en kpsi: Sut = {Sut:.0f}/6.895 = {s_k:.1f} kpsi",
             "$\\sqrt{a} = 0.246 - 3.08(10^{-3})S_{ut} + 1.51(10^{-5})S_{ut}^2 - 2.67(10^{-8})S_{ut}^3$",
             f"$\\sqrt{{a}} = {R['raiz_a']:.4f}\\ \\sqrt{{\\text{{in}}}}$",
             f"El radio en pulgadas: r = {P['r']:g}/25.4 = {r_in:.4f} in",
             f"$q = \\dfrac{{1}}{{1 + \\sqrt{{a}}/\\sqrt{{r}}}} = \\dfrac{{1}}{{1 + {R['raiz_a']:.4f}/\\sqrt{{{r_in:.4f}}}}} = {R['q']:.3f}$",
             "También puedes leer q de la gráfica de sensibilidad a la muesca; la diferencia debe ser pequeña."],
            f"{pid}_q", tol=0.04, mostrar=mostrar, ayuda="Ecuación de Neuber o gráfica de q.",
            pistas=[(q_mm, "Usaste r en mm; la constante de Neuber requiere r en pulgadas.")]))
        res.append(paso(sig(), "Factor de concentración a la fatiga", "Kf", R["Kf"], "",
            [f"$K_f = 1 + q\\,(K_t - 1) = 1 + {R['q']:.3f}({P['Kt']:.2f} - 1) = {R['Kf']:.3f}$"],
            f"{pid}_Kf", mostrar=mostrar,
            pistas=[(P["Kt"], "Ese es Kt; el material no es totalmente sensible a la muesca (q < 1).")]))

    # 7. sigma
    res.append(paso(sig(), "Esfuerzo invertido en el punto crítico", "σ", R["sigma"], "MPa",
        [f"$\\sigma = K_f\\,\\sigma_0 = ({R['Kf']:.3f})({P['sigma0']:.0f}) = {R['sigma']:.1f}\\ \\text{{MPa}}$",
         f"Verificación de fluencia: $n_y = S_y/\\sigma = {Sy:.0f}/{R['sigma']:.1f} = {R['ny']:.2f}$ "
         + ("→ no fluye." if not R["fluye"] else "→ **fluye en el primer ciclo**.")],
        f"{pid}_sig", fmt="%.1f", mostrar=mostrar,
        pistas=[(P["sigma0"] if P["Kt"] > 1 else None, "Falta multiplicar por Kf.")]))

    # 8. nf
    res.append(paso(sig(), "Factor de seguridad para vida infinita", "nf", R["nf"], "",
        [f"$n_f = \\dfrac{{S_e}}{{\\sigma}} = \\dfrac{{{R['Se']:.1f}}}{{{R['sigma']:.1f}}} = {R['nf']:.2f}$",
         ("Como nf ≥ 1, el esfuerzo no supera el límite de resistencia: **vida infinita**." if R["infinita"]
          else "Como nf < 1, el esfuerzo supera el límite de resistencia: **vida finita**. Hay que calcular N.")],
        f"{pid}_nf", fmt="%.2f", mostrar=mostrar,
        pistas=[(1 / R["nf"], "Está invertido: nf = Se/σ."), (R["ny"], "Ese es el factor contra la fluencia, Sy/σ.")]))

    # 9-12. vida finita
    if not R["infinita"]:
        res.append(paso(sig(), "Fracción de resistencia a 10³ ciclos", "f", R["f"], "",
            [texto_f(Sut, P.get("f_manual")),
             f"$f = {R['f']:.3f} \\quad\\Rightarrow\\quad f\\,S_{{ut}} = {R['f'] * Sut:.1f}\\ \\text{{MPa}}$"],
            f"{pid}_f", mostrar=mostrar, ayuda="Léela de la gráfica del libro."))
        res.append(paso(sig(), "Coeficiente a", "a", R["a"], "MPa",
            [f"$a = \\dfrac{{(f\\,S_{{ut}})^2}}{{S_e}} = \\dfrac{{({R['f'] * Sut:.1f})^2}}{{{R['Se']:.1f}}} = {R['a']:.1f}\\ \\text{{MPa}}$"],
            f"{pid}_a", fmt="%.1f", tol=0.03, mostrar=mostrar,
            pistas=[((R["f"] * Sut) ** 2 / R["Se_p"], "Usaste S′e de la probeta; va Se de la pieza.")]))
        res.append(paso(sig(), "Exponente b", "b", R["b"], "",
            [f"$b = -\\dfrac{{1}}{{3}}\\log\\!\\left(\\dfrac{{f\\,S_{{ut}}}}{{S_e}}\\right) = -\\dfrac{{1}}{{3}}\\log\\!\\left(\\dfrac{{{R['f'] * Sut:.1f}}}{{{R['Se']:.1f}}}\\right) = {R['b']:.4f}$"],
            f"{pid}_b", fmt="%.4f", tol=0.03, mostrar=mostrar,
            pistas=[(-R["b"], "b es negativo: la resistencia baja al aumentar N."),
                    (R["b"] * math.log(10), "Usaste logaritmo natural; va logaritmo base 10.")]))
        lin = [f"$N = \\left(\\dfrac{{\\sigma}}{{a}}\\right)^{{1/b}} = \\left(\\dfrac{{{R['sigma']:.1f}}}{{{R['a']:.1f}}}\\right)^{{1/({R['b']:.4f})}} = {sci(R['N'])}\\ \\text{{ciclos}}$",
               "La vida es muy sensible al redondeo de a y b; por eso aquí la tolerancia es de 15 %."]
        if R["bajo_ciclaje"]:
            lin.append("**Atención:** N < 10³ ciclos. La recta de alto ciclaje no es válida en este intervalo.")
        res.append(paso(sig(), "Vida esperada", "N", R["N"], "ciclos", lin, f"{pid}_N",
                        fmt="%.0f", tol=TOL_N, mostrar=mostrar))

    if R["fluye"]:
        st.warning(f"El esfuerzo ({R['sigma']:.0f} MPa) supera Sy ({Sy:.0f} MPa): la pieza fluye en el primer "
                   "ciclo y el método esfuerzo-vida de alto ciclaje no es aplicable.")

    cierre(res, mostrar, grafica_sn(Sut, R["f"], R["Se"], R["a"], R["b"], R["Se_p"], R["sigma"], R["N"], alto=380))


# ═════════════════════════ FORMULARIO ═════════════════════════
def formulario(probeta: bool):
    f1, f2 = st.columns(2, gap="large")
    with f1:
        st.subheader("Límite de resistencia")
        st.latex(r"S'_e = \begin{cases} 0.5\,S_{ut} & S_{ut} \le 1400\ \text{MPa} \\ 700\ \text{MPa} & S_{ut} > 1400\ \text{MPa} \end{cases}")
        if probeta:
            st.markdown("En la probeta de laboratorio, $S_e = S'_e$.")
            st.subheader("Verificación de fluencia")
            st.latex(r"n_y = \frac{S_y}{\sigma}")
            st.markdown("Si $\\sigma > S_y$, la probeta fluye en el primer ciclo y la recta de alto ciclaje no aplica.")
        else:
            st.latex(r"S_e = k_a\,k_b\,k_c\,k_d\,k_e\,k_f\,S'_e")
            st.subheader("Factores de Marin")
            st.markdown("**Superficie** (tabla 6-2): $k_a = a\\,S_{ut}^{\\,b}$")
            st.table({"Acabado": list(c.ACABADOS), "a (Sut en kpsi)": ["1.34", "2.70", "14.4", "39.9"],
                      "a (Sut en MPa)": [f"{v[0]:g}" for v in c.ACABADOS.values()],
                      "b": [f"{v[1]:g}" for v in c.ACABADOS.values()]})
            st.markdown("**Tamaño** (flexión; en axial $k_b = 1$):")
            st.latex(r"k_b = \begin{cases} 1.24\,d^{-0.107} & 2.79 \le d \le 51\ \text{mm} \\ 1.51\,d^{-0.157} & 51 < d \le 254\ \text{mm} \end{cases}")
            st.markdown("No giratoria: redonda $d_e = 0.370\\,d$; rectangular $d_e = 0.808\\sqrt{bh}$")
            st.markdown("**Carga:** $k_c = 1$ (flexión), $0.85$ (axial)")
            st.markdown("**Confiabilidad:**")
            st.table({"Confiabilidad": list(c.CONFIABILIDAD), "ke": [f"{v:.3f}" for v in c.CONFIABILIDAD.values()]})
    with f2:
        if not probeta:
            st.subheader("Concentración de esfuerzo")
            st.latex(r"K_f = 1 + q\,(K_t - 1) \qquad q = \frac{1}{1 + \sqrt{a}/\sqrt{r}}")
            st.markdown("Constante de Neuber para flexión o axial (Sut en kpsi, r en pulgadas):")
            st.latex(r"\sqrt{a} = 0.246 - 3.08(10^{-3})S_{ut} + 1.51(10^{-5})S_{ut}^2 - 2.67(10^{-8})S_{ut}^3")
        st.subheader("Vida finita (10³ a 10⁶ ciclos)")
        st.latex(r"S_f = a\,N^{\,b} \qquad N = \left(\frac{\sigma}{a}\right)^{1/b}")
        st.latex(r"a = \frac{(f\,S_{ut})^2}{S_e} \qquad b = -\frac{1}{3}\log\!\left(\frac{f\,S_{ut}}{S_e}\right)")
        st.markdown("$f$: de la gráfica de $f$ contra $S_{ut}$; $f = 0.9$ si $S_{ut} < 483$ MPa (70 kpsi). Ecuación:")
        st.latex(r"f = \frac{\sigma'_F}{S_{ut}}\,(2\cdot10^3)^{b'} \quad \sigma'_F = S_{ut} + 345\ \text{MPa} \quad b' = -\frac{\log(\sigma'_F / S'_e)}{\log(2\cdot10^6)}")
        if not probeta:
            st.subheader("Factores de seguridad")
            st.latex(r"n_f = \frac{S_e}{\sigma} \qquad n_y = \frac{S_y}{\sigma} \qquad \sigma = K_f\,\sigma_0")
        st.subheader("Alcance")
        st.markdown("- Aceros, carga completamente invertida ($\\sigma_m = 0$)"
                    + (" en la probeta de viga rotatoria.\n" if probeta else " en flexión o axial.\n"
                       "- Kt se lee de las gráficas del libro (apéndice A-15).\n")
                    + "- Esfuerzos fluctuantes, torsión y cargas combinadas llegan en fases posteriores.")


# ───────────────────────── página ─────────────────────────
st.title("Laboratorio de fatiga")
st.caption("Resistencia a la fatiga con el método esfuerzo-vida · Referencia: "
           "Budynas y Nisbett, *Diseño en ingeniería mecánica de Shigley*, cap. 6")

NIVELES = ["Sesión 2 · Probeta de laboratorio", "Sesión 3 · Pieza real"]
nivel = st.radio("Nivel", NIVELES, horizontal=True, key="nivel",
                 help="Sesión 2: sólo la probeta (S′e, f, a, b, Sf y N). "
                      "Sesión 3: agrega factores de Marin y concentración de esfuerzo.")
es_probeta = nivel == NIVELES[0]

tab_explora, tab_resuelve, tab_form = st.tabs(["Explora el diagrama S-N", "Resuelve y compara", "Formulario"])
with tab_explora:
    if es_probeta:
        explora_probeta()
    else:
        explora_pieza()
with tab_resuelve:
    if es_probeta:
        resuelve_probeta()
    else:
        resuelve_pieza()
with tab_form:
    formulario(es_probeta)
