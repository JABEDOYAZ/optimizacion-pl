# Aplicación de Programación Lineal (Optimización I)

Aplicación de escritorio desarrollada en Python con interfaz gráfica nativa (**Tkinter**) para formular, validar y resolver problemas de Programación Lineal mediante el **Método de la Gran M** y el **Método Gráfico (2D)**, incluyendo soporte para aritmética con fracciones exactas.

Proyecto desarrollado para la asignatura **Optimización I** — Facultad de Ingeniería, Departamento de Ingeniería de Sistemas, **Universidad de Antioquia**.

---

## Características Principales

* **Interfaz Gráfica Guiada (Tkinter):** Flujo de ingreso por etapas con validación progresiva, edición dinámica del modelo sin reiniciar la aplicación y visualización organizada por pestañas.
* **Validación Estricta del Modelo:** Verificación automática de coeficientes no nulos en la función objetivo ($c_j \neq 0$), restricciones no vacías, cobertura de variables en la matriz $A$, lados derechos de cualquier signo y control de no negatividad ($X_j \ge 0$ o variables libres).
* **Forma Estándar y Gran M Exacto:** Conversión automática de desigualdades ($\le, \ge, =$) mediante variables de holgura ($s_i$), exceso ($e_i$) y artificiales ($a_i$) utilizando aritmética exacta (`fractions.Fraction`).
* **Método Gráfico 2D (`n = 2`):** Renderizado interactivo con Matplotlib que muestra la región factible sombreada, rectas de restricción rotuladas, evaluación de vértices, recta de isoutilidad/isocosto en el óptimo y detección matemática de problemas **infactibles** o **no acotados**.
* **Persistencia en JSON:** Exportación de la configuración del modelo actual a formato `.json`.

---

## Estructura del Proyecto

```text
optimizacion-pl/
├── app.py              # Interfaz gráfica de escritorio (Tkinter) y control de vistas
├── validaciones.py     # Reglas de validación del modelo y serialización JSON
├── solver.py           # Motor matemático: estandarización y Método de la Gran M
├── graph.py            # Motor gráfico 2D (Matplotlib + NumPy)
├── requirements.txt    # Dependencias externas de Python
└── README.md           # Documentación de instalación y uso
```

---

## Requisitos Previos

1. **Python 3.10 o superior.**
2. **Tkinter (paquete del sistema para interfaz gráfica):**
   * **Linux Mint / Ubuntu / Debian:**
     ```bash
     sudo apt update
     sudo apt install python3-tk -y
     ```
   * **Windows / macOS:** Viene incluido por defecto con el instalador oficial de Python.
3. **Dependencias de Python:** `numpy`, `matplotlib` y `sympy`.

---

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/JABEDOYAZ/optimizacion-pl.git](https://github.com/JABEDOYAZ/optimizacion-pl.git)
   cd optimizacion-pl
   ```

2. **Crear y activar un entorno virtual:**
   * **En Linux Mint / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * **En Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Instalar las librerías requeridas:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Ejecución

Al tratarse de una aplicación de escritorio nativa construida con Tkinter, no requiere servidor web ni navegador. Con el entorno virtual activo, ejecuta desde la raíz del proyecto:

```bash
python3 app.py
```

---

## Equipo de Desarrollo

* **Jonatan Andrés Bedoya Zapata**
* **Sergio Idarraga**