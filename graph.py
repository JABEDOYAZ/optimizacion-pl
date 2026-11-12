import matplotlib.pyplot as plt # Importación de Matplotlib para la generación de gráficos en 2D
import numpy as np # Importación de NumPy para manejo de mallas numéricas y cálculos vectoriales

def generar_grafico_2d(tipo_obj, coef_z, restricciones, permitir_negativos=False):
    """
    Construye y retorna una figura de Matplotlib con el gráfico 2D de Programación Lineal:
    - Región factible sombreada
    - Rectas de restricción rotuladas
    - Vértices factibles identificados con su valor de Z
    - Recta de la función objetivo en el punto óptimo (Isoutilidad / Isocosto)
    - Manejo de regiones no acotadas o vacías (infactibles)
    """

    fig, ax = plt.subplots(figsize=(8, 6)) # Creación de la figura y del eje principal de dibujo
    
    c1, c2 = coef_z[0], coef_z[1] # Extracción de los coeficientes c1 y c2 de la función objetivo
    
    # ---------------------------------------------------------
    # PASO 1: Determinar las intersecciones y límites de los ejes
    # ---------------------------------------------------------
    puntos_interseccion = [] 
    

    rectas = [] 
    for r in restricciones: 
        rectas.append((r["coefs"][0], r["coefs"][1], r["b"], r["signo"])) 
        
    # Si las variables no pueden ser negativas (X1 >= 0, X2 >= 0), agregamos las rectas de los ejes
    if not permitir_negativos: # Evalúa la bandera de restricción de signo
        rectas.append((1, 0, 0, ">=")) # Restricción implícita X1 >= 0
        rectas.append((0, 1, 0, ">=")) # Restricción implícita X2 >= 0
        
    n_rectas = len(rectas) # Total de rectas a evaluar
    for i in range(n_rectas): 
        for j in range(i + 1, n_rectas): 
            a11, a12, b1, _ = rectas[i] # Coeficientes de la primera recta
            a21, a22, b2, _ = rectas[j] # Coeficientes de la segunda recta
            
            det = a11 * a22 - a12 * a21 # Determinante del sistema 2x2
            if abs(det) != 0: # Si el determinante es distinto de cero, las rectas se cortan en un punto
                x1_int = (b1 * a22 - a12 * b2) / det 
                x2_int = (a11 * b2 - b1 * a21) / det 
                puntos_interseccion.append((x1_int, x2_int)) # Guarda el punto de intersección
                
    # Determinar rango adecuado de los ejes X1 y X2 para la gráfica
    if puntos_interseccion: # Si existen puntos de corte calculados
        x1_vals = [p[0] for p in puntos_interseccion] # Extrae todos los valores de X1
        x2_vals = [p[1] for p in puntos_interseccion] # Extrae todos los valores de X2
        
        # Establece límites máximos con margen visual del 20%
        max_x1 = max(max(x1_vals, default=10), 5) * 1.2 # Límite superior eje X1
        max_x2 = max(max(x2_vals, default=10), 5) * 1.2 # Límite superior eje X2
        
        min_x1 = min(min(x1_vals, default=0), 0) - (abs(max_x1) * 0.1 if permitir_negativos else 0.5) # Límite inferior X1
        min_x2 = min(min(x2_vals, default=0), 0) - (abs(max_x2) * 0.1 if permitir_negativos else 0.5) # Límite inferior X2
    else: # Límites por defecto si no hay intersecciones válidas
        min_x1, max_x1 = -1 if permitir_negativos else -0.5, 10
        min_x2, max_x2 = -1 if permitir_negativos else -0.5, 10
        
    # ---------------------------------------------------------
    # PASO 2: Evaluar la factibilidad de los vértices
    # ---------------------------------------------------------
    vertices_factibles = [] # Lista para los vértices que cumplen TODAS las restricciones
    for px1, px2 in puntos_interseccion: # Recorre cada intersección calculada
        es_factible = True 
        
        # Comprobar restricciones del dominio de variables (No negatividad)
        if not permitir_negativos and (px1 < -1e-5 or px2 < -1e-5): # Si X1 < 0 o X2 < 0 cuando no se permiten negativos
            es_factible = False # Punto no factible
            
        # Comprobar restricciones ingresadas por el usuario
        for r in restricciones: # Inspecciona cada restricción del problema
            val_lh = r["coefs"][0] * px1 + r["coefs"][1] * px2 # Calcula la parte izquierda (A1*X1 + A2*X2)
            if r["signo"] == "<=" and val_lh > r["b"] + 1e-5: # Violación de <=
                es_factible = False
            elif r["signo"] == ">=" and val_lh < r["b"] - 1e-5: # Violación de >=
                es_factible = False
            elif r["signo"] == "=" and abs(val_lh - r["b"]) > 1e-5: # Violación de =
                es_factible = False
                
        if es_factible: # Si el punto pasó todas los chequeos de restricción
            # Evitar guardar puntos duplicados por imprecisión flotante
            if not any(abs(px1 - v[0]) < 1e-4 and abs(px2 - v[1]) < 1e-4 for v in vertices_factibles):
                z_val = c1 * px1 + c2 * px2 # Calcula el valor de Z en el vértice
                vertices_factibles.append((px1, px2, z_val)) # Almacena (X1, X2, Z)
                
    # ---------------------------------------------------------
    # PASO 3: Sombreado de la Región Factible (Malla de Puntos 2D)
    # ---------------------------------------------------------
    grid_x1 = np.linspace(min_x1, max_x1, 400) # Genera 400 puntos equidistantes en el eje X1
    grid_x2 = np.linspace(min_x2, max_x2, 400) # Genera 400 puntos equidistantes en el eje X2
    X1_mesh, X2_mesh = np.meshgrid(grid_x1, grid_x2) # Crea la malla 2D de coordenadas
    
    region_mask = np.ones(X1_mesh.shape, dtype=bool) 
    
    # Filtro de no negatividad en la malla
    if not permitir_negativos: # Si X_j >= 0
        region_mask &= (X1_mesh >= 0) & (X2_mesh >= 0) # Aplica filtro X1 >= 0 y X2 >= 0
        
    # Filtro de restricciones de la interfaz en la malla
    for r in restricciones: # Recorre cada restricción del usuario
        lh = r["coefs"][0] * X1_mesh + r["coefs"][1] * X2_mesh # Evalúa A1*X1 + A2*X2 en la malla
        if r["signo"] == "<=": # Aplica filtro <=
            region_mask &= (lh <= r["b"] + 1e-5)
        elif r["signo"] == ">=": # Aplica filtro >=
            region_mask &= (lh >= r["b"] - 1e-5)
        elif r["signo"] == "=": # Aplica tolerancia para igualdad =
            region_mask &= (np.abs(lh - r["b"]) <= (max_x1 - min_x1) * 0.005)

    # Dibuja la región factible sombreada en azul transparente
    ax.imshow(
        region_mask, 
        extent=(min_x1, max_x1, min_x2, max_x2), 
        origin='lower', 
        cmap='Blues', 
        alpha=0.3 # Opacidad transparente para visualizar el fondo
    )

    # ---------------------------------------------------------
    # PASO 4: Dibujar y rotular las rectas de restricción
    # ---------------------------------------------------------
    colores_rectas = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'] # Paleta de colores para las rectas
    for i, r in enumerate(restricciones): # Recorre cada restricción para trazar su recta
        a1, a2, b, signo = r["coefs"][0], r["coefs"][1], r["b"], r["signo"] # Coeficientes de la restricción i
        color = colores_rectas[i % len(colores_rectas)] # Asigna un color distinto a cada recta
        
        if abs(a2) > 1e-5: # Si a2 != 0, despejamos X2 = (b - a1*X1) / a2
            x1_line = np.array([min_x1, max_x1]) # Puntos X1 de extremo a extremo
            x2_line = (b - a1 * x1_line) / a2 # Puntos X2 correspondientes despejados
            ax.plot(x1_line, x2_line, label=f"R{i+1}: {a1}X1 + {a2}X2 {signo} {b}", color=color, linewidth=2) # Dibuja la recta
        else: # Si a2 == 0, es una recta vertical X1 = b / a1
            x1_val = b / a1 # Coordenada vertical fija en X1
            ax.axvline(x=x1_val, label=f"R{i+1}: {a1}X1 {signo} {b}", color=color, linewidth=2) # Dibuja recta vertical

    # ---------------------------------------------------------
    # PASO 5: Dibujar vértices, evaluar Z y destacar la solución óptima
    # ---------------------------------------------------------
    if vertices_factibles: # Si se encontraron vértices factibles
        # Ordena los vértices para determinar el punto óptimo
        if tipo_obj == "MAXIMIZAR": # Si el objetivo es Maximizar Z
            vertices_factibles.sort(key=lambda item: item[2], reverse=True) # Ordena de mayor a menor Z
        else: # Si el objetivo es Minimizar Z
            vertices_factibles.sort(key=lambda item: item[2]) # Ordena de menor a mayor Z
            
        optimo_x1, optimo_x2, optimo_z = vertices_factibles[0] # El primer elemento es el punto óptimo (X1*, X2*, Z*)
        
        # Marcado de todos los vértices factibles en la gráfica
        for vx1, vx2, vz in vertices_factibles: # Recorre los vértices factibles
            ax.scatter(vx1, vx2, color='black', s=40, zorder=5) # Dibuja punto negro en cada vértice
            ax.annotate(
                f"({round(vx1, 2)}, {round(vx2, 2)})\nZ={round(vz, 2)}", # Texto del vértice (X1, X2) y su Z
                (vx1, vx2), # Coordenadas del texto
                textcoords="offset points", 
                xytext=(8, 8), # Desplazamiento del texto
                ha='left', 
                fontsize=8, 
                bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.6) # Caja amarilla para legibilidad
            )

        # Destacar el Punto Óptimo con un marcador dorado grande
        ax.scatter(optimo_x1, optimo_x2, color='gold', edgecolor='black', s=150, zorder=6, label=f"Óptimo: ({round(optimo_x1,2)}, {round(optimo_x2,2)})")

        # ---------------------------------------------------------
        # PASO 6: Trazar la recta de Isoutilidad / Isocosto (F.O. en el óptimo)
        # ---------------------------------------------------------
        if abs(c2) > 1e-5: # Si c2 != 0, despejamos X2 = (Z* - c1*X1) / c2
            x1_iso = np.array([min_x1, max_x1]) # Extensión de la recta en X1
            x2_iso = (optimo_z - c1 * x1_iso) / c2 # Puntos X2 de la recta de isoutilidad
            ax.plot(x1_iso, x2_iso, 'r--', linewidth=2.5, label=f"F.O. Óptima (Z*={round(optimo_z, 2)})") # Recta roja punteada
        elif abs(c1) > 1e-5: # Si c2 == 0, la recta de isoutilidad es vertical X1 = Z* / c1
            ax.axvline(x=optimo_z / c1, color='r', linestyle='--', linewidth=2.5, label=f"F.O. Óptima (Z*={round(optimo_z, 2)})")

    else: # Si no existen vértices factibles (Problema Infactible)
        ax.text(
            0.5, 0.5, "❌ No tiene solución factible", # Texto en el centro de la gráfica
            transform=ax.transAxes, 
            ha='center', va='center', 
            fontsize=14, color='red', weight='bold',
            bbox=dict(boxstyle="round", fc="white", ec="red")
        )

    # ---------------------------------------------------------
    # PASO 7: Formato final de la figura (Títulos, Ejes y Leyendas)
    # ---------------------------------------------------------
    ax.set_xlim(min_x1, max_x1) # Aplica límites en el eje X1
    ax.set_ylim(min_x2, max_x2) # Aplica límites en el eje X2
    ax.set_xlabel("Variable X1", fontsize=11, fontweight='bold') # Etiqueta eje horizontal
    ax.set_ylabel("Variable X2", fontsize=11, fontweight='bold') # Etiqueta eje vertical
    ax.set_title("Método Gráfico - Región Factible e Isoutilidad", fontsize=13, fontweight='bold') # Título del gráfico
    ax.axhline(0, color='black', linewidth=1) # Dibuja la línea del eje X1 (y=0)
    ax.axvline(0, color='black', linewidth=1) # Dibuja la línea del eje X2 (x=0)
    ax.grid(True, linestyle=':', alpha=0.6) # Red de cuadrícula de fondo
    ax.legend(loc='upper right', fontsize=8) # Despliega la leyenda con los colores de las restricciones
    
    return fig # Retorna el objeto figura listo para renderizar en Streamlit con st.pyplot(fig)