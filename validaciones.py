import json

def validar_funcion_objetivo(coef_z):
    """Verifica que todas las variables de decisión tengan coeficiente distinto de cero en Z."""
    vars_c_cero = [f"X{j+1}" for j, c in enumerate(coef_z) if c == 0]
    if vars_c_cero:
        mensaje = (
            f"❌ **Modelo mal formulado en la Función Objetivo:** La(s) variable(s) **{', '.join(vars_c_cero)}** "
            f"tiene(n) un coeficiente igual a 0. Todas las variables deben tener un coeficiente distinto de cero."
        )
        return False, mensaje
    return True, ""

def validar_restricciones(restricciones, n_vars):
    """Verifica que no existan restricciones vacías y que cada variable X_j aparezca en al menos una restricción."""
    errores = []

    # 1. Verificar que ninguna restricción tenga todos sus coeficientes en cero
    for i, r in enumerate(restricciones):
        if all(c == 0 for c in r["coefs"]):
            errores.append(f"❌ **Restricción {i+1} inválida:** Todos los coeficientes a_{i+1}j son cero.")

    # 2. Verificar que cada variable X_j tenga al menos un coeficiente distinto de cero en la matriz A
    vars_sin_restriccion = []
    for j in range(n_vars):
        if not any(r["coefs"][j] != 0 for r in restricciones):
            vars_sin_restriccion.append(f"X{j+1}")

    if vars_sin_restriccion:
        errores.append(
            f"❌ **Modelo mal diseñado en las Restricciones:** La(s) variable(s) **{', '.join(vars_sin_restriccion)}** "
            f"no aparece(n) acotada(s) en ninguna restricción (todos sus coeficientes son 0)."
        )

    return len(errores) == 0, errores


def generar_json_modelo(modelo):
    """Convierte el diccionario del modelo actual a texto JSON formateado para su descarga."""
    return json.dumps(modelo, indent=4, ensure_ascii=False)