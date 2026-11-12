import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from solver import GranM
from graph import generar_grafico_2d
from validaciones import validar_funcion_objetivo, validar_restricciones, generar_json_modelo


class AplicacionPL:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplicación de Programación Lineal")
        self.root.geometry("1050x720")

        # Variables de control de la interfaz
        self.tipo_obj_var = tk.StringVar(value="MAXIMIZAR")
        self.n_vars_var = tk.IntVar(value=2)
        self.m_cons_var = tk.IntVar(value=3)
        self.permitir_neg_var = tk.BooleanVar(value=False)
        self.modo_sol_var = tk.StringVar(value="Paso a paso")
        self.fracciones_var = tk.BooleanVar(value=True)

        # Listas para guardar las referencias a las cajas de texto (Entry / Combobox)
        self.entradas_z = []
        self.entradas_restricciones = []
        self.modelo_actual = {}

        # Contenedor principal dinámico (cambia entre Formulación y Resultados)
        self.contenedor_principal = tk.Frame(self.root, padx=15, pady=15)
        self.contenedor_principal.pack(fill="both", expand=True)

        self.mostrar_vista_formulacion()

    def limpiar_contenedor(self):
        """Elimina los widgets actuales antes de cambiar de vista."""
        for widget in self.contenedor_principal.winfo_children():
            widget.destroy()

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
        frame_etapa1 = tk.LabelFrame(self.contenedor_principal, text="1. Configuración General y Función Objetivo", padx=10, pady=10)
        frame_etapa1.pack(fill="x", pady=5)

        fila_dim = tk.Frame(frame_etapa1)
        fila_dim.pack(fill="x", pady=5)

        tk.Label(fila_dim, text="Objetivo:").pack(side="left", padx=5)
        ttk.Combobox(fila_dim, textvariable=self.tipo_obj_var, values=["MAXIMIZAR", "MINIMIZAR"], state="readonly", width=12).pack(side="left", padx=5)

        tk.Label(fila_dim, text="Variables (n):").pack(side="left", padx=5)
        tk.Spinbox(fila_dim, from_=2, to=10, textvariable=self.n_vars_var, width=5).pack(side="left", padx=5)

        tk.Label(fila_dim, text="Restricciones (m):").pack(side="left", padx=5)
        tk.Spinbox(fila_dim, from_=1, to=15, textvariable=self.m_cons_var, width=5).pack(side="left", padx=5)

        tk.Button(fila_dim, text="Generar campos de Z", command=self.construir_campos_z).pack(side="left", padx=15)

        # Subcontenedor donde se dibujan los coeficientes c_j
        self.frame_z = tk.Frame(frame_etapa1)
        self.frame_z.pack(fill="x", pady=8)
        self.construir_campos_z()

        tk.Button(
            frame_etapa1,
            text="Continuar a Restricciones ➡️",
            bg="#1f77b4", fg="white",
            command=self.validar_y_abrir_etapa2
        ).pack(anchor="e", pady=5)

        # --- ETAPA 2: Matriz de Restricciones (se habilita al validar Z) ---
        self.frame_etapa2 = tk.LabelFrame(self.contenedor_principal, text="2. Restricciones (Sujeto a) y Signo de Variables", padx=10, pady=10)

        # --- ETAPA 3: Opciones de Salida y Resolver (se habilita al validar Restricciones) ---
        self.frame_etapa3 = tk.LabelFrame(self.contenedor_principal, text="3. Modo de Solución", padx=10, pady=10)

    def construir_campos_z(self):
        """Crea dinámicamente las cajas de entrada para c_1, c_2, ..., c_n."""
        for w in self.frame_z.winfo_children():
            w.destroy()
        self.entradas_z.clear()

        tk.Label(self.frame_z, text="Z = ", font=("Arial", 10, "bold")).pack(side="left")
        n = self.n_vars_var.get()
        for j in range(n):
            entry = tk.Entry(self.frame_z, width=7, justify="center")
            entry.insert(0, "0")
            entry.pack(side="left", padx=3)
            self.entradas_z.append(entry)

            etiqueta = f"X{j+1} + " if j < n - 1 else f"X{j+1}"
            tk.Label(self.frame_z, text=etiqueta).pack(side="left")

    def validar_y_abrir_etapa2(self):
        """Valida los coeficientes de Z usando validaciones.py y despliega las restricciones."""
        try:
            coef_z = [float(e.get()) for e in self.entradas_z]
        except ValueError:
            messagebox.showerror("Error de entrada", "Todos los coeficientes de Z deben ser valores numéricos.")
            return

        valido, msg = validar_funcion_objetivo(coef_z)
        if not valido:
            messagebox.showerror("Función Objetivo inválida", msg.replace("*", ""))
            return

        # Limpiar y mostrar Etapa 2
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

            for j in range(n):
                e_a = tk.Entry(grid_rest, width=7, justify="center")
                e_a.insert(0, "1" if i == j else "0")
                e_a.grid(row=i, column=col_actual, padx=2)
                fila_entries.append(e_a)
                col_actual += 1

                txt_var = f"X{j+1} +" if j < n - 1 else f"X{j+1}"
                tk.Label(grid_rest, text=txt_var).grid(row=i, column=col_actual, padx=2)
                col_actual += 1

            combo_signo = ttk.Combobox(grid_rest, values=["<=", ">=", "="], state="readonly", width=4)
            combo_signo.set("<=")
            combo_signo.grid(row=i, column=col_actual, padx=5)
            col_actual += 1

            e_b = tk.Entry(grid_rest, width=8, justify="center")
            e_b.insert(0, "10")
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
        """Valida la matriz A y RHS usando validaciones.py y muestra el botón Resolver."""
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
            text="Resolver Problema",
            bg="#2ca02c", fg="white", font=("Arial", 10, "bold"),
            command=self.mostrar_vista_resultados
        ).pack(side="right", padx=10)

    # =========================================================
    # VISTA 2: RESULTADOS (PESTAÑAS)
    # =========================================================
    def mostrar_vista_resultados(self):
        self.limpiar_contenedor()
        mod = self.modelo_actual

        # Barra superior: Editar modelo y Guardar JSON
        barra_top = tk.Frame(self.contenedor_principal)
        barra_top.pack(fill="x", pady=(0, 10))

        tk.Button(barra_top, text="⬅️ Editar modelo actual", command=self.mostrar_vista_formulacion).pack(side="left", padx=5)
        tk.Button(barra_top, text="💾 Guardar problema (.json)", command=self.guardar_json).pack(side="left", padx=5)

        # Ejecutar estandarización del solver
        solver = GranM(mod["tipo_objetivo"], mod["coef_z"], mod["restricciones"], permitir_negativos=mod["permitir_negativos"])
        info_estandar = solver.estandarizar()

        # Creación de pestañas (equivalente a st.tabs)
        notebook = ttk.Notebook(self.contenedor_principal)
        notebook.pack(fill="both", expand=True)

        tab_pasos = tk.Frame(notebook, padx=10, pady=10)
        tab_grafico = tk.Frame(notebook, padx=10, pady=10)
        tab_sensibilidad = tk.Frame(notebook, padx=10, pady=10)

        notebook.add(tab_pasos, text="Solución / Paso a Paso")
        notebook.add(tab_grafico, text="Método Gráfico")
        notebook.add(tab_sensibilidad, text="Análisis de Sensibilidad")

        # --- Contenido Pestaña 1: Paso a paso / Directa ---
        texto_salida = tk.Text(tab_pasos, wrap="word", font=("Consolas", 10))
        texto_salida.pack(fill="both", expand=True)

        if self.modo_sol_var.get() == "Paso a paso":
            texto_salida.insert("end", "=== 1. MODELO ===\n")
            texto_salida.insert("end", f"Variables identificadas: {', '.join(info_estandar['nombres_vars'])}\n")
            texto_salida.insert("end", f"Base Inicial: {', '.join(info_estandar['vars_basicas_iniciales'])}\n\n")
            texto_salida.insert("end", "Ecuaciones:\n")
            for eq in info_estandar["forma_estandar"]:
                texto_salida.insert("end", f"  {eq}\n")
            texto_salida.insert("end", "\n=== 2. ITERACIONES GRAN M ===\n(Pendiente de implementar iteraciones)")
        else:
            texto_salida.insert("end", "=== SOLUCIÓN ÓPTIMA DIRECTA ===\n(Aquí se mostrará Z*, X* y holguras)")

        texto_salida.config(state="disabled")  # Solo lectura

        # --- Contenido Pestaña 2: Método Gráfico 2D ---
        if mod["n_vars"] == 2:
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
        tk.Label(tab_sensibilidad, text="Tabla de Análisis de Sensibilidad (En desarrollo)", font=("Arial", 11)).pack(pady=20)

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