import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from solver import GranM, TerminoM
from graph import generar_grafico_2d
from validaciones import validar_funcion_objetivo, validar_restricciones, generar_json_modelo


class AplicacionPL:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplicación de Programación Lineal - UdeA")
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
        """Elimina los widgets actuales antes de cambiar de vista."""
        for widget in self.contenedor_principal.winfo_children():
            widget.destroy()

    def al_cerrar(self):
        """Cierra las figuras de Matplotlib, detiene Tkinter y finaliza el proceso."""
        plt.close("all")
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    # =========================================================
    # VISTA 1: FORMULACIÓN DEL MODELO POR ETAPAS
    # =========================================================
    def mostrar_vista_formulacion(self):
        self.limpiar_contenedor()

        tk.Label(
            self.contenedor_principal,
            text="Definición del Modelo de Programación Lineal",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(0, 10))

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

        # Si venimos de "Editar modelo actual", precargamos los coeficientes guardados
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

        # Si el usuario pulsó "Editar modelo actual", desplegamos de inmediato Etapas 2 y 3 con sus datos
        if self.modelo_actual:
            self.validar_y_abrir_etapa2(restricciones_previas=self.modelo_actual["restricciones"])
            self.validar_y_abrir_etapa3()

    def al_cambiar_dimensiones(self):
        """Actualiza los campos de Z y reinicia las etapas inferiores si cambian n o m."""
        self.modelo_actual = None  # Invalidamos caché previa al cambiar dimensiones
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
            val_inicial = f"{valores_previos[j]:g}" if (valores_previos and j < len(valores_previos)) else "0"
            entry.insert(0, val_inicial)
            entry.pack(side="left", padx=3)
            self.entradas_z.append(entry)

            etiqueta = f"X{j+1} + " if j < n - 1 else f"X{j+1}"
            tk.Label(self.frame_z, text=etiqueta).pack(side="left")

    def validar_y_abrir_etapa2(self, restricciones_previas=None):
        """Valida los coeficientes de Z y despliega la matriz de restricciones."""
        try:
            coef_z = [float(e.get()) for e in self.entradas_z]
        except ValueError:
            messagebox.showerror("Error de entrada", "Todos los coeficientes de Z deben ser valores numéricos.")
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
                    val_a = f"{restricciones_previas[i]['coefs'][j]:g}"
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
            val_b = f"{restricciones_previas[i]['b']:g}" if tiene_prev else "10"
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

    def validar_y_abrir_etapa3(self):
        """Valida la matriz A y RHS y muestra las opciones de ejecución."""
        try:
            coef_z = [float(e.get()) for e in self.entradas_z]
            restricciones = []
            for fila_entries, combo_signo, e_b in self.entradas_restricciones:
                coefs = [float(e.get()) for e in fila_entries]
                b_val = float(e_b.get())
                restricciones.append({"coefs": coefs, "signo": combo_signo.get(), "b": b_val})
        except ValueError:
            messagebox.showerror("Error de entrada", "Todos los coeficientes y lados derechos deben ser numéricos.")
            return

        valido_z, msg_z = validar_funcion_objetivo(coef_z)
        if not valido_z:
            messagebox.showerror("Error en Z", msg_z.replace("*", ""))
            return

        valido_r, errores_r = validar_restricciones(restricciones, self.n_vars_var.get())
        if not valido_r:
            messagebox.showerror("Error en Restricciones", "\n".join(errores_r).replace("*", ""))
            return

        # Guardamos el modelo validado en memoria
        self.modelo_actual = {
            "tipo_objetivo": self.tipo_obj_var.get(),
            "n_vars": self.n_vars_var.get(),
            "m_cons": self.m_cons_var.get(),
            "coef_z": coef_z,
            "restricciones": restricciones,
            "permitir_negativos": self.permitir_neg_var.get(),
        }

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
            text="🚀 Resolver Problema",
            bg="#2ca02c", fg="white", font=("Arial", 10, "bold"),
            command=self.mostrar_vista_resultados
        ).pack(side="right", padx=10)

    # =========================================================
    # VISTA 2: RESULTADOS (PESTAÑAS)
    # =========================================================
    def mostrar_vista_resultados(self):
        self.limpiar_contenedor()
        mod = self.modelo_actual
        usar_frac = self.fracciones_var.get()

        # Barra superior: Editar modelo y Guardar JSON
        barra_top = tk.Frame(self.contenedor_principal)
        barra_top.pack(fill="x", pady=(0, 10))

        tk.Button(barra_top, text="⬅️ Editar modelo actual", command=self.mostrar_vista_formulacion).pack(side="left", padx=5)
        tk.Button(barra_top, text="💾 Guardar problema (.json)", command=self.guardar_json).pack(side="left", padx=5)

        # Ejecutar estandarización y obtener Iteración 0
        solver = GranM(
            mod["tipo_objetivo"],
            mod["coef_z"],
            mod["restricciones"],
            permitir_negativos=mod["permitir_negativos"]
        )
        info_estandar = solver.estandarizar()
        iter0 = solver.generar_iteracion_0()

        # Pestañas de salida
        notebook = ttk.Notebook(self.contenedor_principal)
        notebook.pack(fill="both", expand=True)

        tab_pasos = tk.Frame(notebook, padx=10, pady=10)
        tab_grafico = tk.Frame(notebook, padx=10, pady=10)
        tab_sensibilidad = tk.Frame(notebook, padx=10, pady=10)

        notebook.add(tab_pasos, text="Solución / Paso a Paso")
        notebook.add(tab_grafico, text="Método Gráfico")
        notebook.add(tab_sensibilidad, text="Análisis de Sensibilidad")

        # --- Contenido Pestaña 1: Forma Estándar e Iteración 0 ---
        if self.modo_sol_var.get() == "Paso a paso":
            # Bloque de texto superior: Forma estándar y preparación de Ecuación (0)
            texto_info = tk.Text(tab_pasos, height=11, wrap="word", font=("Consolas", 10))
            texto_info.pack(fill="x", pady=(0, 10))

            texto_info.insert("end", "=== 1. FORMA ESTÁNDAR DEL MODELO ===\n")
            texto_info.insert(
                "end",
                f"Variables: {', '.join(info_estandar['nombres_vars'])}  |  "
                f"Base Inicial: {', '.join(info_estandar['vars_basicas_iniciales'])}\n"
            )
            for idx, eq in enumerate(info_estandar["forma_estandar"], start=1):
                texto_info.insert("end", f"  ({idx}) {eq}\n")

            if iter0["operaciones_eliminacion"]:
                texto_info.insert("end", "\n=== 2. PREPARACIÓN DE ECUACIÓN (0) (ELIMINACIÓN DE ARTIFICIALES) ===\n")
                for op in iter0["operaciones_eliminacion"]:
                    texto_info.insert("end", f"  {op}\n")

            texto_info.config(state="disabled")

            # Encabezado de la tabla Iteración = 0
            tk.Label(
                tab_pasos, text="Iteración = 0",
                font=("Arial", 12, "bold"), fg="#1f77b4"
            ).pack(anchor="w", pady=(5, 2))

            # Contenedor de tabla con barra de desplazamiento horizontal
            frame_tabla = tk.Frame(tab_pasos)
            frame_tabla.pack(fill="x", pady=5)

            columnas = ["Ec #", "VB", "Z"] + iter0["nombres_vars"] + ["Lado derecho", "Razón"]
            tabla_tree = ttk.Treeview(
                frame_tabla,
                columns=columnas,
                show="headings",
                height=len(iter0["vars_basicas"]) + 1
            )

            scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=tabla_tree.xview)
            tabla_tree.configure(xscrollcommand=scroll_x.set)

            for col in columnas:
                tabla_tree.heading(col, text=col)
                ancho = 55 if col in ["Ec #", "VB", "Z"] else (120 if col == "Lado derecho" else 90)
                tabla_tree.column(col, width=ancho, minwidth=ancho, anchor="center", stretch=False)

            # Fila (0): Función Objetivo
            vals_f0 = (
                ["(0)", "Z", "-1"]
                + [t.formatear(usar_frac) for t in iter0["fila_0_coefs"]]
                + [iter0["fila_0_rhs"].formatear(usar_frac), "-"]
            )
            tabla_tree.insert("", "end", values=vals_f0)

            # Filas (1) .. (m): Restricciones
            for i, r in enumerate(iter0["filas_restricciones"]):
                vb = iter0["vars_basicas"][i]
                coefs_txt = [TerminoM._fmt_num(c, usar_frac) for c in r["coefs"]]
                rhs_txt = TerminoM._fmt_num(r["b"], usar_frac)
                razon_val = iter0["razones"][i]
                razon_txt = TerminoM._fmt_num(razon_val, usar_frac) if razon_val is not None else "-"

                vals_fila = [f"({i+1})", vb, "0"] + coefs_txt + [rhs_txt, razon_txt]
                tabla_tree.insert("", "end", values=vals_fila)

            tabla_tree.pack(fill="x")
            scroll_x.pack(fill="x")

            # Resumen de criterios de pivoteo detectados en la Iteración 0
            frame_pivote = tk.LabelFrame(
                tab_pasos,
                text="Criterios de Pivoteo (Iteración 0 → Iteración 1)",
                padx=10, pady=8
            )
            frame_pivote.pack(fill="x", pady=10)

            if iter0["var_entrante"] is None:
                tk.Label(
                    frame_pivote,
                    text="✅ Ninguna variable mejora Z en la Ecuación (0). La Iteración 0 ya es óptima.",
                    fg="green", font=("Arial", 10, "bold")
                ).pack(anchor="w")
            elif iter0["var_saliente"] is None:
                tk.Label(
                    frame_pivote,
                    text=f"⚠️ Variable entrante: {iter0['var_entrante']}, pero no hay coeficientes positivos en su columna. Problema NO ACOTADO.",
                    fg="red", font=("Arial", 10, "bold")
                ).pack(anchor="w")
            else:
                razon_min_txt = TerminoM._fmt_num(iter0["menor_razon"], usar_frac)
                piv_txt = TerminoM._fmt_num(iter0["elemento_pivote"], usar_frac)
                resumen = (
                    f"• Columna pivote (Variable que entra): {iter0['var_entrante']} (mayor valor absoluto entre las variables que mejoran Z)\n"
                    f"• Fila pivote (Variable que sale): {iter0['var_saliente']} (Ec ({iter0['fila_pivote'] + 1}), razón mínima = {razon_min_txt})\n"
                    f"• Elemento pivote: {piv_txt}"
                )
                tk.Label(frame_pivote, text=resumen, justify="left", font=("Consolas", 10)).pack(anchor="w")

        else:
            tk.Label(
                tab_pasos,
                text="Modo Solución Directa: Se habilitará al completar el bucle de iteraciones.",
                font=("Arial", 11)
            ).pack(pady=20)

        # --- Contenido Pestaña 2: Método Gráfico 2D ---
        if mod["n_vars"] == 2:
            plt.close("all")
            fig_2d = generar_grafico_2d(
                mod["tipo_objetivo"],
                mod["coef_z"],
                mod["restricciones"],
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