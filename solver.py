import copy
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
        """Convierte el término (const + m*M) a texto legible, ej: '-1.1M+0.4'."""
        if self.m == 0:
            return self._fmt_num(self.const, usar_fracciones)

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
        self.mapeo_restricciones = []  # Guarda qué variable s_h o e_k corresponde a cada restricción

    def estandarizar(self):
        """Convierte el modelo original a la Forma Estándar con holguras, excesos y artificiales."""
        self.nombres_vars = []
        self.forma_estandar_str = []
        self.vars_basicas = []
        self.filas_restricciones = []
        self.mapeo_restricciones = []
        self.n_holguras = 0
        self.n_excesos = 0
        self.n_artificiales = 0

        # Variables de decisión (se desdoblan en X+ y X- si permiten negativos)
        coef_z_decision = []
        for j in range(self.n_vars_orig):
            if not self.permitir_negativos:
                self.nombres_vars.append(f"X{j+1}")
                coef_z_decision.append(self.coef_z_orig[j])
            else:
                self.nombres_vars.extend([f"X{j+1}+", f"X{j+1}-"])
                coef_z_decision.extend([self.coef_z_orig[j], -self.coef_z_orig[j]])

        # Procesar restricciones y corregir lados derechos negativos (b_i < 0)
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

        # Contar holguras, excesos y artificiales
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

        self.coef_z_expandido = coef_z_decision + [Fraction(0)] * (self.n_holguras + self.n_excesos + self.n_artificiales)

        # Construir filas numéricas y ecuaciones en texto
        total_vars = len(self.nombres_vars)
        idx_s, idx_e, idx_a = 1, 1, 1

        for i, r in enumerate(restricciones_proc):
            fila = [Fraction(0)] * total_vars
            for idx, val in enumerate(r["coefs"]):
                fila[idx] = val

            terminos_txt = []
            for idx, val in enumerate(r["coefs"]):
                if val != 0:
                    terminos_txt.append(f"{val}*{self.nombres_vars[idx]}")
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
                self.mapeo_restricciones.append({"restriccion": f"R{i+1}", "tipo": "Igualdad (sin holgura/exceso)", "var": None})
                idx_a += 1

            self.forma_estandar_str.append(eq_str)
            self.filas_restricciones.append({"coefs": fila, "b": r["b"]})

        return {
            "nombres_vars": self.nombres_vars,
            "forma_estandar": self.forma_estandar_str,
            "vars_basicas_iniciales": list(self.vars_basicas)
        }

    def _evaluar_tablero(self, num_iter, fila_0_coefs, fila_0_rhs, filas_rest, vars_basicas):
        """Evalúa el estado de un tablero: busca variable entrante, calcula razones y detecta fila pivote."""
        total_vars = len(self.nombres_vars)

        # 1. Buscar columna pivote (mayor magnitud entre las variables que mejoran Z)
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

        # 2. Calcular columna Razón y prueba de la razón mínima (piv_val > 0)
        razones = []
        fila_pivote = None
        menor_razon = None
        empate_razon = False

        for i, r in enumerate(filas_rest):
            if col_pivote is None:
                razones.append(None)
            else:
                piv_val = r["coefs"][col_pivote]
                if piv_val != 0:
                    razon = r["b"] / piv_val
                    razones.append(razon)
                    if piv_val > 0:
                        if menor_razon is None or razon < menor_razon:
                            menor_razon = razon
                            fila_pivote = i
                            empate_razon = False
                        elif razon == menor_razon:
                            empate_razon = True
                else:
                    razones.append(None)

        var_saliente = vars_basicas[fila_pivote] if fila_pivote is not None else None
        elemento_pivote = (
            filas_rest[fila_pivote]["coefs"][col_pivote]
            if (fila_pivote is not None and col_pivote is not None)
            else None
        )

        return {
            "iteracion": num_iter,
            "nombres_vars": list(self.nombres_vars),
            "fila_0_coefs": copy.deepcopy(fila_0_coefs),
            "fila_0_rhs": copy.deepcopy(fila_0_rhs),
            "filas_restricciones": copy.deepcopy(filas_rest),
            "vars_basicas": list(vars_basicas),
            "col_pivote": col_pivote,
            "var_entrante": var_entrante,
            "razones": razones,
            "fila_pivote": fila_pivote,
            "var_saliente": var_saliente,
            "elemento_pivote": elemento_pivote,
            "menor_razon": menor_razon,
            "empate_razon": empate_razon,
            "operaciones_pivote": []
        }

    def _aplicar_pivoteo(self, fila_0_coefs, fila_0_rhs, filas_rest, vars_basicas, fila_piv, col_piv, usar_fracciones=True):
        """Ejecuta la eliminación de Gauss-Jordan sobre una copia del tablero y retorna las operaciones."""
        f0_c = copy.deepcopy(fila_0_coefs)
        f0_rhs = copy.deepcopy(fila_0_rhs)
        f_rest = copy.deepcopy(filas_rest)
        v_bas = list(vars_basicas)
        operaciones = []

        total_vars = len(self.nombres_vars)
        pivote = f_rest[fila_piv]["coefs"][col_piv]

        # Paso 1: Normalizar fila pivote (dividir por el elemento pivote)
        for j in range(total_vars):
            f_rest[fila_piv]["coefs"][j] /= pivote
        f_rest[fila_piv]["b"] /= pivote
        v_bas[fila_piv] = self.nombres_vars[col_piv]

        piv_txt = TerminoM._fmt_num(pivote, usar_fracciones)
        operaciones.append(f"Ec ({fila_piv + 1}) ← Ec ({fila_piv + 1}) / ({piv_txt})   [Normalizar fila pivote]")

        # Paso 2: Hacer ceros en la columna pivote de las demás restricciones
        for i in range(len(f_rest)):
            if i != fila_piv:
                factor = f_rest[i]["coefs"][col_piv]
                if factor != 0:
                    for j in range(total_vars):
                        f_rest[i]["coefs"][j] -= factor * f_rest[fila_piv]["coefs"][j]
                    f_rest[i]["b"] -= factor * f_rest[fila_piv]["b"]

                    fac_txt = TerminoM._fmt_num(factor, usar_fracciones)
                    operaciones.append(f"Ec ({i + 1}) ← Ec ({i + 1}) - ({fac_txt}) · Ec ({fila_piv + 1})")

        # Paso 3: Hacer cero en la columna pivote de la Ecuación (0)
        factor_0 = f0_c[col_piv]
        if not factor_0.es_cero():
            for j in range(total_vars):
                f0_c[j] = f0_c[j] - (factor_0 * f_rest[fila_piv]["coefs"][j])
            f0_rhs = f0_rhs - (factor_0 * f_rest[fila_piv]["b"])

            fac0_txt = factor_0.formatear(usar_fracciones)
            operaciones.append(f"Ec (0) ← Ec (0) - ({fac0_txt}) · Ec ({fila_piv + 1})")

        return f0_c, f0_rhs, f_rest, v_bas, operaciones

    def _extraer_valores_solucion(self, fila_0_rhs, filas_rest, vars_basicas):
        """Calcula el valor final de Z, las variables X_1..X_n y las holguras/excesos."""
        valores_columnas = {nombre: Fraction(0) for nombre in self.nombres_vars}
        for i, vb in enumerate(vars_basicas):
            valores_columnas[vb] = filas_rest[i]["b"]

        # Reconstruir variables de decisión originales X_1 .. X_n
        solucion_x = {}
        for j in range(self.n_vars_orig):
            if not self.permitir_negativos:
                solucion_x[f"X{j+1}"] = valores_columnas[f"X{j+1}"]
            else:
                solucion_x[f"X{j+1}"] = valores_columnas[f"X{j+1}+"] - valores_columnas[f"X{j+1}-"]

        # Extraer holguras y excesos de cada restricción
        detalle_restricciones = []
        for item in self.mapeo_restricciones:
            val_var = valores_columnas[item["var"]] if item["var"] else Fraction(0)
            detalle_restricciones.append({
                "restriccion": item["restriccion"],
                "tipo": item["tipo"],
                "variable": item["var"] if item["var"] else "-",
                "valor": val_var
            })

        # Como la columna Z tiene coeficiente -1 (-Z = RHS), Z* = -RHS
        valor_z = -fila_0_rhs.const
        return valor_z, solucion_x, detalle_restricciones

    def resolver(self, usar_fracciones=True, max_iteraciones=50):
        """
        Ejecuta el algoritmo completo de la Gran M desde la Iteración 0 hasta la parada:
        - Retorna todos los tableros intermedios, operaciones de Gauss-Jordan y diagnóstico final.
        """
        info_estandar = self.estandarizar()
        total_vars = len(self.nombres_vars)
        signo_penalizacion = Fraction(1) if self.tipo_obj == "MINIMIZAR" else Fraction(-1)

        # Preparar Fila (0) inicial y eliminar variables artificiales básicas
        fila_0_coefs = [TerminoM(c, 0) for c in self.coef_z_expandido]
        for a in range(1, self.n_artificiales + 1):
            col_a = self.nombres_vars.index(f"a{a}")
            fila_0_coefs[col_a] = TerminoM(0, signo_penalizacion)
        fila_0_rhs = TerminoM(0, 0)

        operaciones_eliminacion = []
        for idx_fila, vb in enumerate(self.vars_basicas):
            if vb.startswith("a"):
                mult_m = -signo_penalizacion
                fila_r = self.filas_restricciones[idx_fila]
                for j in range(total_vars):
                    fila_0_coefs[j] = fila_0_coefs[j] + TerminoM(0, mult_m * fila_r["coefs"][j])
                fila_0_rhs = fila_0_rhs + TerminoM(0, mult_m * fila_r["b"])

                signo_txt = "-M" if mult_m < 0 else "+M"
                operaciones_eliminacion.append(
                    f"Ec (0) ← Ec (0) + ({signo_txt}) · Ec ({idx_fila + 1})   [Eliminar {vb} de Ec (0)]"
                )

        filas_actuales = copy.deepcopy(self.filas_restricciones)
        vars_basicas_actuales = list(self.vars_basicas)

        iteraciones = []
        estado = "OPTIMO"
        mensaje_estado = ""
        es_degenerado = False
        es_multiple = False
        vars_alternativas = []
        solucion_alternativa = None

        # Bucle principal de iteraciones Simplex
        for k in range(max_iteraciones):
            tablero = self._evaluar_tablero(k, fila_0_coefs, fila_0_rhs, filas_actuales, vars_basicas_actuales)
            if tablero["empate_razon"]:
                es_degenerado = True

            # Caso 1: Criterio de optimalidad alcanzado (no hay variable que mejore Z)
            if tablero["col_pivote"] is None:
                iteraciones.append(tablero)
                break

            # Caso 2: Problema no acotado (hay variable entrante pero ningún coeficiente > 0 en su columna)
            if tablero["fila_pivote"] is None:
                estado = "NO_ACOTADO"
                mensaje_estado = (
                    f"Problema NO ACOTADO: La variable {tablero['var_entrante']} debe entrar a la base, "
                    f"pero todos sus coeficientes en las restricciones son menores o iguales a cero."
                )
                iteraciones.append(tablero)
                break

            # Realizar pivoteo de Gauss-Jordan para generar el siguiente tablero
            fila_0_coefs, fila_0_rhs, filas_actuales, vars_basicas_actuales, ops = self._aplicar_pivoteo(
                fila_0_coefs,
                fila_0_rhs,
                filas_actuales,
                vars_basicas_actuales,
                tablero["fila_pivote"],
                tablero["col_pivote"],
                usar_fracciones=usar_fracciones
            )
            tablero["operaciones_pivote"] = ops
            iteraciones.append(tablero)

        # Diagnóstico posterior al tablero final
        tablero_final = iteraciones[-1]
        valor_z = None
        solucion_x = {}
        detalle_restricciones = []

        if estado == "OPTIMO":
            # Verificar si alguna variable artificial quedó en la base con valor > 0 (Infactibilidad)
            artificiales_positivas = [
                vb for i, vb in enumerate(tablero_final["vars_basicas"])
                if vb.startswith("a") and tablero_final["filas_restricciones"][i]["b"] > 0
            ]

            if artificiales_positivas:
                estado = "INFACTIBLE"
                mensaje_estado = (
                    f"Problema INFACTIBLE: No existe región factible que satisfaga todas las restricciones "
                    f"(la(s) variable(s) artificial(es) {', '.join(artificiales_positivas)} permanecen en la base con valor positivo)."
                )
            else:
                valor_z, solucion_x, detalle_restricciones = self._extraer_valores_solucion(
                    tablero_final["fila_0_rhs"],
                    tablero_final["filas_restricciones"],
                    tablero_final["vars_basicas"]
                )

                # Verificar degeneración (alguna variable básica en 0 en el óptimo)
                if any(r["b"] == 0 for r in tablero_final["filas_restricciones"]):
                    es_degenerado = True

                # Verificar soluciones óptimas múltiples (variable no básica no-artificial con coef 0 en Ec 0)
                set_basicas = set(tablero_final["vars_basicas"])
                for j, nombre in enumerate(self.nombres_vars):
                    if nombre not in set_basicas and not nombre.startswith("a"):
                        if tablero_final["fila_0_coefs"][j].es_cero():
                            vars_alternativas.append(nombre)

                if vars_alternativas:
                    es_multiple = True
                    # Calcular un punto extremo alternativo pivoteando la primera variable alternativa
                    col_alt = self.nombres_vars.index(vars_alternativas[0])
                    fila_alt = None
                    menor_r_alt = None
                    for i, r in enumerate(tablero_final["filas_restricciones"]):
                        piv_alt = r["coefs"][col_alt]
                        if piv_alt > 0:
                            raz_alt = r["b"] / piv_alt
                            if menor_r_alt is None or raz_alt < menor_r_alt:
                                menor_r_alt = raz_alt
                                fila_alt = i
                    if fila_alt is not None:
                        _, f0_rhs_alt, f_rest_alt, v_bas_alt, _ = self._aplicar_pivoteo(
                            tablero_final["fila_0_coefs"],
                            tablero_final["fila_0_rhs"],
                            tablero_final["filas_restricciones"],
                            tablero_final["vars_basicas"],
                            fila_alt,
                            col_alt,
                            usar_fracciones=usar_fracciones
                        )
                        _, sol_x_alt, _ = self._extraer_valores_solucion(f0_rhs_alt, f_rest_alt, v_bas_alt)
                        solucion_alternativa = sol_x_alt

                mensaje_estado = "Solución óptima alcanzada correctamente."

        return {
            "info_estandar": info_estandar,
            "operaciones_eliminacion": operaciones_eliminacion,
            "iteraciones": iteraciones,
            "estado": estado,
            "mensaje_estado": mensaje_estado,
            "es_degenerado": es_degenerado,
            "es_multiple": es_multiple,
            "vars_alternativas": vars_alternativas,
            "solucion_alternativa": solucion_alternativa,
            "valor_z": valor_z,
            "solucion_x": solucion_x,
            "detalle_restricciones": detalle_restricciones
        }