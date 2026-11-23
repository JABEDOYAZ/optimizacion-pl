import json
from fractions import Fraction


def parsear_numero(texto):
    """
    Convierte una cadena ingresada por el usuario a una fracción exacta (Fraction).
    Soporta enteros ('5'), decimales con punto ('0.1') o coma ('0,1') y fracciones ('1/10').
    """
    limpio = str(texto).strip().replace(",", ".")
    if not limpio:
        raise ValueError("El campo no puede estar vacío.")

    try:
        return Fraction(limpio)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"Valor numérico inválido: '{texto}'") from exc


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
    # Convertimos los objetos Fraction a cadenas de texto para que json.dumps pueda serializarlos
    modelo_serializable = {
        "tipo_objetivo": modelo["tipo_objetivo"],
        "n_vars": modelo["n_vars"],
        "m_cons": modelo["m_cons"],
        "coef_z": [str(c) for c in modelo["coef_z"]],
        "restricciones": [
            {
                "coefs": [str(c) for c in r["coefs"]],
                "signo": r["signo"],
                "b": str(r["b"])
            }
            for r in modelo["restricciones"]
        ],
        "permitir_negativos": modelo["permitir_negativos"]
    }
    return json.dumps(modelo_serializable, indent=4, ensure_ascii=False)