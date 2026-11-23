from fractions import Fraction


class TerminoM:
    """
    Representa un número simbólico de la forma: constante + coef_m * M
    Permite realizar aritmética exacta en la Fila (0) del método de la Gran M.
    """
    def __init__(self, constante=0, coef_m=0):
        self.const = constante if isinstance(constante, Fraction) else Fraction(str(constante))
        self.m = coef_m if isinstance(coef_m, Fraction) else Fraction(str(coef_m))

    def __add__(self, otro):
        otro = otro if isinstance(otro, TerminoM) else TerminoM(otro)
        return TerminoM(self.const + otro.const, self.m + otro.m)

    def __sub__(self, otro):
        otro = otro if isinstance(otro, TerminoM) else TerminoM(otro)
        return TerminoM(self.const - otro.const, self.m - otro.m)

    def __mul__(self, escalar):
        esc = escalar if isinstance(escalar, Fraction) else Fraction(str(escalar))
        return TerminoM(self.const * esc, self.m * esc)

    def es_cero(self):
        return self.const == 0 and self.m == 0

    def es_positivo(self):
        """Para M suficientemente grande (M -> +inf), evalúa si el término es > 0."""
        if self.m != 0:
            return self.m > 0
        return self.const > 0

    def es_negativo(self):
        """Para M suficientemente grande (M -> +inf), evalúa si el término es < 0."""
        if self.m != 0:
            return self.m < 0
        return self.const < 0

    def clave_magnitud(self):
        """Tupla para comparar valores absolutos |coef_m * M + const| cuando M es muy grande."""
        return (abs(self.m), abs(self.const))

    @staticmethod
    def _fmt_num(frac, usar_fracciones=True):
        """Formatea una Fraction como fracción ('2/5') o decimal legible ('0.4')."""
        if usar_fracciones or frac.denominator == 1:
            return str(frac)
        val = round(float(frac), 4)
        return f"{val:g}"

    def formatear(self, usar_fracciones=True):
        """Convierte el término (const + m*M) a texto legible, ej: '-1.1M + 0.4'."""
        if self.m == 0:
            return self._fmt_num(self.const, usar_fracciones)

        # Formatear la parte con M
        if self.m == 1:
            parte_m = "M"
        elif self.m == -1:
            parte_m = "-M"
        else:
            parte_m = f"{self._fmt_num(self.m, usar_fracciones)}M"

        if self.const == 0:
            return parte_m

        signo_c = "+" if self.const > 0 else "-"
        parte_c = self._fmt_num(abs(self.const), usar_fracciones)
        return f"{parte_m}{signo_c}{parte_c}"


class GranM:
    def __init__(self, tipo_obj, coef_z, restricciones, permitir_negativos=False):
        self.tipo_obj = tipo_obj
        self.n_vars_orig = len(coef_z)
        self.coef_z_orig = [Fraction(str(c)) for c in coef_z]
        self.restricciones_orig = restricciones
        self.permitir_negativos = permitir_negativos

        self.n_holguras = 0
        self.n_excesos = 0
        self.n_artificiales = 0

        self.nombres_vars = []          # ['X1', 'X2', ..., 's1', ..., 'e1', ..., 'a1', ...]
        self.forma_estandar_str = []    # Ecuaciones en texto
        self.vars_basicas = []          # Base inicial ['s1', 'a1', ...]
        self.filas_restricciones = []   # Matriz numérica (Fraction) de restricciones [coefs..., b]
        self.coef_z_expandido = []      # Coeficientes originales de Z alineados con self.nombres_vars

    def estandarizar(self):
        """
        1. Corrige lados derechos negativos (b_i < 0).
        2. Expande variables libres si permitir_negativos=True (X_j = X_j+ - X_j-).
        3. Agrega holguras (+s), excesos (-e) y artificiales (+a).
        4. Construye la matriz numérica exacta para armar la Iteración 0.
        """
        self.nombres_vars = []
        self.forma_estandar_str = []
        self.vars_basicas = []
        self.filas_restricciones = []
        self.n_holguras = 0
        self.n_excesos = 0
        self.n_artificiales = 0

        # Nombres y coeficientes de variables de decisión (considerando si permiten negativos)
        coef_z_decision = []
        for j in range(self.n_vars_orig):
            if not self.permitir_negativos:
                self.nombres_vars.append(f"X{j+1}")
                coef_z_decision.append(self.coef_z_orig[j])
            else:
                self.nombres_vars.extend([f"X{j+1}+", f"X{j+1}-"])
                coef_z_decision.extend([self.coef_z_orig[j], -self.coef_z_orig[j]])

        # Procesar restricciones y corregir lados derechos negativos
        restricciones_proc = []
        for r in self.restricciones_orig:
            coefs_raw = [Fraction(str(c)) for c in r["coefs"]]
            signo = r["signo"]
            b = Fraction(str(r["b"]))

            if b < 0:
                coefs_raw = [-c for c in coefs_raw]
                b = -b
                if signo == "<=":
                    signo = ">="
                elif signo == ">=":
                    signo = "<="

            # Expandir coeficientes si hay variables sin restricción de signo
            coefs_exp = []
            for c in coefs_raw:
                if not self.permitir_negativos:
                    coefs_exp.append(c)
                else:
                    coefs_exp.extend([c, -c])

            restricciones_proc.append({"coefs": coefs_exp, "signo": signo, "b": b})

        # Contar holguras, excesos y artificiales
        for r in restricciones_proc:
            if r["signo"] == "<=":
                self.n_holguras += 1
            elif r["signo"] == ">=":
                self.n_excesos += 1
                self.n_artificiales += 1
            elif r["signo"] == "=":
                self.n_artificiales += 1

        # Completar encabezados de columnas
        for h in range(1, self.n_holguras + 1):
            self.nombres_vars.append(f"s{h}")
        for e in range(1, self.n_excesos + 1):
            self.nombres_vars.append(f"e{e}")
        for a in range(1, self.n_artificiales + 1):
            self.nombres_vars.append(f"a{a}")

        # Vector de costos originales completo (0 para holguras/excesos, +-M se maneja en Iteración 0)
        self.coef_z_expandido = coef_z_decision + [Fraction(0)] * (self.n_holguras + self.n_excesos + self.n_artificiales)

        # Construir filas numéricas y ecuaciones en texto
        total_vars = len(self.nombres_vars)
        idx_s, idx_e, idx_a = 1, 1, 1

        for r in restricciones_proc:
            fila = [Fraction(0)] * total_vars
            for idx, val in enumerate(r["coefs"]):
                fila[idx] = val

            # Cadena legible de variables de decisión
            terminos_txt = []
            for idx, val in enumerate(r["coefs"]):
                if val != 0:
                    terminos_txt.append(f"{val}*{self.nombres_vars[idx]}")
            eq_str = " + ".join(terminos_txt) if terminos_txt else "0"

            if r["signo"] == "<=":
                col_s = self.nombres_vars.index(f"s{idx_s}")
                fila[col_s] = Fraction(1)
                eq_str += f" + s{idx_s} = {r['b']}"
                self.vars_basicas.append(f"s{idx_s}")
                idx_s += 1
            elif r["signo"] == ">=":
                col_e = self.nombres_vars.index(f"e{idx_e}")
                col_a = self.nombres_vars.index(f"a{idx_a}")
                fila[col_e] = Fraction(-1)
                fila[col_a] = Fraction(1)
                eq_str += f" - e{idx_e} + a{idx_a} = {r['b']}"
                self.vars_basicas.append(f"a{idx_a}")
                idx_e += 1
                idx_a += 1
            elif r["signo"] == "=":
                col_a = self.nombres_vars.index(f"a{idx_a}")
                fila[col_a] = Fraction(1)
                eq_str += f" + a{idx_a} = {r['b']}"
                self.vars_basicas.append(f"a{idx_a}")
                idx_a += 1

            self.forma_estandar_str.append(eq_str)
            self.filas_restricciones.append({"coefs": fila, "b": r["b"]})

        return {
            "nombres_vars": self.nombres_vars,
            "forma_estandar": self.forma_estandar_str,
            "vars_basicas_iniciales": self.vars_basicas
        }

    def generar_iteracion_0(self):
        """
        Construye el tablero inicial (Iteración = 0) siguiendo la convención de clase:
        - Ecuación (0): -Z + sum(c_j * X_j) (+- M * a_k) = 0
        - Elimina las variables artificiales de la Ecuación (0) sumando (-+M * Fila_i)
        - Identifica la columna pivote (mayor valor absoluto entre las variables que mejoran Z)
        - Calcula la columna Razón (Lado derecho / coef_pivote para coef_pivote > 0)
        """
        if not self.nombres_vars:
            self.estandarizar()

        total_vars = len(self.nombres_vars)
        # En MIN se penaliza con +M*a_k; en MAX se penaliza con -M*a_k
        signo_penalizacion = Fraction(1) if self.tipo_obj == "MINIMIZAR" else Fraction(-1)

        # 1. Fila (0) inicial antes de eliminar las artificiales de la base
        fila_0_coefs = [TerminoM(c, 0) for c in self.coef_z_expandido]
        for a in range(1, self.n_artificiales + 1):
            col_a = self.nombres_vars.index(f"a{a}")
            fila_0_coefs[col_a] = TerminoM(0, signo_penalizacion)
        fila_0_rhs = TerminoM(0, 0)

        # 2. Eliminar variables artificiales básicas de la Fila (0) (Método Figura 2)
        operaciones_eliminacion = []
        for idx_fila, vb in enumerate(self.vars_basicas):
            if vb.startswith("a"):
                # Multiplicador: -M en MINIMIZAR, +M en MAXIMIZAR
                mult_m = -signo_penalizacion
                fila_r = self.filas_restricciones[idx_fila]

                for j in range(total_vars):
                    fila_0_coefs[j] = fila_0_coefs[j] + TerminoM(0, mult_m * fila_r["coefs"][j])
                fila_0_rhs = fila_0_rhs + TerminoM(0, mult_m * fila_r["b"])

                signo_txt = "-M" if mult_m < 0 else "+M"
                operaciones_eliminacion.append(
                    f"Ec (0) ← Ec (0) + ({signo_txt}) · Ec ({idx_fila + 1})   [Para eliminar {vb} de la base]"
                )

        # 3. Determinar la columna pivote (variable que entra)
        # Con ecuación -Z + sum(coef_j * X_j) = RHS:
        # - En MAXIMIZAR entran coeficientes positivos (el mayor)
        # - En MINIMIZAR entran coeficientes negativos (el de mayor valor absoluto)
        col_pivote = None
        mejor_clave = (-Fraction(1), -Fraction(1))

        for j in range(total_vars):
            termino = fila_0_coefs[j]
            es_candidata = termino.es_positivo() if self.tipo_obj == "MAXIMIZAR" else termino.es_negativo()
            if es_candidata:
                clave = termino.clave_magnitud()
                if clave > mejor_clave:
                    mejor_clave = clave
                    col_pivote = j

        var_entrante = self.nombres_vars[col_pivote] if col_pivote is not None else None

        # 4. Calcular la columna Razón (Lado derecho / coef_pivote) y detectar fila pivote
        razones = []
        fila_pivote = None
        menor_razon = None

        for i, r in enumerate(self.filas_restricciones):
            if col_pivote is None:
                razones.append(None)
            else:
                piv_val = r["coefs"][col_pivote]
                if piv_val != 0: # Se evita división por cero
                    razon = r["b"] / piv_val
                    razones.append(razon)
                    if menor_razon is None or razon < menor_razon:
                        menor_razon = razon
                        fila_pivote = i
                else:
                    razones.append(None)

        var_saliente = self.vars_basicas[fila_pivote] if fila_pivote is not None else None
        elemento_pivote = (
            self.filas_restricciones[fila_pivote]["coefs"][col_pivote]
            if (fila_pivote is not None and col_pivote is not None)
            else None
        )

        return {
            "nombres_vars": self.nombres_vars,
            "fila_0_coefs": fila_0_coefs,
            "fila_0_rhs": fila_0_rhs,
            "filas_restricciones": self.filas_restricciones,
            "vars_basicas": self.vars_basicas,
            "operaciones_eliminacion": operaciones_eliminacion,
            "col_pivote": col_pivote,
            "var_entrante": var_entrante,
            "razones": razones,
            "fila_pivote": fila_pivote,
            "var_saliente": var_saliente,
            "elemento_pivote": elemento_pivote,
            "menor_razon": menor_razon
        }