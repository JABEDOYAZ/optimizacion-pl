import streamlit as st 
import numpy as np
from solver import GranM # Importación de la clase principal GranM desde el módulo solver.py

st.set_page_config(page_title="Optimizador PL", layout="wide")

# Título principal de la aplicación y autoría del proyecto
st.title("Aplicación de Programación Lineal") # Encabezado principal de la página
st.markdown("**Hecho por Jonatan Andrés Bedoya Zapata**") # Subtítulo con información del desarrollador

# ---------------------------------------------------------
# BARRA LATERAL: Opciones de Configuración y Gestión de Archivos
# ---------------------------------------------------------
with st.sidebar: # Apertura del contenedor de la barra lateral izquierda
    st.header("Ajustes") # Título de la sección de ajustes en la barra lateral
    modo_solucion = st.radio("Modos de solución:", ["Paso a paso", "Solución directa"]) # Selector de radio para cambiar entre modo educativo o directo
    mostrar_fracciones = st.checkbox("Mostrar en fracciones exactas", value=True) # Casilla de verificación para alternar entre fracciones o decimales

    st.divider() 
    st.header("Archivo (JSON)") # Encabezado para la sección de persistencia de datos
    st.file_uploader("Cargar problema (.json)", type=["json"]) # Componente para subir archivos guardados previamente
    if st.button("Guardar el problema actual"): # Botón para exportar la configuración actual del modelo
        st.toast("Función de guardado pendiente de implementación") # Notificación emergente temporal en pantalla

# ---------------------------------------------------------
# SECCIÓN 1: Formulación del Modelo
# ---------------------------------------------------------
st.header("Definición del Modelo de Programación Lineal a resolver") 

col_type, col_vars, col_cons = st.columns(3) # Creación de tres columnas de igual ancho para organizar los controles principales

with col_type: # Columna 1: Selección del objetivo de optimización
    tipo_objetivo = st.selectbox("Objetivo:", ["MAXIMIZAR", "MINIMIZAR"])

with col_vars: # Columna 2: Selección de la cantidad de variables de decisión
    n_vars = st.number_input("Número de Variables (n):", min_value=2, max_value=10, value=2, step=1) # Entrada numérica entera para n (mínimo 2)

with col_cons: # Columna 3: Selección de la cantidad de restricciones del problema
    m_cons = st.number_input("Número de Restricciones (m):", min_value=1, max_value=15, value=3, step=1) # Entrada numérica entera para m (mínimo 1)

st.divider()

# ---------------------------------------------------------
# SECCIÓN 2: Coeficientes de la Función Objetivo (Z)
# ---------------------------------------------------------
st.subheader("Función Objetivo Z")
cols_f_obj = st.columns(int(n_vars)) # Generación dinámica de 'n' columnas para ingresar cada coeficiente c_j
coef_z = [] # Lista vacía donde se almacenarán los coeficientes c_j ingresados

for j in range(int(n_vars)): # Bucle para iterar a través de cada variable de decisión X_j
    with cols_f_obj[j]: # Asignación de cada campo de entrada a su respectiva columna
        val = st.number_input(f"c_{j+1} (X{j+1})", value=0.0, key=f"z_{j}") # Campo numérico para el coeficiente c_j
        coef_z.append(val) # Adición del valor ingresado a la lista coef_z

st.divider()

# ---------------------------------------------------------
# SECCIÓN 3: Matriz de Restricciones y Dominio de Variables
# ---------------------------------------------------------
st.subheader("Restricciones (Sujeto a) - Ax ≤ b, Ax ≥ b, Ax = b") 

restricciones = [] # Lista donde se guardará cada restricción procesada como un diccionario
for i in range(int(m_cons)): # Bucle para construir cada una de las 'm' filas de restricciones
    cols_r = st.columns(int(n_vars) + 2) # Se crean (n + 2) columnas: n para coeficientes A, 1 para el signo y 1 para RHS (b)
    row_coefs = [] # Lista temporal para los coeficientes a_ij de la fila actual
    
    # Captura de Coeficientes a_ij de la matriz A
    for j in range(int(n_vars)): # Iteración sobre las variables de decisión de la restricción
        with cols_r[j]: # Posicionamiento del campo de texto en la columna correspondiente
            val = st.number_input(f"a_{i+1}{j+1}", value=1.0 if i==j else 0.0, key=f"a_{i}_{j}") # Valor inicial 1.0 en diagonal, 0.0 en el resto
            row_coefs.append(val) # Inserción del coeficiente a_ij en la lista de la fila
            
    # Captura del Operador/Signo de la restricción
    with cols_r[-2]: # Penúltima columna dedicada al selector del signo de desigualdad/igualdad
        signo = st.selectbox(f"Signo de R{i+1}", ["<=", ">=", "="], key=f"signo_{i}") # Opciones de signo soportadas
        
    # Captura del Término Independiente Lado Derecho (RHS / b_i)
    with cols_r[-1]: # Última columna dedicada al valor escalar del lado derecho b_i
        b_val = st.number_input(f"b_{i+1}", value=10.0, key=f"b_{i}") # Campo numérico para el lado derecho (permite valores negativos)
        
    # Agrupación de la restricción completa en la estructura de datos principal
    restricciones.append({"coefs": row_coefs, "signo": signo, "b": b_val})

# Configuración del dominio de signo para las variables de decisión (Restricciones implícitas X >= 0)
st.markdown("##### Restricción de Signo de las Variables") # Sub-encabezado de configuración de signo
permitir_negativos = st.checkbox("Permitir valores negativos en las variables de decisión (Variables no restringidas de signo)", 
    value=False, # Valor predeterminado desmarcado (asume X_j >= 0)
    help="Si está desmarcado, se asume la condición estándar X_j >= 0 para todas las variables." # Mensaje de ayuda contextual
)

if not permitir_negativos: # Condicional para mostrar en pantalla el estado actual del dominio de variables
    st.caption("Condición activa: **X_j ≥ 0** para todo j = 1, ..., n") 
else:
    st.caption("Condición activa: Las variables de decisión **pueden ser negativas** (sin restricción de signo).")

# ---------------------------------------------------------
# SECCIÓN 4: Validación, Ejecución y Organización de Resultados
# ---------------------------------------------------------
st.divider() 

if st.button("Resolver Problema", type="primary"):
    
    # Validación básica de datos de entrada antes de resolver
    es_valido = True 
    for i, r in enumerate(restricciones): # Inspección de cada restricción ingresada
        if all(c == 0 for c in r["coefs"]): # Verificación: Si todos los coeficientes a_ij en una restricción son 0
            st.error(f"Error en Restricción {i+1}: Todos los coeficientes son cero.")
            es_valido = False
            
    if es_valido: # Si la entrada superó los controles de consistencia
        st.success("Modelo validado correctamente. Generando solución...")

        solver = GranM(tipo_objetivo, coef_z, restricciones, permitir_negativos=permitir_negativos)
        info_estandar = solver.estandarizar()

        # Creación de pestañas ordenadas para la visualización de salidas según rúbrica
        tab_pasos, tab_grafico, tab_sensibilidad = st.tabs([ 
            "Solución / Paso a Paso", # Pestaña 1: Algoritmo y tableros
            "Método Gráfico", # Pestaña 2: Representación gráfica 2D
            "Análisis de Sensibilidad" # Pestaña 3: Precios sombra y rangos
        ])

        with tab_pasos: 
            st.subheader(f"Modo Seleccionado: {modo_solucion}")
            
            if modo_solucion == "Paso a paso":
                st.markdown("---") 
                st.subheader("1. Forma Estándar del Modelo")
                st.write("**Variables identificadas:**", ", ".join(info_estandar["nombres_vars"])) 
                st.write("**Base Inicial:**", ", ".join(info_estandar["vars_basicas_iniciales"]))
            
                st.markdown("##### Ecuaciones Estandarizadas:") 
                for eq in info_estandar["forma_estandar"]:
                    st.code(eq, language="text")

                st.markdown("---") 
                st.subheader("2. Iteraciones del Método Simplex (Gran M)")

                st.info("Aquí se mostrarán las tablas iterativas paso a paso, mostrando variable entrante, prueba de la razón mínima, pivote y variable saliente.") # Trabajar en esta parte - Falta implementar la lógica de iteración y visualización de tablas
            
            else: 
                st.markdown("---") 
                st.subheader("Solución Óptima Directa")
                st.info("Aquí se desplegará únicamente el resultado final óptimo (Valor de Z*, X* y holguras/excesos).")

        with tab_grafico: 
            if n_vars == 2: 
                st.subheader("Gráfica del Área Factible (2D)") 
                st.info("Aquí renderizaremos la región factible sombreada, vértices evaluados y recta de isoutilidad.") 
            else: 
                st.warning("El método gráfico no aplica para problemas con más de 2 variables de decisión.") 

        with tab_sensibilidad: 
            st.subheader("Tabla de Sensibilidad") 
            st.info("Aquí se mostrarán precios sombra, costos reducidos y rangos permisibles de variación.")