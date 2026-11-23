import sys
import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt

from validaciones import generar_json_modelo
from vista_formulacion import VistaFormulacion
from vista_resultados import VistaResultados


class AplicacionPL:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplicación de Programación Lineal")
        self.root.geometry("1100x750")
        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        # Estado compartido entre vistas
        self.tipo_obj_var = tk.StringVar(value="MAXIMIZAR")
        self.n_vars_var = tk.IntVar(value=2)
        self.m_cons_var = tk.IntVar(value=3)
        self.permitir_neg_var = tk.BooleanVar(value=False)
        self.metodo_var = tk.StringVar(value="Gran M (Tablero)")
        self.modo_sol_var = tk.StringVar(value="Paso a paso")
        self.fracciones_var = tk.BooleanVar(value=True)
        self.modelo_actual = None

        self.contenedor_principal = tk.Frame(self.root, padx=15, pady=15)
        self.contenedor_principal.pack(fill="both", expand=True)

        self.mostrar_vista_formulacion()

    def limpiar_contenedor(self):
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        self.root.unbind_all("<MouseWheel>")
        for widget in self.contenedor_principal.winfo_children():
            widget.destroy()

    def al_cerrar(self):
        plt.close("all")
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def mostrar_vista_formulacion(self):
        self.limpiar_contenedor()
        VistaFormulacion(self.contenedor_principal, self)

    def mostrar_vista_resultados(self):
        self.limpiar_contenedor()
        VistaResultados(self.contenedor_principal, self)

    def guardar_json(self):
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