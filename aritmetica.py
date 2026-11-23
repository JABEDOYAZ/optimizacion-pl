from fractions import Fraction


def formatear_numero(frac, usar_fracciones=True):
    """Formatea una Fraction como fracción ('2/5') o decimal legible ('0.4')."""
    if not isinstance(frac, Fraction):
        frac = Fraction(str(frac))
    if usar_fracciones or frac.denominator == 1:
        return str(frac)
    val = round(float(frac), 4)
    return f"{val:g}"


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
        return self.m > 0 if self.m != 0 else self.const > 0

    def es_negativo(self):
        """Para M suficientemente grande (M -> +inf), evalúa si el término es < 0."""
        return self.m < 0 if self.m != 0 else self.const < 0

    def clave_magnitud(self):
        """Tupla para comparar valores absolutos |coef_m * M + const| cuando M es muy grande."""
        return (abs(self.m), abs(self.const))

    def formatear(self, usar_fracciones=True):
        """Convierte el término (const + m*M) a texto legible, ej: '-1.1M+0.4'."""
        if self.m == 0:
            return formatear_numero(self.const, usar_fracciones)

        if self.m == 1:
            parte_m = "M"
        elif self.m == -1:
            parte_m = "-M"
        else:
            parte_m = f"{formatear_numero(self.m, usar_fracciones)}M"

        if self.const == 0:
            return parte_m

        signo_c = "+" if self.const > 0 else "-"
        parte_c = formatear_numero(abs(self.const), usar_fracciones)
        return f"{parte_m}{signo_c}{parte_c}"