from fractions import Fraction 
import numpy as np 

class GranM: 
    def __init__(self, tipo_obj, coef_z, restricciones, permitir_negativos=False): 
        """
        Inicializa la instancia del solver de la Gran M.
        :param tipo_obj: String ('MAXIMIZAR' o 'MINIMIZAR') que define la dirección de la optimización.
        :param coef_z: Lista con los coeficientes numéricos de la función objetivo [c1, c2, ...].
        :param restricciones: Lista de diccionarios [{'coefs': [...], 'signo': '<=', 'b': val}, ...].
        :param permitir_negativos: Booleano que indica si las variables pueden asumir valores negativos.
        """
        self.tipo_obj = tipo_obj 
        self.n_vars_orig = len(coef_z) 
        self.coef_z_orig = [Fraction(str(c)) for c in coef_z] # Convierte los coeficientes de Z a formato de fracción exacta
        self.restricciones_orig = restricciones 
        self.permitir_negativos = permitir_negativos
        
        self.n_holguras = 0 # variables de holgura (+s) a agregar
        self.n_excesos = 0 # variables de exceso (-e) a agregar
        self.n_artificiales = 0 # variables artificiales (+a) a agregar
        
        self.nombres_vars = [] # Lista que almacenará todos los encabezados de columnas (Xj, s_i, e_i, a_i)
        self.forma_estandar_str = [] # Lista de cadenas de texto con la representación algebraica en forma estándar
        self.vars_basicas = [] # Lista que contiene los nombres de las variables que conforman la base inicial
        
        self.tabla = [] # Matriz/Tablero Simplex de trabajo
        self.pasos = [] # Colección del historial de tableros e interpretaciones para el modo paso a paso
        self.estado = None # Variable de estado del problema ('OPTIMO', 'INFACTIBLE', 'NO_ACOTADO')

    def estandarizar(self):
        """
        Transforma el modelo original a la Forma Estándar:
        1. Invierte restricciones con lados derechos negativos (b_i < 0).
        2. Clasifica y agrega variables de holgura (+s), exceso (-e) y artificiales (+a).
        3. Determina las variables básicas iniciales para el método Simplex.
        4. Genera la representación en texto de las ecuaciones estandarizadas.
        """
        # Paso 1: Inicialización de los nombres de las variables de decisión originales
        self.nombres_vars = [f"X{j+1}" for j in range(self.n_vars_orig)] # Crea etiquetas ["X1", "X2", ..., "Xn"]
        
        # Creación de una copia procesada para corregir lados derechos negativos (RHS < 0)
        restricciones_procesadas = [] # Lista temporal para las restricciones con b_i >= 0
        for r in self.restricciones_orig: # Recorre cada restricción original proporcionada por la interfaz
            coefs = [Fraction(str(c)) for c in r['coefs']] # Convierte los coeficientes a fracciones exactas
            signo = r['signo'] # Extrae el operador actual ('<=', '>=', '=')
            b = Fraction(str(r['b'])) # Convierte el lado derecho b a fracción exacta
            
            # Regla de estandarización: Si el lado derecho b_i es negativo, se multiplica toda la restricción por -1
            if b < 0:
                coefs = [-c for c in coefs] # Invierte el signo de todos los coeficientes a_ij
                b = -b # Convierte el valor de b a positivo
                if signo == "<=": # Si el signo era <= pasa a >=
                    signo = ">="
                elif signo == ">=": # Si el signo era >= pasa a <=
                    signo = "<="
                # Si el signo es '=', se mantiene igual
            
            restricciones_procesadas.append({'coefs': coefs, 'signo': signo, 'b': b})
        
        # Paso 2: Conteo de los tipos de variables requeridas según los signos de restricción
        for i, r in enumerate(restricciones_procesadas): 
            if r['signo'] == "<=": # Las restricciones de tipo <= requieren únicamente una variable de holgura
                self.n_holguras += 1 
            elif r['signo'] == ">=": # Las restricciones de tipo >= requieren variable de exceso y variable artificial
                self.n_excesos += 1 
                self.n_artificiales += 1 
            elif r['signo'] == "=": # Las restricciones de tipo = requieren una variable artificial
                self.n_artificiales += 1 # Incrementa contador de artificiales

        for h in range(1, self.n_holguras + 1): 
            self.nombres_vars.append(f"s{h}") # Añade etiquetas s1, s2, ...
        for e in range(1, self.n_excesos + 1): 
            self.nombres_vars.append(f"e{e}") # Añade etiquetas e1, e2, ...
        for a in range(1, self.n_artificiales + 1):
            self.nombres_vars.append(f"a{a}") # Añade etiquetas a1, a2, ...
            
        # Paso 3: Construcción de la representación algebraica y asignación de la base inicial
        idx_s, idx_e, idx_a = 1, 1, 1 # Subíndices contadores independientes para etiquetado
        
        for i, r in enumerate(restricciones_procesadas): 

            eq_str = " + ".join([f"{r['coefs'][j]}*X{j+1}" for j in range(self.n_vars_orig) if r['coefs'][j] != 0])
            
            if r['signo'] == "<=": # Caso de restricción <=
                eq_str += f" + s{idx_s} = {r['b']}" # Construye ecuación agregando la holgura (+s_i)
                self.vars_basicas.append(f"s{idx_s}") 
                idx_s += 1 
            elif r['signo'] == ">=": # Caso de restricción >=
                eq_str += f" - e{idx_e} + a{idx_a} = {r['b']}" # Construye ecuación resta de exceso (-e_i) y suma de artificial (+a_i)
                self.vars_basicas.append(f"a{idx_a}") 
                idx_e += 1 
                idx_a += 1 
            elif r['signo'] == "=": # Caso de restricción =
                eq_str += f" + a{idx_a} = {r['b']}" # Construye ecuación agregando la variable artificial (+a_i)
                self.vars_basicas.append(f"a{idx_a}") 
                idx_a += 1 
                
            self.forma_estandar_str.append(eq_str) 

        # Retorna un diccionario estructurado con los datos
        return {
            "nombres_vars": self.nombres_vars, # Lista de todas las variables involucradas
            "forma_estandar": self.forma_estandar_str, # Lista de strings de las ecuaciones estandarizadas
            "vars_basicas_iniciales": self.vars_basicas # Nombres de las variables en la base inicial
        }