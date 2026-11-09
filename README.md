# Aplicación de Programación Lineal — Método de la Gran M y Simplex Revisado

**Autor:** Jonatan Andrés Bedoya Zapata

---

## Descripción del Proyecto

Esta aplicación es una herramienta web interactiva desarrollada íntegramente en **Python** utilizando **Streamlit**, diseñada para la formulación, resolución y análisis didáctico de problemas de **Programación Lineal (PL)**.

La aplicación permite resolver modelos de optimización ($MAX$ y $MIN$) mediante una implementación propia del **Método de la Gran M** y del **Método Simplex Revisado**, mostrando tanto la solución directa como el desarrollo detallado paso a paso (forma estándar, prueba de la razón mínima, variables entrantes/salientes, pivotes y tableros iterativos con fracciones exactas).

---

## Requisitos del Sistema y Dependencias

### Prerrequisitos
* **Sistema Operativo:** Linux (Ubuntu/Mint), macOS o Windows.
* **Python:** Versión `3.10` o superior.
* **Git:** Para el control de versiones.

### Librerías de Python requeridas
* `streamlit` — Interfaz gráfica web interactiva.
* `numpy` — Manejo y operaciones matriciales.
* `matplotlib` — Renderizado de la región factible y gráficos 2D.
* `sympy` — Operaciones simbólicas.

---

## Instalación y Configuración Local

Sigue estos pasos en tu terminal para clonar y ejecutar el proyecto localmente:

### 1. Clonar el repositorio
```bash
git clone https://github.com/JABEDOYAZ/optimizacion-pl.git
cd optimizacion-pl
```

### 2. Crear y activar el entorno virtual
En **Linux / macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

En **Windows (PowerShell)**:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar las dependencias
```bash
pip install --upgrade pip
pip install streamlit numpy matplotlib sympy
```

*(Opcional: usando el archivo `requirements.txt`)*
```bash
pip install -r requirements.txt
```

---

## Ejecución de la Aplicación

Para iniciar el servidor local de Streamlit, ejecuta en la terminal activa:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador web en la dirección:
`http://localhost:8501`

Para detener la ejecución de la aplicación en la terminal, presiona `Ctrl + C`.


---

## 📁 Estructura del Código

```text
optimizacion-pl/
├── app.py              # Interfaz de usuario interactiva (Streamlit)
├── solver.py           # Algoritmo de solución (Gran M y Simplex Revisado)
├── graph.py            # Módulo gráfico 2D para la región factible (n = 2)
├── sensitivity.py      # Módulo para el análisis de sensibilidad y rangos
├── README.md           # Documentación general del proyecto
└── requirements.txt    # Lista de dependencias del proyecto
```

---

## Funcionalidades Implementadas

- [x] **Entrada y Validación:** Formulación general con $n$ variables, $m$ restricciones ($\le, \ge, =$), lados derechos de cualquier signo y opción de variables no restringidas de signo.
- [x] **Forma Estándar:** Identificación de variables de holgura ($s_i$), exceso ($e_i$) y artificiales ($a_i$).
- [x] **Diferenciación de Modos:** Selección entre *Solución directa* y *Paso a paso*.
- [ ] **Tableros Iterativos (Gran M):** Mostrar prueba de razón mínima, variable entrante, saliente y elemento pivote.
- [ ] **Método Gráfico ($n = 2$):** Región factible sombreada, vértices evaluados y recta de isoutilidad.
- [ ] **Análisis de Sensibilidad:** Precios sombra, costos reducidos y rangos permisibles de variación.
- [ ] **Casos Especiales:** Detección de infactibilidad, no acotamiento, soluciones múltiples y degeneración.

---

## Licencia y Uso Académico

Este proyecto se desarrolla exclusivamente con fines académicos para la asignatura Optimización I de la Universidad de Antioquia.
