
# Aplicación de Programación Lineal (Optimización I)

Aplicación de escritorio desarrollada en Python con interfaz gráfica nativa (**Tkinter**) para formular, validar y resolver problemas de Programación Lineal mediante el **Método Simplex de la Gran M** y el **Método Gráfico (2D)**, con soporte para aritmética exacta mediante fracciones y arquitectura modular escalable a nuevos algoritmos (como Simplex Revisado y Análisis de Sensibilidad).

Proyecto desarrollado para la asignatura **Optimización I** — Facultad de Ingeniería, Departamento de Ingeniería de Sistemas, **Universidad de Antioquia**.

---

## Características Principales

* **Arquitectura Modular y Escalable:** Separación clara entre interfaz gráfica, estandarización matricial, aritmética simbólica y motores de resolución, facilitando la incorporación de nuevos métodos basados en Simplex.
* **Interfaz Gráfica Guiada (Tkinter):** Flujo de formulación por etapas con validación progresiva, edición dinámica del modelo sin reiniciar la aplicación y visualización de resultados por pestañas (*Solución / Paso a Paso*, *Método Gráfico* y *Análisis de Sensibilidad*).
* **Formulación Manual o Carga desde JSON:** Permite ingresar problemas manualmente o importar modelos completos desde archivos `.json`, así como exportar el modelo actual a `.json` para reutilizarlo.
* **Formatos Numéricos Flexibles:** Admite enteros (`5`), decimales con punto o coma (`0.1` / `0,1`) y fracciones (`1/10`), permitiendo visualizar las iteraciones y resultados tanto en fracciones exactas como en decimales.
* **Validación Estricta del Modelo:** Verificación automática de coeficientes no nulos en la función objetivo ($c_j \neq 0$), restricciones no vacías, cobertura de todas las variables en la matriz $A$, lados derechos de cualquier signo y control de dominio ($X_j \ge 0$ o variables sin restricción de signo).
* **Diagnóstico Completo de Soluciones:** Ejecución paso a paso (con operaciones elementales de Gauss-Jordan) o solución directa, identificando soluciones óptimas únicas, **soluciones óptimas múltiples** (calculando un vértice óptimo alternativo), **soluciones degeneradas**, problemas **no acotados** y problemas **infactibles**.
* **Método Gráfico 2D (`n = 2`):** Renderizado con Matplotlib que muestra la región factible sombreada, rectas de restricción rotuladas, evaluación de vértices y recta de isoutilidad/isocosto en el punto óptimo.

---

## Estructura del Proyecto

```text
optimizacion-pl/
├── app.py                  # Orquestador principal, ventana raíz y navegación entre vistas
├── vista_formulacion.py    # Interfaz de ingreso manual, validaciones por etapa y carga JSON
├── vista_resultados.py     # Interfaz de resultados (tableros iterativos, resumen y gráfico)
├── aritmetica.py           # Clase TerminoM (aritmética con M) y formateo fracción/decimal
├── estandarizador.py       # Construcción de forma aumentada (holguras, excesos, artificiales)
├── solver_gran_m.py        # Motor matemático del Método Simplex de la Gran M
├── validaciones.py         # Parseo numérico, reglas de validación y lectura/escritura JSON
├── graph.py                # Motor gráfico 2D (Matplotlib + NumPy)
├── requirements.txt        # Dependencias externas de Python
└── README.md               # Documentación de instalación y uso
```

---

## Requisitos Previos

1. **Python 3.10 o superior.**
2. **Tkinter (paquete del sistema para interfaz gráfica):**
   * **Linux Mint / Ubuntu / Debian:**
```sh
     sudo apt update
     sudo apt install python3-tk -y
```

   * **Windows / macOS:** Viene incluido por defecto con el instalador oficial de Python.
3. **Dependencias externas de Python:** `numpy` y `matplotlib`.

---

## Instalación

1. **Clonar el repositorio:**
```sh
   git clone [https://github.com/JABEDOYAZ/optimizacion-pl.git](https://github.com/JABEDOYAZ/optimizacion-pl.git)
   cd optimizacion-pl
```

2. **Crear y activar un entorno virtual:**
   * **En Linux Mint / macOS:**
```sh
     python3 -m venv venv
     source venv/bin/activate
```

   * **En Windows (PowerShell):**
```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
```

3. **Instalar las librerías requeridas:**
```sh
   pip install -r requirements.txt
```

---

## Ejecución

Con el entorno virtual activo, ejecuta desde la raíz del proyecto:

```sh
python3 app.py
```

---

## Equipo de Desarrollo

* **Jonatan Andrés Bedoya Zapata**
* **Sergio Idárraga**
* **Jose Albornoz**
