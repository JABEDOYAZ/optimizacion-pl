import json
from fractions import Fraction


def parsear_numero(texto):
    """
    Convierte una cadena o número a una fracción exacta (Fraction).
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

def cargar_json_modelo(ruta_archivo):
    """
    Lee un archivo .json, valida su estructura y valores numéricos,
    y retorna (True, modelo_dict) o (False, mensaje_error).
    """
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as exc:
        return False, f"El archivo no tiene un formato JSON válido:\n{exc}"
    except OSError as exc:
        return False, f"No se pudo leer el archivo:\n{exc}"

    if not isinstance(datos, dict):
        return False, "La raíz del archivo JSON debe ser un objeto con las claves del modelo."

    for clave in ["tipo_objetivo", "coef_z", "restricciones"]:
        if clave not in datos:
            return False, f"Falta la clave obligatoria '{clave}' en el archivo JSON."

    tipo_obj = str(datos["tipo_objetivo"]).strip().upper()
    if tipo_obj not in ["MAXIMIZAR", "MINIMIZAR"]:
        return False, "La clave 'tipo_objetivo' debe ser 'MAXIMIZAR' o 'MINIMIZAR'."

    if not isinstance(datos["coef_z"], list) or not isinstance(datos["restricciones"], list):
        return False, "Las claves 'coef_z' y 'restricciones' deben ser listas."

    n_vars = int(datos.get("n_vars", len(datos["coef_z"])))
    m_cons = int(datos.get("m_cons", len(datos["restricciones"])))

    if not (2 <= n_vars <= 10):
        return False, f"El número de variables (n={n_vars}) debe estar entre 2 y 10."
    if not (1 <= m_cons <= 15):
        return False, f"El número de restricciones (m={m_cons}) debe estar entre 1 y 15."
    if len(datos["coef_z"]) != n_vars:
        return False, f"La cantidad de coeficientes en 'coef_z' ({len(datos['coef_z'])}) no coincide con n_vars ({n_vars})."
    if len(datos["restricciones"]) != m_cons:
        return False, f"La cantidad de restricciones ({len(datos['restricciones'])}) no coincide con m_cons ({m_cons})."

    try:
        coef_z = [parsear_numero(c) for c in datos["coef_z"]]
    except ValueError as exc:
        return False, f"Error en 'coef_z': {exc}"

    restricciones_proc = []
    for i, r in enumerate(datos["restricciones"]):
        if not isinstance(r, dict) or not all(k in r for k in ["coefs", "signo", "b"]):
            return False, f"La restricción {i+1} debe contener las claves 'coefs', 'signo' y 'b'."
        if len(r["coefs"]) != n_vars:
            return False, f"La restricción {i+1} tiene {len(r['coefs'])} coeficientes, pero se esperaban {n_vars}."
        if r["signo"] not in ["<=", ">=", "="]:
            return False, f"Signo inválido '{r['signo']}' en la restricción {i+1}. Use '<=', '>=' o '='."
        try:
            coefs_r = [parsear_numero(c) for c in r["coefs"]]
            b_r = parsear_numero(r["b"])
        except ValueError as exc:
            return False, f"Error numérico en la restricción {i+1}: {exc}"

        restricciones_proc.append({"coefs": coefs_r, "signo": r["signo"], "b": b_r})

    # Ejecutar las validaciones matemáticas del modelo
    valido_z, msg_z = validar_funcion_objetivo(coef_z)
    if not valido_z:
        return False, msg_z.replace("*", "")

    valido_r, errores_r = validar_restricciones(restricciones_proc, n_vars)
    if not valido_r:
        return False, "\n".join(errores_r).replace("*", "")

    modelo_validado = {
        "tipo_objetivo": tipo_obj,
        "n_vars": n_vars,
        "m_cons": m_cons,
        "coef_z": coef_z,
        "restricciones": restricciones_proc,
        "permitir_negativos": bool(datos.get("permitir_negativos", False))
    }
    return True, modelo_validado