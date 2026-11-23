import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from solver import GranM, TerminoM
from graph import generar_grafico_2d
from validaciones import (
    parsear_numero,
    validar_funcion_objetivo,
    validar_restricciones,
    generar_json_modelo,
    cargar_json_modelo
)


class AplicacionPL:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplicación de Programación Lineal")
        self.root.geometry("1100x750")

        # Intercepta el clic en la 'X' de la ventana para cerrar todo el proceso limpiamente
        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        # Variables de control de la interfaz
        self.tipo_obj_var = tk.StringVar(value="MAXIMIZAR")
        self.n_vars_var = tk.IntVar(value=2)
        self.m_cons_var = tk.IntVar(value=3)
        self.permitir_neg_var = tk.BooleanVar(value=False)
        self.modo_sol_var = tk.StringVar(value="Paso a paso")
        self.fracciones_var = tk.BooleanVar(value=True)

        # Referencias a los widgets de entrada y memoria del modelo
        self.entradas_z = []
        self.entradas_restricciones = []
        self.modelo_actual = None

        self.contenedor_principal = tk.Frame(self.root, padx=15, pady=15)
        self.contenedor_principal.pack(fill="both", expand=True)

        self.mostrar_vista_formulacion()

    def limpiar_contenedor(self):
        """Elimina los widgets actuales y desvincula eventos globales de scroll antes de cambiar de vista."""
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        self.root.unbind_all("<MouseWheel>")
        for widget in self.contenedor_principal.winfo_children():
            widget.destroy()

    def al_cerrar(self):
        """Cierra las figuras de Matplotlib, detiene Tkinter y finaliza el proceso."""
        plt.close("all")
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    # =========================================================
    # VISTA 1: FORMULACIÓN DEL MODELO (MANUAL O DESDE JSON)
    # =========================================================
    def mostrar_vista_formulacion(self):
        self.limpiar_contenedor()

        tk.Label(
            self.contenedor_principal,
            text="Definición del Modelo de Programación Lineal",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            self.contenedor_principal,
            text="Formatos numéricos admitidos: enteros (5), decimales con punto o coma (0.1 / 0,1) y fracciones (1/10).",
            font=("Arial", 9, "italic"), fg="#444444"
        ).pack(anchor="w", pady=(0, 8))

        # --- BARRA DE MODO DE INGRESO: ARCHIVO JSON VS MANUAL ---
        frame_origen = tk.LabelFrame(
            self.contenedor_principal,
            text="Modo de Ingreso del Problema",
            padx=10, pady=8
        )
        frame_origen.pack(fill="x", pady=(0, 6))

        tk.Button(
            frame_origen,
            text="📂 Abrir problema desde archivo (.json)",
            bg="#6f42c1", fg="white", font=("Arial", 9, "bold"),
            command=self.abrir_json
        ).pack(side="left", padx=5)

        tk.Button(
            frame_origen,
            text="📝 Nuevo modelo manual (Limpiar campos)",
            command=self.reiniciar_modelo_manual
        ).pack(side="left", padx=10)

        # --- ETAPA 1: Objetivo, n, m y Función Objetivo ---
        frame_etapa1 = tk.LabelFrame(
            self.contenedor_principal,
            text="1. Configuración General y Función Objetivo",
            padx=10, pady=10
        )
        frame_etapa1.pack(fill="x", pady=5)

        fila_dim = tk.Frame(frame_etapa1)
        fila_dim.pack(fill="x", pady=5)

        tk.Label(fila_dim, text="Objetivo:").pack(side="left", padx=5)
        ttk.Combobox(
            fila_dim, textvariable=self.tipo_obj_var,
            values=["MAXIMIZAR", "MINIMIZAR"], state="readonly", width=12
        ).pack(side="left", padx=5)

        tk.Label(fila_dim, text="Variables (n):").pack(side="left", padx=5)
        tk.Spinbox(
            fila_dim, from_=2, to=10, textvariable=self.n_vars_var,
            width=5, command=self.al_cambiar_dimensiones
        ).pack(side="left", padx=5)

        tk.Label(fila_dim, text="Restricciones (m):").pack(side="left", padx=5)
        tk.Spinbox(
            fila_dim, from_=1, to=15, textvariable=self.m_cons_var,
            width=5, command=self.al_cambiar_dimensiones
        ).pack(side="left", padx=5)

        # Subcontenedor para los coeficientes c_j
        self.frame_z = tk.Frame(frame_etapa1)
        self.frame_z.pack(fill="x", pady=8)

        # Si venimos de "Editar modelo actual" o de cargar un JSON, precargamos los coeficientes
        valores_z_previos = self.modelo_actual["coef_z"] if self.modelo_actual else None
        self.construir_campos_z(valores_z_previos)

        tk.Button(
            frame_etapa1,
            text="Continuar a Restricciones ➡️",
            bg="#1f77b4", fg="white",
            command=self.validar_y_abrir_etapa2
        ).pack(anchor="e", pady=5)

        # Contenedores para Etapa 2 y Etapa 3
        self.frame_etapa2 = tk.LabelFrame(
            self.contenedor_principal,
            text="2. Restricciones (Sujeto a) y Signo de Variables",
            padx=10, pady=10
        )
        self.frame_etapa3 = tk.LabelFrame(
            self.contenedor_principal,
            text="3. Modo de Solución",
            padx=10, pady=10
        )

        # Si existe un modelo cargado (por edición o desde JSON), desplegamos Etapas 2 y 3 con sus datos
        if self.modelo_actual:
            self.validar_y_abrir_etapa2(restricciones_previas=self.modelo_actual["restricciones"])
            self.validar_y_abrir_etapa3()

    def abrir_json(self):
        """Abre un archivo JSON, valida el modelo y lo carga directamente en la interfaz."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de modelo (.json)",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if not ruta:
            return

        exito, resultado = cargar_json_modelo(ruta)
        if not exito:
            messagebox.showerror("Error al cargar JSON", resultado)
            return

        # Sincronizar variables de control de Tkinter con los datos del JSON
        self.tipo_obj_var.set(resultado["tipo_objetivo"])
        self.n_vars_var.set(resultado["n_vars"])
        self.m_cons_var.set(resultado["m_cons"])
        self.permitir_neg_var.set(resultado["permitir_negativos"])
        self.modelo_actual = resultado

        # Redibujar la vista con todas las etapas rellenas
        self.mostrar_vista_formulacion()
        messagebox.showinfo("Modelo cargado", "El archivo JSON se cargó correctamente. Puedes revisarlo o presionar 'Resolver Problema'.")

    def reiniciar_modelo_manual(self):
        """Limpia cualquier modelo cargado en memoria y reinicia el formulario manual."""
        self.modelo_actual = None
        self.tipo_obj_var.set("MAXIMIZAR")
        self.n_vars_var.set(2)
        self.m_cons_var.set(3)
        self.permitir_neg_var.set(False)
        self.mostrar_vista_formulacion()

    def al_cambiar_dimensiones(self):
        """Actualiza los campos de Z y reinicia las etapas inferiores si cambian n o m."""
        self.modelo_actual = None
        self.construir_campos_z()
        self.frame_etapa2.pack_forget()
        self.frame_etapa3.pack_forget()

    def construir_campos_z(self, valores_previos=None):
        """Crea dinámicamente las cajas de entrada para c_1, c_2, ..., c_n."""
        for w in self.frame_z.winfo_children():
            w.destroy()
        self.entradas_z.clear()

        tk.Label(self.frame_z, text="Z = ", font=("Arial", 10, "bold")).pack(side="left")
        n = self.n_vars_var.get()
        for j in range(n):
            entry = tk.Entry(self.frame_z, width=8, justify="center")
            val_inicial = str(valores_previos[j]) if (valores_previos and j < len(valores_previos)) else "0"
            entry.insert(0, val_inicial)
            entry.pack(side="left", padx=3)
            self.entradas_z.append(entry)

            etiqueta = f"X{j+1} + " if j < n - 1 else f"X{j+1}"
            tk.Label(self.frame_z, text=etiqueta).pack(side="left")

    def validar_y_abrir_etapa2(self, restricciones_previas=None):
        """Valida los coeficientes de Z y despliega la matriz de restricciones."""
        try:
            coef_z = [parsear_numero(e.get()) for e in self.entradas_z]
        except ValueError:
            messagebox.showerror("Error de entrada", "Todos los coeficientes de Z deben ser números válidos (ej. 5, 0.4, 0,4 o 2/5).")
            return

        valido, msg = validar_funcion_objetivo(coef_z)
        if not valido:
            messagebox.showerror("Función Objetivo inválida", msg.replace("*", ""))
            return

        for w in self.frame_etapa2.winfo_children():
            w.destroy()
        self.frame_etapa2.pack(fill="x", pady=5)
        self.entradas_restricciones.clear()

        grid_rest = tk.Frame(self.frame_etapa2)
        grid_rest.pack(fill="x", pady=5)

        n = self.n_vars_var.get()
        m = self.m_cons_var.get()

        for i in range(m):
            fila_entries = []
            tk.Label(grid_rest, text=f"R{i+1}:", font=("Arial", 9, "bold")).grid(row=i, column=0, padx=5, pady=3)
            col_actual = 1

            tiene_prev = restricciones_previas and i < len(restricciones_previas)

            for j in range(n):
                e_a = tk.Entry(grid_rest, width=8, justify="center")
                if tiene_prev and j < len(restricciones_previas[i]["coefs"]):
                    val_a = str(restricciones_previas[i]["coefs"][j])
                else:
                    val_a = "1" if i == j else "0"
                e_a.insert(0, val_a)
                e_a.grid(row=i, column=col_actual, padx=2)
                fila_entries.append(e_a)
                col_actual += 1

                txt_var = f"X{j+1} +" if j < n - 1 else f"X{j+1}"
                tk.Label(grid_rest, text=txt_var).grid(row=i, column=col_actual, padx=2)
                col_actual += 1

            combo_signo = ttk.Combobox(grid_rest, values=["<=", ">=", "="], state="readonly", width=4)
            combo_signo.set(restricciones_previas[i]["signo"] if tiene_prev else "<=")
            combo_signo.grid(row=i, column=col_actual, padx=5)
            col_actual += 1

            e_b = tk.Entry(grid_rest, width=9, justify="center")
            val_b = str(restricciones_previas[i]["b"]) if tiene_prev else "10"
            e_b.insert(0, val_b)
            e_b.grid(row=i, column=col_actual, padx=5)

            self.entradas_restricciones.append((fila_entries, combo_signo, e_b))

        tk.Checkbutton(
            self.frame_etapa2,
            text="Permitir valores negativos en las variables (Sin restricción de signo X_j >= 0)",
            variable=self.permitir_neg_var
        ).pack(anchor="w", pady=5)

        tk.Button(
            self.frame_etapa2,
            text="Continuar a Opciones de Solución ➡️",
            bg="#1f77b4", fg="white",
            command=self.validar_y_abrir_etapa3
        ).pack(anchor="e", pady=5)

    def _recopilar_y_validar_modelo(self):
        """Lee los widgets actuales de pantalla, valida todo el modelo y actualiza self.modelo_actual."""
        try:
            coef_z = [parsear_numero(e.get()) for e in self.entradas_z]
            restricciones = []
            for fila_entries, combo_signo, e_b in self.entradas_restricciones:
                coefs = [parsear_numero(e.get()) for e in fila_entries]
                b_val = parsear_numero(e_b.get())
                restricciones.append({"coefs": coefs, "signo": combo_signo.get(), "b": b_val})
        except ValueError:
            messagebox.showerror("Error de entrada", "Todos los coeficientes y lados derechos deben ser números válidos (ej. 5, 0.4, 0,4 o 2/5).")
            return False

        valido_z, msg_z = validar_funcion_objetivo(coef_z)
        if not valido_z:
            messagebox.showerror("Error en Z", msg_z.replace("*", ""))
            return False

        valido_r, errores_r = validar_restricciones(restricciones, self.n_vars_var.get())
        if not valido_r:
            messagebox.showerror("Error en Restricciones", "\n".join(errores_r).replace("*", ""))
            return False

        self.modelo_actual = {
            "tipo_objetivo": self.tipo_obj_var.get(),
            "n_vars": self.n_vars_var.get(),
            "m_cons": self.m_cons_var.get(),
            "coef_z": coef_z,
            "restricciones": restricciones,
            "permitir_negativos": self.permitir_neg_var.get(),
        }
        return True

    def validar_y_abrir_etapa3(self):
        """Valida el modelo completo y despliega las opciones de ejecución."""
        if not self._recopilar_y_validar_modelo():
            return

        for w in self.frame_etapa3.winfo_children():
            w.destroy()
        self.frame_etapa3.pack(fill="x", pady=5)

        fila_opciones = tk.Frame(self.frame_etapa3)
        fila_opciones.pack(fill="x")

        tk.Radiobutton(fila_opciones, text="Paso a paso", variable=self.modo_sol_var, value="Paso a paso").pack(side="left", padx=10)
        tk.Radiobutton(fila_opciones, text="Solución directa", variable=self.modo_sol_var, value="Solución directa").pack(side="left", padx=10)
        tk.Checkbutton(fila_opciones, text="Mostrar en fracciones exactas", variable=self.fracciones_var).pack(side="left", padx=20)

        tk.Button(
            fila_opciones,
            text="Resolver Problema",
            bg="#2ca02c", fg="white", font=("Arial", 10, "bold"),
            command=self.ejecutar_y_mostrar_resultados
        ).pack(side="right", padx=10)

    def ejecutar_y_mostrar_resultados(self):
        """Revalida cualquier edición reciente en pantalla antes de mostrar la vista de resultados."""
        if self._recopilar_y_validar_modelo():
            self.mostrar_vista_resultados()

    # =========================================================
    # VISTA 2: RESULTADOS (PESTAÑAS)
    # =========================================================
    def _dibujar_resumen_solucion(self, padre, res, usar_frac):
        """Renderiza la tarjeta con la respuesta óptima (Z*, X* y alertas de casos especiales)."""
        frame_res = tk.LabelFrame(
            padre,
            text="Resultado Final de la Optimización",
            padx=12, pady=10,
            font=("Arial", 11, "bold")
        )
        frame_res.pack(fill="x", pady=10)

        estado = res["estado"]

        if estado == "INFACTIBLE":
            tk.Label(
                frame_res,
                text=f"❌ {res['mensaje_estado']}",
                fg="#d9534f", font=("Arial", 10, "bold"),
                wraplength=950, justify="left"
            ).pack(anchor="w")
            return

        if estado == "NO_ACOTADO":
            tk.Label(
                frame_res,
                text=f"⚠️ {res['mensaje_estado']}",
                fg="#d9534f", font=("Arial", 10, "bold"),
                wraplength=950, justify="left"
            ).pack(anchor="w")
            return

        # Estado ÓPTIMO: Mostrar únicamente Z* y variables de decisión
        z_txt = TerminoM._fmt_num(res["valor_z"], usar_frac)
        tk.Label(
            frame_res,
            text=f"✅ {res['mensaje_estado']}   |   Valor Óptimo Z* = {z_txt}",
            fg="#1e7e34", font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(0, 6))

        vars_txt = "   |   ".join(
            [f"{var} = {TerminoM._fmt_num(val, usar_frac)}" for var, val in res["solucion_x"].items()]
        )
        tk.Label(frame_res, text=f"Variables de decisión:   {vars_txt}", font=("Consolas", 10, "bold")).pack(anchor="w", pady=3)

        if res["es_multiple"]:
            msg_mult = f"ℹ️ Soluciones óptimas múltiples detectadas (variable(s) no básica(s) con costo reducido 0: {', '.join(res['vars_alternativas'])})."
            if res["solucion_alternativa"]:
                alt_txt = ", ".join([f"{k} = {TerminoM._fmt_num(v, usar_frac)}" for k, v in res["solucion_alternativa"].items()])
                msg_mult += f"\n   Vértice óptimo alternativo encontrado: ({alt_txt}) con el mismo Z* = {z_txt}."
            tk.Label(frame_res, text=msg_mult, fg="#0056b3", font=("Arial", 9, "bold"), justify="left").pack(anchor="w", pady=4)

        if res["es_degenerado"]:
            tk.Label(
                frame_res,
                text="ℹ️ Solución degenerada: al menos una variable básica tomó valor igual a 0 (o hubo empate en la razón mínima).",
                fg="#856404", font=("Arial", 9, "bold")
            ).pack(anchor="w", pady=4)

    def mostrar_vista_resultados(self):
        self.limpiar_contenedor()
        mod = self.modelo_actual
        usar_frac = self.fracciones_var.get()

        # Barra superior: Editar modelo y Guardar JSON
        barra_top = tk.Frame(self.contenedor_principal)
        barra_top.pack(fill="x", pady=(0, 10))

        tk.Button(barra_top, text="⬅️ Editar modelo actual", command=self.mostrar_vista_formulacion).pack(side="left", padx=5)
        tk.Button(barra_top, text="💾 Guardar problema (.json)", command=self.guardar_json).pack(side="left", padx=5)

        # Ejecutar el algoritmo completo de la Gran M
        solver = GranM(
            mod["tipo_objetivo"],
            mod["coef_z"],
            mod["restricciones"],
            permitir_negativos=mod["permitir_negativos"]
        )
        res = solver.resolver(usar_fracciones=usar_frac)
        info_estandar = res["info_estandar"]

        # Pestañas de salida
        notebook = ttk.Notebook(self.contenedor_principal)
        notebook.pack(fill="both", expand=True)

        tab_pasos = tk.Frame(notebook, padx=10, pady=10)
        tab_grafico = tk.Frame(notebook, padx=10, pady=10)
        tab_sensibilidad = tk.Frame(notebook, padx=10, pady=10)

        notebook.add(tab_pasos, text="Solución / Paso a Paso")
        notebook.add(tab_grafico, text="Método Gráfico")
        notebook.add(tab_sensibilidad, text="Análisis de Sensibilidad")

        # --- Contenido Pestaña 1: Paso a paso o Solución directa ---
        if self.modo_sol_var.get() == "Paso a paso":
            canvas_scroll = tk.Canvas(tab_pasos, highlightthickness=0)
            scrollbar_y = ttk.Scrollbar(tab_pasos, orient="vertical", command=canvas_scroll.yview)
            frame_scrollable = tk.Frame(canvas_scroll)

            frame_scrollable.bind(
                "<Configure>",
                lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
            )
            win_id = canvas_scroll.create_window((0, 0), window=frame_scrollable, anchor="nw")
            canvas_scroll.bind(
                "<Configure>",
                lambda e: canvas_scroll.itemconfig(win_id, width=e.width)
            )
            canvas_scroll.configure(yscrollcommand=scrollbar_y.set)

            def _on_mousewheel(event):
                if not canvas_scroll.winfo_exists():
                    return
                if event.num == 4:
                    canvas_scroll.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas_scroll.yview_scroll(1, "units")
                elif event.delta:
                    canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

            self.root.bind_all("<Button-4>", _on_mousewheel)
            self.root.bind_all("<Button-5>", _on_mousewheel)
            self.root.bind_all("<MouseWheel>", _on_mousewheel)

            canvas_scroll.pack(side="left", fill="both", expand=True)
            scrollbar_y.pack(side="right", fill="y")

            # 1. Forma aumentada y preparación de Ecuación (0)
            texto_info = tk.Text(frame_scrollable, height=9, wrap="word", font=("Consolas", 10))
            texto_info.pack(fill="x", pady=(0, 10))

            texto_info.insert("end", f"=== 1. FORMA AUMENTADA DEL MODELO ({mod['tipo_objetivo']}) ===\n")
            texto_info.insert(
                "end",
                f"Variables: {', '.join(info_estandar['nombres_vars'])}  |  "
                f"Base Inicial: {', '.join(info_estandar['vars_basicas_iniciales'])}\n"
            )
            for idx, eq in enumerate(info_estandar["forma_estandar"], start=1):
                texto_info.insert("end", f"  ({idx}) {eq}\n")

            if res["operaciones_eliminacion"]:
                texto_info.insert("end", "\n=== 2. PREPARACIÓN DE ECUACIÓN (0) (ELIMINACIÓN DE ARTIFICIALES) ===\n")
                for op in res["operaciones_eliminacion"]:
                    texto_info.insert("end", f"  {op}\n")

            texto_info.config(state="disabled")

            # 2. Renderizar cada tablero iterativo (Iteración = 0, 1, 2, ...)
            for tab in res["iteraciones"]:
                num_it = tab["iteracion"]
                frame_it = tk.LabelFrame(
                    frame_scrollable,
                    text=f"Iteración = {num_it}",
                    font=("Arial", 11, "bold"),
                    fg="#1f77b4",
                    padx=8, pady=6
                )
                frame_it.pack(fill="x", pady=6)

                columnas = ["Ec #", "VB", "Z"] + tab["nombres_vars"] + ["Lado derecho", "Razón"]
                tabla_tree = ttk.Treeview(
                    frame_it,
                    columns=columnas,
                    show="headings",
                    height=len(tab["vars_basicas"]) + 1
                )

                scroll_x = ttk.Scrollbar(frame_it, orient="horizontal", command=tabla_tree.xview)
                tabla_tree.configure(xscrollcommand=scroll_x.set)

                for col in columnas:
                    tabla_tree.heading(col, text=col)
                    ancho = 55 if col in ["Ec #", "VB", "Z"] else (120 if col == "Lado derecho" else 90)
                    tabla_tree.column(col, width=ancho, minwidth=ancho, anchor="center", stretch=False)

                vals_f0 = (
                    ["(0)", "Z", "-1"]
                    + [t.formatear(usar_frac) for t in tab["fila_0_coefs"]]
                    + [tab["fila_0_rhs"].formatear(usar_frac), "-"]
                )
                tabla_tree.insert("", "end", values=vals_f0)

                for i, r in enumerate(tab["filas_restricciones"]):
                    vb = tab["vars_basicas"][i]
                    coefs_txt = [TerminoM._fmt_num(c, usar_frac) for c in r["coefs"]]
                    rhs_txt = TerminoM._fmt_num(r["b"], usar_frac)
                    razon_val = tab["razones"][i]
                    razon_txt = TerminoM._fmt_num(razon_val, usar_frac) if razon_val is not None else "-"

                    vals_fila = [f"({i+1})", vb, "0"] + coefs_txt + [rhs_txt, razon_txt]
                    tabla_tree.insert("", "end", values=vals_fila)

                tabla_tree.pack(fill="x")
                scroll_x.pack(fill="x")

                if tab["var_entrante"] is None:
                    tk.Label(
                        frame_it,
                        text="→ Criterio de parada alcanzado: Ninguna variable mejora Z en la Ecuación (0).",
                        fg="#1e7e34", font=("Arial", 9, "bold")
                    ).pack(anchor="w", pady=(4, 0))
                elif tab["var_saliente"] is None:
                    tk.Label(
                        frame_it,
                        text=f"→ Entra {tab['var_entrante']}, pero no hay coeficientes positivos en su columna (Solución no acotada).",
                        fg="#d9534f", font=("Arial", 9, "bold")
                    ).pack(anchor="w", pady=(4, 0))
                else:
                    razon_min_txt = TerminoM._fmt_num(tab["menor_razon"], usar_frac)
                    piv_txt = TerminoM._fmt_num(tab["elemento_pivote"], usar_frac)
                    ops_txt = "\n   ".join(tab["operaciones_pivote"])
                    detalle_piv = (
                        f"• Entra: {tab['var_entrante']}  |  Sale: {tab['var_saliente']} (Ec ({tab['fila_pivote'] + 1}), razón mínima = {razon_min_txt})  |  Pivote: {piv_txt}\n"
                        f"• Operaciones de Gauss-Jordan hacia Iteración {num_it + 1}:\n   {ops_txt}"
                    )
                    tk.Label(frame_it, text=detalle_piv, justify="left", font=("Consolas", 9)).pack(anchor="w", pady=(4, 0))

            # 3. Resumen final al pie de todas las iteraciones
            self._dibujar_resumen_solucion(frame_scrollable, res, usar_frac)

        else:
            # Modo Solución Directa: muestra únicamente el resultado final
            self._dibujar_resumen_solucion(tab_pasos, res, usar_frac)

        # --- Contenido Pestaña 2: Método Gráfico 2D ---
        if mod["n_vars"] == 2:
            plt.close("all")
            fig_2d = generar_grafico_2d(
                mod["tipo_objetivo"],
                [float(c) for c in mod["coef_z"]],
                [{"coefs": [float(a) for a in r["coefs"]], "signo": r["signo"], "b": float(r["b"])} for r in mod["restricciones"]],
                permitir_negativos=mod["permitir_negativos"]
            )
            canvas = FigureCanvasTkAgg(fig_2d, master=tab_grafico)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(
                tab_grafico,
                text="⚠️ El método gráfico no aplica para problemas con más de 2 variables de decisión.",
                font=("Arial", 12, "bold"), fg="#d9534f"
            ).pack(pady=40)

        # --- Contenido Pestaña 3: Análisis de Sensibilidad ---
        tk.Label(
            tab_sensibilidad,
            text="Tabla de Análisis de Sensibilidad (En desarrollo)",
            font=("Arial", 11)
        ).pack(pady=20)

    def guardar_json(self):
        """Abre un diálogo nativo para guardar el modelo actual en formato JSON."""
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")],
            initialfile="modelo_programacion_lineal.json"
        )
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(generar_json_modelo(self.modelo_actual))
            messagebox.showinfo("Guardado", "El problema se guardó correctamente en formato JSON.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionPL(root)
    root.mainloop()