"""Prueba de la interfaz: respuestas correctas, incorrectas con pista, y datos propios."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from fatiga import calculos as c

APP = str(Path(__file__).resolve().parent.parent / "app.py")
S2, S3 = "Sesión 2 · Probeta de laboratorio", "Sesión 3 · Pieza real"


def _app(nivel):
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.radio(key="nivel").set_value(nivel).run()
    assert not at.exception
    return at


def _campo(at, simbolo):
    return next(n for n in at.number_input if n.label.startswith(f"Tu resultado: {simbolo}"))


def _llenar(at, vals):
    """vals: lista de (símbolo, valor) en el orden en que aparecen los campos."""
    campos = [n for n in at.number_input if n.label.startswith("Tu resultado: ")]
    assert len(campos) == len(vals), ([n.label for n in campos], vals)
    for n, (s, v) in zip(campos, vals):
        assert n.label.startswith(f"Tu resultado: {s}"), (n.label, s)
        n.set_value(v)
    at.run()
    assert not at.exception
    assert len(at.error) == 0, [e.value for e in at.error]
    assert any("Todos los pasos coinciden" in s.value for s in at.success)


def _vals_probeta(R):
    v = [("S′e", R["Se_p"]), ("f", R["f"]), ("a", R["a"]), ("b", R["b"]), ("Sf", R["Sf"])]
    for caso in R["casos"]:
        v.append(("ny", caso["ny"]))
        if caso["N"]:
            v.append(("N", caso["N"]))
    return v


def test_pieza_ejercicios_numerados():
    for num in (1, 2, 3, 5, 8, 10, 13):
        at = _app(S3)
        at.number_input(key="r_num").set_value(num).run()
        R = c.resolver(c.generar_ejercicio(num))
        v = [("S′e", R["Se_p"]), ("ka", R["ka"]), ("kb", R["kb"]), ("Se", R["Se"])]
        if R["q"] is not None:
            v += [("q", R["q"]), ("Kf", R["Kf"])]
        v += [("σ", R["sigma"]), ("nf", R["nf"])]
        if not R["infinita"]:
            v += [("f", R["f"]), ("a", R["a"]), ("b", R["b"]), ("N", R["N"])]
        _llenar(at, v)


def test_pieza_pista_y_datos_propios():
    at = _app(S3)
    P = c.generar_ejercicio(1)
    _campo(at, "S′e").set_value(P["Sut"]).run()
    assert any("falta el factor 0.5" in e.value for e in at.error)
    at.radio(key="r_modo").set_value("Mis propios datos").run()
    assert not at.exception
    _campo(at, "S′e").set_value(295.0).run()   # 1040 CD por omisión
    assert any("Correcto" in s.value for s in at.success)


def test_probeta_ejemplos_de_clase():
    at = AppTest.from_file(APP, default_timeout=30).run()   # nivel inicial: Sesión 2, ejemplo 1040 CD
    assert not at.exception
    # Valores de la presentación de la Sesión 2, redondeados como en clase
    _llenar(at, [("S′e", 295), ("f", 0.866), ("a", 885), ("b", -0.0795), ("Sf", 354), ("ny", 1.225), ("N", 2.2e4)])

    at = _app(S2)
    at.radio(key="p_modo").set_value("Ejercicio de clase: AISI 1050 HR").run()
    _llenar(at, [("S′e", 310), ("f", 0.859), ("a", 914), ("b", -0.0783), ("Sf", 392),
                 ("ny", 1.03), ("N", 4.5e5), ("ny", 0.895)])


def test_probeta_numerados_y_propios():
    for num in (1, 2, 3, 4, 7, 11):
        at = _app(S2)
        at.radio(key="p_modo").set_value("Ejercicio numerado").run()
        at.number_input(key="p_num").set_value(num).run()
        _llenar(at, _vals_probeta(c.resolver_probeta(c.generar_ejercicio_probeta(num))))
    at = _app(S2)
    at.radio(key="p_modo").set_value("Mis propios datos").run()
    assert not at.exception
    _campo(at, "b").set_value(0.0795).run()
    assert any("b es negativo" in e.value for e in at.error)
