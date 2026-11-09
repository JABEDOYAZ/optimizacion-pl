import streamlit as st
import numpy as np

st.set_page_config(page_title="Optimizador PL", layout="wide")

st.title("Aplicación de Programación Lineal")
st.markdown("**Hecho por Jonatan Andrés Bedoya Zapata**")

# ---------------------------------------------------------
# BARRA LATERAL: Opciones y Gestión de Archivos
# ---------------------------------------------------------
with st.sidebar: # Creación de la barra lateral
    st.header("Ajustes") # Título de la barra lateral
    modo_solucion = st.radio("Modos de solución:", ["Paso a paso", "Solución directa"]) # Opciones para seleccionar el modo de solución
    mostrar_fracciones = st.checkbox("Mostrar en fracciones exactas", value=True) # Opción para mostrar resultados en fracciones

    st.divider() # Línea divisoria para separar secciones
    st.header("Archivo (JSON)") # Título de la sección de carga de archivos
    st.file_uploader("Cargar problema (.json)", type=["json"]) # Opción para cargar un archivo JSON con el problema de programación lineal
    if st.button("Guardar el problema actual"): # Botón para guardar el problema actual en un archivo JSON
        st.toast("Función de guardado pendiente de implementación") # Mensaje de notificación indicando que la función de guardado aún no está implementada

# ---------------------------------------------------------
# SECCIÓN 1: Formulación del Modelo
# ---------------------------------------------------------
st.header("Definición del Modelo de Programación Lineal a resolver")

col_type, col_vars, col_cons = st.columns(3) # Creación de tres columnas para la selección del tipo de objetivo, número de variables y número de restricciones

with col_type: # Selección del tipo de objetivo (maximización o minimización)
    tipo_objetivo = st.selectbox("Objetivo:", ["MAXIMIZAR", "MINIMIZAR"])

with col_vars: # Selección del número de variables de decisión (n)
    n_vars = st.number_input("Número de Variables (n):", min_value=2, max_value=10, value=2, step=1) # Número de variables de decisión

with col_cons: # Selección del número de restricciones (m)
    m_cons = st.number_input("Número de Restricciones (m):", min_value=1, max_value=15, value=3, step=1) # Número de restricciones

st.divider() # Línea divisoria para separar secciones

# ---------------------------------------------------------
# SECCIÓN 2: Función Objetivo
# ---------------------------------------------------------
st.subheader("Función Objetivo Z")
cols_f_obj = st.columns(int(n_vars)) # Creación de columnas para ingresar los coeficientes de la función objetivo
coef_z = [] # Lista para almacenar los coeficientes de la función objetivo

for j in range(int(n_vars)): # Iteración para cada variable de decisión
    with cols_f_obj[j]: # Creación de un campo de entrada para cada coeficiente de la función objetivo
        val = st.number_input(f"c_{j+1} (X{j+1})", value=0.0, key=f"z_{j}")
        coef_z.append(val) # Almacenamiento del valor ingresado en la lista de coeficientes

st.divider() # Línea divisoria para separar secciones

# ---------------------------------------------------------
# SECCIÓN 3: Matriz de Restricciones
# ---------------------------------------------------------
st.subheader("Restricciones (Sujeto a) - Ax ≤ b, Ax ≥ b, Ax = b") # Título de la sección de restricciones

restricciones = [] # Lista para almacenar las restricciones ingresadas por el usuario
for i in range(int(m_cons)): # Iteración para cada restricción
    cols_r = st.columns(int(n_vars) + 2) # Creación de columnas para ingresar los coeficientes de la restricción, el signo y el lado derecho
    row_coefs = [] # Lista para almacenar los coeficientes de la restricción actual
    
    # Coeficientes a_ij
    for j in range(int(n_vars)): # Iteración para cada coeficiente de la restricción
        with cols_r[j]: # Creación de un campo de entrada para cada coeficiente de la restricción
            val = st.number_input(f"a_{i+1}{j+1}", value=1.0 if i==j else 0.0, key=f"a_{i}_{j}") # Valor predeterminado: 1.0 para la diagonal, 0.0 para los demás
            row_coefs.append(val) # Almacenamiento del valor ingresado en la lista de coeficientes de la restricción actual
            
    # Signo de la restricción (<=, >=, =)
    with cols_r[-2]: # Creación de un campo de selección para el signo de la restricción
        signo = st.selectbox(f"Signo de R{i+1}", ["<=", ">=", "="], key=f"signo_{i}") # Almacenamiento del signo seleccionado en la variable 'signo'
        
    # Lado derecho b_i (acepta cualquier signo)
    with cols_r[-1]: # Creación de un campo de entrada para el lado derecho de la restricción
        b_val = st.number_input(f"b_{i+1}", value=10.0, key=f"b_{i}")
        # Almacenamiento del valor ingresado en la variable 'b_val'
        
    restricciones.append({"coefs": row_coefs, "signo": signo, "b": b_val})
    # Almacenamiento de la restricción completa en la lista de restricciones

# ---------------------------------------------------------
# SECCIÓN 4: Ejecución y Pestañas de Resultados
# ---------------------------------------------------------
st.divider()

if st.button("Resolver Problema", type="primary"):
    
    # Validación básica de datos
    es_valido = True # Variable para controlar la validez del modelo
    for i, r in enumerate(restricciones): # Iteración para validar cada restricción
        if all(c == 0 for c in r["coefs"]):
            st.error(f"Error en Restricción {i+1}: Todos los coeficientes son cero.")
            es_valido = False
            
    if es_valido:
        st.success("Modelo validado correctamente. Generando solución...")
        
        # Pestañas requeridas
        tab_pasos, tab_grafico, tab_sensibilidad = st.tabs([
            "Solución / Paso a Paso", 
            "Método Gráfico", 
            "Análisis de Sensibilidad"
        ])
        
        with tab_pasos: # Pestaña para mostrar la solución paso a paso
            st.subheader(f"Modo Seleccionado: {modo_solucion}")
            st.info("Aquí se mostrarán la Forma Estándar, prueba de razón mínima, variables entrantes/salientes y tableros iterativos.")
            
        with tab_grafico: # Pestaña para mostrar el método gráfico
            if n_vars == 2:
                st.subheader("Gráfica del Área Factible (2D)")
                st.info("Aquí renderizaremos la región factible sombreada, vértices evaluados y recta de isoutilidad.")
            else:
                st.warning("⚠️ El método gráfico no aplica para problemas con más de 2 variables de decisión.")
                
        with tab_sensibilidad:
            st.subheader("Tabla de Sensibilidad")
            st.info("Aquí se mostrarán precios sombra, costos reducidos y rangos permisibles de variación.")