import streamlit as st
import numpy as np
from solver import GranM

st.set_page_config(page_title="Optimizador PL", layout="wide")

st.title("Aplicación de Programación Lineal") 
st.markdown("**Hecho por Jonatan Andrés Bedoya Zapata**") 

with st.sidebar: 
    st.header("Ajustes") 
    modo_solucion = st.radio("Modos de solución:", ["Paso a paso", "Solución directa"]) # Selector de radio para cambiar entre modo educativo o directo
    mostrar_fracciones = st.checkbox("Mostrar en fracciones exactas", value=True) # Casilla de verificación para alternar entre fracciones o decimales

    st.divider()
    st.header("Archivo (JSON)")
    st.file_uploader("Cargar problema (.json)", type=["json"]) # Componente para subir archivos guardados previamente
    if st.button("Guardar el problema actual"): # Botón para exportar la configuración actual del modelo
        st.toast("Función de guardado pendiente de implementación") 

st.header("Definición del Modelo de Programación Lineal a resolver") 

col_type, col_vars, col_cons = st.columns(3) # Creación de tres columnas de igual ancho para organizar los controles principales

with col_type: # Columna 1: Selección del objetivo de optimización
    tipo_objetivo = st.selectbox("Objetivo:", ["MAXIMIZAR", "MINIMIZAR"]) 

with col_vars: # Columna 2: Selección de la cantidad de variables de decisión
    n_vars = st.number_input("Número de Variables (n):", min_value=2, max_value=10, value=2, step=1) # Entrada numérica para n (mínimo 2)

with col_cons: # Columna 3: Selección de la cantidad de restricciones del problema
    m_cons = st.number_input("Número de Restricciones (m):", min_value=1, max_value=15, value=3, step=1) # Entrada numérica para m (mínimo 1)

st.divider() 

st.subheader("Función Objetivo Z") 
cols_f_obj = st.columns(int(n_vars)) # Generación dinámica de 'n' columnas para ingresar cada coeficiente c_j
coef_z = [] 

for j in range(int(n_vars)):
    with cols_f_obj[j]: 
        val = st.number_input(f"c_{j+1} (X{j+1})", value=0.0, key=f"z_{j}")
        coef_z.append(val)

st.divider()

st.subheader("Restricciones (Sujeto a) - Ax ≤ b, Ax ≥ b, Ax = b")

restricciones = [] # Lista donde se guardará cada restricción procesada como un diccionario
for i in range(int(m_cons)): # Bucle para construir cada una de las 'm' filas de restricciones
    cols_r = st.columns(int(n_vars) + 2) # Se crean (n + 2) columnas: n para coeficientes A, 1 para el signo y 1 para RHS (b)
    row_coefs = [] 
    
    # Captura de Coeficientes a_ij de la matriz A
    for j in range(int(n_vars)): 
        with cols_r[j]: 
            val = st.number_input(f"a_{i+1}{j+1}", value=1.0 if i==j else 0.0, key=f"a_{i}_{j}") 
            row_coefs.append(val)
            
    with cols_r[-2]: # Penúltima columna dedicada al selector del signo de desigualdad/igualdad
        signo = st.selectbox(f"Signo de R{i+1}", ["<=", ">=", "="], key=f"signo_{i}") 
        
    # Captura del Término Independiente Lado Derecho (RHS / b_i)
    with cols_r[-1]: 
        b_val = st.number_input(f"b_{i+1}", value=10.0, key=f"b_{i}") 
        
    # Agrupación de la restricción completa en la estructura de datos principal
    restricciones.append({"coefs": row_coefs, "signo": signo, "b": b_val})

st.markdown("##### Restricción de Signo de las Variables")
permitir_negativos = st.checkbox("Permitir valores negativos en las variables de decisión (Variables no restringidas de signo)", 
    value=False, # Valor predeterminado desmarcado (asume X_j >= 0)
    help="Si está desmarcado, se asume la condición estándar X_j >= 0 para todas las variables."
)

if not permitir_negativos: # Condicional para mostrar en pantalla el estado actual del dominio de variables
    st.caption("Condición activa: **X_j ≥ 0** para todo j = 1, ..., n") 
else:
    st.caption("Condición activa: Las variables de decisión **pueden ser negativas** (sin restricción de signo).") 

st.divider() 

if st.button("Resolver Problema", type="primary"): # Disparador principal para ejecutar la validación y el solver
    
    # Validez del modelo matemático
    es_valido = True 

    # VALIDACIÓN: Coeficientes de la Función Objetivo (c_j != 0 para todo j)

    vars_c_cero = [f"X{j+1}" for j, c in enumerate(coef_z) if c == 0] 

    if vars_c_cero: # Si existe al menos una variable con coeficiente 0 en Z
        st.error(
            f"❌ **Modelo mal formulado en la Función Objetivo:** La(s) variable(s) **{', '.join(vars_c_cero)}** tiene(n) un coeficiente igual a 0. "
            f"Para que el modelo sea válido y se pueda encontrar una solución, todas las variables de decisión deben tener un coeficiente c_j distinto de cero."
        ) 
        es_valido = False 

    # VALIDACIÓN : Restricciones completamente vacías (a_i1 = a_i2 = ... = 0)

    for i, r in enumerate(restricciones): # Inspección de cada restricción ingresada
        if all(c == 0 for c in r["coefs"]): # Si todos los coeficientes a_ij en la restricción i son 0
            st.error(f"❌ **Modelo mal formulado en Restricción {i+1}:** Todos los coeficientes a_{i+1}j son cero.") 
            es_valido = False 

    vars_sin_restriccion = [] # Lista para almacenar variables que no están acotadas por ninguna restricción
    for j in range(int(n_vars)): # Recorre cada variable de decisión j = 1, ..., n
        # Verifica si existe al menos alguna restricción i donde el coeficiente a_ij sea distinto de 0
        tiene_coeficiente = any(restricciones[i]["coefs"][j] != 0 for i in range(int(m_cons)))
        if not tiene_coeficiente: # Si la variable X_j tiene coeficiente 0 en TODAS las restricciones
            vars_sin_restriccion.append(f"X{j+1}") # Se agrega a la lista de variables no restringidas

    if vars_sin_restriccion: # Si se encontraron variables aisladas/no restringidas
        st.error(
            f"❌ **Modelo mal diseñado en la Matriz de Restricciones:** La(s) variable(s) **{', '.join(vars_sin_restriccion)}** "
            f"no aparece(n) acotada(s) en ninguna de las restricciones ingresadas (todos sus coeficientes a_ij son 0). "
            f"Cada variable de decisión debe tener un coeficiente distinto de cero en por lo menos una restricción."
        ) 
        es_valido = False
            
    # EJECUCIÓN DEL SOLVER (Solo si pasa todas las validaciones)

    if es_valido: # Si la entrada superó todos los controles de consistencia
        st.success("✅ Modelo validado correctamente. Generando solución...") # Notificación de éxito en la validación

        # Instanciación de la clase solver GranM con los parámetros configurados
        solver = GranM(tipo_objetivo, coef_z, restricciones, permitir_negativos=permitir_negativos) # Objeto solver
        info_estandar = solver.estandarizar() # Ejecución de la estandarización previa del modelo

        # Creación de pestañas ordenadas para la visualización de salidas
        tab_pasos, tab_grafico, tab_sensibilidad = st.tabs([ 
            "Solución / Paso a Paso", # Pestaña 1: Algoritmo y tableros
            "Método Gráfico", # Pestaña 2: Representación gráfica 2D
            "Análisis de Sensibilidad" # Pestaña 3: Precios sombra y rangos
        ])

        with tab_pasos: 
            st.subheader(f"Modo Seleccionado: {modo_solucion}") 
            
            if modo_solucion == "Paso a paso": 
                st.markdown("---") 
                st.subheader("1. Forma del Modelo") 
                st.write("**Variables identificadas:**", ", ".join(info_estandar["nombres_vars"])) 
                st.write("**Base Inicial:**", ", ".join(info_estandar["vars_basicas_iniciales"])) 
            
                st.markdown("##### Ecuaciones:") 
                for eq in info_estandar["forma_estandar"]: 
                    st.code(eq, language="text") 

                st.markdown("---") 
                st.subheader("2. Iteraciones del Método Simplex (Gran M)") 
                st.info("Aquí se mostrarán las tablas iterativas paso a paso, mostrando variable entrante, prueba de la razón mínima, pivote y variable saliente.")
            
            else: 
                st.markdown("---") 
                st.subheader("Solución Óptima Directa") 
                st.info("Aquí se desplegará únicamente el resultado final óptimo (Valor de Z*, X* y holguras/excesos).") 

        with tab_grafico: 
            if n_vars == 2: # Verificación del número de variables de decisión
                st.subheader("Gráfica del Área Factible (2D)")
                st.info("Aquí renderizaremos la región factible sombreada, vértices evaluados y recta de isoutilidad.") 
            else: # Si n > 2 variables de decisión
                st.warning("El método gráfico no aplica para problemas con más de 2 variables de decisión.") 

        with tab_sensibilidad:
            st.subheader("Tabla de Sensibilidad")
            st.info("Aquí se mostrarán precios sombra, costos reducidos y rangos permisibles de variación.")