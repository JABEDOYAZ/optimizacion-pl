from fractions import Fraction


class EstandarizadorModelo:
    """
    Convierte un modelo general de Programación Lineal a su Forma Aumentada:
    - Corrige lados derechos negativos (b_i < 0).
    - Desdobla variables sin restricción de signo (X_j = X_j+ - X_j-).
    - Agrega variables de holgura (s), exceso (e) y artificiales (a).
    """
    def __init__(self, tipo_obj, coef_z, restricciones, permitir_negativos=False):
        self.tipo_obj = tipo_obj
        self.n_vars_orig = len(coef_z)
        self.coef_z_orig = [c if isinstance(c, Fraction) else Fraction(str(c)) for c in coef_z]
        self.restricciones_orig = restricciones
        self.permitir_negativos = permitir_negativos

        self.n_holguras = 0
        self.n_excesos = 0
        self.n_artificiales = 0

        self.nombres_vars = []
        self.forma_estandar_str = []
        self.vars_basicas = []
        self.filas_restricciones = []
        self.coef_z_expandido = []
        self.mapeo_restricciones = []

    def construir(self):
        """Construye y retorna los datos matriciales y textuales del modelo aumentado."""
        self.nombres_vars = []
        self.forma_estandar_str = []
        self.vars_basicas = []
        self.filas_restricciones = []
        self.mapeo_restricciones = []
        self.n_holguras = 0
        self.n_excesos = 0
        self.n_artificiales = 0

        # 1. Variables de decisión (X_j o X_j+ - X_j-)
        coef_z_decision = []
        for j in range(self.n_vars_orig):
            if not self.permitir_negativos:
                self.nombres_vars.append(f"X{j+1}")
                coef_z_decision.append(self.coef_z_orig[j])
            else:
                self.nombres_vars.extend([f"X{j+1}+", f"X{j+1}-"])
                coef_z_decision.extend([self.coef_z_orig[j], -self.coef_z_orig[j]])

        # 2. Normalizar lados derechos negativos (b_i < 0)
        restricciones_proc = []
        for r in self.restricciones_orig:
            coefs_raw = [c if isinstance(c, Fraction) else Fraction(str(c)) for c in r["coefs"]]
            signo = r["signo"]
            b = r["b"] if isinstance(r["b"], Fraction) else Fraction(str(r["b"]))

            if b < 0:
                coefs_raw = [-c for c in coefs_raw]
                b = -b
                if signo == "<=":
                    signo = ">="
                elif signo == ">=":
                    signo = "<="

            coefs_exp = []
            for c in coefs_raw:
                if not self.permitir_negativos:
                    coefs_exp.append(c)
                else:
                    coefs_exp.extend([c, -c])

            restricciones_proc.append({"coefs": coefs_exp, "signo": signo, "b": b})

        # 3. Contar y nombrar columnas auxiliares (s, e, a)
        for r in restricciones_proc:
            if r["signo"] == "<=":
                self.n_holguras += 1
            elif r["signo"] == ">=":
                self.n_excesos += 1
                self.n_artificiales += 1
            elif r["signo"] == "=":
                self.n_artificiales += 1

        for h in range(1, self.n_holguras + 1):
            self.nombres_vars.append(f"s{h}")
        for e in range(1, self.n_excesos + 1):
            self.nombres_vars.append(f"e{e}")
        for a in range(1, self.n_artificiales + 1):
            self.nombres_vars.append(f"a{a}")

        self.coef_z_expandido = coef_z_decision + [Fraction(0)] * (
            self.n_holguras + self.n_excesos + self.n_artificiales
        )

        # 4. Armar filas numéricas y ecuaciones legibles
        total_vars = len(self.nombres_vars)
        idx_s, idx_e, idx_a = 1, 1, 1

        for i, r in enumerate(restricciones_proc):
            fila = [Fraction(0)] * total_vars
            for idx, val in enumerate(r["coefs"]):
                fila[idx] = val

            terminos_txt = [
                f"{val}*{self.nombres_vars[idx]}"
                for idx, val in enumerate(r["coefs"]) if val != 0
            ]
            eq_str = " + ".join(terminos_txt) if terminos_txt else "0"

            if r["signo"] == "<=":
                var_s = f"s{idx_s}"
                fila[self.nombres_vars.index(var_s)] = Fraction(1)
                eq_str += f" + {var_s} = {r['b']}"
                self.vars_basicas.append(var_s)
                self.mapeo_restricciones.append({"restriccion": f"R{i+1}", "tipo": "Holgura", "var": var_s})
                idx_s += 1
            elif r["signo"] == ">=":
                var_e = f"e{idx_e}"
                var_a = f"a{idx_a}"
                fila[self.nombres_vars.index(var_e)] = Fraction(-1)
                fila[self.nombres_vars.index(var_a)] = Fraction(1)
                eq_str += f" - {var_e} + {var_a} = {r['b']}"
                self.vars_basicas.append(var_a)
                self.mapeo_restricciones.append({"restriccion": f"R{i+1}", "tipo": "Exceso", "var": var_e})
                idx_e += 1
                idx_a += 1
            elif r["signo"] == "=":
                var_a = f"a{idx_a}"
                fila[self.nombres_vars.index(var_a)] = Fraction(1)
                eq_str += f" + {var_a} = {r['b']}"
                self.vars_basicas.append(var_a)
                self.mapeo_restricciones.append({"restriccion": f"R{i+1}", "tipo": "Igualdad", "var": None})
                idx_a += 1

            self.forma_estandar_str.append(eq_str)
            self.filas_restricciones.append({"coefs": fila, "b": r["b"]})

        return {
            "nombres_vars": list(self.nombres_vars),
            "forma_estandar": list(self.forma_estandar_str),
            "vars_basicas_iniciales": list(self.vars_basicas)
        }

    def reconstruir_variables_decision(self, valores_columnas):
        """A partir de todas las columnas aumentadas, calcula los valores finales X_1..X_n."""
        solucion_x = {}
        for j in range(self.n_vars_orig):
            if not self.permitir_negativos:
                solucion_x[f"X{j+1}"] = valores_columnas[f"X{j+1}"]
            else:
                solucion_x[f"X{j+1}"] = valores_columnas[f"X{j+1}+"] - valores_columnas[f"X{j+1}-"]
        return solucion_x