"""
Genera los LUTs .cube del Resolve Pro Pack de forma reproducible.

Todos los looks esperan entrada Rec.709 / Gamma 2.4 (imagen ya "normalizada").
Con material log, primero convierte a Rec.709 (CST o gestion de color) y aplica el LUT despues.

Uso:  python tools/generate_luts.py      (escribe en LUTs/)
La matematica de cada look es identica a su version DCTL en DCTL/ (mismos valores por defecto).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZE = 33

# Coeficientes Rec.709
KR, KG, KB = 0.2126, 0.7152, 0.0722
CB_DIV, CR_DIV = 1.8556, 1.5748


def clamp01(x):
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def teal_orange(r, g, b, contraste=0.30, tonificado=1.0, eje=1.0):
    """Teal & orange: contraste en S, sombras frias/altas calidas, croma empujado al eje piel-cian."""
    # 1. contraste en S alrededor de 0.5
    def s_curve(x):
        x = clamp01(x)
        return x + contraste * (x * x * (3.0 - 2.0 * x) - x)
    r, g, b = s_curve(r), s_curve(g), s_curve(b)

    # 2. split toning segun luminancia
    y = KR * r + KG * g + KB * b
    sh, hi = (1.0 - y) ** 2, y * y
    r += tonificado * (-0.035 * sh + 0.045 * hi)
    g += tonificado * (0.010 * sh + 0.012 * hi)
    b += tonificado * (0.040 * sh - 0.045 * hi)

    # 3. croma hacia el eje naranja (piel) <-> cian
    y = KR * r + KG * g + KB * b
    cb, cr = (b - y) / CB_DIV, (r - y) / CR_DIV
    ux, uy = -0.6487, 0.7610              # direccion del naranja piel en el plano CbCr
    along = cb * ux + cr * uy
    px, py = cb - along * ux, cr - along * uy
    k_along, k_perp = 1.0 + 0.12 * eje, 1.0 - 0.28 * eje
    cb = along * k_along * ux + px * k_perp
    cr = along * k_along * uy + py * k_perp
    r = y + CR_DIV * cr
    b = y + CB_DIV * cb
    g = (y - KR * r - KB * b) / KG
    return clamp01(r), clamp01(g), clamp01(b)


def saturate(r, g, b, k):
    y = KR * r + KG * g + KB * b
    return y + (r - y) * k, y + (g - y) * k, y + (b - y) * k


def frio_thriller(r, g, b):
    """Frio thriller: contraste alto, saturacion contenida, sombras verde-azuladas, altas neutras-frias."""
    def s_curve(x):
        x = clamp01(x)
        return x + 0.45 * (x * x * (3.0 - 2.0 * x) - x)
    r, g, b = s_curve(r), s_curve(g), s_curve(b)
    r, g, b = saturate(r, g, b, 0.72)
    y = KR * r + KG * g + KB * b
    sh, hi = (1.0 - y) ** 2, y * y
    r += -0.030 * sh - 0.010 * hi
    g += 0.012 * sh + 0.004 * hi
    b += 0.030 * sh + 0.020 * hi
    return clamp01(r), clamp01(g), clamp01(b)


def film_suave(r, g, b):
    """Film suave: negros levantados, hombro suave en altas, calidez ligera, saturacion algo reducida."""
    def tone(x):
        x = clamp01(x)
        x = x + 0.15 * (x * x * (3.0 - 2.0 * x) - x)      # contraste suave
        x = 1.0 - (1.0 - x) ** 1.12                         # hombro en altas
        return 0.035 + x * (0.975 - 0.035)                  # negros y blancos "de pelicula"
    r, g, b = tone(r), tone(g), tone(b)
    r, g, b = saturate(r, g, b, 0.88)
    y = KR * r + KG * g + KB * b
    mid = 4.0 * y * (1.0 - y)
    r += 0.018 * mid
    g += 0.006 * mid
    b -= 0.020 * mid
    return clamp01(r), clamp01(g), clamp01(b)


def pelicula_print(r, g, b):
    """Estilo copia de proyeccion (print film): pie y hombro suaves, densidad en rojos,
    sombras cian-verdosas, altas calidas, saturacion que baja en los extremos."""
    def tone(x):
        x = clamp01(x)
        x = x + 0.35 * (x * x * (3.0 - 2.0 * x) - x)        # contraste de copia
        x = 1.0 - (1.0 - x) ** 1.25                          # hombro
        return 0.02 + x * (0.96 - 0.02)
    r, g, b = tone(r), tone(g), tone(b)
    y = KR * r + KG * g + KB * b
    k = 0.95 - 0.25 * (2.0 * y - 1.0) ** 2                  # menos saturacion en sombras y altas
    r, g, b = saturate(r, g, b, k)
    r -= 0.03 * max(0.0, r - (g + b) / 2)                    # densidad en rojos saturados
    y = KR * r + KG * g + KB * b
    sh, hi = (1.0 - y) ** 2, y * y
    r += -0.025 * sh + 0.030 * hi
    g += 0.012 * sh + 0.010 * hi
    b += 0.020 * sh - 0.035 * hi
    return clamp01(r), clamp01(g), clamp01(b)


def bn_contraste(r, g, b):
    """Blanco y negro con contraste, con mezcla de canales tipo filtro naranja (cielos mas oscuros, piel limpia)."""
    y = 0.40 * r + 0.48 * g + 0.12 * b
    y = clamp01(y)
    y = y + 0.5 * (y * y * (3.0 - 2.0 * y) - y)
    y = 0.01 + y * 0.98
    return clamp01(y), clamp01(y), clamp01(y)


def cozy_ambar(r, g, b):
    """Cozy / flat-lay: negros suaves, medios y altas hacia el ambar, verdes y azules apagados."""
    def tone(x):
        x = clamp01(x)
        x = x + 0.12 * (x * x * (3.0 - 2.0 * x) - x)
        return 0.04 + x * (0.97 - 0.04)
    r, g, b = tone(r), tone(g), tone(b)
    r, g, b = saturate(r, g, b, 0.85)
    y = KR * r + KG * g + KB * b
    w = y ** 0.8
    r += 0.035 * w
    g += 0.012 * w
    b -= 0.045 * w
    g -= 0.015 * max(0.0, g - (r + b) / 2)                   # verdes menos chillones
    return clamp01(r), clamp01(g), clamp01(b)


def digicam_y2k(r, g, b):
    """Camara digital de los 2000: contraste duro, saturacion alta, sombras frias y altas que se queman pronto."""
    def tone(x):
        x = clamp01(x * 1.06)
        return x + 0.35 * (x * x * (3.0 - 2.0 * x) - x)
    r, g, b = tone(r), tone(g), tone(b)
    r, g, b = saturate(r, g, b, 1.25)
    y = KR * r + KG * g + KB * b
    sh = (1.0 - y) ** 2
    r += -0.02 * sh
    g += 0.01 * sh
    b += 0.035 * sh
    return clamp01(r), clamp01(g), clamp01(b)


def limpio_luminoso(r, g, b):
    """Limpio y luminoso ("clean girl"): exposicion alta, poco contraste, saturacion baja y piel rosada."""
    def tone(x):
        x = clamp01(x)
        x = 1.0 - (1.0 - x) ** 1.25                         # levanta medios
        return 0.03 + x * (0.985 - 0.03)
    r, g, b = tone(r), tone(g), tone(b)
    r, g, b = saturate(r, g, b, 0.8)
    y = KR * r + KG * g + KB * b
    mid = 4.0 * y * (1.0 - y)
    r += 0.015 * mid
    b += 0.008 * mid
    g -= 0.006 * mid
    return clamp01(r), clamp01(g), clamp01(b)


LOOKS = {
    "PRO_Look_CozyAmbar": ("PRO Cozy Ambar (entrada Rec.709 G2.4)", cozy_ambar),
    "PRO_Look_DigicamY2K": ("PRO Digicam Y2K (entrada Rec.709 G2.4)", digicam_y2k),
    "PRO_Look_LimpioLuminoso": ("PRO Limpio Luminoso (entrada Rec.709 G2.4)", limpio_luminoso),
    "PRO_Look_PeliculaPrint": ("PRO Pelicula Print (entrada Rec.709 G2.4)", pelicula_print),
    "PRO_Look_BN_Contraste": ("PRO B/N Contraste (entrada Rec.709 G2.4)", bn_contraste),
    "PRO_Look_TealOrange": ("PRO Teal & Orange (entrada Rec.709 G2.4)", teal_orange),
    "PRO_Look_FrioThriller": ("PRO Frio Thriller (entrada Rec.709 G2.4)", frio_thriller),
    "PRO_Look_FilmSuave": ("PRO Film Suave (entrada Rec.709 G2.4)", film_suave),
}


def write_cube(name, title, fn):
    out = ROOT / "LUTs" / f"{name}.cube"
    lines = [f'TITLE "{title}"',
             "# Resolve Pro Pack - generado por tools/generate_luts.py",
             "# Entrada: Rec.709 Gamma 2.4. Salida: Rec.709 Gamma 2.4.",
             f"LUT_3D_SIZE {SIZE}",
             "DOMAIN_MIN 0.0 0.0 0.0",
             "DOMAIN_MAX 1.0 1.0 1.0"]
    n = SIZE - 1
    # Orden .cube: R varia mas rapido, luego G, luego B
    for bi in range(SIZE):
        for gi in range(SIZE):
            for ri in range(SIZE):
                r, g, b = fn(ri / n, gi / n, bi / n)
                lines.append(f"{r:.6f} {g:.6f} {b:.6f}")
    out.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    print(f"{out.name}: {SIZE ** 3} filas")


if __name__ == "__main__":
    (ROOT / "LUTs").mkdir(exist_ok=True)
    for name, (title, fn) in LOOKS.items():
        write_cube(name, title, fn)
