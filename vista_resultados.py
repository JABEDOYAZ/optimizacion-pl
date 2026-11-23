import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from aritmetica import formatear_numero
from solver_gran_m import GranM
from graph import generar_grafico_2d


class VistaResultados(tk.Frame):
    """Vista encargada de presentar tableros iterativos, solución óptima, gráfico 2D y sensibilidad."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pack(fill="both", expand=True)
        self._construir_ui()

    def _construir_ui(self):
        mod = self.app.modelo_actual
        usar_frac = self.app.fracciones_var.get()

        # Barra superior
        barra_top = tk.Frame(self)
        barra_top.pack(fill="x", pady=(0, 10))

        tk.Button(barra_top, text="⬅️ Editar modelo actual", command=self.app.mostrar_vista_formulacion).pack(side="left", padx=5)
        tk.Button(barra_top, text="💾 Guardar problema (.json)", command=self.app.guardar_json).pack(side="left", padx=5)

        # Seleccionar solver según el método elegido (preparado para Simplex Revisado)
        solver = GranM(
            mod["tipo_objetivo"],
            mod["coef_z"],
            mod["restricciones"],
            permitir_negativos=mod["permitir_negativos"]
        )
        res = solver.resolver(usar_fracciones=usar_frac)

        # Pestañas
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        tab_pasos = tk.Frame(notebook, padx=10, pady=10)
        tab_grafico = tk.Frame(notebook, padx=10, pady=10)
        tab_sensibilidad = tk.Frame(notebook, padx=10, pady=10)

        notebook.add(tab_pasos, text="Solución / Paso a Paso")
        notebook.add(tab_grafico, text="Método Gráfico")
        notebook.add(tab_sensibilidad, text="Análisis de Sensibilidad")

        # --- Pestaña 1: Paso a paso o Solución directa ---
        if self.app.modo_sol_var.get() == "Paso a paso":
            self._construir_paso_a_paso(tab_pasos, mod, res, usar_frac)
        else:
            self._dibujar_resumen_solucion(tab_pasos, res, usar_frac)

        # --- Pestaña 2: Método Gráfico 2D ---
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

        # --- Pestaña 3: Análisis de Sensibilidad ---
        tk.Label(
            tab_sensibilidad,
            text="Tabla de Análisis de Sensibilidad (En desarrollo)",
            font=("Arial", 11)
        ).pack(pady=20)

    def _construir_paso_a_paso(self, contenedor, mod, res, usar_frac):
        info_estandar = res["info_estandar"]

        canvas_scroll = tk.Canvas(contenedor, highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(contenedor, orient="vertical", command=canvas_scroll.yview)
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

        self.app.root.bind_all("<Button-4>", _on_mousewheel)
        self.app.root.bind_all("<Button-5>", _on_mousewheel)
        self.app.root.bind_all("<MouseWheel>", _on_mousewheel)

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

        # 2. Tableros iterativos
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
                coefs_txt = [formatear_numero(c, usar_frac) for c in r["coefs"]]
                rhs_txt = formatear_numero(r["b"], usar_frac)
                razon_val = tab["razones"][i]
                razon_txt = formatear_numero(razon_val, usar_frac) if razon_val is not None else "-"

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
                razon_min_txt = formatear_numero(tab["menor_razon"], usar_frac)
                piv_txt = formatear_numero(tab["elemento_pivote"], usar_frac)
                ops_txt = "\n   ".join(tab["operaciones_pivote"])
                detalle_piv = (
                    f"• Entra: {tab['var_entrante']}  |  Sale: {tab['var_saliente']} (Ec ({tab['fila_pivote'] + 1}), razón mínima = {razon_min_txt})  |  Pivote: {piv_txt}\n"
                    f"• Operaciones de Gauss-Jordan hacia Iteración {num_it + 1}:\n   {ops_txt}"
                )
                tk.Label(frame_it, text=detalle_piv, justify="left", font=("Consolas", 9)).pack(anchor="w", pady=(4, 0))

        # 3. Resumen final
        self._dibujar_resumen_solucion(frame_scrollable, res, usar_frac)

    def _dibujar_resumen_solucion(self, padre, res, usar_frac):
        frame_res = tk.LabelFrame(
            padre,
            text="Resultado Final de la Optimización",
            padx=12, pady=10,
            font=("Arial", 11, "bold")
        )
        frame_res.pack(fill="x", pady=10)

        estado = res["estado"]

        if estado in ("INFACTIBLE", "NO_ACOTADO"):
            icono = "❌" if estado == "INFACTIBLE" else "⚠️"
            tk.Label(
                frame_res,
                text=f"{icono} {res['mensaje_estado']}",
                fg="#d9534f", font=("Arial", 10, "bold"),
                wraplength=950, justify="left"
            ).pack(anchor="w")
            return

        z_txt = formatear_numero(res["valor_z"], usar_frac)
        tk.Label(
            frame_res,
            text=f"✅ {res['mensaje_estado']}   |   Valor Óptimo Z* = {z_txt}",
            fg="#1e7e34", font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(0, 6))

        vars_txt = "   |   ".join(
            [f"{var} = {formatear_numero(val, usar_frac)}" for var, val in res["solucion_x"].items()]
        )
        tk.Label(frame_res, text=f"Variables de decisión:   {vars_txt}", font=("Consolas", 10, "bold")).pack(anchor="w", pady=3)

        if res["es_multiple"]:
            msg_mult = f"ℹ️ Soluciones óptimas múltiples detectadas (variable(s) no básica(s) con costo reducido 0: {', '.join(res['vars_alternativas'])})."
            if res["solucion_alternativa"]:
                alt_txt = ", ".join([f"{k} = {formatear_numero(v, usar_frac)}" for k, v in res["solucion_alternativa"].items()])
                msg_mult += f"\n   Vértice óptimo alternativo encontrado: ({alt_txt}) con el mismo Z* = {z_txt}."
            tk.Label(frame_res, text=msg_mult, fg="#0056b3", font=("Arial", 9, "bold"), justify="left").pack(anchor="w", pady=4)

        if res["es_degenerado"]:
            tk.Label(
                frame_res,
                text="ℹ️ Solución degenerada: al menos una variable básica tomó valor igual a 0 (o hubo empate en la razón mínima).",
                fg="#856404", font=("Arial", 9, "bold")
            ).pack(anchor="w", pady=4)