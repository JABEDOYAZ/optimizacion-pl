import copy
from fractions import Fraction
from aritmetica import TerminoM, formatear_numero
from estandarizador import EstandarizadorModelo


class GranM:
    """Resuelve modelos de Programación Lineal mediante el Método Simplex de la Gran M."""

    def __init__(self, tipo_obj, coef_z, restricciones, permitir_negativos=False):
        self.tipo_obj = tipo_obj
        self.estandarizador = EstandarizadorModelo(
            tipo_obj, coef_z, restricciones, permitir_negativos
        )

    def _evaluar_tablero(self, num_iter, fila_0_coefs, fila_0_rhs, filas_rest, vars_basicas):
        """Evalúa optimalidad, variable entrante, columna razón y variable saliente."""
        nombres_vars = self.estandarizador.nombres_vars
        total_vars = len(nombres_vars)

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

        var_entrante = nombres_vars[col_pivote] if col_pivote is not None else None

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
            "nombres_vars": list(nombres_vars),
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
        """Ejecuta eliminación de Gauss-Jordan y retorna el tablero actualizado con sus operaciones."""
        nombres_vars = self.estandarizador.nombres_vars
        total_vars = len(nombres_vars)

        f0_c = copy.deepcopy(fila_0_coefs)
        f0_rhs = copy.deepcopy(fila_0_rhs)
        f_rest = copy.deepcopy(filas_rest)
        v_bas = list(vars_basicas)
        operaciones = []

        pivote = f_rest[fila_piv]["coefs"][col_piv]

        for j in range(total_vars):
            f_rest[fila_piv]["coefs"][j] /= pivote
        f_rest[fila_piv]["b"] /= pivote
        v_bas[fila_piv] = nombres_vars[col_piv]

        piv_txt = formatear_numero(pivote, usar_fracciones)
        operaciones.append(f"Ec ({fila_piv + 1}) ← Ec ({fila_piv + 1}) / ({piv_txt})   [Normalizar fila pivote]")

        for i in range(len(f_rest)):
            if i != fila_piv:
                factor = f_rest[i]["coefs"][col_piv]
                if factor != 0:
                    for j in range(total_vars):
                        f_rest[i]["coefs"][j] -= factor * f_rest[fila_piv]["coefs"][j]
                    f_rest[i]["b"] -= factor * f_rest[fila_piv]["b"]

                    fac_txt = formatear_numero(factor, usar_fracciones)
                    operaciones.append(f"Ec ({i + 1}) ← Ec ({i + 1}) - ({fac_txt}) · Ec ({fila_piv + 1})")

        factor_0 = f0_c[col_piv]
        if not factor_0.es_cero():
            for j in range(total_vars):
                f0_c[j] = f0_c[j] - (factor_0 * f_rest[fila_piv]["coefs"][j])
            f0_rhs = f0_rhs - (factor_0 * f_rest[fila_piv]["b"])

            fac0_txt = factor_0.formatear(usar_fracciones)
            operaciones.append(f"Ec (0) ← Ec (0) - ({fac0_txt}) · Ec ({fila_piv + 1})")

        return f0_c, f0_rhs, f_rest, v_bas, operaciones

    def _extraer_solucion(self, fila_0_rhs, filas_rest, vars_basicas):
        """Obtiene Z* y reconstruye los valores de las variables de decisión X_1..X_n."""
        valores_columnas = {nombre: Fraction(0) for nombre in self.estandarizador.nombres_vars}
        for i, vb in enumerate(vars_basicas):
            valores_columnas[vb] = filas_rest[i]["b"]

        solucion_x = self.estandarizador.reconstruir_variables_decision(valores_columnas)
        valor_z = -fila_0_rhs.const
        return valor_z, solucion_x

    def resolver(self, usar_fracciones=True, max_iteraciones=50):
        """Ejecuta todo el proceso iterativo de la Gran M hasta llegar a criterio de parada."""
        info_estandar = self.estandarizador.construir()
        nombres_vars = self.estandarizador.nombres_vars
        total_vars = len(nombres_vars)
        signo_penalizacion = Fraction(1) if self.tipo_obj == "MINIMIZAR" else Fraction(-1)

        # Preparar Ecuación (0) inicial y eliminar artificiales de la base
        fila_0_coefs = [TerminoM(c, 0) for c in self.estandarizador.coef_z_expandido]
        for a in range(1, self.estandarizador.n_artificiales + 1):
            col_a = nombres_vars.index(f"a{a}")
            fila_0_coefs[col_a] = TerminoM(0, signo_penalizacion)
        fila_0_rhs = TerminoM(0, 0)

        operaciones_eliminacion = []
        for idx_fila, vb in enumerate(self.estandarizador.vars_basicas):
            if vb.startswith("a"):
                mult_m = -signo_penalizacion
                fila_r = self.estandarizador.filas_restricciones[idx_fila]
                for j in range(total_vars):
                    fila_0_coefs[j] = fila_0_coefs[j] + TerminoM(0, mult_m * fila_r["coefs"][j])
                fila_0_rhs = fila_0_rhs + TerminoM(0, mult_m * fila_r["b"])

                signo_txt = "-M" if mult_m < 0 else "+M"
                operaciones_eliminacion.append(
                    f"Ec (0) ← Ec (0) + ({signo_txt}) · Ec ({idx_fila + 1})   [Eliminar {vb} de Ec (0)]"
                )

        filas_actuales = copy.deepcopy(self.estandarizador.filas_restricciones)
        vars_basicas_actuales = list(self.estandarizador.vars_basicas)

        iteraciones = []
        estado = "OPTIMO"
        mensaje_estado = ""
        es_degenerado = False
        es_multiple = False
        vars_alternativas = []
        solucion_alternativa = None

        for k in range(max_iteraciones):
            tablero = self._evaluar_tablero(k, fila_0_coefs, fila_0_rhs, filas_actuales, vars_basicas_actuales)
            if tablero["empate_razon"]:
                es_degenerado = True

            if tablero["col_pivote"] is None:
                iteraciones.append(tablero)
                break

            if tablero["fila_pivote"] is None:
                estado = "NO_ACOTADO"
                mensaje_estado = (
                    f"Problema NO ACOTADO: La variable {tablero['var_entrante']} debe entrar a la base, "
                    f"pero todos sus coeficientes en las restricciones son menores o iguales a cero."
                )
                iteraciones.append(tablero)
                break

            fila_0_coefs, fila_0_rhs, filas_actuales, vars_basicas_actuales, ops = self._aplicar_pivoteo(
                fila_0_coefs, fila_0_rhs, filas_actuales, vars_basicas_actuales,
                tablero["fila_pivote"], tablero["col_pivote"], usar_fracciones
            )
            tablero["operaciones_pivote"] = ops
            iteraciones.append(tablero)

        tablero_final = iteraciones[-1]
        valor_z = None
        solucion_x = {}

        if estado == "OPTIMO":
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
                valor_z, solucion_x = self._extraer_solucion(
                    tablero_final["fila_0_rhs"],
                    tablero_final["filas_restricciones"],
                    tablero_final["vars_basicas"]
                )

                if any(r["b"] == 0 for r in tablero_final["filas_restricciones"]):
                    es_degenerado = True

                set_basicas = set(tablero_final["vars_basicas"])
                for j, nombre in enumerate(nombres_vars):
                    if nombre not in set_basicas and not nombre.startswith("a"):
                        if tablero_final["fila_0_coefs"][j].es_cero():
                            vars_alternativas.append(nombre)

                if vars_alternativas:
                    es_multiple = True
                    col_alt = nombres_vars.index(vars_alternativas[0])
                    fila_alt, menor_r_alt = None, None
                    for i, r in enumerate(tablero_final["filas_restricciones"]):
                        piv_alt = r["coefs"][col_alt]
                        if piv_alt > 0:
                            raz_alt = r["b"] / piv_alt
                            if menor_r_alt is None or raz_alt < menor_r_alt:
                                menor_r_alt = raz_alt
                                fila_alt = i
                    if fila_alt is not None:
                        _, f0_rhs_alt, f_rest_alt, v_bas_alt, _ = self._aplicar_pivoteo(
                            tablero_final["fila_0_coefs"], tablero_final["fila_0_rhs"],
                            tablero_final["filas_restricciones"], tablero_final["vars_basicas"],
                            fila_alt, col_alt, usar_fracciones
                        )
                        _, sol_x_alt = self._extraer_solucion(f0_rhs_alt, f_rest_alt, v_bas_alt)
                        solucion_alternativa = sol_x_alt

                mensaje_estado = "Solución óptima alcanzada correctamente."

        return {
            "metodo": "Gran M",
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
            "solucion_x": solucion_x
        }