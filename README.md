# Laboratorio de fatiga · Fase 1

Herramienta en Streamlit para el curso de Mecánica de materiales. Acompaña las sesiones 2 y 3 del
tema de falla por fatiga (Shigley, cap. 6): límite de resistencia, factores de Marin, sensibilidad a
la muesca y vida finita con el método esfuerzo-vida.

## Niveles

El selector **Nivel**, arriba de las pestañas, adapta toda la herramienta:

- **Sesión 2 · Probeta de laboratorio.** Sólo S′e, f, a, b, Sf, N y la verificación de fluencia.
  Incluye el ejemplo (AISI 1040 CD) y el ejercicio (AISI 1050 HR) de la presentación de la Sesión 2,
  ejercicios numerados y datos propios.
- **Sesión 3 · Pieza real.** Agrega los factores de Marin (ka, kb, kc, kd, ke), la sensibilidad a la
  muesca (q, Kf) y el factor de seguridad nf.

## Qué incluye

- **Explora el diagrama S-N.** Controles para material, acabado, tamaño, carga, confiabilidad, Kt y
  esfuerzo. La curva de la pieza se compara en vivo con la de la probeta. Incluye cinco retos guiados.
- **Resuelve y compara.** El alumno resuelve a mano y captura su resultado en cada paso. La herramienta
  indica si coincide (tolerancia de 2 %; 15 % en la vida N), da pistas para errores frecuentes y
  muestra el procedimiento con la sustitución numérica.
  - *Ejercicio numerado:* el mismo número genera el mismo problema para todos (útil para tareas).
  - *Mis propios datos:* para verificar problemas del libro.
- **Formulario.** Ecuaciones y tablas usadas.

Alcance: aceros, carga completamente invertida en flexión o axial, unidades SI. Kt se lee de las
gráficas del libro.

## Ejecutar en una computadora

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`.

## Publicar en línea (Streamlit Community Cloud, gratuito)

La app queda en una dirección `https://<nombre>.streamlit.app` que los alumnos abren desde el
navegador del centro de cómputo, sin instalar nada.

1. Entra a <https://share.streamlit.io> y firma con tu cuenta de GitHub. La primera vez hay que
   autorizar la aplicación de Streamlit.
2. Pulsa **Create app** y elige la opción de desplegar desde un repositorio existente.
3. Llena los campos:
   - *Repository:* `VickAlc/<nombre-del-repositorio>`
   - *Branch:* `main`
   - *Main file path:* `app.py`
   - *App URL:* el subdominio que quieras (por ejemplo `laboratorio-fatiga`).
4. Pulsa **Deploy**. El primer arranque tarda unos minutos mientras instala las dependencias.

Cada vez que se suba un cambio a la rama `main`, la app se actualiza sola.

### Notas

- El plan gratuito permite **apps públicas ilimitadas y una sola app privada**. Para un grupo de
  alumnos conviene que el repositorio sea público.
- Si la app queda inactiva varios días, Community Cloud la duerme. Despierta sola al abrirla, pero
  tarda un minuto: conviene abrirla antes de la clase.
- Los recursos son limitados (alrededor de 1 GB de memoria). Esta herramienta sólo hace cálculos
  aritméticos, así que va sobrada.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest
```

- `tests/test_calculos.py` valida las ecuaciones contra ejemplos del cap. 6 de Shigley y contra los
  ejemplos de las Sesiones 2 y 3 del curso.
- `tests/test_app.py` recorre la interfaz completa resolviendo ejercicios y comprobando las pistas.

## Estructura

```
app.py                 interfaz de Streamlit
fatiga/calculos.py     ecuaciones (sin dependencias de Streamlit)
tests/                 pruebas
.streamlit/config.toml tema de colores
requirements.txt       dependencias de la app
requirements-dev.txt   dependencias para correr las pruebas
```

## Verificar antes de usar en clase

Los valores de la tabla de aceros (`ACEROS` en `fatiga/calculos.py`) y los coeficientes de la
tabla 6-2 provienen del cap. 6 de Shigley. Conviene cotejarlos contra la edición que use el curso
antes de calificar tareas con la herramienta.
