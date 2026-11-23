import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from validaciones import (
    parsear_numero,
    validar_funcion_objetivo,
    validar_restricciones,
    cargar_json_modelo
)


class VistaFormulacion(tk.Frame):
    """Vista encargada de la definición manual o carga desde JSON del modelo de PL."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.entradas_z = []
        self.entradas_restricciones = []

        self.pack(fill="both", expand=True)
        self._construir_ui()

    def _construir_ui(self):
        tk.Label(
            self,
            text="Definición del Modelo de Programación Lineal",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            self,
            text="Formatos numéricos admitidos: enteros (5), decimales con punto o coma (0.1 / 0,1) y fracciones (1/10).",
            font=("Arial", 9, "italic"), fg="#444444"
        ).pack(anchor="w", pady=(0, 8))

        # --- BARRA DE MODO DE INGRESO: ARCHIVO JSON VS MANUAL ---
        frame_origen = tk.LabelFrame(self, text="Modo de Ingreso del Problema", padx=10, pady=8)
        frame_origen.pack(fill="x", pady=(0, 6))

        tk.Button(
            frame_origen,
            text="📂 Abrir problema desde archivo (.json)",
            bg="#6f42c1", fg="white", font=("Arial", 9, "bold"),
            command=self._abrir_json
        ).pack(side="left", padx=5)

        tk.Button(
            frame_origen,
            text="📝 Nuevo modelo manual (Limpiar campos)",
            command=self._reiniciar_manual
        ).pack(side="left", padx=10)

        # --- ETAPA 1: Objetivo, n, m y Función Objetivo ---
        frame_etapa1 = tk.LabelFrame(self, text="1. Configuración General y Función Objetivo", padx=10, pady=10)
        frame_etapa1.pack(fill="x", pady=5)

        fila_dim = tk.Frame(frame_etapa1)
        fila_dim.pack(fill="x", pady=5)

        tk.Label(fila_dim, text="Objetivo:").pack(side="left", padx=5)
        ttk.Combobox(
            fila_dim, textvariable=self.app.tipo_obj_var,
            values=["MAXIMIZAR", "MINIMIZAR"], state="readonly", width=12
        ).pack(side="left", padx=5)

        tk.Label(fila_dim, text="Variables (n):").pack(side="left", padx=5)
        tk.Spinbox(
            fila_dim, from_=2, to=10, textvariable=self.app.n_vars_var,
            width=5, command=self._al_cambiar_dimensiones
        ).pack(side="left", padx=5)

        tk.Label(fila_dim, text="Restricciones (m):").pack(side="left", padx=5)
        tk.Spinbox(
            fila_dim, from_=1, to=15, textvariable=self.app.m_cons_var,
            width=5, command=self._al_cambiar_dimensiones
        ).pack(side="left", padx=5)

        self.frame_z = tk.Frame(frame_etapa1)
        self.frame_z.pack(fill="x", pady=8)

        valores_z_previos = self.app.modelo_actual["coef_z"] if self.app.modelo_actual else None
        self._construir_campos_z(valores_z_previos)

        tk.Button(
            frame_etapa1,
            text="Continuar a Restricciones ➡️",
            bg="#1f77b4", fg="white",
            command=self._validar_y_abrir_etapa2
        ).pack(anchor="e", pady=5)

        self.frame_etapa2 = tk.LabelFrame(self, text="2. Restricciones (Sujeto a) y Signo de Variables", padx=10, pady=10)
        self.frame_etapa3 = tk.LabelFrame(self, text="3. Método y Opciones de Solución", padx=10, pady=10)

        if self.app.modelo_actual:
            self._validar_y_abrir_etapa2(restricciones_previas=self.app.modelo_actual["restricciones"])
            self._validar_y_abrir_etapa3()

    def _abrir_json(self):
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

        self.app.tipo_obj_var.set(resultado["tipo_objetivo"])
        self.app.n_vars_var.set(resultado["n_vars"])
        self.app.m_cons_var.set(resultado["m_cons"])
        self.app.permitir_neg_var.set(resultado["permitir_negativos"])
        self.app.modelo_actual = resultado

        self.app.mostrar_vista_formulacion()
        messagebox.showinfo("Modelo cargado", "El archivo JSON se cargó correctamente. Puedes revisarlo o presionar 'Resolver Problema'.")

    def _reiniciar_manual(self):
        self.app.modelo_actual = None
        self.app.tipo_obj_var.set("MAXIMIZAR")
        self.app.n_vars_var.set(2)
        self.app.m_cons_var.set(3)
        self.app.permitir_neg_var.set(False)
        self.app.mostrar_vista_formulacion()

    def _al_cambiar_dimensiones(self):
        self.app.modelo_actual = None
        self._construir_campos_z()
        self.frame_etapa2.pack_forget()
        self.frame_etapa3.pack_forget()

    def _construir_campos_z(self, valores_previos=None):
        for w in self.frame_z.winfo_children():
            w.destroy()
        self.entradas_z.clear()

        tk.Label(self.frame_z, text="Z = ", font=("Arial", 10, "bold")).pack(side="left")
        n = self.app.n_vars_var.get()
        for j in range(n):
            entry = tk.Entry(self.frame_z, width=8, justify="center")
            val_inicial = str(valores_previos[j]) if (valores_previos and j < len(valores_previos)) else "0"
            entry.insert(0, val_inicial)
            entry.pack(side="left", padx=3)
            self.entradas_z.append(entry)

            etiqueta = f"X{j+1} + " if j < n - 1 else f"X{j+1}"
            tk.Label(self.frame_z, text=etiqueta).pack(side="left")

    def _validar_y_abrir_etapa2(self, restricciones_previas=None):
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

        n = self.app.n_vars_var.get()
        m = self.app.m_cons_var.get()

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
            variable=self.app.permitir_neg_var
        ).pack(anchor="w", pady=5)

        tk.Button(
            self.frame_etapa2,
            text="Continuar a Opciones de Solución ➡️",
            bg="#1f77b4", fg="white",
            command=self._validar_y_abrir_etapa3
        ).pack(anchor="e", pady=5)

    def _recopilar_y_validar_modelo(self):
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

        valido_r, errores_r = validar_restricciones(restricciones, self.app.n_vars_var.get())
        if not valido_r:
            messagebox.showerror("Error en Restricciones", "\n".join(errores_r).replace("*", ""))
            return False

        self.app.modelo_actual = {
            "tipo_objetivo": self.app.tipo_obj_var.get(),
            "n_vars": self.app.n_vars_var.get(),
            "m_cons": self.app.m_cons_var.get(),
            "coef_z": coef_z,
            "restricciones": restricciones,
            "permitir_negativos": self.app.permitir_neg_var.get(),
        }
        return True

    def _validar_y_abrir_etapa3(self):
        if not self._recopilar_y_validar_modelo():
            return

        for w in self.frame_etapa3.winfo_children():
            w.destroy()
        self.frame_etapa3.pack(fill="x", pady=5)

        fila_opciones = tk.Frame(self.frame_etapa3)
        fila_opciones.pack(fill="x")

        tk.Label(fila_opciones, text="Método:", font=("Arial", 9, "bold")).pack(side="left", padx=(5, 2))
        ttk.Combobox(
            fila_opciones,
            textvariable=self.app.metodo_var,
            values=["Gran M (Tablero)"],  # Aquí se agregará "Simplex Revisado" más adelante
            state="readonly", width=18
        ).pack(side="left", padx=5)

        tk.Radiobutton(fila_opciones, text="Paso a paso", variable=self.app.modo_sol_var, value="Paso a paso").pack(side="left", padx=10)
        tk.Radiobutton(fila_opciones, text="Solución directa", variable=self.app.modo_sol_var, value="Solución directa").pack(side="left", padx=10)
        tk.Checkbutton(fila_opciones, text="Mostrar en fracciones exactas", variable=self.app.fracciones_var).pack(side="left", padx=15)

        tk.Button(
            fila_opciones,
            text="🚀 Resolver Problema",
            bg="#2ca02c", fg="white", font=("Arial", 10, "bold"),
            command=self._ejecutar
        ).pack(side="right", padx=10)

    def _ejecutar(self):
        if self._recopilar_y_validar_modelo():
            self.app.mostrar_vista_resultados()