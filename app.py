import streamlit as st
from solver import GranM
from graph import generar_grafico_2d
from validaciones import validar_funcion_objetivo, validar_restricciones, generar_json_modelo

st.set_page_config(page_title="Optimizador PL", layout="wide")

st.title("Aplicación de Programación Lineal")
st.markdown(" Hecho por Jonatan Bedoya y Sergio Idarraga")

# ---------------------------------------------------------
# INICIALIZACIÓN DEL ESTADO DE LA SESIÓN (Persistencia de datos)
# ---------------------------------------------------------
if "vista" not in st.session_state:
    st.session_state.vista = "formulacion"  # Controla si se muestra 'formulacion' o 'resultados'

if "paso_manual" not in st.session_state:
    st.session_state.paso_manual = 1  # Controla el avance progresivo (1: Z, 2: Restricciones, 3: Opciones)

if "modelo" not in st.session_state:
    st.session_state.modelo = {
        "tipo_objetivo": "MAXIMIZAR",
        "n_vars": 2,
        "m_cons": 3,
        "coef_z": [0.0, 0.0],
        "restricciones": [
            {"coefs": [1.0, 0.0], "signo": "<=", "b": 10.0},
            {"coefs": [0.0, 1.0], "signo": "<=", "b": 10.0},
            {"coefs": [0.0, 0.0], "signo": "<=", "b": 10.0},
        ],
        "permitir_negativos": False,
        "modo_solucion": "Paso a paso",
        "mostrar_fracciones": True,
    }


def ajustar_dimensiones_modelo(n_vars, m_cons):
    """Ajusta el tamaño de las listas guardadas en memoria si el usuario cambia n o m."""
    # Ajustar lista de coeficientes Z
    coef_z = st.session_state.modelo["coef_z"]
    if len(coef_z) < n_vars:
        coef_z.extend([0.0] * (n_vars - len(coef_z)))
    else:
        coef_z = coef_z[:n_vars]
    st.session_state.modelo["coef_z"] = coef_z

    # Ajustar matriz de restricciones
    restricciones = st.session_state.modelo["restricciones"]
    if len(restricciones) < m_cons:
        for i in range(len(restricciones), m_cons):
            fila = [1.0 if i == j else 0.0 for j in range(n_vars)]
            restricciones.append({"coefs": fila, "signo": "<=", "b": 10.0})
    else:
        restricciones = restricciones[:m_cons]

    for i, r in enumerate(restricciones):
        if len(r["coefs"]) < n_vars:
            r["coefs"].extend([0.0] * (n_vars - len(r["coefs"])))
        else:
            r["coefs"] = r["coefs"][:n_vars]

    st.session_state.modelo["restricciones"] = restricciones


# =========================================================
# VISTA 1: FORMULACIÓN DEL MODELO
# =========================================================
if st.session_state.vista == "formulacion":

    # Selección inicial limpia: Manual vs JSON
    metodo_ingreso = st.radio(
        "Selecciona cómo deseas iniciar:",
        ["Ingresar formulación manualmente", "Cargar desde archivo JSON"],
        horizontal=True
    )
    st.divider()

    # -----------------------------------------------------
    # OPCIÓN A: CARGA POR ARCHIVO JSON (Pendiente de lógica)
    # -----------------------------------------------------
    if metodo_ingreso == "Cargar desde archivo JSON":
        st.subheader("Cargar problema desde archivo (.json)")
        archivo_json = st.file_uploader("Selecciona un archivo JSON válido", type=["json"])
        if archivo_json is not None:
            st.info("Archivo recibido. La lectura automática de JSON se implementará en el siguiente paso.")

    # -----------------------------------------------------
    # OPCIÓN B: FORMULACIÓN MANUAL POR PASOS
    # -----------------------------------------------------
    else:
        mod = st.session_state.modelo

        # --- ETAPA 1: Objetivo, Dimensiones y Función Objetivo ---
        st.subheader("1. Definición General y Función Objetivo")
        col_type, col_vars, col_cons = st.columns(3)

        with col_type:
            idx_obj = 0 if mod["tipo_objetivo"] == "MAXIMIZAR" else 1
            tipo_objetivo = st.selectbox("Objetivo:", ["MAXIMIZAR", "MINIMIZAR"], index=idx_obj)

        with col_vars:
            n_vars = st.number_input("Número de Variables (n):", min_value=2, max_value=10, value=int(mod["n_vars"]), step=1)

        with col_cons:
            m_cons = st.number_input("Número de Restricciones (m):", min_value=1, max_value=15, value=int(mod["m_cons"]), step=1)

        # Si el usuario modificó n o m, redimensionamos la memoria y reiniciamos el paso de validación
        if n_vars != mod["n_vars"] or m_cons != mod["m_cons"]:
            mod["n_vars"] = int(n_vars)
            mod["m_cons"] = int(m_cons)
            ajustar_dimensiones_modelo(int(n_vars), int(m_cons))
            st.session_state.paso_manual = 1

        mod["tipo_objetivo"] = tipo_objetivo

        st.markdown("**Coeficientes de la Función Objetivo Z:**")
        cols_f_obj = st.columns(int(n_vars))
        coef_z_actual = []
        for j in range(int(n_vars)):
            with cols_f_obj[j]:
                val = st.number_input(f"c_{j+1} (X{j+1})", value=float(mod["coef_z"][j]), key=f"z_{j}")
                coef_z_actual.append(val)
        mod["coef_z"] = coef_z_actual

        # Botón Continuar (Etapa 1 -> Etapa 2)
        if st.button("Continuar", key="btn_continuar_1"):
            valido_z, msg_z = validar_funcion_objetivo(coef_z_actual)
            if valido_z:
                st.session_state.paso_manual = max(st.session_state.paso_manual, 2)
                st.rerun()
            else:
                st.error(msg_z)

        # --- ETAPA 2: Restricciones y Signo de Variables ---
        if st.session_state.paso_manual >= 2:
            st.divider()
            st.subheader("2. Restricciones (Sujeto a) y Signo de Variables")

            signos_opciones = ["<=", ">=", "="]
            restricciones_actuales = []

            for i in range(int(m_cons)):
                cols_r = st.columns(int(n_vars) + 2)
                row_coefs = []

                for j in range(int(n_vars)):
                    with cols_r[j]:
                        val = st.number_input(
                            f"a_{i+1}{j+1}",
                            value=float(mod["restricciones"][i]["coefs"][j]),
                            key=f"a_{i}_{j}"
                        )
                        row_coefs.append(val)

                with cols_r[-2]:
                    idx_signo = signos_opciones.index(mod["restricciones"][i]["signo"])
                    signo = st.selectbox(f"Signo R{i+1}", signos_opciones, index=idx_signo, key=f"signo_{i}")

                with cols_r[-1]:
                    b_val = st.number_input(f"b_{i+1}", value=float(mod["restricciones"][i]["b"]), key=f"b_{i}")

                restricciones_actuales.append({"coefs": row_coefs, "signo": signo, "b": b_val})

            mod["restricciones"] = restricciones_actuales

            # Restricción de signo de las variables
            st.markdown("##### Restricción de Signo de las Variables")
            permitir_negativos = st.checkbox(
                "Permitir valores negativos en las variables de decisión (Variables no restringidas de signo)",
                value=bool(mod["permitir_negativos"]),
                help="Si está desmarcado, se asume la condición estándar X_j >= 0 para todas las variables."
            )
            mod["permitir_negativos"] = permitir_negativos

            if not permitir_negativos:
                st.caption("Condición activa: **X_j ≥ 0** para todo j = 1, ..., n")
            else:
                st.caption("Condición activa: Las variables de decisión **pueden ser negativas** (sin restricción de signo).")

            # Botón Continuar (Etapa 2 -> Etapa 3)
            if st.button("Continuar", key="btn_continuar_2"):
                valido_z, msg_z = validar_funcion_objetivo(mod["coef_z"])
                valido_r, errores_r = validar_restricciones(restricciones_actuales, int(n_vars))

                if not valido_z:
                    st.error(msg_z)
                elif not valido_r:
                    for err in errores_r:
                        st.error(err)
                else:
                    st.session_state.paso_manual = max(st.session_state.paso_manual, 3)
                    st.rerun()

        # --- ETAPA 3: Opciones de Solución y Ejecución ---
        if st.session_state.paso_manual >= 3:
            st.divider()
            st.subheader("3. Configuración de Salida")

            col_modo, col_frac = st.columns(2)
            with col_modo:
                idx_modo = 0 if mod["modo_solucion"] == "Paso a paso" else 1
                mod["modo_solucion"] = st.radio("Modo de solución:", ["Paso a paso", "Solución directa"], index=idx_modo)

            with col_frac:
                st.write("")  # Espaciado visual
                mod["mostrar_fracciones"] = st.checkbox("Mostrar en fracciones exactas", value=bool(mod["mostrar_fracciones"]))

            if st.button("Resolver", type="primary"):
                # Revalidación final antes de cambiar de vista (protege si el usuario editó algo arriba)
                valido_z, msg_z = validar_funcion_objetivo(mod["coef_z"])
                valido_r, errores_r = validar_restricciones(mod["restricciones"], int(n_vars))

                if not valido_z:
                    st.error(msg_z)
                elif not valido_r:
                    for err in errores_r:
                        st.error(err)
                else:
                    st.session_state.vista = "resultados"
                    st.rerun()


# =========================================================
# VISTA 2: RESULTADOS DE LA OPTIMIZACIÓN
# =========================================================
elif st.session_state.vista == "resultados":
    mod = st.session_state.modelo

    # Barra superior de acciones: Volver a editar y Guardar JSON
    col_volver, col_guardar, _ = st.columns([2, 2, 4])
    with col_volver:
        if st.button("⬅️ Editar modelo actual"):
            st.session_state.vista = "formulacion"
            st.rerun()

    with col_guardar:
        json_str = generar_json_modelo(mod)
        st.download_button(
            label="💾 Guardar el problema actual",
            data=json_str,
            file_name="modelo_programacion_lineal.json",
            mime="application/json"
        )

    st.divider()

    # Instanciación del solver con los datos persistidos en session_state
    solver = GranM(
        mod["tipo_objetivo"],
        mod["coef_z"],
        mod["restricciones"],
        permitir_negativos=mod["permitir_negativos"]
    )
    info_estandar = solver.estandarizar()

    # Pestañas de resultados
    tab_pasos, tab_grafico, tab_sensibilidad = st.tabs([
        "Solución / Paso a Paso",
        "Método Gráfico",
        "Análisis de Sensibilidad"
    ])

    with tab_pasos:
        st.subheader(f"Modo Seleccionado: {mod['modo_solucion']}")

        if mod["modo_solucion"] == "Paso a paso":
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
        if mod["n_vars"] == 2:
            st.subheader("Gráfica del Área Factible (2D)")
            fig_2d = generar_grafico_2d(
                mod["tipo_objetivo"],
                mod["coef_z"],
                mod["restricciones"],
                permitir_negativos=mod["permitir_negativos"]
            )
            st.pyplot(fig_2d)
        else:
            st.warning("El método gráfico no aplica para problemas con más de 2 variables de decisión.")

    with tab_sensibilidad:
        st.subheader("Tabla de Sensibilidad")
        st.info("Aquí se mostrarán precios sombra, costos reducidos y rangos permisibles de variación.")