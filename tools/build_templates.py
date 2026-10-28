"""
Genera las plantillas de Fusion del lote "Dinamico y Cine".

Uso:  python tools/build_templates.py      (escribe en Effects/ y Transitions/)
Las 4 piezas del piloto estan escritas a mano y este script no las toca.
"""
from pathlib import Path

from fusion_builder import (FuID, I, PI, Tool, clamp01, envelope_ucs, frame_format, macro,
                            mask_format, pub, pub_color, smooth, uc)

ROOT = Path(__file__).resolve().parent.parent
BUILT = {}


def register(category, name):
    def deco(fn):
        BUILT[(category, name)] = fn
        return fn
    return deco


def solid(name, rgb, pos, alpha=1, mask=None):
    inputs = {}
    if mask:
        inputs["EffectMask"] = I(link=mask, out="Mask")
    inputs.update(frame_format())
    inputs.update({"TopLeftRed": I(rgb[0]), "TopLeftGreen": I(rgb[1]),
                   "TopLeftBlue": I(rgb[2]), "TopLeftAlpha": I(alpha)})
    return Tool(name, "Background", inputs, pos=pos)


def merge(name, bg, fg, pos, mode=None, blend=None, blend_expr=None, ucs=None, extra=None):
    inputs = {}
    if bg:
        inputs["Background"] = I(link=bg)
    inputs["Foreground"] = I(link=fg)
    if mode:
        inputs["ApplyMode"] = I(FuID(mode))
    if blend is not None or blend_expr:
        inputs["Blend"] = I(blend if blend is not None else 1, blend_expr)
    inputs["PerformDepthMerge"] = I(0)
    inputs.update(extra or {})
    return Tool(name, "Merge", inputs, ucs, pos)


# ======================================================================= EFECTOS DINAMICOS
@register("Effects", "PRO_FX_Din_PunchIn")
def punch_in(name, anim):
    h = "Zoom"
    ucs, env = envelope_ucs(h, 0.08, 0)
    ucs.insert(1, uc("ZoomExtra", "Zoom extra", 0.15, 0, 1))
    tools = [Tool(h, "Transform", {
        "Center": I((0.5, 0.5)),
        "Size": I(1, f"1 + {h}.ZoomExtra*{h}.Env"),
        "Progreso": I(link=anim, out="Value"),
        "ZoomExtra": I(0.15), **env}, ucs, (0, 0))]
    pubs = [pub(h, "ZoomExtra", "Zoom extra", 0.15),
            pub(h, "Center", "Centro del zoom"),
            pub(h, "Entrada", "Duración entrada (% del clip)", 0.08),
            pub(h, "Salida", "Duración salida (% del clip, 0 = sin salida)", 0)]
    return macro(name, [(h, "Input")], pubs, h, tools, anim)


@register("Effects", "PRO_FX_Din_Shake")
def shake(name, anim):
    h = "Sacudida"
    v = f"{h}.Velocidad"
    amp = f"{h}.Intensidad*0.03*(1 - {h}.Decaimiento*{h}.Progreso)"
    cx = f"0.5 + {h}.Amp*(0.6*sin(time*0.9*{v}) + 0.4*sin(time*2.3*{v} + 1.3))"
    cy = f"0.5 + {h}.Amp*(0.6*sin(time*1.1*{v} + 0.7) + 0.4*sin(time*2.9*{v} + 2.1))"
    ang = f"{h}.Rotacion*2.5*(1 - {h}.Decaimiento*{h}.Progreso)*sin(time*0.7*{v} + 0.4)"
    size = f"1 + {h}.Intensidad*0.07 + {h}.Rotacion*0.05"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1),
           uc("Intensidad", "Intensidad", 0.3, 0, 1),
           uc("Velocidad", "Velocidad", 1, 0.1, 3),
           uc("Rotacion", "Rotación", 0.3, 0, 1),
           uc("Decaimiento", "Decaimiento (1 = se calma al final)", 0, 0, 1),
           uc("Amp", "Amplitud interna", 0, 0, 1, clamp=False)]
    tools = [Tool(h, "Transform", {
        "Center": I((0.5, 0.5), f"Point({cx}, {cy})"),
        "Size": I(1, size),
        "Angle": I(0, ang),
        "Progreso": I(link=anim, out="Value"),
        "Intensidad": I(0.3), "Velocidad": I(1), "Rotacion": I(0.3), "Decaimiento": I(0),
        "Amp": I(0, amp)}, ucs, (0, 0))]
    pubs = [pub(h, "Intensidad", "Intensidad", 0.3), pub(h, "Velocidad", "Velocidad", 1),
            pub(h, "Rotacion", "Rotación", 0.3), pub(h, "Decaimiento", "Decaimiento (1 = se calma al final)", 0)]
    return macro(name, [(h, "Input")], pubs, h, tools, anim)


@register("Effects", "PRO_FX_Din_RGBSplit")
def rgb_split(name, anim):
    h = "Aberracion"
    a = f"{h}.Angulo*{PI}/180"
    pulse = f"(1 - {h}.Pulso + {h}.Pulso*sin(time*1.7*{h}.VelPulso)*sin(time*1.7*{h}.VelPulso)*sin(time*0.37*{h}.VelPulso + 1)*sin(time*0.37*{h}.VelPulso + 1)*4)"
    off = f"{h}.Separacion*{pulse}"
    dx, dy = f"{h}.Off*sin({a} + 1.5707963)", f"{h}.Off*sin({a})*1.7778"
    ucs = [uc("Separacion", "Separación", 0.006, 0, 0.05),
           uc("Angulo", "Ángulo (grados)", 0, -180, 180),
           uc("Pulso", "Pulso glitch", 0, 0, 1),
           uc("VelPulso", "Velocidad del pulso", 1, 0.1, 4),
           uc("Off", "Desplazamiento interno", 0, 0, 1, clamp=False)]
    tools = [
        Tool("Entrada", "PipeRouter", pos=(-330, 0)),
        Tool("Rojo", "Transform", {"Input": I(link="Entrada"),
                                   "Center": I((0.5, 0.5), f"Point(0.5 + {dx}, 0.5 + {dy})")}, pos=(-220, -66)),
        Tool("Azul", "Transform", {"Input": I(link="Entrada"),
                                   "Center": I((0.5, 0.5), f"Point(0.5 - {dx}, 0.5 - {dy})")}, pos=(-220, 66)),
        solid("SoloRojo", (1, 0, 0), (-110, -99)),
        solid("SoloVerde", (0, 1, 0), (-110, -33)),
        solid("SoloAzul", (0, 0, 1), (-110, 99)),
        merge("CanalR", "Rojo", "SoloRojo", (0, -66), "Multiply"),
        merge("CanalG", "Entrada", "SoloVerde", (0, 0), "Multiply"),
        merge("CanalB", "Azul", "SoloAzul", (0, 66), "Multiply"),
        merge("SumaRG", "CanalR", "CanalG", (110, -33), "Screen"),
        merge("SumaRGB", "SumaRG", "CanalB", (110, 33), "Screen"),
        merge(h, "Entrada", "SumaRGB", (220, 0), blend=1, ucs=ucs, extra={
            "Separacion": I(0.006), "Angulo": I(0), "Pulso": I(0), "VelPulso": I(1),
            "Off": I(0, off)}),
    ]
    pubs = [pub(h, "Separacion", "Separación", 0.006), pub(h, "Angulo", "Ángulo (grados)", 0),
            pub(h, "Pulso", "Pulso glitch", 0), pub(h, "VelPulso", "Velocidad del pulso", 1),
            pub(h, "Blend", "Mezcla con el original", 1)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_FlashBeat")
def flash_beat(name, anim):
    h = "Destello"
    decay = f"(1 - {clamp01(f'{h}.Progreso/max({h}.Duracion, 0.0001)')})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1),
           uc("Intensidad", "Intensidad del flash", 0.8, 0, 1),
           uc("Duracion", "Duración (% del clip)", 0.12, 0.01, 1),
           uc("Exposicion", "Golpe de exposición", 0.3, 0, 2),
           uc("Caida", "Caída interna", 0, 0, 1, clamp=False)]
    tools = [
        Tool("Exposicion", "BrightnessContrast", {"Gain": I(1, f"1 + {h}.Exposicion*{h}.Caida")}, pos=(-110, 0)),
        solid("ColorFlash", (1, 1, 1), (-110, -66)),
        merge(h, "Exposicion", "ColorFlash", (0, 0), blend_expr=f"{h}.Intensidad*{h}.Caida", blend=0, ucs=ucs, extra={
            "Progreso": I(link=anim, out="Value"), "Intensidad": I(0.8), "Duracion": I(0.12),
            "Exposicion": I(0.3), "Caida": I(0, f"{decay}*{decay}")}),
    ]
    pubs = [pub(h, "Intensidad", "Intensidad del flash", 0.8), pub(h, "Duracion", "Duración (% del clip)", 0.12),
            pub_color("ColorFlash", "Color del flash", (1, 1, 1), 3), pub(h, "Exposicion", "Golpe de exposición", 0.3)]
    return macro(name, [("Exposicion", "Input")], pubs, h, tools, anim)


# ======================================================================= EFECTOS CINE
@register("Effects", "PRO_FX_Cine_Letterbox")
def letterbox(name, anim):
    h = "Barras"
    ucs, env = envelope_ucs(h, 0.1, 0)
    ucs += [uc("AspDest", "Aspecto destino", 2.39, 1, 3),
            uc("AspTL", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778, 0.4, 3),
            uc("H", "Altura interna", 0, 0, 1, clamp=False)]
    tools = [
        solid("Negro", (0, 0, 0), (-110, -66)),
        Tool("BarraSup", "Transform", {"Input": I(link="Negro"),
                                       "Center": I((0.5, 1.5), f"Point(0.5, 1.5 - {h}.H)")}, pos=(0, -99)),
        Tool("BarraInf", "Transform", {"Input": I(link="Negro"),
                                       "Center": I((0.5, -0.5), f"Point(0.5, -0.5 + {h}.H)")}, pos=(0, -33)),
        merge("ConSup", None, "BarraSup", (110, 0)),
        merge(h, "ConSup", "BarraInf", (220, 0), ucs=ucs, extra={
            "Progreso": I(link=anim, out="Value"), **env, "AspDest": I(2.39), "AspTL": I(1.7778),
            "H": I(0, f"max(0, (1 - {h}.AspTL/{h}.AspDest)/2)*{h}.Env")}),
    ]
    pubs = [pub(h, "AspDest", "Aspecto destino", 2.39),
            pub(h, "AspTL", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778),
            pub(h, "Entrada", "Duración entrada (% del clip)", 0.1),
            pub(h, "Salida", "Duración salida (% del clip, 0 = sin salida)", 0),
            pub_color("Negro", "Color de las barras", (0, 0, 0), 5)]
    return macro(name, [("ConSup", "Background")], pubs, h, tools, anim)


@register("Effects", "PRO_FX_Cine_Vineta")
def vineta(name, anim):
    tools = [
        Tool("Ovalo", "EllipseMask", {**mask_format(), "Invert": I(1), "SoftEdge": I(0.35),
                                      "Width": I(1.25), "Height": I(0.8)}, pos=(-110, -66)),
        solid("Sombra", (0, 0, 0), (-110, -33), mask="Ovalo"),
        merge("Vineta", None, "Sombra", (0, 0), blend=0.5),
    ]
    pubs = [pub("Vineta", "Blend", "Intensidad", 0.5), pub("Ovalo", "SoftEdge", "Suavidad", 0.35),
            pub("Ovalo", "Width", "Ancho", 1.25), pub("Ovalo", "Height", "Alto", 0.8),
            pub("Ovalo", "Center", "Centro"), pub_color("Sombra", "Color", (0, 0, 0), 6)]
    return macro(name, [("Vineta", "Background")], pubs, "Vineta", tools)


@register("Effects", "PRO_FX_Cine_Difusion")
def difusion(name, anim):
    tools = [
        Tool("Entrada", "PipeRouter", pos=(-330, 0)),
        Tool("Altas", "BrightnessContrast", {"Input": I(link="Entrada"), "Low": I(0.6), "High": I(1)}, pos=(-220, -66)),
        Tool("Halo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(60), "Input": I(link="Altas")}, pos=(-110, -66)),
        Tool("Suave", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(8), "Input": I(link="Entrada")}, pos=(-220, 66)),
        merge("Suavizado", "Entrada", "Suave", (-110, 0), blend=0.25),
        merge("Brillo", "Suavizado", "Halo", (0, 0), "Screen", blend=0.45),
        Tool("Negros", "BrightnessContrast", {"Input": I(link="Brillo"), "Lift": I(0.02)}, pos=(110, 0)),
    ]
    pubs = [pub("Brillo", "Blend", "Brillo en altas luces", 0.45), pub("Altas", "Low", "Umbral de altas luces", 0.6),
            pub("Halo", "XBlurSize", "Radio del brillo", 60), pub("Suavizado", "Blend", "Suavizado del detalle", 0.25),
            pub("Negros", "Lift", "Negros levantados", 0.02)]
    return macro(name, [("Entrada", "Input")], pubs, "Negros", tools)


# ======================================================================= TRANSICIONES
@register("Transitions", "PRO_TR_ZoomPunch")
def zoom_punch(name, anim):
    h = "Mezcla"
    p = f"{h}.Progreso"
    a, b = f"min(1, 2*{p})", f"(1 - max(0, 2*{p} - 1))"
    blur = f"{h}.Desenfoque*sin({p}*{PI})*sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Zoom", "Zoom", 1, 0, 3), uc("Desenfoque", "Desenfoque", 20, 0, 100)]
    tools = [
        Tool("ZoomSaliente", "Transform", {"Size": I(1, f"1 + {h}.Zoom*{a}*{a}")}, pos=(-220, -33)),
        Tool("ZoomEntrante", "Transform", {"Size": I(1, f"1 + {h}.Zoom*{b}*{b}")}, pos=(-220, 33)),
        Tool("BlurSaliente", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, blur),
                                      "Input": I(link="ZoomSaliente")}, pos=(-110, -33)),
        Tool("BlurEntrante", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, blur),
                                      "Input": I(link="ZoomEntrante")}, pos=(-110, 33)),
        Tool(h, "Dissolve", {
            "Mix": I(0, smooth(clamp01(f"({p} - 0.4)/0.2"))),
            "Background": I(link="BlurSaliente"), "Foreground": I(link="BlurEntrante"),
            "Progreso": I(link=anim, out="Value"), "Zoom": I(1), "Desenfoque": I(20)}, ucs, (0, 0)),
    ]
    pubs = [pub(h, "Zoom", "Zoom", 1), pub(h, "Desenfoque", "Desenfoque", 20)]
    return macro(name, [("ZoomSaliente", "Input"), ("ZoomEntrante", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_WhipPan")
def whip_pan(name, anim):
    h = "Barrido"
    p, d, v, e = f"{h}.Progreso", f"{h}.Direccion", f"{h}.Vertical", f"{h}.Env"
    blur = f"{h}.Desenfoque*sin({p}*{PI})*sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1),
           uc("Direccion", "Dirección (1 / -1)", 1, -1, 1, integer=True),
           uc("Vertical", "Barrido vertical", 0, 0, 1, checkbox=True),
           uc("Desenfoque", "Desenfoque de movimiento", 80, 0, 200),
           uc("Raw", "Curva interna", 0, 0, 1, clamp=False),
           uc("Env", "Curva interna suave", 0, 0, 1, clamp=False)]

    def blur_tool(tname, pos):
        # desenfoque solo en el eje del movimiento (LockXY = 0 separa X e Y)
        return Tool(tname, "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0),
                                    "XBlurSize": I(0, f"{blur}*(1 - {v})"),
                                    "YBlurSize": I(0, f"{blur}*{v}")}, pos=pos)

    tools = [
        blur_tool("BlurSaliente", (-220, -33)),
        blur_tool("BlurEntrante", (-220, 33)),
        Tool("MoverSaliente", "Transform", {"Input": I(link="BlurSaliente"), "Center": I(
            (0.5, 0.5), f"Point(0.5 - {d}*{e}*(1 - {v}), 0.5 - {d}*{e}*{v})")}, pos=(-110, -33)),
        Tool("MoverEntrante", "Transform", {"Input": I(link="BlurEntrante"), "Center": I(
            (0.5, 0.5), f"Point(0.5 + {d}*(1 - {e})*(1 - {v}), 0.5 + {d}*(1 - {e})*{v})")}, pos=(-110, 33)),
        merge(h, "MoverSaliente", "MoverEntrante", (0, 0), ucs=ucs, extra={
            "Progreso": I(link=anim, out="Value"), "Direccion": I(1), "Vertical": I(0), "Desenfoque": I(80),
            "Raw": I(0, smooth(p)), "Env": I(0, smooth(f"{h}.Raw"))}),
    ]
    pubs = [pub(h, "Direccion", "Dirección (1 / -1)", 1), pub(h, "Vertical", "Barrido vertical", 0),
            pub(h, "Desenfoque", "Desenfoque de movimiento", 80)]
    return macro(name, [("BlurSaliente", "Input"), ("BlurEntrante", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_LightLeak")
def light_leak(name, anim):
    h = "Mezcla"
    p = f"{h}.Progreso"
    bell = f"{h}.Intensidad*sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Intensidad", "Intensidad de la fuga", 0.9, 0, 1)]
    tools = [
        Tool(h, "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.3)/0.4"))),
                             "Progreso": I(link=anim, out="Value"), "Intensidad": I(0.9)}, ucs, (0, 0)),
        Tool("Ovalo1", "EllipseMask", {**mask_format(), "SoftEdge": I(0.5), "Width": I(0.9), "Height": I(0.9),
                                       "Center": I((0.5, 0.5), f"Point(-0.3 + 1.6*{p}, 0.6 + 0.1*sin({p}*{PI}))")},
             pos=(0, -132)),
        Tool("Ovalo2", "EllipseMask", {**mask_format(), "SoftEdge": I(0.4), "Width": I(0.6), "Height": I(0.6),
                                       "Center": I((0.5, 0.5), f"Point(1.2 - 1.2*{p}, 0.35)")}, pos=(110, -132)),
        solid("Fuga1", (1, 0.55, 0.2), (0, -99), mask="Ovalo1"),
        solid("Fuga2", (1, 0.25, 0.1), (110, -99), mask="Ovalo2"),
        merge("Luz1", h, "Fuga1", (110, 0), "Screen", blend=0, blend_expr=bell),
        merge("Luz2", "Luz1", "Fuga2", (220, 0), "Screen", blend=0, blend_expr=f"0.8*{bell}"),
    ]
    pubs = [pub(h, "Intensidad", "Intensidad de la fuga", 0.9),
            pub_color("Fuga1", "Color principal", (1, 0.55, 0.2), 2),
            pub_color("Fuga2", "Color secundario", (1, 0.25, 0.1), 3)]
    return macro(name, [(h, "Background"), (h, "Foreground")], pubs, "Luz2", tools, anim)


# ======================================================================= LENTES (bloques reutilizables)
def blk_radial_ca(p, src, host, pos_x):
    """Aberracion cromatica lateral: R y B escalados hacia fuera desde el centro (franja magenta/verde en bordes).
    Ambos canales crecen (>= 1) para no dejar huecos en los bordes."""
    k = f"{host}.Aberracion*0.004"
    return [
        Tool(f"{p}R", "Transform", {"Input": I(link=src), "Size": I(1, f"1 + {k}")}, pos=(pos_x, -66)),
        Tool(f"{p}B", "Transform", {"Input": I(link=src), "Size": I(1, f"1 + 2*{k}")}, pos=(pos_x, 66)),
        solid(f"{p}SoloR", (1, 0, 0), (pos_x + 55, -99)),
        solid(f"{p}SoloG", (0, 1, 0), (pos_x + 55, -33)),
        solid(f"{p}SoloB", (0, 0, 1), (pos_x + 55, 99)),
        merge(f"{p}CanalR", f"{p}R", f"{p}SoloR", (pos_x + 110, -66), "Multiply"),
        merge(f"{p}CanalG", src, f"{p}SoloG", (pos_x + 110, 0), "Multiply"),
        merge(f"{p}CanalB", f"{p}B", f"{p}SoloB", (pos_x + 110, 66), "Multiply"),
        merge(f"{p}RG", f"{p}CanalR", f"{p}CanalG", (pos_x + 165, -33), "Screen"),
        merge(f"{p}RGB", f"{p}RG", f"{p}CanalB", (pos_x + 220, 0), "Screen"),
    ], f"{p}RGB"


def blk_soft_edges(p, src, pos_x, blur=12, x_only=False, soft=0.5, w=1.1, h=0.75):
    """Bordes y esquinas blandos: version desenfocada mezclada fuera de un ovalo central."""
    binputs = {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(blur), "Input": I(link=src)}
    if x_only:
        binputs.update({"LockXY": I(0), "YBlurSize": I(0)})
    return [
        Tool(f"{p}Blur", "Blur", binputs, pos=(pos_x, -66)),
        Tool(f"{p}Mascara", "EllipseMask", {**mask_format(), "Invert": I(1), "SoftEdge": I(soft),
                                             "Width": I(w), "Height": I(h)}, pos=(pos_x + 55, -99)),
        merge(f"{p}Bordes", src, f"{p}Blur", (pos_x + 110, 0), blend=1,
              extra={"EffectMask": I(link=f"{p}Mascara", out="Mask")}),
    ], f"{p}Bordes"


def blk_bloom(p, src, pos_x, low=0.7, radius=40, blend=0.3, tint=None):
    tools = [Tool(f"{p}Altas", "BrightnessContrast", {"Input": I(link=src), "Low": I(low), "High": I(1)}, pos=(pos_x, -66)),
             Tool(f"{p}Halo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(radius),
                                       "Input": I(link=f"{p}Altas")}, pos=(pos_x + 55, -66))]
    last = f"{p}Halo"
    if tint:
        tools += [solid(f"{p}Tinte", tint, (pos_x + 55, -99)),
                  merge(f"{p}Tenido", last, f"{p}Tinte", (pos_x + 110, -66), "Multiply")]
        last = f"{p}Tenido"
    tools.append(merge(f"{p}Bloom", src, last, (pos_x + 165, 0), "Screen", blend=blend))
    return tools, f"{p}Bloom"


def blk_cast(p, src, pos_x, rgb, blend):
    """Dominante de color: multiplicar por un color casi blanco."""
    return [solid(f"{p}Color", rgb, (pos_x, -66)),
            merge(f"{p}Dominante", src, f"{p}Color", (pos_x + 55, 0), "Multiply", blend=blend)], f"{p}Dominante"


def blk_tone(p, src, pos_x, contrast=0.0, lift=0.0, sat=1.0):
    return [Tool(f"{p}Tono", "BrightnessContrast", {"Input": I(link=src), "Contrast": I(contrast),
                                                    "Lift": I(lift), "Saturation": I(sat)}, pos=(pos_x, 0))], f"{p}Tono"


def blk_vignette(p, src, pos_x, amount=0.4, soft=0.5, w=1.25, h=0.85):
    return [Tool(f"{p}Ovalo", "EllipseMask", {**mask_format(), "Invert": I(1), "SoftEdge": I(soft),
                                              "Width": I(w), "Height": I(h)}, pos=(pos_x, -99)),
            solid(f"{p}Sombra", (0, 0, 0), (pos_x, -66), mask=f"{p}Ovalo"),
            merge(f"{p}Vineta", src, f"{p}Sombra", (pos_x + 55, 0), blend=amount)], f"{p}Vineta"


def host_router(name, ucs, extra, pos):
    """Herramienta final que recibe la imagen y aloja los controles compartidos (PipeRouter no admite controles fiables)."""
    return Tool(name, "BrightnessContrast", extra, ucs, pos)


# ======================================================================= LENTES
@register("Effects", "PRO_FX_Lente_Anamorfico")
def lente_anamorfico(name, anim):
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Fuentes", "BrightnessContrast", {"Input": I(link="Entrada"), "Low": I(0.85), "High": I(1),
                                                    "Saturation": I(0)}, pos=(-330, -132))]
    for tname, length, y in (("RayaLarga", 400, -165), ("RayaCorta", 90, -99)):
        tools.append(Tool(tname, "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0),
                                          "XBlurSize": I(length), "YBlurSize": I(1),
                                          "Input": I(link="Fuentes")}, pos=(-220, y)))
    tools += [merge("Rayas", "RayaLarga", "RayaCorta", (-110, -132), "Screen"),
              solid("ColorRaya", (0.35, 0.6, 1), (-110, -198)),
              merge("RayaTenida", "Rayas", "ColorRaya", (0, -132), "Multiply"),
              merge("Destellos", "Entrada", "RayaTenida", (110, 0), "Screen", blend=0.6)]
    t, last = blk_soft_edges("Lat", "Destellos", 165, blur=18, x_only=True, soft=0.6, w=1.4, h=1.4)
    tools += t
    t, last = blk_cast("Frio", last, 330, (0.94, 0.98, 1), 1)
    tools += t
    t, last = blk_vignette("Vin", last, 440, amount=0.3)
    tools += t
    pubs = [pub("Destellos", "Blend", "Destellos (intensidad)", 0.6),
            pub("Fuentes", "Low", "Destellos (umbral de luces)", 0.85),
            pub("RayaLarga", "XBlurSize", "Destellos (longitud)", 400),
            pub_color("ColorRaya", "Destellos (color)", (0.35, 0.6, 1), 4),
            pub("LatBlur", "XBlurSize", "Estiramiento en laterales", 18),
            pub("FrioDominante", "Blend", "Dominante fría", 1),
            pub("VinVineta", "Blend", "Viñeta", 0.3)]
    return macro(name, [("Entrada", "Input")], pubs, last, tools)


def lens_chain(prefix_tools, ca, edges, bloom, tone, cast, vig):
    """Cadena comun de lentes de caracter: CA -> bordes -> bloom -> tono -> dominante -> vineta."""
    tools = list(prefix_tools)
    t, last = blk_radial_ca("CA", "Entrada", "Lente", -330)
    tools += t
    t, last = blk_soft_edges("Esq", last, -55, **edges)
    tools += t
    t, last = blk_bloom("Brillo", last, 110, **bloom)
    tools += t
    t, last = blk_tone("Grade", last, 330, **tone)
    tools += t
    t, last = blk_cast("Calidez", last, 385, *cast)
    tools += t
    t, last = blk_vignette("Vin", last, 495, **vig)
    tools += t
    tools.append(host_router("Lente", [uc("Aberracion", "Aberración cromática", ca, 0, 5)],
                             {"Input": I(link=last), "Aberracion": I(ca)}, (605, 0)))
    pubs = [pub("Lente", "Aberracion", "Aberración cromática", ca),
            pub("EsqBlur", "XBlurSize", "Esquinas blandas", edges["blur"]),
            pub("BrilloBloom", "Blend", "Halo en luces", bloom["blend"]),
            pub("GradeTono", "Contrast", "Contraste", tone["contrast"]),
            pub("GradeTono", "Lift", "Negros levantados", tone["lift"]),
            pub("GradeTono", "Saturation", "Saturación", tone["sat"]),
            pub("CalidezDominante", "Blend", "Dominante de color", cast[1]),
            pub_color("CalidezColor", "Color de la dominante", cast[0], 9),
            pub("VinVineta", "Blend", "Viñeta", vig["amount"])]
    return tools, pubs


@register("Effects", "PRO_FX_Lente_Vintage")
def lente_vintage(name, anim):
    tools, pubs = lens_chain([Tool("Entrada", "PipeRouter", pos=(-440, 0))], ca=1.0,
                             edges=dict(blur=10, soft=0.5, w=1.1, h=0.75),
                             bloom=dict(low=0.65, radius=35, blend=0.35, tint=(1, 0.85, 0.7)),
                             tone=dict(contrast=-0.12, lift=0.03, sat=0.85),
                             cast=((1, 0.95, 0.86), 0.8), vig=dict(amount=0.35))
    return macro(name, [("Entrada", "Input")], pubs, "Lente", tools)


@register("Effects", "PRO_FX_Lente_Lomo")
def lente_lomo(name, anim):
    tools, pubs = lens_chain([Tool("Entrada", "PipeRouter", pos=(-440, 0))], ca=2.0,
                             edges=dict(blur=20, soft=0.4, w=0.95, h=0.65),
                             bloom=dict(low=0.75, radius=25, blend=0.2, tint=None),
                             tone=dict(contrast=0.2, lift=0.0, sat=1.35),
                             cast=((0.95, 1, 0.9), 0.6), vig=dict(amount=0.75, soft=0.35, w=1.05, h=0.75))
    return macro(name, [("Entrada", "Input")], pubs, "Lente", tools)


@register("Effects", "PRO_FX_Lente_AberracionRadial")
def lente_ca(name, anim):
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0))]
    t, last = blk_radial_ca("CA", "Entrada", "Lente", -330)
    tools += t
    tools.append(host_router("Lente", [uc("Aberracion", "Intensidad", 2.0, 0, 10)],
                             {"Input": I(link=last), "Aberracion": I(2.0)}, (0, 0)))
    pubs = [pub("Lente", "Aberracion", "Intensidad", 2.0)]
    return macro(name, [("Entrada", "Input")], pubs, "Lente", tools)


@register("Effects", "PRO_FX_Lente_TiltShift")
def lente_tiltshift(name, anim):
    tools = [Tool("Entrada", "PipeRouter", pos=(-330, 0)),
             Tool("Desenfoque", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(25),
                                         "Input": I(link="Entrada")}, pos=(-220, -66)),
             Tool("Franja", "RectangleMask", {**mask_format(), "Invert": I(1), "SoftEdge": I(0.12),
                                              "Center": I((0.5, 0.45)), "Width": I(4), "Height": I(0.15),
                                              "Angle": I(0)}, pos=(-110, -99)),
             merge("Miniatura", "Entrada", "Desenfoque", (-110, 0), blend=1,
                   extra={"EffectMask": I(link="Franja", out="Mask")}),
             Tool("Juguete", "BrightnessContrast", {"Input": I(link="Miniatura"), "Contrast": I(0.1),
                                                    "Saturation": I(1.3)}, pos=(0, 0))]
    pubs = [pub("Franja", "Center", "Posición de la franja enfocada"),
            pub("Franja", "Height", "Ancho de la franja", 0.15),
            pub("Franja", "SoftEdge", "Transición", 0.12),
            pub("Franja", "Angle", "Ángulo", 0),
            pub("Desenfoque", "XBlurSize", "Desenfoque", 25),
            pub("Juguete", "Saturation", "Saturación (efecto maqueta)", 1.3)]
    return macro(name, [("Entrada", "Input")], pubs, "Juguete", tools)


# ======================================================================= ESTILO PLUGINS DE PAGO (lote 4)
def blk_channel_shift(p, src, dx, dy, pos_x):
    """Separa R y B en direcciones opuestas (dx, dy son expresiones) y recombina en Screen."""
    return [
        Tool(f"{p}R", "Transform", {"Input": I(link=src), "Center": I((0.5, 0.5), f"Point(0.5 + {dx}, 0.5 + {dy})")}, pos=(pos_x, -66)),
        Tool(f"{p}B", "Transform", {"Input": I(link=src), "Center": I((0.5, 0.5), f"Point(0.5 - {dx}, 0.5 - {dy})")}, pos=(pos_x, 66)),
        solid(f"{p}SoloR", (1, 0, 0), (pos_x + 55, -99)),
        solid(f"{p}SoloG", (0, 1, 0), (pos_x + 55, -33)),
        solid(f"{p}SoloB", (0, 0, 1), (pos_x + 55, 99)),
        merge(f"{p}CanalR", f"{p}R", f"{p}SoloR", (pos_x + 110, -66), "Multiply"),
        merge(f"{p}CanalG", src, f"{p}SoloG", (pos_x + 110, 0), "Multiply"),
        merge(f"{p}CanalB", f"{p}B", f"{p}SoloB", (pos_x + 110, 66), "Multiply"),
        merge(f"{p}RG", f"{p}CanalR", f"{p}CanalG", (pos_x + 165, -33), "Screen"),
        merge(f"{p}RGB", f"{p}RG", f"{p}CanalB", (pos_x + 220, 0), "Screen"),
    ], f"{p}RGB"


def blk_weave_breath(p, src, host, pos_x):
    """Gate weave (vaiven mecanico del fotograma) + film breath (parpadeo de exposicion/color)."""
    t = "time"
    w = f"{host}.Weave*{host}.EscalaFormato"
    r = f"{host}.Respiracion*{host}.EscalaFormato"
    cx = f"0.5 + {w}*0.0015*(sin({t}*0.37) + 0.5*sin({t}*1.13 + 2))"
    cy = f"0.5 + {w}*0.0025*(sin({t}*0.29 + 1) + 0.5*sin({t}*0.91))"
    return [
        Tool(f"{p}Weave", "Transform", {"Input": I(link=src), "Center": I((0.5, 0.5), f"Point({cx}, {cy})"),
                                        "Size": I(1, f"1 + {w}*0.006")}, pos=(pos_x, 0)),
        Tool(f"{p}Respira", "BrightnessContrast", {
            "Input": I(link=f"{p}Weave"),
            "Gain": I(1, f"1 + {r}*0.025*sin({t}*7.3)*sin({t}*3.1 + 1)"),
            "Saturation": I(1, f"1 + {r}*0.03*sin({t}*5.7 + 2)*sin({t}*2.3)")}, pos=(pos_x + 55, 0)),
    ], f"{p}Respira"


def blk_grain(p, src, blend_expr, pos_x, scale=40):
    return [Tool(f"{p}Ruido", "FastNoise", {**frame_format(), "Detail": I(4), "Contrast": I(1.5), "XScale": I(scale),
                                            "SeetheRate": I(1), "Discontinuous": I(1)}, pos=(pos_x, 66)),
            merge(f"{p}Grano", src, f"{p}Ruido", (pos_x + 55, 0), "Overlay", blend=0.1, blend_expr=blend_expr)], f"{p}Grano"


def blk_dust_scratch(p, src, host, pos_x):
    """Polvo (motas oscuras que cambian cada fotograma) y rayas verticales intermitentes."""
    t = "time"
    return [
        Tool(f"{p}Motas", "FastNoise", {**frame_format(), "Detail": I(8), "Contrast": I(2), "XScale": I(25),
                                        "SeetheRate": I(3), "Discontinuous": I(1)}, pos=(pos_x, 99)),
        Tool(f"{p}Umbral", "BrightnessContrast", {"Input": I(link=f"{p}Motas"), "Low": I(0.93), "High": I(1),
                                                  "Saturation": I(0)}, pos=(pos_x + 55, 99)),
        solid(f"{p}Blanco", (1, 1, 1), (pos_x + 55, 132)),
        merge(f"{p}Invertir", f"{p}Blanco", f"{p}Umbral", (pos_x + 110, 99), "Difference"),
        merge(f"{p}Polvo", src, f"{p}Invertir", (pos_x + 165, 0), "Multiply", blend=0.6, blend_expr=f"{host}.Polvo"),
        Tool(f"{p}Linea", "RectangleMask", {**mask_format(), "Width": I(0.0015), "Height": I(3), "SoftEdge": I(0.001),
                                            "Center": I((0.5, 0.5), f"Point(0.5 + 0.35*sin({t}*0.13)*sin({t}*0.071 + 1), 0.5)")},
             pos=(pos_x + 165, -99)),
        solid(f"{p}Raya", (0.95, 0.95, 0.9), (pos_x + 165, -66), mask=f"{p}Linea"),
        merge(f"{p}Rayas", f"{p}Polvo", f"{p}Raya", (pos_x + 220, 0), blend=0,
              blend_expr=f"{host}.Rayas*max(0, sin({t}*0.05))*max(0, sin({t}*0.05))"),
    ], f"{p}Rayas"


@register("Effects", "PRO_FX_Film_Proyector")
def film_proyector(name, anim):
    h = "Proyector"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0))]
    t, last = blk_weave_breath("Mec", "Entrada", h, -330)
    tools += t
    t, last = blk_dust_scratch("Dano", last, h, -165)
    tools += t
    ucs = [uc("Weave", "Gate weave (vaivén)", 1, 0, 5), uc("Respiracion", "Respiración (parpadeo)", 1, 0, 5),
           uc("Polvo", "Polvo", 0.6, 0, 1), uc("Rayas", "Rayas", 0.4, 0, 1),
           uc("EscalaFormato", "Escala interna", 1, 0, 10, clamp=False)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Weave": I(1), "Respiracion": I(1),
                                                "Polvo": I(0.6), "Rayas": I(0.4), "EscalaFormato": I(1)}, ucs, (110, 0)))
    pubs = [pub(h, "Weave", "Gate weave (vaivén)", 1), pub(h, "Respiracion", "Respiración (parpadeo)", 1),
            pub(h, "Polvo", "Polvo", 0.6), pub(h, "Rayas", "Rayas", 0.4)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Film_Completo")
def film_completo(name, anim):
    """Pila de emulacion de pelicula estilo Dehancer, con 'Formato (mm)' que escala grano/weave/respiracion."""
    h = "Pelicula"
    tools = [Tool("Entrada", "PipeRouter", pos=(-550, 0))]
    t, last = blk_weave_breath("Mec", "Entrada", h, -440)
    tools += t
    tools += [Tool("HalAltas", "BrightnessContrast", {"Input": I(link=last), "Low": I(0.75), "High": I(1),
                                                       "Saturation": I(0.6)}, pos=(-330, -66)),
              Tool("HalBlur", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(30),
                                       "Input": I(link="HalAltas")}, pos=(-275, -66)),
              solid("HalColor", (1, 0.25, 0.08), (-275, -99)),
              merge("HalTenido", "HalBlur", "HalColor", (-220, -66), "Multiply"),
              merge("Halation", last, "HalTenido", (-165, 0), "Screen", blend=0.3, blend_expr=f"{h}.Halation")]
    t, last = blk_bloom("Bl", "Halation", -110, low=0.6, radius=60, blend=0.2)
    tools += t
    tools[-1].inputs["Blend"] = I(0.2, f"{h}.Bloom")
    t, last = blk_grain("Gr", last, f"{h}.Grano*{h}.EscalaGrano", 110)
    tools += t
    t, last = blk_vignette("Vin", last, 220, amount=0.25)
    tools += t
    tools[-1].inputs["Blend"] = I(0.25, f"{h}.Vineta")
    ucs = [uc("Formato", "Formato (mm): 8 / 16 / 35 / 65", 35, 8, 65),
           uc("Grano", "Grano", 0.1, 0, 0.5), uc("Halation", "Halation", 0.3, 0, 1), uc("Bloom", "Bloom", 0.2, 0, 1),
           uc("Weave", "Gate weave", 1, 0, 5), uc("Respiracion", "Respiración", 1, 0, 5), uc("Vineta", "Viñeta", 0.25, 0, 1),
           uc("EscalaFormato", "Escala interna formato", 1, 0, 10, clamp=False),
           uc("EscalaGrano", "Escala interna grano", 1, 0, 10, clamp=False)]
    tools.append(Tool(h, "BrightnessContrast", {
        "Input": I(link=last), "Formato": I(35), "Grano": I(0.1), "Halation": I(0.3), "Bloom": I(0.2),
        "Weave": I(1), "Respiracion": I(1), "Vineta": I(0.25),
        "EscalaFormato": I(1, f"min(4, 35/{h}.Formato)"),
        "EscalaGrano": I(1, f"min(2.5, 0.4 + 0.6*35/{h}.Formato)")}, ucs, (330, 0)))
    pubs = [pub(h, "Formato", "Formato (mm): 8 / 16 / 35 / 65", 35), pub(h, "Grano", "Grano", 0.1),
            pub(h, "Halation", "Halation", 0.3), pub_color("HalColor", "Color de halation", (1, 0.25, 0.08), 4),
            pub(h, "Bloom", "Bloom", 0.2), pub(h, "Weave", "Gate weave", 1), pub(h, "Respiracion", "Respiración", 1),
            pub(h, "Vineta", "Viñeta", 0.25)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Lente_Flare")
def lente_flare(name, anim):
    """Destello de lente procedural: nucleo + raya + fantasmas alineados a traves del centro (estilo Sapphire)."""
    n = "Nucleo"

    def along(k):
        return f"Point({n}.Center.X + (0.5 - {n}.Center.X)*{k}, {n}.Center.Y + (0.5 - {n}.Center.Y)*{k})"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             solid("Base", (0, 0, 0), (-330, -198)),
             Tool(n, "EllipseMask", {**mask_format(), "Center": I((0.75, 0.75)), "Width": I(0.35), "Height": I(0.35),
                                     "SoftEdge": I(0.25)}, pos=(-330, -264)),
             solid("Luz", (1, 0.9, 0.75), (-275, -231), mask=n),
             Tool("RayaMasc", "RectangleMask", {**mask_format(), "Width": I(2.5), "Height": I(0.003), "SoftEdge": I(0.006),
                                                "Center": I((0.75, 0.75), f"Point({n}.Center.X, {n}.Center.Y)")},
                  pos=(-220, -264)),
             solid("Raya", (0.5, 0.7, 1), (-220, -231), mask="RayaMasc"),
             merge("F1", "Base", "Luz", (-275, -198), "Screen"),
             merge("F2", "F1", "Raya", (-220, -198), "Screen", blend=0.8)]
    ghosts = [(0.6, 0.08, (0.3, 0.8, 0.5)), (1.3, 0.05, (0.6, 0.4, 1)), (1.7, 0.14, (1, 0.6, 0.3)), (2.2, 0.22, (0.3, 0.5, 1))]
    last = "F2"
    for i, (k, size, col) in enumerate(ghosts, 1):
        x = -165 + 55 * i
        tools += [Tool(f"G{i}Masc", "EllipseMask", {**mask_format(), "Center": I((0.5, 0.5), along(k)),
                                                    "Width": I(size), "Height": I(size), "SoftEdge": I(size * 0.4)},
                       pos=(x, -264)),
                  solid(f"G{i}", col, (x, -231), mask=f"G{i}Masc"),
                  merge(f"F{i + 2}", last, f"G{i}", (x, -198), "Screen", blend=0.35)]
        last = f"F{i + 2}"
    tools.append(merge("Destello", "Entrada", last, (110, 0), "Screen", blend=0.8))
    pubs = [pub(n, "Center", "Posición del destello (animable)"), pub("Destello", "Blend", "Intensidad", 0.8),
            pub(n, "Width", "Tamaño del núcleo", 0.35), pub_color("Luz", "Color del núcleo", (1, 0.9, 0.75), 4),
            pub("F2", "Blend", "Raya anamórfica", 0.8), pub_color("Raya", "Color de la raya", (0.5, 0.7, 1), 9),
            pub("F3", "Blend", "Fantasma 1", 0.35), pub("F4", "Blend", "Fantasma 2", 0.35),
            pub("F5", "Blend", "Fantasma 3", 0.35), pub("F6", "Blend", "Fantasma 4", 0.35)]
    return macro(name, [("Entrada", "Input")], pubs, "Destello", tools)


@register("Effects", "PRO_FX_Retro_VHS")
def retro_vhs(name, anim):
    h = "VHS"
    t = "time"
    tools = [Tool("Entrada", "PipeRouter", pos=(-550, 0)),
             Tool("Temblor", "Transform", {"Input": I(link="Entrada"), "Center": I(
                 (0.5, 0.5), f"Point(0.5 + {h}.Temblor*0.0015*sin({t}*13.7)*sin({t}*5.3), 0.5)")}, pos=(-440, 0)),
             Tool("Corrido", "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0), "XBlurSize": I(10),
                                      "YBlurSize": I(0), "Input": I(link="Temblor")}, pos=(-385, -66)),
             merge("Croma", "Temblor", "Corrido", (-330, 0), "Color", blend=0.7)]
    sep = f"{h}.Separacion"
    t2, last = blk_channel_shift("Sep", "Croma", sep, "0", -275)
    tools += t2
    tools += [Tool("Cinta", "BrightnessContrast", {"Input": I(link=last), "Lift": I(0.05), "Gain": I(1.05),
                                                   "Saturation": I(1.2), "Contrast": I(0.05)}, pos=(0, 0))]
    t2, last = blk_grain("Ru", "Cinta", None, 55, scale=60)
    tools += t2
    tools[-1].inputs["Blend"] = I(0.15)
    tools += [Tool("BandaMasc", "RectangleMask", {**mask_format(), "Width": I(3), "Height": I(0.05), "SoftEdge": I(0.03),
                                                  "Center": I((0.5, 0.5), f"Point(0.5, 0.5 + 0.6*sin({t}*0.02*{h}.VelBanda))")},
                   pos=(165, -99)),
              Tool("BandaDesp", "Transform", {"Input": I(link=last), "Center": I((0.51, 0.5))}, pos=(165, -66)),
              Tool("BandaLuz", "BrightnessContrast", {"Input": I(link="BandaDesp"), "Gain": I(1.3)}, pos=(220, -66)),
              merge("Banda", last, "BandaLuz", (275, 0), blend=0.8,
                    extra={"EffectMask": I(link="BandaMasc", out="Mask")})]
    ucs = [uc("Temblor", "Temblor horizontal", 1, 0, 5), uc("Separacion", "Separación de color", 0.003, 0, 0.02),
           uc("VelBanda", "Velocidad de la banda", 1, 0, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Banda"), "Temblor": I(1), "Separacion": I(0.003),
                                                "VelBanda": I(1)}, ucs, (385, 0)))
    pubs = [pub(h, "Temblor", "Temblor horizontal", 1), pub(h, "Separacion", "Separación de color", 0.003),
            pub("Croma", "Blend", "Corrimiento de color", 0.7), pub("RuGrano", "Blend", "Ruido", 0.15),
            pub("Banda", "Blend", "Banda de tracking", 0.8), pub(h, "VelBanda", "Velocidad de la banda", 1),
            pub("Cinta", "Saturation", "Saturación", 1.2)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Transitions", "PRO_TR_Glitch")
def tr_glitch(name, anim):
    h = "Mezcla"
    p, t = f"{h}.Progreso", "time"
    bell = f"sin({p}*{PI})*sin({p}*{PI})"
    mix = clamp01(f"2*{p} - 0.5 + 0.8*sin({t}*5.1)*sin({t}*2.3 + 1)*sin({p}*{PI})")
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Glitch", "Intensidad del glitch", 1, 0, 3)]
    tools = [Tool(h, "Dissolve", {"Mix": I(0, mix), "Progreso": I(link=anim, out="Value"), "Glitch": I(1)}, ucs, (0, 0))]
    t2, last = blk_channel_shift("Sep", h, f"{h}.Glitch*0.012*{bell}", "0", 55)
    tools += t2
    for i, (y, spd, off) in enumerate(((0.3, 3.3, 0.06), (0.7, 4.7, -0.08)), 1):
        tools += [Tool(f"Corte{i}Masc", "RectangleMask", {**mask_format(), "Width": I(3), "Height": I(0.07),
                                                         "Center": I((0.5, y), f"Point(0.5, {y} + 0.25*sin({t}*{spd}))")},
                       pos=(330, -99 - 33 * i)),
                  Tool(f"Corte{i}Desp", "Transform", {"Input": I(link=last), "Center": I(
                      (0.5, 0.5), f"Point(0.5 + {h}.Glitch*{off}*{bell}*sin({t}*7.7 + {i}), 0.5)")}, pos=(330, -66 * i)),
                  merge(f"Corte{i}", last, f"Corte{i}Desp", (385 + 55 * i, 0), blend=1,
                        extra={"EffectMask": I(link=f"Corte{i}Masc", out="Mask")})]
        last = f"Corte{i}"
    pubs = [pub(h, "Glitch", "Intensidad del glitch", 1)]
    return macro(name, [(h, "Background"), (h, "Foreground")], pubs, last, tools, anim)


@register("Transitions", "PRO_TR_FilmBurn")
def tr_filmburn(name, anim):
    h = "Mezcla"
    p = f"{h}.Progreso"
    bell = f"sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Quemado", "Intensidad del quemado", 1, 0, 2)]
    tools = [Tool(h, "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.35)/0.3"))),
                                  "Progreso": I(link=anim, out="Value"), "Quemado": I(1)}, ucs, (0, 0)),
             Tool("Sobreexpo", "BrightnessContrast", {"Input": I(link=h),
                                                      "Gain": I(1, f"1 + 1.5*{h}.Quemado*{bell}*{bell}")}, pos=(55, 0)),
             Tool("QuemaMasc", "EllipseMask", {**mask_format(), "Center": I((0.3, 0.4)), "SoftEdge": I(0.8),
                                               "Width": I(0.2, f"0.2 + 2.5*{bell}"), "Height": I(0.2, f"0.2 + 2.0*{bell}")},
                  pos=(110, -99)),
             solid("QuemaColor", (1, 0.45, 0.12), (110, -66), mask="QuemaMasc"),
             Tool("NucleoMasc", "EllipseMask", {**mask_format(), "SoftEdge": I(0.5),
                                                "Center": I((0.3, 0.4), "Point(QuemaMasc.Center.X, QuemaMasc.Center.Y)"),
                                                "Width": I(0.1, f"0.1 + 1.2*{bell}*{bell}"), "Height": I(0.1, f"0.1 + 1.0*{bell}*{bell}")},
                  pos=(165, -99)),
             solid("NucleoColor", (1, 0.92, 0.75), (165, -66), mask="NucleoMasc"),
             merge("Quemado1", "Sobreexpo", "QuemaColor", (165, 0), "Screen", blend=0, blend_expr=f"{h}.Quemado*{bell}"),
             merge("Quemado2", "Quemado1", "NucleoColor", (220, 0), "Screen", blend=0, blend_expr=f"{h}.Quemado*{bell}*{bell}")]
    pubs = [pub(h, "Quemado", "Intensidad del quemado", 1), pub("QuemaMasc", "Center", "Origen del quemado"),
            pub_color("QuemaColor", "Color del quemado", (1, 0.45, 0.12), 3)]
    return macro(name, [(h, "Background"), (h, "Foreground")], pubs, "Quemado2", tools, anim)


# ======================================================================= TRANSICIONES DE CINTA (lote 5)
def film_host(h, anim, pos, extra_ucs=(), extra_inputs=None, danos=1.0):
    """Herramienta final que aloja Progreso y los danos de pelicula, escalados por una campana (maximo a mitad)."""
    bell = f"sin({h}.Progreso*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Danos", "Daños de película", danos, 0, 3), *extra_ucs,
           uc("Polvo", "Polvo interno", 0, 0, 1, clamp=False), uc("Rayas", "Rayas internas", 0, 0, 1, clamp=False),
           uc("Weave", "Weave interno", 0, 0, 10, clamp=False), uc("Respiracion", "Respiración interna", 0, 0, 10, clamp=False),
           uc("EscalaFormato", "Escala interna", 1, 0, 10, clamp=False)]
    inputs = {"Progreso": I(link=anim, out="Value"), "Danos": I(danos),
              "Polvo": I(0, f"min(1, 0.8*{h}.Danos*{bell})"), "Rayas": I(0, f"min(1, 0.7*{h}.Danos*{bell})"),
              "Weave": I(0, f"3*{h}.Danos*{bell}"), "Respiracion": I(0, f"4*{h}.Danos*{bell}"),
              "EscalaFormato": I(1)}
    inputs.update(extra_inputs or {})
    return ucs, inputs


@register("Transitions", "PRO_TR_SaltoCinta")
def tr_salto_cinta(name, anim):
    """El fotograma se 'escapa' en el proyector: A sube, aparece la linea negra entre fotogramas y entra B."""
    h = "Pelicula"
    p = f"{h}.Progreso"
    env, gap, d = smooth(p), f"(1 + {h}.Linea)", f"{h}.Direccion"
    bell = f"sin({p}*{PI})"
    tools = [Tool("Saliente", "Transform", {"Center": I((0.5, 0.5), f"Point(0.5, 0.5 + {d}*{env}*{gap})")}, pos=(-330, -33)),
             Tool("Entrante", "Transform", {"Center": I((0.5, 0.5), f"Point(0.5, 0.5 - {d}*(1 - {env})*{gap})")}, pos=(-330, 33)),
             solid("Negro", (0, 0, 0), (-275, -99)),
             merge("ConA", "Negro", "Saliente", (-220, 0)),
             merge("ConB", "ConA", "Entrante", (-165, 0)),
             Tool("Arrastre", "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0), "XBlurSize": I(0),
                                       "YBlurSize": I(0, f"{h}.Desenfoque*{bell}*{bell}"), "Input": I(link="ConB")}, pos=(-110, 0)),
             Tool("Parpadeo", "BrightnessContrast", {"Input": I(link="Arrastre"),
                                                     "Gain": I(1, f"1 + 0.5*{h}.Danos*{bell}*sin(time*9.1)*sin(time*3.7 + 1)")}, pos=(-55, 0))]
    t, last = blk_dust_scratch("Dano", "Parpadeo", h, 0)
    tools += t
    ucs, inputs = film_host(h, anim, (330, 0), extra_ucs=[
        uc("Linea", "Línea de fotograma", 0.08, 0, 0.3), uc("Desenfoque", "Desenfoque de arrastre", 60, 0, 200),
        uc("Direccion", "Dirección (1 arriba / -1 abajo)", 1, -1, 1, integer=True)],
        extra_inputs={"Linea": I(0.08), "Desenfoque": I(60), "Direccion": I(1)})
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), **inputs}, ucs, (330, 0)))
    pubs = [pub(h, "Linea", "Línea de fotograma", 0.08), pub(h, "Desenfoque", "Desenfoque de arrastre", 60),
            pub(h, "Direccion", "Dirección (1 arriba / -1 abajo)", 1), pub(h, "Danos", "Daños de película", 1)]
    return macro(name, [("Saliente", "Input"), ("Entrante", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_CintaPelicula")
def tr_cinta_pelicula(name, anim):
    """La imagen se aleja y se ve la tira de pelicula con perforaciones, que avanza un fotograma."""
    h = "Pelicula"
    p = f"{h}.Progreso"
    bell = f"sin({p}*{PI})"
    s = f"{h}.Escala"
    env = smooth(p)
    gap = "1.08"
    tools = [Tool("Saliente", "Transform", {"Size": I(1, s), "Center": I((0.5, 0.5), f"Point(0.5, 0.5 + {env}*{gap}*{s})")}, pos=(-440, -33)),
             Tool("Entrante", "Transform", {"Size": I(1, s), "Center": I((0.5, 0.5), f"Point(0.5, 0.5 - (1 - {env})*{gap}*{s})")}, pos=(-440, 33)),
             solid("Negro", (0, 0, 0), (-385, -132))]
    # perforaciones: dos cadenas de mascaras (izquierda / derecha) que avanzan con la pelicula
    offsets = [round(-1.28 + 0.16 * i, 2) for i in range(17)]
    for side, sx in (("Izq", -0.56), ("Der", 0.56)):
        prev = None
        for i, c in enumerate(offsets):
            mname = f"Perf{side}{i}"
            inputs = {**mask_format(), "CornerRadius": I(0.3),
                      "Center": I((0.5, 0.5), f"Point(0.5 + {sx}*{s}, 0.5 + {s}*({c} + {env}*{gap}))"),
                      "Width": I(0.035, f"0.035*{s}"), "Height": I(0.05, f"0.05*{s}")}
            if prev:
                inputs["EffectMask"] = I(link=prev, out="Mask")
            tools.append(Tool(mname, "RectangleMask", inputs, pos=(-385 + 11 * i, -231 if side == "Izq" else -198)))
            prev = mname
        tools.append(solid(f"Luz{side}", (0.92, 0.88, 0.78), (-220, -165 if side == "Izq" else -132), mask=prev))
    tools += [merge("ConPerfI", "Negro", "LuzIzq", (-165, -99)),
              merge("ConPerfD", "ConPerfI", "LuzDer", (-110, -99)),
              merge("ConA", "ConPerfD", "Saliente", (-55, 0)),
              merge("ConB", "ConA", "Entrante", (0, 0)),
              Tool("Parpadeo", "BrightnessContrast", {"Input": I(link="ConB"),
                                                      "Gain": I(1, f"1 + 0.4*{h}.Danos*{bell}*sin(time*9.1)*sin(time*3.7 + 1)")}, pos=(55, 0))]
    t, last = blk_dust_scratch("Dano", "Parpadeo", h, 110)
    tools += t
    ucs, inputs = film_host(h, anim, (440, 0), extra_ucs=[
        uc("Alejamiento", "Alejamiento", 0.3, 0, 0.6), uc("Escala", "Escala interna", 1, 0, 2, clamp=False)],
        extra_inputs={"Alejamiento": I(0.3), "Escala": I(1, f"1 - {h}.Alejamiento*{bell}")})
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), **inputs}, ucs, (440, 0)))
    pubs = [pub(h, "Alejamiento", "Alejamiento", 0.3), pub(h, "Danos", "Daños de película", 1),
            pub_color("LuzIzq", "Color de la luz en perforaciones", (0.92, 0.88, 0.78), 3)]
    return macro(name, [("Saliente", "Input"), ("Entrante", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_QuemaOrganica")
def tr_quema_organica(name, anim):
    """Quemado con formas organicas (ruido umbralizado) + sobreexposicion + danos y vaiven de pelicula."""
    h = "Pelicula"
    p = f"{h}.Progreso"
    bell = f"sin({p}*{PI})"
    q = f"{h}.Quemado"
    tools = [Tool("Mezcla", "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.4)/0.2")))}, pos=(-440, 0))]
    t, last = blk_weave_breath("Mec", "Mezcla", h, -385)
    tools += t
    tools += [Tool("Expo", "BrightnessContrast", {"Input": I(link=last), "Gain": I(1, f"1 + 1.2*{q}*{bell}*{bell}")}, pos=(-275, 0)),
              Tool("Fuego", "FastNoise", {**frame_format(), "Detail": I(6), "Contrast": I(1.6), "XScale": I(2.5),
                                          "SeetheRate": I(0.03)}, pos=(-275, -132)),
              Tool("Borde", "BrightnessContrast", {"Input": I(link="Fuego"), "Saturation": I(0),
                                                   "Low": I(1, f"1 - 0.9*{q}*{bell}"), "High": I(1.08, "Borde.Low + 0.08")}, pos=(-220, -132)),
              Tool("BordeBlur", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(12), "Input": I(link="Borde")}, pos=(-165, -132)),
              solid("ColorFuego", (1, 0.42, 0.1), (-165, -165)),
              merge("FuegoTenido", "BordeBlur", "ColorFuego", (-110, -132), "Multiply"),
              Tool("Nucleo", "BrightnessContrast", {"Input": I(link="Fuego"), "Saturation": I(0),
                                                    "Low": I(1, f"1 - 0.7*{q}*{bell}*{bell}"), "High": I(1.05, "Nucleo.Low + 0.05")}, pos=(-220, -66)),
              solid("ColorNucleo", (1, 0.93, 0.78), (-165, -33)),
              merge("NucleoTenido", "Nucleo", "ColorNucleo", (-110, -66), "Multiply"),
              merge("Quema1", "Expo", "FuegoTenido", (-55, 0), "Screen"),
              merge("Quema2", "Quema1", "NucleoTenido", (0, 0), "Screen")]
    t, last = blk_dust_scratch("Dano", "Quema2", h, 55)
    tools += t
    ucs, inputs = film_host(h, anim, (385, 0), extra_ucs=[uc("Quemado", "Intensidad del quemado", 1, 0, 1.5)],
                            extra_inputs={"Quemado": I(1)})
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), **inputs}, ucs, (385, 0)))
    pubs = [pub(h, "Quemado", "Intensidad del quemado", 1), pub(h, "Danos", "Daños de película", 1),
            pub_color("ColorFuego", "Color del borde quemado", (1, 0.42, 0.1), 3),
            pub("Fuego", "XScale", "Tamaño de las manchas (más alto = más pequeñas)", 2.5)]
    return macro(name, [("Mezcla", "Background"), ("Mezcla", "Foreground")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_FlashFotogramas")
def tr_flash_fotogramas(name, anim):
    """Final de rollo: parpadeo rapido entre A y B, fotogramas sobreexpuestos, saltos y danos."""
    h = "Pelicula"
    p = f"{h}.Progreso"
    bell = f"sin({p}*{PI})"
    mix = clamp01(f"({p} - 0.5)*8 + 3*sin(time*2.9)*sin(time*1.7 + 1)*{bell}")
    tools = [Tool("Mezcla", "Dissolve", {"Mix": I(0, mix)}, pos=(-385, 0)),
             Tool("Salto", "Transform", {"Input": I(link="Mezcla"), "Center": I(
                 (0.5, 0.5), f"Point(0.5, 0.5 + {h}.Saltos*0.04*{bell}*sin(time*3.7)*sin(time*1.9 + 2))"),
                 "Size": I(1, f"1 + {h}.Saltos*0.04*{bell}")}, pos=(-330, 0)),
             Tool("Destellos", "BrightnessContrast", {"Input": I(link="Salto"), "Gain": I(
                 1, f"1 + {h}.Flashes*{bell}*6*max(0, sin(time*4.1)*sin(time*1.3 + 2))")}, pos=(-275, 0))]
    t, last = blk_weave_breath("Mec", "Destellos", h, -220)
    tools += t
    t, last = blk_dust_scratch("Dano", last, h, -110)
    tools += t
    ucs, inputs = film_host(h, anim, (220, 0), extra_ucs=[
        uc("Flashes", "Destellos", 1, 0, 2), uc("Saltos", "Saltos de fotograma", 1, 0, 3)],
        extra_inputs={"Flashes": I(1), "Saltos": I(1)})
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), **inputs}, ucs, (220, 0)))
    pubs = [pub(h, "Flashes", "Destellos", 1), pub(h, "Saltos", "Saltos de fotograma", 1),
            pub(h, "Danos", "Daños de película", 1)]
    return macro(name, [("Mezcla", "Background"), ("Mezcla", "Foreground")], pubs, h, tools, anim)


# ======================================================================= REELS / SOCIAL (lote 6)
def ease_back(t, host):
    """easeOutBack con 'Rebote' (0 = easeOutCubic sin rebote)."""
    c = f"(1.70158*{host}.Rebote)"
    return f"(1 + ({c} + 1)*({t} - 1)*({t} - 1)*({t} - 1) + {c}*({t} - 1)*({t} - 1))"


def pingpong_bg(name, end_expr, pos, stops=((0, (0, 0, 0, 1)), (1, (1, 1, 1, 1)))):
    """Gradiente lineal repetido en ping-pong (onda triangular 0..1) desde el centro."""
    from fusion_builder import gradient
    return Tool(name, "Background", {**frame_format(), "Type": I(FuID("Gradient")), "Repeat": I(FuID("Ping-Pong")),
                                     "Start": I((0.5, 0.5)), "End": I((0.5, 0.55), end_expr),
                                     "Gradient": I(gradient(stops))}, pos=pos)


@register("Effects", "PRO_FX_Social_SombraLarga")
def sombra_larga(name, anim):
    """Sombra larga direccional para PNG recortados (estilo 'deep shadow')."""
    h = "Sombra"
    a = f"{h}.Angulo*{PI}/180"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Silueta", "BrightnessContrast", {"Input": I(link="Entrada"), "Gain": I(0)}, pos=(-385, -66)),
             solid("Vacio", (0, 0, 0), (-330, -132), alpha=0)]
    last = "Vacio"
    n = 6
    for k in range(1, n + 1):
        f = k / n
        tools += [Tool(f"Paso{k}", "Transform", {"Input": I(link="Silueta"), "Center": I(
                      (0.5, 0.5), f"Point(0.5 + {h}.Distancia*{f:g}*sin({a} + 1.5707963)/{h}.Aspecto, 0.5 + {h}.Distancia*{f:g}*sin({a}))")},
                       pos=(-330 + 33 * k, -99)),
                  merge(f"Capa{k}", last, f"Paso{k}", (-330 + 33 * k, -66), blend=1,
                        blend_expr=f"max(0, 1 - {h}.Decaimiento*{f:g})")]
        last = f"Capa{k}"
    tools += [Tool("Suaviza", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(6), "Input": I(link=last)}, pos=(0, -66)),
              merge("Opacidad", "Vacio", "Suaviza", (55, -66), blend=0.6)]
    ucs = [uc("Angulo", "Ángulo (grados)", -45, -180, 180), uc("Distancia", "Longitud", 0.08, 0, 0.5),
           uc("Decaimiento", "Decaimiento", 0.7, 0, 1), uc("Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625, 0.4, 3)]
    tools.append(merge(h, "Opacidad", "Entrada", (110, 0), ucs=ucs, extra={
        "Angulo": I(-45), "Distancia": I(0.08), "Decaimiento": I(0.7), "Aspecto": I(0.5625)}))
    pubs = [pub(h, "Angulo", "Ángulo (grados)", -45), pub(h, "Distancia", "Longitud", 0.08),
            pub(h, "Decaimiento", "Decaimiento", 0.7), pub("Opacidad", "Blend", "Opacidad", 0.6),
            pub("Suaviza", "XBlurSize", "Suavidad", 6), pub(h, "Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Social_Halftone")
def halftone(name, anim):
    """Trama de puntos: los puntos crecen donde la imagen es oscura."""
    h = "Trama"
    cell = f"{h}.Tamano"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Luma", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(0), "Contrast": I(0.1)}, pos=(-385, -66)),
             pingpong_bg("OndaX", f"Point(0.5 + {cell}/2/{h}.Aspecto, 0.5)", (-385, -165)),
             pingpong_bg("OndaY", f"Point(0.5, 0.5 + {cell}/2)", (-330, -165)),
             merge("Puntos", "OndaX", "OndaY", (-330, -132), "Multiply"),
             solid("Blanco", (1, 1, 1), (-275, -198)),
             merge("PuntosInv", "Blanco", "Puntos", (-275, -132), "Difference"),
             merge("Suma", "Luma", "PuntosInv", (-220, -66), extra={"SubtractiveAdditive": I(0)}),
             Tool("Binario", "BrightnessContrast", {"Input": I(link="Suma"), "Low": I(0.97), "High": I(1.03)}, pos=(-165, -66)),
             Tool("Color", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(1)}, pos=(-165, 0))]
    ucs = [uc("Tamano", "Tamaño de la trama", 0.012, 0.003, 0.05), uc("Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625, 0.4, 3)]
    tools.append(merge(h, "Color", "Binario", (-110, 0), "Multiply", blend=1, ucs=ucs,
                       extra={"Tamano": I(0.012), "Aspecto": I(0.5625)}))
    pubs = [pub(h, "Tamano", "Tamaño de la trama", 0.012), pub(h, "Blend", "Intensidad", 1),
            pub("Color", "Saturation", "Saturación (0 = blanco y negro)", 1),
            pub("Binario", "Low", "Umbral", 0.97), pub(h, "Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Anim_Flow")
def anim_flow(name, anim):
    """Animacion de entrada/salida para PNG y clips: desplazamiento, zoom, giro, rebote, desenfoque y fundido."""
    h = "Anim"
    p = f"{h}.Progreso"
    t_in = clamp01(f"{p}/{h}.Duracion")
    t_out = clamp01(f"(1 - {p})/{h}.Duracion")
    a = f"{h}.Direccion*{PI}/180"
    inv = f"(1 - {h}.E)"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1),
           uc("Salida", "Modo salida (desmarcado = entrada)", 0, 0, 1, checkbox=True),
           uc("Duracion", "Duración (% del clip)", 0.25, 0.02, 1),
           uc("Direccion", "Dirección (grados, 180 = desde la izquierda)", 180, -180, 180),
           uc("Distancia", "Distancia", 0.6, 0, 2), uc("Zoom", "Zoom (-1 = pop desde 0)", 0, -1, 2),
           uc("Giro", "Giro (grados)", 0, -180, 180), uc("Rebote", "Rebote", 1, 0, 3),
           uc("Fundido", "Fundido", 0, 0, 1), uc("Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625, 0.4, 3),
           uc("T", "t interno", 0, 0, 1, clamp=False), uc("E", "Curva interna", 1, -1, 2, clamp=False)]
    tools = [Tool("Mover", "Transform", {
                 "Center": I((0.5, 0.5), f"Point(0.5 + {h}.Distancia*sin({a} + 1.5707963)/{h}.Aspecto*{inv}, 0.5 + {h}.Distancia*sin({a})*{inv})"),
                 "Size": I(1, f"max(0, 1 + {h}.Zoom*{inv})"), "Angle": I(0, f"{h}.Giro*{inv}")}, pos=(-220, 0)),
             Tool("Estela", "Blur", {"Filter": I(FuID("Fast Gaussian")), "Input": I(link="Mover"),
                                     "XBlurSize": I(0, f"{h}.Desenfoque*max(0, {inv})")}, pos=(-110, 0)),
             solid("Vacio", (0, 0, 0), (-110, -66), alpha=0)]
    ucs.insert(9, uc("Desenfoque", "Desenfoque de movimiento", 15, 0, 100))
    tools.append(merge(h, "Vacio", "Estela", (0, 0), blend=1,
                       blend_expr=f"1 - {h}.Fundido*(1 - min(1, 2*{h}.T))", ucs=ucs, extra={
        "Progreso": I(link=anim, out="Value"), "Salida": I(0), "Duracion": I(0.25), "Direccion": I(180),
        "Distancia": I(0.6), "Zoom": I(0), "Giro": I(0), "Rebote": I(1), "Fundido": I(0), "Desenfoque": I(15),
        "Aspecto": I(0.5625),
        "T": I(0, f"(1 - {h}.Salida)*{t_in} + {h}.Salida*{t_out}"),
        "E": I(1, ease_back(f"{h}.T", h))}))
    pubs = [pub(h, "Salida", "Modo salida (desmarcado = entrada)", 0), pub(h, "Duracion", "Duración (% del clip)", 0.25),
            pub(h, "Direccion", "Dirección (grados, 180 = desde la izquierda)", 180), pub(h, "Distancia", "Distancia", 0.6),
            pub(h, "Zoom", "Zoom (-1 = pop desde 0)", 0), pub(h, "Giro", "Giro (grados)", 0), pub(h, "Rebote", "Rebote", 1),
            pub(h, "Desenfoque", "Desenfoque de movimiento", 15), pub(h, "Fundido", "Fundido", 0),
            pub(h, "Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625)]
    return macro(name, [("Mover", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_Empuje")
def tr_empuje(name, anim):
    """Empuje entre escenas con desenfoque de movimiento y picos de glow y flash en el centro (estilo FlowShift)."""
    h = "Empuje"
    p = f"{h}.Progreso"
    env = f"{h}.Env"
    dx, dy = f"{h}.DirX", f"{h}.DirY"
    bell2 = f"sin({p}*{PI})*sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1),
           uc("DirX", "Dirección X (-1 izquierda / 1 derecha)", -1, -1, 1, integer=True),
           uc("DirY", "Dirección Y (-1 abajo / 1 arriba)", 0, -1, 1, integer=True),
           uc("Desenfoque", "Desenfoque de movimiento", 60, 0, 200), uc("Glow", "Glow", 0.5, 0, 2),
           uc("Flash", "Flash", 0.4, 0, 1),
           uc("Raw", "Curva interna", 0, 0, 1, clamp=False), uc("Env", "Curva interna suave", 0, 0, 1, clamp=False)]

    def blur(tname, pos):
        return Tool(tname, "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0),
                                    "XBlurSize": I(0, f"{h}.Desenfoque*{bell2}*{dx}*{dx}"),
                                    "YBlurSize": I(0, f"{h}.Desenfoque*{bell2}*{dy}*{dy}")}, pos=pos)
    tools = [blur("BlurA", (-330, -33)), blur("BlurB", (-330, 33)),
             Tool("MoverA", "Transform", {"Input": I(link="BlurA"), "Center": I((0.5, 0.5), f"Point(0.5 + {dx}*{env}, 0.5 + {dy}*{env})")}, pos=(-275, -33)),
             Tool("MoverB", "Transform", {"Input": I(link="BlurB"), "Center": I((0.5, 0.5), f"Point(0.5 - {dx}*(1 - {env}), 0.5 - {dy}*(1 - {env}))")}, pos=(-275, 33)),
             merge("Juntos", "MoverA", "MoverB", (-220, 0)),
             Tool("GlowAltas", "BrightnessContrast", {"Input": I(link="Juntos"), "Low": I(0.6), "High": I(1)}, pos=(-165, -66)),
             Tool("GlowBlur", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(40), "Input": I(link="GlowAltas")}, pos=(-110, -66)),
             merge("ConGlow", "Juntos", "GlowBlur", (-110, 0), "Screen", blend=0, blend_expr=f"{h}.Glow*{bell2}"),
             solid("Blanco", (1, 1, 1), (-55, -66))]
    tools.append(merge(h, "ConGlow", "Blanco", (0, 0), "Screen", blend=0, blend_expr=f"{h}.Flash*{bell2}*{bell2}", ucs=ucs, extra={
        "Progreso": I(link=anim, out="Value"), "DirX": I(-1), "DirY": I(0), "Desenfoque": I(60), "Glow": I(0.5), "Flash": I(0.4),
        "Raw": I(0, smooth(p)), "Env": I(0, smooth(f"{h}.Raw"))}))
    pubs = [pub(h, "DirX", "Dirección X (-1 izquierda / 1 derecha)", -1), pub(h, "DirY", "Dirección Y (-1 abajo / 1 arriba)", 0),
            pub(h, "Desenfoque", "Desenfoque de movimiento", 60), pub(h, "Glow", "Glow", 0.5), pub(h, "Flash", "Flash", 0.4)]
    return macro(name, [("BlurA", "Input"), ("BlurB", "Input")], pubs, h, tools, anim)


@register("Titles", "PRO_TTL_Social_AnilloGiratorio")
def anillo(name, anim):
    """Anillo de guiones que gira sin parar (fondo de producto en reels)."""
    h = "Anillo"
    n = 24
    tools = [solid("Lienzo", (0, 0, 0), (-330, 0), alpha=0)]
    prev = None
    for i in range(n):
        ai = 2 * 3.14159265 * i / n
        th = f"({ai:.5f} + time*{h}.Velocidad*0.02)"
        inputs = {**mask_format(),
                  "Center": I((0.5, 0.5), f"Point(0.5 + {h}.Radio*sin({th} + 1.5707963)/{h}.Aspecto, 0.5 + {h}.Radio*sin({th}))"),
                  "Angle": I(0, f"{th}*57.29578 + 90"),
                  "Width": I(0.03, f"{h}.Largo"), "Height": I(0.006, f"{h}.Grosor")}
        if prev:
            inputs["EffectMask"] = I(link=prev, out="Mask")
        tools.append(Tool(f"Guion{i}", "RectangleMask", inputs, pos=(-275 + 11 * i, -99)))
        prev = f"Guion{i}"
    tools += [solid("ColorAnillo", (0.1, 0.1, 0.1), (0, -66), mask=prev),
              merge("Union", "Lienzo", "ColorAnillo", (55, 0))]
    ucs = [uc("Radio", "Radio", 0.2, 0.02, 0.6), uc("Velocidad", "Velocidad (negativo = al otro lado)", 1, -10, 10),
           uc("Largo", "Largo del guion", 0.03, 0.002, 0.2), uc("Grosor", "Grosor del guion", 0.006, 0.001, 0.05),
           uc("Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625, 0.4, 3)]
    tools.append(Tool(h, "Transform", {"Input": I(link="Union"), "Radio": I(0.2), "Velocidad": I(1), "Largo": I(0.03),
                                       "Grosor": I(0.006), "Aspecto": I(0.5625)}, ucs, (110, 0)))
    pubs = [pub(h, "Radio", "Radio", 0.2), pub(h, "Velocidad", "Velocidad (negativo = al otro lado)", 1),
            pub(h, "Largo", "Largo del guion", 0.03), pub(h, "Grosor", "Grosor del guion", 0.006),
            pub_color("ColorAnillo", "Color", (0.1, 0.1, 0.1), 5), pub(h, "Center", "Posición"),
            pub(h, "Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625)]
    return macro(name, [], pubs, h, tools)


@register("Generators", "PRO_GEN_Social_Cuadricula")
def cuadricula(name, anim):
    """Fondo de papel cuadriculado que se desvanece hacia los bordes."""
    h = "Cuadricula"
    cell = f"{h}.Celda"
    tools = [pingpong_bg("LineasH", f"Point(0.5, 0.5 + {cell}/2)", (-330, -66)),
             pingpong_bg("LineasV", f"Point(0.5 + {cell}/2/{h}.Aspecto, 0.5)", (-330, 66)),
             Tool("FinoH", "BrightnessContrast", {"Input": I(link="LineasH"), "Low": I(0), "High": I(0.06, f"{h}.GrosorLinea")}, pos=(-275, -66)),
             Tool("FinoV", "BrightnessContrast", {"Input": I(link="LineasV"), "Low": I(0), "High": I(0.06, f"{h}.GrosorLinea")}, pos=(-275, 66)),
             merge("Rejilla", "FinoH", "FinoV", (-220, 0), "Multiply"),
             solid("ColorFondo", (1, 1, 1), (-220, -132)),
             solid("ColorLinea", (0.1, 0.1, 0.1), (-165, -132)),
             solid("Blanco", (1, 1, 1), (-165, 99)),
             merge("FondoTenido", "ColorFondo", "Rejilla", (-165, -66), "Multiply"),
             merge("LineasInv", "Blanco", "Rejilla", (-165, 66), "Difference"),
             merge("LineasTenidas", "LineasInv", "ColorLinea", (-110, 66), "Multiply"),
             merge("Papel", "FondoTenido", "LineasTenidas", (-55, 0), "Screen"),
             Tool("Desvanecer", "RectangleMask", {**mask_format(), "Width": I(0.9), "Height": I(0.9), "SoftEdge": I(0.15)}, pos=(0, -99)),
             merge("ConMascara", "ColorFondo", "Papel", (0, 0), blend=1, extra={"EffectMask": I(link="Desvanecer", out="Mask")})]
    ucs = [uc("Celda", "Tamaño de celda", 0.06, 0.01, 0.3), uc("GrosorLinea", "Grosor de línea", 0.06, 0.005, 0.5),
           uc("Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625, 0.4, 3)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConMascara"), "Celda": I(0.06), "GrosorLinea": I(0.06),
                                                "Aspecto": I(0.5625)}, ucs, (55, 0)))
    pubs = [pub(h, "Celda", "Tamaño de celda", 0.06), pub(h, "GrosorLinea", "Grosor de línea", 0.06),
            pub_color("ColorFondo", "Color del fondo", (1, 1, 1), 3), pub_color("ColorLinea", "Color de las líneas", (0.1, 0.1, 0.1), 6),
            pub("ConMascara", "Blend", "Intensidad de la cuadrícula", 1), pub("Desvanecer", "SoftEdge", "Desvanecido en bordes", 0.15),
            pub("Desvanecer", "Width", "Ancho visible", 0.9), pub("Desvanecer", "Height", "Alto visible", 0.9),
            pub(h, "Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625)]
    return macro(name, [], pubs, h, tools)


@register("Titles", "PRO_TTL_Social_TextoPop")
def texto_pop(name, anim):
    """Texto que entra con rebote, sube y se funde (y sale al reves). Pensado para reels."""
    h = "Pop"
    p = f"{h}.Progreso"
    t = clamp01(f"min({p}/{h}.Entrada, (1 - {p})/max({h}.Salida, 0.0001))")
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Entrada", "Duración entrada (% del clip)", 0.15, 0.01, 0.5),
           uc("Salida", "Duración salida (% del clip)", 0.1, 0, 0.5), uc("Rebote", "Rebote", 1.2, 0, 3),
           uc("T", "t interno", 1, 0, 1, clamp=False), uc("E", "Curva interna", 1, -1, 2, clamp=False)]
    tools = [solid("Lienzo", (0, 0, 0), (-220, -66), alpha=0),
             Tool("Texto", "TextPlus", {**frame_format(), "StyledText": I("TU TEXTO AQUÍ"), "Font": I("Arial"),
                                        "Style": I("Bold"), "Size": I(0.09), "Red1": I(1), "Green1": I(1), "Blue1": I(1)},
                  pos=(-220, 0)),
             Tool("Escala", "Transform", {"Input": I(link="Texto"),
                                          "Size": I(1, f"max(0, 0.6 + 0.4*{h}.E)"),
                                          "Center": I((0.5, 0.5), f"Point(0.5, 0.5 - 0.04*(1 - {h}.E))")}, pos=(-110, 0))]
    tools.append(merge(h, "Lienzo", "Escala", (0, 0), blend=1, blend_expr=f"min(1, 2*{h}.T)", ucs=ucs, extra={
        "Progreso": I(link=anim, out="Value"), "Entrada": I(0.15), "Salida": I(0.1), "Rebote": I(1.2),
        "T": I(1, t), "E": I(1, ease_back(f"{h}.T", h))}))
    tools.append(Tool("Posicion", "Transform", {"Input": I(link=h)}, pos=(110, 0)))
    pubs = [pub("Texto", "StyledText", "Texto"), pub("Texto", "Font", "Fuente", group=2), pub("Texto", "Style", group=2),
            pub("Texto", "Size", "Tamaño", 0.09), pub_color("Texto", "Color", (1, 1, 1), 5, prefix="", suffix="1"),
            pub("Posicion", "Center", "Posición"), pub(h, "Rebote", "Rebote", 1.2),
            pub(h, "Entrada", "Duración entrada (% del clip)", 0.15), pub(h, "Salida", "Duración salida (% del clip)", 0.1)]
    return macro(name, [], pubs, "Posicion", tools, anim)


# ======================================================================= GRAFICOS ANIMADOS (lote 7)
def kit(h, entrada=0.2, salida=0.12, extra_ucs=(), extra_inputs=None):
    """Controles comunes de titulos: U = avance de la entrada (0..1), Xs = factor de salida suave (1..0)."""
    p = f"{h}.Progreso"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Entrada", "Duración entrada (% del clip)", entrada, 0.01, 0.8),
           uc("Salida", "Duración salida (% del clip, 0 = sin salida)", salida, 0, 0.5), *extra_ucs,
           uc("U", "Avance interno", 1, 0, 1, clamp=False), uc("Xs", "Salida interna", 1, 0, 1, clamp=False)]
    inputs = {"Progreso": I(link="PRO_ANIM", out="Value"), "Entrada": I(entrada), "Salida": I(salida),
              "U": I(1, clamp01(f"{p}/{h}.Entrada")),
              "Xs": I(1, smooth(clamp01(f"(1 - {p})/max({h}.Salida, 0.0001)")))}
    inputs.update(extra_inputs or {})
    return ucs, inputs


def stage(h, a, b):
    """Envolvente de una fase de la entrada (de a a b, fracciones de la entrada) por la salida."""
    return f"{smooth(clamp01(f'({h}.U - {a:g})/{b - a:g}'))}*{h}.Xs"


def text_tool(name, text, size, center, pos, rgb=(1, 1, 1), font="Arial", style="Bold", left=False, extra=None):
    inputs = {**frame_format(), "Center": I(center), "StyledText": I(text), "Font": I(font), "Style": I(style),
              "Size": I(size), "Red1": I(rgb[0]), "Green1": I(rgb[1]), "Blue1": I(rgb[2])}
    if left:
        inputs["HorizontalLeftCenterRight"] = I(-1)
    inputs.update(extra or {})
    return Tool(name, "TextPlus", inputs, pos=pos)


def rect(name, pos, **kw):
    """Mascara rectangular. kw: valores I(...) para Center, Width, Height, CornerRadius, Angle, Solid, BorderWidth, SoftEdge."""
    return Tool(name, "RectangleMask", {**mask_format(), **kw}, pos=pos)


def ellipse(name, pos, **kw):
    return Tool(name, "EllipseMask", {**mask_format(), **kw}, pos=pos)


def compose(layers, base="Lienzo", x0=0):
    """Apila capas sobre el lienzo: layers = [(herramienta, expresion de opacidad o None)]."""
    tools, last = [], base
    for i, (fg, blend_expr) in enumerate(layers):
        name = f"M{i + 1}"
        tools.append(merge(name, last, fg, (x0 + 55 * i, 0), blend=1 if blend_expr else None, blend_expr=blend_expr))
        last = name
    return tools, last


def title(name, h, ucs, inputs, body, layers, pubs, x_end=440):
    """Lienzo transparente + cuerpo + capas + transform final que aloja los controles (Posicion/Escala)."""
    tools = [solid("Lienzo", (0, 0, 0), (-440, 0), alpha=0)] + body
    t, last = compose(layers, x0=110)
    tools += t
    tools.append(Tool(h, "Transform", {"Input": I(link=last), **inputs}, ucs, (x_end, 0)))
    pubs = pubs + [pub(h, "Center", "Posición"), pub(h, "Size", "Escala", 1),
                   pub(h, "Entrada", "Duración entrada (% del clip)", inputs["Entrada"].split("Value = ")[1].split(",")[0]),
                   pub(h, "Salida", "Duración salida (% del clip, 0 = sin salida)", inputs["Salida"].split("Value = ")[1].split(",")[0])]
    for p in pubs:
        if isinstance(p, dict) and isinstance(p["default"], str):
            p["default"] = float(p["default"])
    anim = "PRO" + name.split("_", 2)[-1].replace("_", "") + "Anim"
    return macro(name, [], pubs, h, tools, anim).replace('"PRO_ANIM"', f'"{anim}"')


@register("Titles", "PRO_TTL_Barra_Progreso")
def barra_progreso(name, anim):
    h = "Barra"
    p = f"{h}.Progreso"
    ucs, inputs = kit(h, 0.05, 0.03, [uc("Ancho", "Ancho total", 0.8, 0.05, 1), uc("Alto", "Grosor", 0.012, 0.002, 0.1),
                                      uc("PosY", "Altura en pantalla", 0.06, 0, 1), uc("Redondeo", "Redondeo", 0.5, 0, 1)],
                      {"Ancho": I(0.8), "Alto": I(0.012), "PosY": I(0.06), "Redondeo": I(0.5)})
    body = [rect("MascFondo", (-385, -99), Center=I((0.5, 0.06), f"Point(0.5, {h}.PosY)"), Width=I(0.8, f"{h}.Ancho"),
                 Height=I(0.012, f"{h}.Alto"), CornerRadius=I(0.5, f"{h}.Redondeo")),
            solid("Pista", (1, 1, 1), (-385, -66), alpha=0.25, mask="MascFondo"),
            rect("MascRelleno", (-330, -99), Center=I((0.5, 0.06), f"Point(0.5 - {h}.Ancho/2 + {h}.Ancho*{p}/2, {h}.PosY)"),
                 Width=I(0, f"{h}.Ancho*{p}"), Height=I(0.012, f"{h}.Alto"), CornerRadius=I(0.5, f"{h}.Redondeo")),
            solid("Relleno", (1, 0.25, 0.25), (-330, -66), mask="MascRelleno")]
    pubs = [pub_color("Pista", "Color de la pista", (1, 1, 1), 1), pub("Pista", "TopLeftAlpha", "Opacidad de la pista", 0.25),
            pub_color("Relleno", "Color del relleno", (1, 0.25, 0.25), 5), pub(h, "Ancho", "Ancho total", 0.8),
            pub(h, "Alto", "Grosor", 0.012), pub(h, "PosY", "Altura en pantalla", 0.06), pub(h, "Redondeo", "Redondeo", 0.5)]
    return title(name, h, ucs, inputs, body, [("Pista", f"{h}.Xs*{stage(h, 0, 1)}"), ("Relleno", f"{h}.Xs")], pubs)


@register("Titles", "PRO_TTL_Contador")
def contador(name, anim):
    h = "Contador"
    t = clamp01(f"{h}.Progreso/{h}.Duracion")
    e = f"(1 - (1 - {t})*(1 - {t})*(1 - {t}))"
    ucs, inputs = kit(h, 0.1, 0.1, [uc("Inicio", "Valor inicial", 0, -1e6, 1e6, clamp=False),
                                    uc("Fin", "Valor final", 1000, -1e6, 1e6, clamp=False),
                                    uc("Duracion", "Duración del conteo (% del clip)", 0.6, 0.05, 1)],
                      {"Inicio": I(0), "Fin": I(1000), "Duracion": I(0.6)})
    body = [text_tool("Numero", "0", 0.14, (0.5, 0.55), (-385, -66),
                      extra={"StyledText": I("0", f'Text(string.format("%.0f", {h}.Inicio + ({h}.Fin - {h}.Inicio)*{e}))')}),
            text_tool("Etiqueta", "SEGUIDORES", 0.04, (0.5, 0.4), (-330, -66), rgb=(0.85, 0.85, 0.85), style="Regular",
                      extra={"CharacterSpacing": I(1.3)})]
    pubs = [pub(h, "Inicio", "Valor inicial", 0), pub(h, "Fin", "Valor final", 1000),
            pub(h, "Duracion", "Duración del conteo (% del clip)", 0.6),
            pub("Numero", "Font", "Fuente del número", group=4), pub("Numero", "Style", group=4),
            pub_color("Numero", "Color del número", (1, 1, 1), 6, prefix="", suffix="1"),
            pub("Etiqueta", "StyledText", "Etiqueta"), pub_color("Etiqueta", "Color de la etiqueta", (0.85, 0.85, 0.85), 10, prefix="", suffix="1")]
    return title(name, h, ucs, inputs, body, [("Numero", stage(h, 0, 0.6)), ("Etiqueta", stage(h, 0.4, 1))], pubs)


@register("Titles", "PRO_TTL_Callout_Flecha")
def callout(name, anim):
    h = "Callout"
    a = f"{h}.Angulo*{PI}/180"
    dx, dy = f"sin({a} + 1.5707963)", f"sin({a})*{h}.Aspecto"
    sl = stage(h, 0.2, 0.7)
    ucs, inputs = kit(h, 0.3, 0.12, [uc("Angulo", "Ángulo de la línea", 35, -180, 180), uc("Largo", "Largo de la línea", 0.18, 0.02, 0.6),
                                     uc("Aspecto", "Aspecto del timeline (16:9 = 1.778)", 1.7778, 0.4, 3)],
                      {"Angulo": I(35), "Largo": I(0.18), "Aspecto": I(1.7778)})
    body = [ellipse("MascPunto", (-385, -132), Center=I((0.4, 0.4)), Width=I(0.014), Height=I(0.014)),
            ellipse("MascAro", (-330, -132), Center=I((0.4, 0.4), "Point(MascPunto.Center.X, MascPunto.Center.Y)"),
                    Width=I(0.03), Height=I(0.03), Solid=I(0), BorderWidth=I(0.002)),
            rect("MascLinea", (-275, -132), Width=I(0, f"{h}.Largo*{sl}"), Height=I(0.0025), Angle=I(35, f"{h}.Angulo"),
                 Center=I((0.5, 0.5), f"Point(MascPunto.Center.X + {dx}*{h}.Largo*{sl}/2, MascPunto.Center.Y + {dy}*{h}.Largo*{sl}/2)")),
            solid("Punto", (1, 1, 1), (-385, -99), mask="MascPunto"),
            solid("Aro", (1, 1, 1), (-330, -99), mask="MascAro"),
            solid("Linea", (1, 1, 1), (-275, -99), mask="MascLinea"),
            text_tool("Etiqueta", "Detalle importante", 0.04, (0.5, 0.5), (-220, -99), extra={
                "Center": I((0.5, 0.5), f"Point(MascPunto.Center.X + {dx}*({h}.Largo + 0.02), MascPunto.Center.Y + {dy}*({h}.Largo + 0.02) + 0.02)")})]
    pubs = [pub("MascPunto", "Center", "Punto señalado"), pub(h, "Angulo", "Ángulo de la línea", 35), pub(h, "Largo", "Largo de la línea", 0.18),
            pub("Etiqueta", "StyledText", "Texto"), pub("Etiqueta", "Size", "Tamaño del texto", 0.04),
            pub_color("Punto", "Color", (1, 1, 1), 7), pub(h, "Aspecto", "Aspecto del timeline (16:9 = 1.778)", 1.7778)]
    # el color del punto se replica en aro, linea y texto
    for tname in ("Aro", "Linea"):
        for ch in ("Red", "Green", "Blue"):
            next(t for t in body if t.name == tname).inputs[f"TopLeft{ch}"] = I(1, f"Punto.TopLeft{ch}")
    for ch in ("Red", "Green", "Blue"):
        next(t for t in body if t.name == "Etiqueta").inputs[f"{ch}1"] = I(1, f"Punto.TopLeft{ch}")
    layers = [("Punto", stage(h, 0, 0.3)), ("Aro", stage(h, 0.1, 0.4)), ("Linea", f"{h}.Xs"), ("Etiqueta", stage(h, 0.6, 1))]
    return title(name, h, ucs, inputs, body, layers, pubs)


@register("Titles", "PRO_TTL_EndScreen")
def end_screen(name, anim):
    h = "Final"
    ucs, inputs = kit(h, 0.15, 0.08)
    body = [text_tool("Titulo", "¡GRACIAS POR VER!", 0.06, (0.5, 0.86), (-385, -165)),
            rect("MascVideo1", (-385, -132), Center=I((0.28, 0.55)), Width=I(0.36), Height=I(0.2025), CornerRadius=I(0.06),
                 Solid=I(0), BorderWidth=I(0.003)),
            rect("MascVideo2", (-330, -132), Center=I((0.72, 0.55)), Width=I(0.36), Height=I(0.2025), CornerRadius=I(0.06),
                 Solid=I(0), BorderWidth=I(0.003)),
            ellipse("MascCanal", (-275, -132), Center=I((0.5, 0.2)), Width=I(0.13), Height=I(0.13), Solid=I(0), BorderWidth=I(0.003)),
            solid("Video1", (1, 1, 1), (-385, -99), mask="MascVideo1"),
            solid("Video2", (1, 1, 1), (-330, -99), mask="MascVideo2"),
            solid("Canal", (1, 1, 1), (-275, -99), mask="MascCanal"),
            text_tool("Pie", "Suscríbete para más", 0.03, (0.5, 0.07), (-220, -99), style="Regular")]
    for tname in ("Video2", "Canal"):
        for ch in ("Red", "Green", "Blue"):
            next(t for t in body if t.name == tname).inputs[f"TopLeft{ch}"] = I(1, f"Video1.TopLeft{ch}")
    pubs = [pub("Titulo", "StyledText", "Título"), pub("Pie", "StyledText", "Texto inferior"),
            pub("Titulo", "Font", "Fuente", group=3), pub("Titulo", "Style", group=3),
            pub_color("Video1", "Color de los marcos", (1, 1, 1), 5), pub_color("Titulo", "Color del texto", (1, 1, 1), 8, prefix="", suffix="1")]
    for ch in ("Red", "Green", "Blue"):
        next(t for t in body if t.name == "Pie").inputs[f"{ch}1"] = I(1, f"Titulo.{ch}1")
    layers = [("Titulo", stage(h, 0, 0.5)), ("Video1", stage(h, 0.2, 0.6)), ("Video2", stage(h, 0.35, 0.75)),
              ("Canal", stage(h, 0.5, 0.9)), ("Pie", stage(h, 0.6, 1))]
    return title(name, h, ucs, inputs, body, layers, pubs)


@register("Titles", "PRO_TTL_Suscribete")
def suscribete(name, anim):
    h = "CTA"
    p = f"{h}.Progreso"
    pulse = f"max(0, sin(({p} - 0.45)/0.1*{PI}))*min(1, max(0, ({p} - 0.45)*100))*min(1, max(0, (0.55 - {p})*100))"
    ucs, inputs = kit(h, 0.15, 0.1, [uc("Rebote", "Rebote", 1.5, 0, 3), uc("E", "Curva interna", 1, -1, 2, clamp=False)],
                      {"Rebote": I(1.5), "E": I(1, ease_back(f"{h}.U", h))})
    body = [rect("MascBoton", (-385, -132), Center=I((0.5, 0.2)), Width=I(0.26), Height=I(0.065), CornerRadius=I(1)),
            solid("Boton", (0.9, 0.1, 0.1), (-385, -99), mask="MascBoton"),
            text_tool("Texto", "SUSCRÍBETE", 0.04, (0.5, 0.2), (-330, -99), extra={"CharacterSpacing": I(1.1)}),
            merge("Pastilla", "Lienzo", "Boton", (-275, -66)),
            merge("ConTexto", "Pastilla", "Texto", (-220, -66)),
            Tool("Pop", "Transform", {"Input": I(link="ConTexto"), "Pivot": I((0.5, 0.2)), "Center": I((0.5, 0.2)),
                                      "Size": I(1, f"max(0, {h}.E*{h}.Xs*(1 - 0.12*{pulse}))")}, pos=(-165, -66))]
    pubs = [pub("Texto", "StyledText", "Texto"), pub_color("Boton", "Color del botón", (0.9, 0.1, 0.1), 2),
            pub_color("Texto", "Color del texto", (1, 1, 1), 5, prefix="", suffix="1"), pub(h, "Rebote", "Rebote", 1.5)]
    return title(name, h, ucs, inputs, body, [("Pop", None)], pubs)


@register("Titles", "PRO_TTL_Cita")
def cita(name, anim):
    h = "Cita"
    sl = stage(h, 0.3, 0.8)
    ucs, inputs = kit(h, 0.25, 0.12)
    body = [text_tool("Comillas", "“", 0.25, (0.5, 0.72), (-385, -132), rgb=(0.95, 0.75, 0.3), font="Georgia"),
            text_tool("Frase", "La creatividad es la inteligencia\ndivirtiéndose.", 0.05, (0.5, 0.52), (-330, -132),
                      font="Georgia", style="Italic"),
            rect("MascRaya", (-275, -165), Center=I((0.5, 0.38)), Width=I(0, f"0.12*{sl}"), Height=I(0.002)),
            solid("Raya", (0.95, 0.75, 0.3), (-275, -132), mask="MascRaya"),
            text_tool("Autor", "ALBERT EINSTEIN", 0.028, (0.5, 0.33), (-220, -132), rgb=(0.8, 0.8, 0.8), style="Regular",
                      extra={"CharacterSpacing": I(1.3)})]
    for ch in ("Red", "Green", "Blue"):
        next(t for t in body if t.name == "Raya").inputs[f"TopLeft{ch}"] = I(1, f"Comillas.{ch}1")
    pubs = [pub("Frase", "StyledText", "Frase"), pub("Autor", "StyledText", "Autor"),
            pub("Frase", "Font", "Fuente de la frase", group=3), pub("Frase", "Style", group=3),
            pub("Frase", "Size", "Tamaño de la frase", 0.05),
            pub_color("Comillas", "Color de acento", (0.95, 0.75, 0.3), 6, prefix="", suffix="1")]
    layers = [("Comillas", stage(h, 0, 0.4)), ("Frase", stage(h, 0.15, 0.6)), ("Raya", f"{h}.Xs"), ("Autor", stage(h, 0.6, 1))]
    return title(name, h, ucs, inputs, body, layers, pubs)


@register("Titles", "PRO_TTL_Titulo_Apertura")
def titulo_apertura(name, anim):
    h = "Apertura"
    s_main = stage(h, 0, 1)
    sl = stage(h, 0.3, 1)
    ucs, inputs = kit(h, 0.35, 0.15, [uc("Tracking", "Separación inicial de letras", 0.4, 0, 2)], {"Tracking": I(0.4)})
    body = [text_tool("Principal", "TÍTULO DE LA PELÍCULA", 0.075, (0.5, 0.52), (-385, -132), font="Georgia", style="Regular",
                      extra={"CharacterSpacing": I(1, f"1 + {h}.Tracking*(1 - {s_main})")}),
            text_tool("Sub", "UNA HISTORIA ORIGINAL", 0.025, (0.5, 0.42), (-330, -132), rgb=(0.8, 0.8, 0.8), style="Regular",
                      extra={"CharacterSpacing": I(1.6)}),
            rect("MascSup", (-275, -165), Center=I((0.5, 0.6)), Width=I(0, f"0.3*{sl}"), Height=I(0.0015)),
            rect("MascInf", (-220, -165), Center=I((0.5, 0.385)), Width=I(0, f"0.3*{sl}"), Height=I(0.0015)),
            solid("LineaSup", (1, 1, 1), (-275, -132), alpha=0.7, mask="MascSup"),
            solid("LineaInf", (1, 1, 1), (-220, -132), alpha=0.7, mask="MascInf")]
    pubs = [pub("Principal", "StyledText", "Título"), pub("Sub", "StyledText", "Subtítulo"),
            pub("Principal", "Font", "Fuente", group=3), pub("Principal", "Style", group=3), pub("Principal", "Size", "Tamaño", 0.075),
            pub_color("Principal", "Color", (1, 1, 1), 6, prefix="", suffix="1"), pub(h, "Tracking", "Separación inicial de letras", 0.4)]
    layers = [("Principal", s_main), ("LineaSup", f"{h}.Xs"), ("LineaInf", f"{h}.Xs"), ("Sub", stage(h, 0.5, 1))]
    return title(name, h, ucs, inputs, body, layers, pubs)


@register("Titles", "PRO_TTL_Separador")
def separador(name, anim):
    h = "Separador"
    sl = stage(h, 0, 0.7)
    ucs, inputs = kit(h, 0.25, 0.12, [uc("Largo", "Largo", 0.4, 0.02, 1)], {"Largo": I(0.4)})
    body = [rect("MascLinea", (-385, -132), Center=I((0.5, 0.5)), Width=I(0, f"{h}.Largo*{sl}"), Height=I(0.0018)),
            ellipse("MascIzq", (-330, -132), Center=I((0.5, 0.5), f"Point(0.5 - {h}.Largo*{sl}/2, 0.5)"), Width=I(0.008), Height=I(0.008)),
            ellipse("MascDer", (-275, -132), Center=I((0.5, 0.5), f"Point(0.5 + {h}.Largo*{sl}/2, 0.5)"), Width=I(0.008), Height=I(0.008),
                    EffectMask=I(link="MascIzq", out="Mask")),
            solid("Linea", (1, 1, 1), (-385, -99), mask="MascLinea"),
            solid("Puntos", (1, 1, 1), (-330, -99), mask="MascDer"),
            text_tool("Texto", "CAPÍTULO UNO", 0.03, (0.5, 0.54), (-275, -99), style="Regular", extra={"CharacterSpacing": I(1.5)})]
    for ch in ("Red", "Green", "Blue"):
        next(t for t in body if t.name == "Puntos").inputs[f"TopLeft{ch}"] = I(1, f"Linea.TopLeft{ch}")
    pubs = [pub("Texto", "StyledText", "Texto (vacío = solo línea)"), pub(h, "Largo", "Largo", 0.4),
            pub_color("Linea", "Color de la línea", (1, 1, 1), 3), pub_color("Texto", "Color del texto", (1, 1, 1), 6, prefix="", suffix="1")]
    layers = [("Linea", f"{h}.Xs"), ("Puntos", stage(h, 0, 0.3)), ("Texto", stage(h, 0.5, 1))]
    return title(name, h, ucs, inputs, body, layers, pubs)


@register("Titles", "PRO_TTL_LineaTiempo")
def linea_tiempo(name, anim):
    h = "Cronologia"
    n = 5
    xs = [0.15 + 0.7 * i / (n - 1) for i in range(n)]
    years = ["1990", "2000", "2010", "2020", "2030"]
    ucs, inputs = kit(h, 0.6, 0.1)
    body = [rect("MascBase", (-385, -198), Center=I((0.5, 0.5), f"Point(0.15 + 0.35*{stage(h, 0, 0.3)}, 0.5)"),
                 Width=I(0, f"0.7*{stage(h, 0, 0.3)}"), Height=I(0.002)),
            solid("Base", (1, 1, 1), (-385, -165), alpha=0.6, mask="MascBase")]
    layers = [("Base", f"{h}.Xs")]
    for i, x in enumerate(xs, 1):
        a = 0.25 + 0.14 * (i - 1)
        body += [ellipse(f"MascHito{i}", (-330 + 44 * i, -198), Center=I((x, 0.5)), Width=I(0.014), Height=I(0.014)),
                 solid(f"Hito{i}", (1, 0.8, 0.3), (-330 + 44 * i, -165), mask=f"MascHito{i}"),
                 text_tool(f"Anio{i}", years[i - 1], 0.035, (x, 0.56), (-330 + 44 * i, -132)),
                 text_tool(f"Nota{i}", f"Evento {i}", 0.022, (x, 0.43), (-330 + 44 * i, -99), rgb=(0.8, 0.8, 0.8), style="Regular")]
        if i > 1:
            for ch in ("Red", "Green", "Blue"):
                body[-3].inputs[f"TopLeft{ch}"] = I(1, f"Hito1.TopLeft{ch}")
        layers += [(f"Hito{i}", stage(h, a, a + 0.12)), (f"Anio{i}", stage(h, a + 0.04, a + 0.18)), (f"Nota{i}", stage(h, a + 0.08, a + 0.22))]
    pubs = []
    for i in range(1, n + 1):
        pubs += [pub(f"Anio{i}", "StyledText", f"Año {i}"), pub(f"Nota{i}", "StyledText", f"Texto {i}")]
    pubs += [pub_color("Hito1", "Color de los hitos", (1, 0.8, 0.3), 30)]
    return title(name, h, ucs, inputs, body, layers, pubs, x_end=660)


# ======================================================================= GENERADORES (lote 7)
@register("Generators", "PRO_GEN_Degradado_Animado")
def degradado_animado(name, anim):
    from fusion_builder import gradient
    h = "Degradado"
    th = f"({h}.Progreso*{h}.Vueltas*6.2831853 + {h}.AnguloIni*{PI}/180)"
    tools = [Tool("Rampa", "Background", {**frame_format(), "Type": I(FuID("Gradient")),
                                          "Start": I((0, 0.5), f"Point(0.5 - 0.5*sin({th} + 1.5707963), 0.5 - 0.5*sin({th}))"),
                                          "End": I((1, 0.5), f"Point(0.5 + 0.5*sin({th} + 1.5707963), 0.5 + 0.5*sin({th}))"),
                                          "Gradient": I(gradient([(0, (0, 0, 0, 1)), (1, (1, 1, 1, 1))]))}, pos=(-330, 0)),
             solid("Blanco", (1, 1, 1), (-330, -66)),
             merge("RampaInv", "Blanco", "Rampa", (-275, -66), "Difference"),
             solid("ColorA", (0.15, 0.1, 0.35), (-275, -132)),
             solid("ColorB", (0.95, 0.35, 0.3), (-275, 66)),
             merge("ParteA", "RampaInv", "ColorA", (-220, -66), "Multiply"),
             merge("ParteB", "Rampa", "ColorB", (-220, 66), "Multiply"),
             merge("Suma", "ParteA", "ParteB", (-165, 0), extra={"SubtractiveAdditive": I(0)})]
    t, last = blk_grain("Gr", "Suma", None, -110)
    tools += t
    tools[-1].inputs["Blend"] = I(0.04)
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Vueltas", "Giro (vueltas por clip)", 0.25, -3, 3),
           uc("AnguloIni", "Ángulo inicial", 30, -180, 180)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Progreso": I(link=anim, out="Value"),
                                                "Vueltas": I(0.25), "AnguloIni": I(30)}, ucs, (0, 0)))
    pubs = [pub_color("ColorA", "Color A", (0.15, 0.1, 0.35), 1), pub_color("ColorB", "Color B", (0.95, 0.35, 0.3), 4),
            pub(h, "Vueltas", "Giro (vueltas por clip)", 0.25), pub(h, "AnguloIni", "Ángulo inicial", 30),
            pub("GrGrano", "Blend", "Textura", 0.04), pub(h, "Saturation", "Saturación", 1)]
    return macro(name, [], pubs, h, tools, anim)


@register("Generators", "PRO_GEN_Bokeh")
def bokeh(name, anim):
    import random
    rnd = random.Random(7)
    h = "Bokeh"
    v = f"{h}.Velocidad"
    tools = [solid("Fondo", (0.03, 0.03, 0.05), (-440, 0)), solid("Blanco", (1, 1, 1), (-440, -66))]
    last = "Fondo"
    for i in range(1, 15):
        x0, y0 = rnd.uniform(0.05, 0.95), rnd.uniform(0.05, 0.95)
        size = rnd.uniform(0.05, 0.16)
        s1, s2, ph = rnd.uniform(0.01, 0.03), rnd.uniform(0.01, 0.03), rnd.uniform(0, 6.28)
        col = "ColorA" if i % 2 else "ColorB"
        tools += [ellipse(f"MascC{i}", (-385 + 33 * i, -132), Width=I(size), Height=I(size), SoftEdge=I(size * 0.15),
                          Center=I((x0, y0), f"Point({x0:.3f} + 0.04*sin(time*{s1:.4f}*{v} + {ph:.2f}), {y0:.3f} + 0.03*sin(time*{s2:.4f}*{v} + {ph * 1.3:.2f}) + time*0.0004*{v})")),
                  Tool(f"C{i}", "Background", {"EffectMask": I(link=f"MascC{i}", out="Mask"), **frame_format(),
                                               "TopLeftRed": I(1, f"{col}.TopLeftRed"), "TopLeftGreen": I(1, f"{col}.TopLeftGreen"),
                                               "TopLeftBlue": I(1, f"{col}.TopLeftBlue"), "TopLeftAlpha": I(1)}, pos=(-385 + 33 * i, -99)),
                  merge(f"Suma{i}", last, f"C{i}", (-385 + 33 * i, 0), "Screen", blend=0.3,
                        blend_expr=f"{h}.Intensidad*{rnd.uniform(0.25, 0.7):.2f}")]
        last = f"Suma{i}"
    tools = tools[:2] + [solid("ColorA", (1, 0.7, 0.35), (-440, -132)), solid("ColorB", (0.45, 0.6, 1), (-440, -165))] + tools[2:]
    tools.append(Tool("Suavidad", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(4), "Input": I(link=last)}, pos=(110, 0)))
    ucs = [uc("Velocidad", "Velocidad", 1, 0, 5), uc("Intensidad", "Intensidad", 1, 0, 2)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Suavidad"), "Velocidad": I(1), "Intensidad": I(1)}, ucs, (165, 0)))
    pubs = [pub_color("Fondo", "Color de fondo", (0.03, 0.03, 0.05), 1), pub_color("ColorA", "Color de luces A", (1, 0.7, 0.35), 4),
            pub_color("ColorB", "Color de luces B", (0.45, 0.6, 1), 7), pub(h, "Intensidad", "Intensidad", 1),
            pub(h, "Velocidad", "Velocidad", 1), pub("Suavidad", "XBlurSize", "Desenfoque", 4)]
    return macro(name, [], pubs, h, tools)


# ======================================================================= EFECTOS (lote 7)
@register("Effects", "PRO_FX_Duotono")
def duotono(name, anim):
    tools = [Tool("Entrada", "PipeRouter", pos=(-385, 0)),
             Tool("Luma", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(0), "Contrast": I(0.15)}, pos=(-330, -66)),
             solid("Blanco", (1, 1, 1), (-330, -132)),
             merge("LumaInv", "Blanco", "Luma", (-275, -132), "Difference"),
             solid("Sombras", (0.1, 0.05, 0.35), (-275, -198)),
             solid("Luces", (1, 0.55, 0.45), (-275, 0)),
             merge("ParteS", "LumaInv", "Sombras", (-220, -132), "Multiply"),
             merge("ParteL", "Luma", "Luces", (-220, -66), "Multiply"),
             merge("Duo", "ParteS", "ParteL", (-165, -99), extra={"SubtractiveAdditive": I(0)}),
             merge("Duotono", "Entrada", "Duo", (-110, 0), blend=1)]
    pubs = [pub_color("Sombras", "Color de sombras", (0.1, 0.05, 0.35), 1), pub_color("Luces", "Color de luces", (1, 0.55, 0.45), 4),
            pub("Luma", "Contrast", "Contraste", 0.15), pub("Duotono", "Blend", "Mezcla con el original", 1)]
    return macro(name, [("Entrada", "Input")], pubs, "Duotono", tools)


@register("Effects", "PRO_FX_Glow_Neon")
def glow_neon(name, anim):
    tools = [Tool("Entrada", "PipeRouter", pos=(-385, 0)),
             Tool("Fuentes", "BrightnessContrast", {"Input": I(link="Entrada"), "Low": I(0.55), "High": I(1), "Saturation": I(1.4)}, pos=(-330, -66)),
             Tool("Nucleo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(8), "Input": I(link="Fuentes")}, pos=(-275, -99)),
             Tool("Halo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(45), "Input": I(link="Fuentes")}, pos=(-275, -33)),
             merge("ConNucleo", "Entrada", "Nucleo", (-220, 0), "Screen", blend=0.7),
             merge("Neon", "ConNucleo", "Halo", (-165, 0), "Screen", blend=0.6)]
    pubs = [pub("Fuentes", "Low", "Umbral (más bajo = más brillo)", 0.55), pub("ConNucleo", "Blend", "Brillo cercano", 0.7),
            pub("Neon", "Blend", "Halo amplio", 0.6), pub("Halo", "XBlurSize", "Radio del halo", 45),
            pub("Nucleo", "XBlurSize", "Radio cercano", 8), pub("Fuentes", "Saturation", "Saturación del brillo", 1.4)]
    return macro(name, [("Entrada", "Input")], pubs, "Neon", tools)


@register("Effects", "PRO_FX_Polvo_Flotante")
def polvo_flotante(name, anim):
    h = "Polvo"
    v = f"{h}.Velocidad"
    tools = [Tool("Entrada", "PipeRouter", pos=(-385, 0))]
    for i, (scale, low, blur, sp) in enumerate(((60, 0.86, 1.5, 1.0), (25, 0.9, 5, 0.6)), 1):
        tools += [Tool(f"Ruido{i}", "FastNoise", {**frame_format(), "Detail": I(8), "Contrast": I(2.5), "XScale": I(scale),
                                                  "SeetheRate": I(0.02),
                                                  "Center": I((0.5, 0.5), f"Point(0.5 + time*0.0004*{sp}*{v}, 0.5 - time*0.0007*{sp}*{v})")},
                       pos=(-330, -132 + 66 * (i - 1))),
                  Tool(f"Motas{i}", "BrightnessContrast", {"Input": I(link=f"Ruido{i}"), "Saturation": I(0),
                                                           "Low": I(low, f"{low} + (1 - {h}.Cantidad)*0.08"), "High": I(1)},
                       pos=(-275, -132 + 66 * (i - 1))),
                  Tool(f"Suave{i}", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(blur), "Input": I(link=f"Motas{i}")},
                       pos=(-220, -132 + 66 * (i - 1)))]
    tools += [merge("Capa1", "Entrada", "Suave1", (-165, 0), "Screen", blend=0.6, blend_expr=f"{h}.Brillo"),
              merge("Capa2", "Capa1", "Suave2", (-110, 0), "Screen", blend=0.4, blend_expr=f"{h}.Brillo*0.7")]
    ucs = [uc("Cantidad", "Cantidad", 0.5, 0, 1), uc("Brillo", "Brillo", 0.6, 0, 1.5), uc("Velocidad", "Velocidad", 1, 0, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Capa2"), "Cantidad": I(0.5), "Brillo": I(0.6), "Velocidad": I(1)}, ucs, (-55, 0)))
    pubs = [pub(h, "Cantidad", "Cantidad", 0.5), pub(h, "Brillo", "Brillo", 0.6), pub(h, "Velocidad", "Velocidad", 1),
            pub("Suave1", "XBlurSize", "Desenfoque de motas", 1.5)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Social_Tarjeta")
def tarjeta(name, anim):
    """El clip reducido como tarjeta con esquinas redondeadas y sombra sobre un fondo de color."""
    h = "Tarjeta"
    tools = [Tool("Reducir", "Transform", {"Size": I(0.85, f"{h}.Tamano")}, pos=(-330, 0)),
             solid("Fondo", (0.95, 0.93, 0.9), (-330, -132)),
             rect("MascTarjeta", (-275, -165), Width=I(0.85, f"{h}.Tamano"), Height=I(1.51, f"{h}.Tamano/{h}.Aspecto"),
                  CornerRadius=I(0.08, f"{h}.Redondeo")),
             rect("MascSombra", (-220, -165), Width=I(0.85, f"{h}.Tamano"), Height=I(1.51, f"{h}.Tamano/{h}.Aspecto"),
                  CornerRadius=I(0.08, f"{h}.Redondeo"), SoftEdge=I(0.03), Center=I((0.5, 0.49))),
             solid("Sombra", (0, 0, 0), (-220, -132), mask="MascSombra"),
             merge("ConSombra", "Fondo", "Sombra", (-165, -66), blend=0.35),
             merge(h, "ConSombra", "Reducir", (-110, 0), blend=1, extra={"EffectMask": I(link="MascTarjeta", out="Mask")},
                   ucs=[uc("Tamano", "Tamaño", 0.85, 0.3, 1), uc("Redondeo", "Redondeo de esquinas", 0.08, 0, 0.5),
                        uc("Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625, 0.4, 3)])]
    tools[-1].inputs.update({"Tamano": I(0.85), "Redondeo": I(0.08), "Aspecto": I(0.5625)})
    pubs = [pub(h, "Tamano", "Tamaño", 0.85), pub(h, "Redondeo", "Redondeo de esquinas", 0.08),
            pub_color("Fondo", "Color del fondo", (0.95, 0.93, 0.9), 3), pub("ConSombra", "Blend", "Sombra", 0.35),
            pub(h, "Aspecto", "Aspecto del timeline (9:16 = 0.5625)", 0.5625)]
    return macro(name, [("Reducir", "Input")], pubs, h, tools)


# ======================================================================= LOTE 8: texto social, transiciones, camaras y clima
def numbered(pubs):
    """Aplana los pub() y cambia los grupos simbolicos ("c1", "f1"...) por el indice del primer control del grupo."""
    flat, first = [], {}
    for p in pubs:
        flat += p if isinstance(p, list) else [p]
    for i, p in enumerate(flat, 1):
        if isinstance(p["group"], str):
            p["group"] = first.setdefault(p["group"], i)
    return flat


def text_pubs(tool, label, size, rgb, key):
    """Fuente, estilo, tamano y color de un Text+ (grupos simbolicos para numbered())."""
    return [pub(tool, "Font", f"Fuente{label}", group=f"f{key}"), pub(tool, "Style", group=f"f{key}"),
            pub(tool, "Size", f"Tamaño{label}", size),
            pub_color(tool, f"Color{label}", rgb, f"c{key}", prefix="", suffix="1")]


def ui_color(tool, src="ColorUI", text=False):
    """Hace que un fondo (o un Text+) tome el color del selector comun."""
    for ch in ("Red", "Green", "Blue"):
        tool.inputs[f"{ch}1" if text else f"TopLeft{ch}"] = I(1, f"{src}.TopLeft{ch}")
    return tool


def timecode(seconds, frames=None):
    """Texto hh:mm:ss (o hh:mm:ss:ff) calculado a partir de una expresion en segundos."""
    s = seconds
    parts = [f"floor({s}/3600) - 24*floor({s}/86400)", f"floor({s}/60) - 60*floor({s}/3600)", f"floor({s}) - 60*floor({s}/60)"]
    fmt = "%02d:%02d:%02d"
    if frames:
        parts.append(f"floor(time) - {frames}*floor(time/{frames})")
        fmt += ":%02d"
    return f'Text(string.format("{fmt}", {", ".join(parts)}))'


def mean_stack(prefix, src, size_expr, center_expr, n, pos_x):
    """n copias escaladas de src promediadas (desenfoque radial aproximado). size_expr/center_expr reciben k/n."""
    tools, last = [], src
    for k in range(1, n + 1):
        f = f"{k / n:g}"
        tinputs = {"Input": I(link=src), "Size": I(1, size_expr(f))}
        if center_expr:
            tinputs["Center"] = I((0.5, 0.5), center_expr(f))
        tools += [Tool(f"{prefix}{k}", "Transform", tinputs, pos=(pos_x + 33 * k, -66)),
                  merge(f"{prefix}Media{k}", last, f"{prefix}{k}", (pos_x + 33 * k, 0), blend=1 / (k + 1))]
        last = f"{prefix}Media{k}"
    return tools, last


# ----------------------------------------------------------------------- titulos de texto
@register("Titles", "PRO_TTL_Texto_Maquina")
def texto_maquina(name, anim):
    """Maquina de escribir: la frase aparece letra a letra, con cursor parpadeante opcional."""
    h = "Maquina"
    src = "Fuente.StyledText.Value"
    n = f"floor({h}.U*string.len({src}) + 0.5)"
    cursor = f'string.rep("|", {h}.Cursor*iif(sin(time*0.5) > 0, 1, 0))'
    ucs, inputs = kit(h, 0.6, 0.1, [uc("Cursor", "Cursor parpadeante", 1, 0, 1, checkbox=True)], {"Cursor": I(1)})
    body = [text_tool("Fuente", "Escribe aquí tu frase...", 0.06, (0.5, 0.5), (-385, -198)),
            text_tool("Texto", "", 0.06, (0.12, 0.5), (-385, -132), font="Courier New", left=True,
                      extra={"StyledText": I("", f"Text(string.sub({src}, 1, {n}) .. {cursor})")})]
    pubs = numbered([pub("Fuente", "StyledText", "Texto"), *text_pubs("Texto", "", 0.06, (1, 1, 1), 1),
                     pub("Texto", "Center", "Inicio del texto"), pub(h, "Cursor", "Cursor parpadeante", 1)])
    return title(name, h, ucs, inputs, body, [("Texto", f"{h}.Xs")], pubs)


@register("Titles", "PRO_TTL_Texto_Resaltado")
def texto_resaltado(name, anim):
    """Palabra con un resaltador de color que se dibuja detras de izquierda a derecha (subtitulos tipo CapCut)."""
    h = "Resaltado"
    grow = smooth(clamp01(f"({h}.U - 0.25)/0.75"))
    ucs, inputs = kit(h, 0.3, 0.12, [uc("Ancho", "Ancho del resaltado", 0.42, 0.02, 1),
                                     uc("Alto", "Alto del resaltado", 0.075, 0.005, 0.3),
                                     uc("Inclinacion", "Inclinación (grados)", -2, -15, 15)],
                      {"Ancho": I(0.42), "Alto": I(0.075), "Inclinacion": I(-2)})
    body = [rect("MascBanda", (-385, -165), Center=I((0.29, 0.497), f"Point(0.5 - {h}.Ancho/2 + {h}.Ancho*{grow}/2, 0.497)"),
                 Width=I(0, f"{h}.Ancho*{grow}"), Height=I(0.075, f"{h}.Alto"), CornerRadius=I(0.15),
                 Angle=I(-2, f"{h}.Inclinacion")),
            solid("Banda", (1, 0.85, 0.1), (-385, -132), mask="MascBanda"),
            text_tool("Texto", "PALABRA CLAVE", 0.07, (0.5, 0.5), (-330, -132), rgb=(0.05, 0.05, 0.05))]
    pubs = numbered([pub("Texto", "StyledText", "Texto"), *text_pubs("Texto", " del texto", 0.07, (0.05, 0.05, 0.05), 1),
                     pub_color("Banda", "Color del resaltado", (1, 0.85, 0.1), "c2"), pub(h, "Ancho", "Ancho del resaltado", 0.42),
                     pub(h, "Alto", "Alto del resaltado", 0.075), pub(h, "Inclinacion", "Inclinación (grados)", -2)])
    return title(name, h, ucs, inputs, body, [("Banda", f"{h}.Xs"), ("Texto", stage(h, 0, 0.35))], pubs)


@register("Titles", "PRO_TTL_Texto_Brillo")
def texto_brillo(name, anim):
    """Texto con un destello diagonal que lo recorre cada cierto numero de fotogramas (estilo logo premium)."""
    h = "Brillo"
    ph = f"(time/{h}.Periodo - floor(time/{h}.Periodo))"
    ucs, inputs = kit(h, 0.15, 0.1, [uc("Periodo", "Fotogramas entre destellos", 60, 10, 300),
                                     uc("Intensidad", "Intensidad del destello", 1.2, 0, 4),
                                     uc("AnchoBrillo", "Ancho del destello", 0.06, 0.005, 0.3)],
                      {"Periodo": I(60), "Intensidad": I(1.2), "AnchoBrillo": I(0.06)})
    body = [text_tool("Texto", "BRILLO", 0.12, (0.5, 0.5), (-385, -132), rgb=(0.95, 0.75, 0.3)),
            rect("Franja", (-330, -165), Center=I((0.5, 0.5), f"Point(-0.3 + 1.6*min(1, {ph}/0.4), 0.5)"),
                 Width=I(0.06, f"{h}.AnchoBrillo"), Height=I(4), Angle=I(20), SoftEdge=I(0.03)),
            Tool("Destello", "BrightnessContrast", {"Input": I(link="Texto"), "EffectMask": I(link="Franja", out="Mask"),
                                                    "Gain": I(2.2, f"1 + {h}.Intensidad"), "Saturation": I(0.4)}, pos=(-275, -132))]
    pubs = numbered([pub("Texto", "StyledText", "Texto"), *text_pubs("Texto", "", 0.12, (0.95, 0.75, 0.3), 1),
                     pub(h, "Periodo", "Fotogramas entre destellos", 60), pub(h, "Intensidad", "Intensidad del destello", 1.2),
                     pub(h, "AnchoBrillo", "Ancho del destello", 0.06)])
    return title(name, h, ucs, inputs, body, [("Destello", stage(h, 0, 1))], pubs)


@register("Titles", "PRO_TTL_Texto_Neon")
def texto_neon(name, anim):
    """Letrero de neon: se enciende parpadeando y despues falla de vez en cuando."""
    h = "Neon"
    falla = f"iif(sin(time*1.37)*sin(time*2.71 + 1)*sin(time*0.53 + 2) > 1 - {h}.Parpadeo*0.6, 0.3, 1)"
    encendido = f"iif({h}.U < 1, iif(sin(time*2.3)*sin(time*0.9 + 1) > 0, 1, 0.15), 1)"
    ucs, inputs = kit(h, 0.25, 0.1, [uc("Glow", "Brillo del halo", 0.8, 0, 1), uc("Parpadeo", "Fallos de parpadeo", 0.3, 0, 1),
                                     uc("F", "Encendido interno", 1, 0, 1, clamp=False)],
                      {"Glow": I(0.8), "Parpadeo": I(0.3), "F": I(1, f"{falla}*{encendido}")})
    body = [text_tool("Texto", "NEON", 0.14, (0.5, 0.5), (-385, -132), rgb=(1, 0.25, 0.7)),
            Tool("Nucleo", "BrightnessContrast", {"Input": I(link="Texto"), "Gain": I(1.3), "Saturation": I(0.35)}, pos=(-330, -165)),
            Tool("HaloCerca", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(10), "Input": I(link="Texto")}, pos=(-330, -132)),
            Tool("HaloLejos", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(45), "Input": I(link="Texto")}, pos=(-330, -99))]
    pubs = numbered([pub("Texto", "StyledText", "Texto"), *text_pubs("Texto", "", 0.14, (1, 0.25, 0.7), 1),
                     pub(h, "Glow", "Brillo del halo", 0.8), pub("HaloLejos", "XBlurSize", "Radio del halo", 45),
                     pub(h, "Parpadeo", "Fallos de parpadeo", 0.3)])
    layers = [("HaloLejos", f"{h}.Glow*0.8*{h}.F*{h}.Xs"), ("HaloCerca", f"{h}.Glow*{h}.F*{h}.Xs"),
              ("Nucleo", f"(0.35 + 0.65*{h}.F)*{h}.Xs")]
    return title(name, h, ucs, inputs, body, layers, pubs)


# ----------------------------------------------------------------------- transiciones
@register("Transitions", "PRO_TR_ZoomRadial")
def tr_zoom_radial(name, anim):
    """Zoom con desenfoque radial (copias escaladas promediadas): A se lanza hacia la camara y B llega desde ella."""
    h = "Mezcla"
    p = f"{h}.Progreso"
    a, b = f"min(1, 2*{p})", f"(1 - max(0, 2*{p} - 1))"
    bell = f"sin({p}*{PI})*sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Zoom", "Zoom", 0.6, 0, 3), uc("Fuerza", "Desenfoque radial", 1, 0, 3)]
    tools = [Tool("ZoomSaliente", "Transform", {"Size": I(1, f"1 + {h}.Zoom*{a}*{a}")}, pos=(-220, -33)),
             Tool("ZoomEntrante", "Transform", {"Size": I(1, f"1 + {h}.Zoom*{b}*{b}")}, pos=(-220, 33)),
             Tool(h, "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.45)/0.1"))),
                                  "Background": I(link="ZoomSaliente"), "Foreground": I(link="ZoomEntrante"),
                                  "Progreso": I(link=anim, out="Value"), "Zoom": I(0.6), "Fuerza": I(1)}, ucs, (-110, 0))]
    t, last = mean_stack("Radial", h, lambda f: f"1 + {h}.Fuerza*0.25*{f}*{bell}", None, 6, -110)
    tools += t
    pubs = [pub(h, "Zoom", "Zoom", 0.6), pub(h, "Fuerza", "Desenfoque radial", 1)]
    return macro(name, [("ZoomSaliente", "Input"), ("ZoomEntrante", "Input")], pubs, last, tools, anim)


@register("Transitions", "PRO_TR_Giro")
def tr_giro(name, anim):
    """Giro: A rota y se desenfoca, B termina el giro en el mismo sentido. El zoom tapa las esquinas."""
    h = "Mezcla"
    p = f"{h}.Progreso"
    a, b = f"min(1, 2*{p})", f"(1 - max(0, 2*{p} - 1))"
    bell = f"sin({p}*{PI})"
    blur = f"{h}.Desenfoque*{bell}*{bell}"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Angulo", "Giro (grados, negativo = al otro lado)", 180, -720, 720),
           uc("Zoom", "Zoom para tapar esquinas", 1, 0, 3), uc("Desenfoque", "Desenfoque", 25, 0, 100)]
    tools = [Tool("GiroSaliente", "Transform", {"Angle": I(0, f"{h}.Angulo*{a}*{a}"), "Size": I(1, f"1 + {h}.Zoom*{bell}")}, pos=(-220, -33)),
             Tool("GiroEntrante", "Transform", {"Angle": I(0, f"-{h}.Angulo*{b}*{b}"), "Size": I(1, f"1 + {h}.Zoom*{bell}")}, pos=(-220, 33)),
             Tool("BlurSaliente", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, blur),
                                           "Input": I(link="GiroSaliente")}, pos=(-110, -33)),
             Tool("BlurEntrante", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, blur),
                                           "Input": I(link="GiroEntrante")}, pos=(-110, 33)),
             Tool(h, "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.42)/0.16"))),
                                  "Background": I(link="BlurSaliente"), "Foreground": I(link="BlurEntrante"),
                                  "Progreso": I(link=anim, out="Value"), "Angulo": I(180), "Zoom": I(1), "Desenfoque": I(25)},
                  ucs, (0, 0))]
    pubs = [pub(h, "Angulo", "Giro (grados, negativo = al otro lado)", 180), pub(h, "Zoom", "Zoom para tapar esquinas", 1),
            pub(h, "Desenfoque", "Desenfoque", 25)]
    return macro(name, [("GiroSaliente", "Input"), ("GiroEntrante", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_Barras")
def tr_barras(name, anim):
    """Barras verticales que entran escalonadas, alternando arriba y abajo, y descubren el clip B (estilo Mister Horse)."""
    h = "Barras"
    p = f"{h}.Progreso"
    n = 8
    tools = [Tool("EntradaA", "PipeRouter", pos=(-440, 0)), Tool("EntradaB", "PipeRouter", pos=(-440, 66))]
    last = "EntradaA"
    for i in range(n):
        e = smooth(clamp01(f"{p}*(1 + {h}.Escalonado) - {h}.Escalonado*{i / (n - 1):g}"))
        d = "1" if i % 2 == 0 else f"(1 - 2*{h}.Alternar)"
        x = (i + 0.5) / n
        tools += [rect(f"MascBarra{i}", (-385 + 44 * i, -99), Center=I((x, 1.55), f"Point({x:g}, 0.5 + {d}*1.05*(1 - {e}))"),
                       Width=I(1 / n + 0.002), Height=I(0.59, f"1.05/{h}.Aspecto")),
                  merge(f"Barra{i}", last, "EntradaB", (-385 + 44 * i, 0), extra={"EffectMask": I(link=f"MascBarra{i}", out="Mask")})]
        last = f"Barra{i}"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Escalonado", "Escalonado", 0.6, 0, 3),
           uc("Alternar", "Alternar arriba / abajo", 1, 0, 1, checkbox=True),
           uc("Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778, 0.4, 3)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Progreso": I(link=anim, out="Value"),
                                                "Escalonado": I(0.6), "Alternar": I(1), "Aspecto": I(1.7778)}, ucs, (0, 0)))
    pubs = [pub(h, "Escalonado", "Escalonado", 0.6), pub(h, "Alternar", "Alternar arriba / abajo", 1),
            pub(h, "Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778)]
    return macro(name, [("EntradaA", "Input"), ("EntradaB", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_Iris")
def tr_iris(name, anim):
    """Circulo que crece desde un punto y descubre el clip B, con un aro de color en el borde."""
    h = "Iris"
    p = f"{h}.Progreso"
    d = f"{h}.Tamano*{smooth(p)}*{smooth(p)}"
    c = f"Point({h}.CX, {h}.CY)"
    tools = [Tool("EntradaA", "PipeRouter", pos=(-330, 0)), Tool("EntradaB", "PipeRouter", pos=(-330, 66)),
             ellipse("MascAro", (-275, -99), Center=I((0.5, 0.5), c), SoftEdge=I(0.003),
                     Width=I(0, f"{d} + {h}.Borde*sin({p}*{PI})"), Height=I(0, f"{d} + {h}.Borde*sin({p}*{PI})")),
             solid("Aro", (1, 1, 1), (-275, -66), mask="MascAro"),
             ellipse("MascIris", (-220, -99), Center=I((0.5, 0.5), c), SoftEdge=I(0.003, f"{h}.Suavidad"),
                     Width=I(0, d), Height=I(0, d)),
             merge("ConAro", "EntradaA", "Aro", (-220, 0)),
             merge("ConIris", "ConAro", "EntradaB", (-165, 0), extra={"EffectMask": I(link="MascIris", out="Mask")})]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("CX", "Origen X", 0.5, 0, 1), uc("CY", "Origen Y", 0.5, 0, 1),
           uc("Borde", "Grosor del aro", 0.03, 0, 0.2), uc("Suavidad", "Suavidad del borde", 0.003, 0, 0.2),
           uc("Tamano", "Tamaño final (súbelo si quedan esquinas)", 4.2, 1, 8)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConIris"), "Progreso": I(link=anim, out="Value"), "CX": I(0.5),
                                                "CY": I(0.5), "Borde": I(0.03), "Suavidad": I(0.003), "Tamano": I(4.2)}, ucs, (-110, 0)))
    pubs = numbered([pub(h, "CX", "Origen X", 0.5), pub(h, "CY", "Origen Y", 0.5), pub(h, "Borde", "Grosor del aro", 0.03),
                     pub_color("Aro", "Color del aro", (1, 1, 1), "c1"), pub(h, "Suavidad", "Suavidad del borde", 0.003),
                     pub(h, "Tamano", "Tamaño final (súbelo si quedan esquinas)", 4.2)])
    return macro(name, [("EntradaA", "Input"), ("EntradaB", "Input")], pubs, h, tools, anim)


# ----------------------------------------------------------------------- camaras
@register("Effects", "PRO_FX_Cam_REC")
def cam_rec(name, anim):
    """Interfaz de videocamara: punto REC parpadeante, codigo de tiempo que corre, bateria y esquinas de encuadre."""
    h = "REC"
    asp = f"{h}.Aspecto"
    tools = [Tool("Entrada", "PipeRouter", pos=(-660, 0)), solid("ColorUI", (1, 1, 1), (-660, -264)),
             solid("Lienzo", (0, 0, 0), (-605, 0), alpha=0)]
    layers = []
    for j, (sx, sy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        cx = f"0.5 + {sx}*(0.5 - {h}.Margen)"
        cy = f"0.5 + {sy}*(0.5 - {h}.Margen*{asp})"
        for k, (center, w, ht) in enumerate(((f"Point({cx} - {sx}*{h}.Largo/2, {cy})", f"{h}.Largo", f"{h}.Grosor"),
                                             (f"Point({cx}, {cy} - {sy}*{h}.Largo*{asp}/2)", f"{h}.Grosor", f"{h}.Largo"))):
            m = f"Esq{j}{k}"
            tools += [rect(f"Masc{m}", (-550 + 33 * (2 * j + k), -198), Center=I((0.5, 0.5), center),
                           Width=I(0.06, w), Height=I(0.004, ht)),
                      ui_color(solid(m, (1, 1, 1), (-550 + 33 * (2 * j + k), -165), mask=f"Masc{m}"))]
            layers.append(m)
    tools += [ellipse("MascPunto", (-275, -198), Center=I((0.09, 0.88)), Width=I(0.022), Height=I(0.022), SoftEdge=I(0.002)),
              solid("Punto", (1, 0.1, 0.1), (-275, -165), mask="MascPunto"),
              ui_color(text_tool("TextoREC", "REC", 0.035, (0.14, 0.88), (-220, -165)), text=True),
              ui_color(text_tool("Codigo", "00:00:00:00", 0.035, (0.82, 0.88), (-165, -165), font="Courier New",
                                 extra={"StyledText": I("00:00:00:00", timecode(f"(time/{h}.FPS + {h}.Inicio)", f"{h}.FPS"))}), text=True),
              ui_color(text_tool("Info", "4K  30p", 0.03, (0.14, 0.12), (-110, -165), style="Regular"), text=True),
              rect("MascPila", (-55, -198), Center=I((0.86, 0.12)), Width=I(0.05), Height=I(0.022), Solid=I(0), BorderWidth=I(0.002)),
              ui_color(solid("Pila", (1, 1, 1), (-55, -165), mask="MascPila")),
              rect("MascCarga", (0, -198), Center=I((0.86, 0.12), f"Point(0.84 + 0.02*{h}.Bateria, 0.12)"),
                   Width=I(0.028, f"0.04*{h}.Bateria"), Height=I(0.014)),
              ui_color(solid("Carga", (1, 1, 1), (0, -165), mask="MascCarga")),
              rect("MascBorne", (55, -198), Center=I((0.888, 0.12)), Width=I(0.004), Height=I(0.01)),
              ui_color(solid("Borne", (1, 1, 1), (55, -165), mask="MascBorne"))]
    blink = f"iif(sin(time*{PI}/{h}.FPS) > 0, 1, 0)"
    t, last = compose([(m, None) for m in layers] + [("Punto", blink), ("TextoREC", None), ("Codigo", None), ("Info", None),
                                                    ("Pila", None), ("Carga", None), ("Borne", None)], x0=-550)
    tools += t
    tools.append(merge("Interfaz", "Entrada", last, (330, 0), blend=0.9))
    ucs = [uc("FPS", "Fotogramas por segundo", 30, 1, 120), uc("Inicio", "Código inicial (segundos)", 0, 0, 86399),
           uc("Bateria", "Carga de la batería", 0.7, 0, 1), uc("Margen", "Margen de las esquinas", 0.05, 0, 0.3),
           uc("Largo", "Largo de las esquinas", 0.06, 0.005, 0.3), uc("Grosor", "Grosor de las líneas", 0.004, 0.001, 0.03),
           uc("Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778, 0.4, 3)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Interfaz"), "FPS": I(30), "Inicio": I(0), "Bateria": I(0.7),
                                                "Margen": I(0.05), "Largo": I(0.06), "Grosor": I(0.004), "Aspecto": I(1.7778)},
                      ucs, (385, 0)))
    pubs = numbered([pub_color("ColorUI", "Color de la interfaz", (1, 1, 1), "c1"), pub("Interfaz", "Blend", "Opacidad", 0.9),
                     pub("Info", "StyledText", "Texto inferior"), pub(h, "FPS", "Fotogramas por segundo", 30),
                     pub(h, "Inicio", "Código inicial (segundos)", 0), pub(h, "Bateria", "Carga de la batería", 0.7),
                     pub(h, "Margen", "Margen de las esquinas", 0.05), pub(h, "Largo", "Largo de las esquinas", 0.06),
                     pub(h, "Grosor", "Grosor de las líneas", 0.004),
                     pub(h, "Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778)])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


def scanlines(name, src, host, pos_x, high=0.5):
    """Lineas horizontales oscuras: onda triangular vertical aplanada, multiplicada sobre la imagen."""
    return [pingpong_bg(f"{name}Onda", f"Point(0.5, 0.5 + 0.5/{host}.NumLineas)", (pos_x, -132)),
            Tool(f"{name}Plana", "BrightnessContrast", {"Input": I(link=f"{name}Onda"), "Low": I(0), "High": I(high)}, pos=(pos_x, -99)),
            merge(name, src, f"{name}Plana", (pos_x + 55, 0), "Multiply", blend=0.3, blend_expr=f"{host}.Lineas")], name


@register("Effects", "PRO_FX_Cam_Seguridad")
def cam_seguridad(name, anim):
    """Camara de seguridad: casi sin color, tinte verdoso, ruido, lineas, nombre de camara, fecha y reloj que corre."""
    h = "CCTV"
    tools = [Tool("Entrada", "PipeRouter", pos=(-550, 0)),
             Tool("Look", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(0.15), "Contrast": I(0.25),
                                                 "Gain": I(1.05), "Lift": I(0.03)}, pos=(-495, 0))]
    t, last = blk_cast("Tinte", "Look", -440, (0.85, 1, 0.9), 1)
    tools += t
    t, last = blk_grain("Gr", last, f"{h}.Ruido", -330, scale=80)
    tools += t
    t, last = scanlines("Lineas", last, h, -220)
    tools += t
    t, last = blk_vignette("Vin", last, -110, amount=0.45)
    tools += t
    s = f"({h}.Hora*3600 + time/{h}.FPS)"
    tools += [solid("Lienzo", (0, 0, 0), (0, -66), alpha=0),
              text_tool("Camara", "CAM 01", 0.035, (0.12, 0.9), (0, -165), font="Courier New"),
              text_tool("Fecha", "27/10/2026", 0.035, (0.17, 0.08), (55, -165), font="Courier New"),
              text_tool("Reloj", "14:30:00", 0.035, (0.85, 0.08), (110, -165), font="Courier New",
                        extra={"StyledText": I("14:30:00", timecode(s))})]
    for tn in ("Fecha", "Reloj"):
        next(x for x in tools if x.name == tn).inputs.update({f"{ch}1": I(1, f"Camara.{ch}1") for ch in ("Red", "Green", "Blue")})
    t, over = compose([("Camara", None), ("Fecha", None), ("Reloj", None)], x0=55)
    tools += t
    tools.append(merge("Textos", last, over, (220, 0), blend=0.9))
    ucs = [uc("Ruido", "Ruido", 0.2, 0, 1), uc("Lineas", "Líneas", 0.3, 0, 1), uc("NumLineas", "Número de líneas", 240, 20, 1000),
           uc("Hora", "Hora inicial (14.5 = 14:30)", 14.5, 0, 24), uc("FPS", "Fotogramas por segundo", 30, 1, 120)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Textos"), "Ruido": I(0.2), "Lineas": I(0.3), "NumLineas": I(240),
                                                "Hora": I(14.5), "FPS": I(30)}, ucs, (275, 0)))
    pubs = numbered([pub("Camara", "StyledText", "Nombre de la cámara"), pub("Fecha", "StyledText", "Fecha"),
                     pub(h, "Hora", "Hora inicial (14.5 = 14:30)", 14.5), pub(h, "FPS", "Fotogramas por segundo", 30),
                     pub("Look", "Saturation", "Color (0 = blanco y negro)", 0.15), pub_color("TinteColor", "Tinte", (0.85, 1, 0.9), "c1"),
                     pub(h, "Ruido", "Ruido", 0.2), pub(h, "Lineas", "Líneas", 0.3), pub(h, "NumLineas", "Número de líneas", 240),
                     pub("VinVineta", "Blend", "Viñeta", 0.45), pub("Textos", "Blend", "Opacidad del texto", 0.9),
                     pub_color("Camara", "Color del texto", (1, 1, 1), "c2", prefix="", suffix="1")])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Cam_VisionNocturna")
def vision_nocturna(name, anim):
    """Vision nocturna: luminancia amplificada en verde, brillo en las luces, grano fuerte y visor circular."""
    h = "Nocturna"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Amplificar", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(0), "Gain": I(1.6),
                                                       "Contrast": I(0.1)}, pos=(-385, 0))]
    t, last = blk_cast("Tono", "Amplificar", -330, (0.25, 1, 0.3), 1)
    tools += t
    t, last = blk_bloom("Bl", last, -220, low=0.6, radius=30, blend=0.4)
    tools += t
    t, last = blk_grain("Gr", last, None, -55, scale=60)
    tools += t
    tools[-1].inputs["Blend"] = I(0.25)
    tools += [ellipse("MascVisor", (55, -99), Invert=I(1), SoftEdge=I(0.12), Width=I(0.9), Height=I(0.9)),
              solid("Negro", (0, 0, 0), (55, -66), mask="MascVisor"),
              merge(h, last, "Negro", (110, 0), blend=1)]
    pubs = numbered([pub("Amplificar", "Gain", "Amplificación", 1.6), pub_color("TonoColor", "Color", (0.25, 1, 0.3), "c1"),
                     pub("BlBloom", "Blend", "Brillo en las luces", 0.4), pub("GrGrano", "Blend", "Grano", 0.25),
                     pub(h, "Blend", "Visor", 1), pub("MascVisor", "Width", "Ancho del visor", 0.9),
                     pub("MascVisor", "Height", "Alto del visor", 0.9), pub("MascVisor", "SoftEdge", "Suavidad del visor", 0.12)])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Cam_Termica")
def cam_termica(name, anim):
    """Camara termica: la luminancia se pinta con tres colores (frio, medio, caliente)."""
    h = "Termica"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Luma", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(0), "Contrast": I(0.2)}, pos=(-385, -66)),
             Tool("Suave", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(3), "Input": I(link="Luma")}, pos=(-330, -66)),
             Tool("Bajo", "BrightnessContrast", {"Input": I(link="Suave"), "Low": I(0), "High": I(0.5)}, pos=(-275, -132)),
             Tool("Alto", "BrightnessContrast", {"Input": I(link="Suave"), "Low": I(0.5), "High": I(1)}, pos=(-275, 0)),
             solid("Blanco", (1, 1, 1), (-275, -198)),
             merge("PesoFrio", "Blanco", "Bajo", (-220, -198), "Difference"),
             merge("PesoMedio", "Bajo", "Alto", (-220, -132), "Difference"),
             solid("Frio", (0.05, 0.05, 0.45), (-165, -231)),
             solid("Medio", (0.9, 0.1, 0.5), (-165, -165)),
             solid("Caliente", (1, 0.9, 0.2), (-165, -33)),
             merge("ParteFrio", "PesoFrio", "Frio", (-110, -198), "Multiply"),
             merge("ParteMedio", "PesoMedio", "Medio", (-110, -132), "Multiply"),
             merge("ParteCaliente", "Alto", "Caliente", (-110, -66), "Multiply"),
             merge("Suma1", "ParteFrio", "ParteMedio", (-55, -165), extra={"SubtractiveAdditive": I(0)}),
             merge("Suma2", "Suma1", "ParteCaliente", (0, -99), extra={"SubtractiveAdditive": I(0)}),
             merge(h, "Entrada", "Suma2", (55, 0), blend=1)]
    pubs = numbered([pub_color("Frio", "Color frío", (0.05, 0.05, 0.45), "c1"), pub_color("Medio", "Color medio", (0.9, 0.1, 0.5), "c2"),
                     pub_color("Caliente", "Color caliente", (1, 0.9, 0.2), "c3"), pub("Luma", "Contrast", "Contraste", 0.2),
                     pub("Suave", "XBlurSize", "Suavidad", 3), pub(h, "Blend", "Mezcla con el original", 1)])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Retro_CRT")
def retro_crt(name, anim):
    """Televisor de tubo: separacion de color, brillo, lineas de barrido, parpadeo y pantalla con esquinas redondeadas."""
    h = "CRT"
    tools = [Tool("Entrada", "PipeRouter", pos=(-550, 0))]
    t, last = blk_channel_shift("Sep", "Entrada", f"{h}.Separacion", "0", -495)
    tools += t
    t, last = blk_bloom("Bl", last, -220, low=0.6, radius=25, blend=0.35)
    tools += t
    t, last = scanlines("Lineas", last, h, -55, high=0.6)
    tools += t
    tools += [Tool("Parpadeo", "BrightnessContrast", {"Input": I(link=last),
                   "Gain": I(1, f"1 + {h}.Parpadeo*0.04*sin(time*9.1)*sin(time*4.3 + 1)")}, pos=(55, 0)),
              rect("MascPantalla", (110, -99), Invert=I(1), Width=I(0.96), Height=I(0.54, f"0.96/{h}.Aspecto"),
                   CornerRadius=I(0.12), SoftEdge=I(0.01)),
              solid("Marco", (0.02, 0.02, 0.02), (110, -66), mask="MascPantalla"),
              merge("ConMarco", "Parpadeo", "Marco", (165, 0), blend=1)]
    t, last = blk_vignette("Vin", "ConMarco", 220, amount=0.35)
    tools += t
    ucs = [uc("Separacion", "Separación de color", 0.002, 0, 0.02), uc("Lineas", "Líneas", 0.3, 0, 1),
           uc("NumLineas", "Número de líneas", 300, 50, 1000), uc("Parpadeo", "Parpadeo", 1, 0, 5),
           uc("Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778, 0.4, 3)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Separacion": I(0.002), "Lineas": I(0.3), "NumLineas": I(300),
                                                "Parpadeo": I(1), "Aspecto": I(1.7778)}, ucs, (330, 0)))
    pubs = [pub(h, "Separacion", "Separación de color", 0.002), pub("BlBloom", "Blend", "Brillo", 0.35),
            pub(h, "Lineas", "Líneas", 0.3), pub(h, "NumLineas", "Número de líneas", 300), pub(h, "Parpadeo", "Parpadeo", 1),
            pub("ConMarco", "Blend", "Marco de la pantalla", 1), pub("MascPantalla", "CornerRadius", "Redondeo de la pantalla", 0.12),
            pub("VinVineta", "Blend", "Viñeta", 0.35), pub(h, "Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


# ----------------------------------------------------------------------- composicion y movimiento
@register("Effects", "PRO_FX_Social_PantallaDividida")
def pantalla_dividida(name, anim):
    """Coloca el clip en una celda de una rejilla (filas x columnas). Pon cada clip en su pista con su celda."""
    h = "Celda"
    cw, ch = f"(1/{h}.Columnas)", f"(1/{h}.Filas)"
    cx, cy = f"(({h}.Columna - 0.5)*{cw})", f"(1 - ({h}.Fila - 0.5)*{ch})"
    tools = [Tool("Colocar", "Transform", {"Center": I((0.5, 0.75), f"Point({cx} + {h}.MoverX, {cy} + {h}.MoverY)"),
                                           "Size": I(1, f"max({cw}, {ch})*{h}.Zoom")}, pos=(-220, 0)),
             solid("Vacio", (0, 0, 0), (-220, -66), alpha=0),
             rect("MascCelda", (-165, -99), Center=I((0.5, 0.75), f"Point({cx}, {cy})"),
                  Width=I(1, f"max(0, {cw} - {h}.Separacion)"), Height=I(0.89, f"max(0, {ch}/{h}.Aspecto - {h}.Separacion)"),
                  CornerRadius=I(0, f"{h}.Redondeo"))]
    ucs = [uc("Columnas", "Columnas", 1, 1, 4, integer=True), uc("Filas", "Filas", 2, 1, 4, integer=True),
           uc("Columna", "Columna de este clip", 1, 1, 4, integer=True), uc("Fila", "Fila de este clip (1 = arriba)", 1, 1, 4, integer=True),
           uc("Separacion", "Separación", 0.01, 0, 0.1), uc("Redondeo", "Redondeo de esquinas", 0, 0, 0.5),
           uc("Zoom", "Zoom dentro de la celda", 1, 0.5, 3), uc("MoverX", "Encuadre X", 0, -0.5, 0.5), uc("MoverY", "Encuadre Y", 0, -0.5, 0.5),
           uc("Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 0.5625, 0.4, 3)]
    tools.append(merge(h, "Vacio", "Colocar", (-110, 0), blend=1, ucs=ucs, extra={
        "EffectMask": I(link="MascCelda", out="Mask"), "Columnas": I(1), "Filas": I(2), "Columna": I(1), "Fila": I(1),
        "Separacion": I(0.01), "Redondeo": I(0), "Zoom": I(1), "MoverX": I(0), "MoverY": I(0), "Aspecto": I(0.5625)}))
    pubs = [pub(h, "Columnas", "Columnas", 1), pub(h, "Filas", "Filas", 2), pub(h, "Columna", "Columna de este clip", 1),
            pub(h, "Fila", "Fila de este clip (1 = arriba)", 1), pub(h, "Separacion", "Separación", 0.01),
            pub(h, "Redondeo", "Redondeo de esquinas", 0), pub(h, "Zoom", "Zoom dentro de la celda", 1),
            pub(h, "MoverX", "Encuadre X", 0), pub(h, "MoverY", "Encuadre Y", 0),
            pub(h, "Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 0.5625)]
    return macro(name, [("Colocar", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_KenBurns")
def ken_burns(name, anim):
    """Zoom y paneo lentos a lo largo del clip (fotos y planos fijos). Se adapta a cualquier duracion."""
    h = "KenBurns"
    p = f"{h}.Progreso"
    e = f"({p} + {h}.Suave*({smooth(p)} - {p}))"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("ZoomIni", "Zoom inicial", 1.1, 1, 3), uc("ZoomFin", "Zoom final", 1.3, 1, 3),
           uc("XIni", "Desplazamiento X inicial", -0.03, -0.5, 0.5), uc("XFin", "Desplazamiento X final", 0.03, -0.5, 0.5),
           uc("YIni", "Desplazamiento Y inicial", 0, -0.5, 0.5), uc("YFin", "Desplazamiento Y final", 0, -0.5, 0.5),
           uc("Suave", "Suavizado (0 = lineal)", 1, 0, 1)]
    tools = [Tool(h, "Transform", {
        "Size": I(1.1, f"{h}.ZoomIni + ({h}.ZoomFin - {h}.ZoomIni)*{e}"),
        "Center": I((0.5, 0.5), f"Point(0.5 + {h}.XIni + ({h}.XFin - {h}.XIni)*{e}, 0.5 + {h}.YIni + ({h}.YFin - {h}.YIni)*{e})"),
        "Progreso": I(link=anim, out="Value"), "ZoomIni": I(1.1), "ZoomFin": I(1.3), "XIni": I(-0.03), "XFin": I(0.03),
        "YIni": I(0), "YFin": I(0), "Suave": I(1)}, ucs, (0, 0))]
    pubs = [pub(h, n, lbl, d) for n, lbl, d in (("ZoomIni", "Zoom inicial", 1.1), ("ZoomFin", "Zoom final", 1.3),
                                                ("XIni", "Desplazamiento X inicial", -0.03), ("XFin", "Desplazamiento X final", 0.03),
                                                ("YIni", "Desplazamiento Y inicial", 0), ("YFin", "Desplazamiento Y final", 0),
                                                ("Suave", "Suavizado (0 = lineal)", 1))]
    return macro(name, [(h, "Input")], pubs, h, tools, anim)


@register("Effects", "PRO_FX_Luz_Rayos")
def luz_rayos(name, anim):
    """Rayos de luz volumetricos desde un punto: las luces altas se estiran en copias escaladas desde el origen."""
    h = "Rayos"

    def center(f):
        s = f"(1 + {h}.Largo*{f})"
        return f"Point(0.5 + ({h}.OX - 0.5)*(1 - {s}), 0.5 + ({h}.OY - 0.5)*(1 - {s}))"
    tools = [Tool("Entrada", "PipeRouter", pos=(-550, 0)),
             Tool("Altas", "BrightnessContrast", {"Input": I(link="Entrada"), "Low": I(0.7), "High": I(1), "Saturation": I(0.6)},
                  pos=(-495, -66))]
    t, last = mean_stack("Rayo", "Altas", lambda f: f"1 + {h}.Largo*{f}", center, 8, -495)
    tools += t
    tools += [Tool("Suaviza", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(3), "Input": I(link=last)}, pos=(-165, -66)),
              solid("Tinte", (1, 0.9, 0.7), (-110, -99)),
              merge("Tenido", "Suaviza", "Tinte", (-110, -66), "Multiply"),
              Tool("Refuerzo", "BrightnessContrast", {"Input": I(link="Tenido"), "Gain": I(3)}, pos=(-55, -66))]
    ucs = [uc("OX", "Origen X", 0.7, 0, 1), uc("OY", "Origen Y", 0.85, 0, 1), uc("Largo", "Largo de los rayos", 0.6, 0, 3)]
    tools.append(merge(h, "Entrada", "Refuerzo", (0, 0), "Screen", blend=0.6, ucs=ucs,
                       extra={"OX": I(0.7), "OY": I(0.85), "Largo": I(0.6)}))
    pubs = numbered([pub(h, "OX", "Origen X", 0.7), pub(h, "OY", "Origen Y", 0.85), pub(h, "Largo", "Largo de los rayos", 0.6),
                     pub(h, "Blend", "Intensidad", 0.6), pub("Altas", "Low", "Umbral de luces", 0.7),
                     pub_color("Tinte", "Color de la luz", (1, 0.9, 0.7), "c1"), pub("Refuerzo", "Gain", "Refuerzo", 3)])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


# ----------------------------------------------------------------------- clima
@register("Effects", "PRO_FX_Clima_Lluvia")
def clima_lluvia(name, anim):
    """Lluvia en dos capas (cerca y lejos): motas de ruido estiradas en vertical que caen, inclinadas por el viento."""
    h = "Lluvia"
    v = f"{h}.Velocidad"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Ambiente", "BrightnessContrast", {"Input": I(link="Entrada"), "Gain": I(0.88, f"1 - 0.25*{h}.Oscurecer"),
                                                     "Saturation": I(0.85, f"1 - 0.3*{h}.Oscurecer")}, pos=(-385, 0))]
    last = "Ambiente"
    for i, (scale, low, yblur, speed, blend) in enumerate(((70, 0.9, 30, 0.035, 0.7), (35, 0.93, 60, 0.07, 0.5)), 1):
        y = -165 + 66 * (i - 1)
        tools += [Tool(f"Gotas{i}", "FastNoise", {**frame_format(), "Detail": I(10), "Contrast": I(3), "XScale": I(scale),
                                                   "SeetheRate": I(0),
                                                   "Center": I((0.5, 0.5), f"Point(0.5, 0.5 - time*{speed}*{v})")}, pos=(-330, y)),
                  Tool(f"Umbral{i}", "BrightnessContrast", {"Input": I(link=f"Gotas{i}"), "Saturation": I(0),
                                                             "Low": I(low, f"{low} + (1 - {h}.Cantidad)*0.06"), "High": I(1)}, pos=(-275, y)),
                  Tool(f"Estela{i}", "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0), "XBlurSize": I(0.5),
                                              "YBlurSize": I(yblur), "Input": I(link=f"Umbral{i}")}, pos=(-220, y)),
                  Tool(f"Realce{i}", "BrightnessContrast", {"Input": I(link=f"Estela{i}"), "Gain": I(6)}, pos=(-165, y)),
                  Tool(f"Viento{i}", "Transform", {"Input": I(link=f"Realce{i}"), "Angle": I(10, f"{h}.Viento"), "Size": I(1.4)},
                       pos=(-110, y)),
                  merge(f"Capa{i}", last, f"Viento{i}", (-110 + 55 * i, 0), "Screen", blend=blend, blend_expr=f"{h}.Brillo*{blend}")]
        last = f"Capa{i}"
    ucs = [uc("Cantidad", "Cantidad", 0.5, 0, 1), uc("Brillo", "Brillo de las gotas", 0.8, 0, 2), uc("Velocidad", "Velocidad", 1, 0, 5),
           uc("Viento", "Inclinación por viento (grados)", 10, -45, 45), uc("Oscurecer", "Oscurecer la escena", 0.5, 0, 1)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Cantidad": I(0.5), "Brillo": I(0.8), "Velocidad": I(1),
                                                "Viento": I(10), "Oscurecer": I(0.5)}, ucs, (110, 0)))
    pubs = [pub(h, "Cantidad", "Cantidad", 0.5), pub(h, "Brillo", "Brillo de las gotas", 0.8), pub(h, "Velocidad", "Velocidad", 1),
            pub(h, "Viento", "Inclinación por viento (grados)", 10), pub(h, "Oscurecer", "Oscurecer la escena", 0.5)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Clima_Nieve")
def clima_nieve(name, anim):
    """Nieve en tres capas de profundidad: copos pequenos y lentos al fondo, grandes y rapidos delante, con vaiven."""
    h = "Nieve"
    v = f"{h}.Velocidad"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0))]
    last = "Entrada"
    for i, (scale, low, blur, speed, blend, ph) in enumerate(((70, 0.88, 1, 0.0015, 0.5, 0), (35, 0.9, 2.5, 0.003, 0.7, 2),
                                                             (18, 0.92, 5, 0.005, 0.8, 4)), 1):
        y = -198 + 66 * (i - 1)
        cx = f"0.5 + time*0.001*{h}.Viento*{v} + 0.01*sin(time*0.03*{v} + {ph})"
        tools += [Tool(f"Copos{i}", "FastNoise", {**frame_format(), "Detail": I(8), "Contrast": I(2.5), "XScale": I(scale),
                                                   "SeetheRate": I(0),
                                                   "Center": I((0.5, 0.5), f"Point({cx}, 0.5 - time*{speed}*{v})")}, pos=(-330, y)),
                  Tool(f"Umbral{i}", "BrightnessContrast", {"Input": I(link=f"Copos{i}"), "Saturation": I(0),
                                                             "Low": I(low, f"{low} + (1 - {h}.Cantidad)*0.06"), "High": I(1)}, pos=(-275, y)),
                  Tool(f"Suave{i}", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(blur), "Input": I(link=f"Umbral{i}")},
                       pos=(-220, y)),
                  merge(f"Capa{i}", last, f"Suave{i}", (-165 + 55 * i, 0), "Screen", blend=blend, blend_expr=f"{h}.Brillo*{blend}")]
        last = f"Capa{i}"
    ucs = [uc("Cantidad", "Cantidad", 0.5, 0, 1), uc("Brillo", "Brillo", 1, 0, 2), uc("Velocidad", "Velocidad", 1, 0, 5),
           uc("Viento", "Viento (negativo = a la izquierda)", 0.5, -5, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Cantidad": I(0.5), "Brillo": I(1), "Velocidad": I(1),
                                                "Viento": I(0.5)}, ucs, (110, 0)))
    pubs = [pub(h, "Cantidad", "Cantidad", 0.5), pub(h, "Brillo", "Brillo", 1), pub(h, "Velocidad", "Velocidad", 1),
            pub(h, "Viento", "Viento (negativo = a la izquierda)", 0.5), pub("Suave3", "XBlurSize", "Desenfoque de copos cercanos", 5)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


# ======================================================================= LOTE 9: estilos de texto con su fuente
# Elementos de sombreado de Text+ (nombres copiados de las plantillas oficiales de Resolve 20):
# 1 = relleno, 2 = contorno, 4 = sombra dura, 6 = caja por linea, 8 = sombra suave.
def shade(outline=None, hard=None, soft=None, box=None):
    d = {}

    def rgb(n, c):
        d.update({f"Red{n}": I(c[0]), f"Green{n}": I(c[1]), f"Blue{n}": I(c[2])})
    if outline:
        d.update({"Enabled2": I(1), "Thickness2": I(outline[1]), "OutsideOnly2": I(1)})
        rgb(2, outline[0])
    if hard:
        d.update({"Enabled4": I(1), "ElementShape4": I(0), "Offset4": I(hard[1])})
        rgb(4, hard[0])
    if box:
        d.update({"Enabled6": I(1), "ElementShape6": I(2), "Level6": I(1), "ExtendHorizontal6": I(box[1]),
                  "ExtendVertical6": I(box[2]), "Round6": I(box[3])})
        rgb(6, box[0])
    if soft:
        d.update({"Enabled8": I(1), "Softness8": I(1), "SoftnessX8": I(soft[2]), "SoftnessY8": I(soft[2]), "Offset8": I(soft[1])})
        rgb(8, soft[0])
    return d


def styled(name, text, font, style, size, pos, rgb=(1, 1, 1), center=(0.5, 0.5), left=False, spacing=None, **shading):
    extra = shade(**shading)
    if spacing is not None:
        extra["CharacterSpacing"] = I(spacing) if not isinstance(spacing, str) else I(1, spacing)
    return text_tool(name, text, size, center, pos, rgb, font, style, left, extra)


def mover(name, src, pos, cx="0.5", cy="0.5", size="1", angle=None):
    inputs = {"Input": I(link=src), "Center": I((0.5, 0.5), f"Point({cx}, {cy})"), "Size": I(1, size)}
    if angle:
        inputs["Angle"] = I(0, angle)
    return Tool(name, "Transform", inputs, pos=pos)


def phase(h, a, b):
    """Avance suave (0..1) de una fase de la entrada, sin la salida."""
    return smooth(clamp01(f"({h}.U - {a:g})/{b - a:g}"))


def pop(h, a, b):
    return ease_back(clamp01(f"({h}.U - {a:g})/{b - a:g}"), h)


def style_title(name, h, ucs, inputs, body, layers, pubs, dy_h=0.0, dy_v=0.0, size_v=1.0):
    """Como title(), con un Transform 'Formato' que recoloca y escala el bloque si se marca 'Formato vertical (9:16)'."""
    v = f"{h}.Vertical"
    ucs = ucs[:-2] + [uc("Vertical", "Formato vertical (9:16)", 0, 0, 1, checkbox=True)] + ucs[-2:]
    inputs = {**inputs, "Vertical": I(0)}
    tools = [solid("Lienzo", (0, 0, 0), (-440, 0), alpha=0)] + body
    t, last = compose(layers, x0=110)
    tools += t
    tools.append(Tool("Formato", "Transform", {"Input": I(link=last),
                                               "Center": I((0.5, 0.5 + dy_h), f"Point(0.5, 0.5 + iif({v} > 0.5, {dy_v:g}, {dy_h:g}))"),
                                               "Size": I(1, f"iif({v} > 0.5, {size_v:g}, 1)")}, pos=(385, 0)))
    tools.append(Tool(h, "Transform", {"Input": I(link="Formato"), **inputs}, ucs, (440, 0)))
    entrada = float(inputs["Entrada"].split("Value = ")[1].split(",")[0])
    salida = float(inputs["Salida"].split("Value = ")[1].split(",")[0])
    pubs = numbered(pubs + [pub(h, "Vertical", "Formato vertical (9:16)", 0), pub(h, "Center", "Posición"), pub(h, "Size", "Escala", 1),
                            pub(h, "Entrada", "Duración entrada (% del clip)", entrada),
                            pub(h, "Salida", "Duración salida (% del clip, 0 = sin salida)", salida)])
    a = "PRO" + name.split("_", 2)[-1].replace("_", "") + "Anim"
    return macro(name, [], pubs, h, tools, a).replace('"PRO_ANIM"', f'"{a}"')


def outline_pubs(tool, key, rgb, thickness):
    return [pub_color(tool, "Color del contorno", rgb, f"o{key}", prefix="", suffix="2"),
            pub(tool, "Thickness2", "Grosor del contorno", thickness)]


@register("Titles", "PRO_TTL_Estilo_Viral")
def estilo_viral(name, anim_):
    """Subtitulo de reels/TikTok: Montserrat Black en mayusculas, contorno negro grueso, sombra y palabra clave en amarillo."""
    h = "Viral"
    ucs, inputs = kit(h, 0.12, 0.08, [uc("Rebote", "Rebote", 1.4, 0, 3)], {"Rebote": I(1.4)})
    sh = dict(outline=((0, 0, 0), 0.07), soft=((0, 0, 0), (0.004, -0.01), 4))
    body = [styled("Linea1", "ESTO LO CAMBIA", "Montserrat", "Black", 0.075, (-385, -132), **sh),
            styled("Linea2", "TODO", "Montserrat", "Black", 0.1, (-330, -132), rgb=(1, 0.85, 0.1), **sh),
            mover("Anim1", "Linea1", (-385, -66), cy="0.54", size=f"max(0, {pop(h, 0, 0.55)})"),
            mover("Anim2", "Linea2", (-330, -66), cy="0.44", size=f"max(0, {pop(h, 0.35, 1)})")]
    pubs = [pub("Linea1", "StyledText", "Línea 1"), pub("Linea2", "StyledText", "Palabra clave"),
            *text_pubs("Linea1", "", 0.075, (1, 1, 1), 1),
            pub_color("Linea2", "Color de la palabra clave", (1, 0.85, 0.1), "c2", prefix="", suffix="1"),
            pub("Linea2", "Font", "Fuente de la palabra clave", group="f2"), pub("Linea2", "Style", group="f2"),
            *outline_pubs("Linea1", 1, (0, 0, 0), 0.07), pub(h, "Rebote", "Rebote", 1.4)]
    # la palabra clave copia el contorno de la linea 1
    body[1].inputs.update({ch: I(0, f"Linea1.{ch}") for ch in ("Red2", "Green2", "Blue2", "Thickness2")})
    layers = [("Anim1", stage(h, 0, 0.25)), ("Anim2", stage(h, 0.35, 0.6))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_h=-0.28, dy_v=-0.14, size_v=1.1)


@register("Titles", "PRO_TTL_Estilo_Gancho")
def estilo_gancho(name, anim_):
    """Gancho de los primeros segundos (YouTube/Shorts): Anton amarillo con sombra dura, cae de golpe y tiembla al aterrizar."""
    h = "Gancho"
    land = clamp01(f"{h}.U/0.6")
    k = clamp01(f"({h}.Progreso - {h}.Entrada*0.6)/0.06")
    shake = f"{h}.Temblor*0.012*(1 - {k})*iif({h}.U >= 0.6, 1, 0)"
    ucs, inputs = kit(h, 0.15, 0.08, [uc("Golpe", "Fuerza del golpe", 2, 0, 5), uc("Temblor", "Temblor al aterrizar", 1, 0, 5),
                                      uc("Inclinacion", "Inclinación (grados)", -4, -20, 20)],
                      {"Golpe": I(2), "Temblor": I(1), "Inclinacion": I(-4)})
    body = [styled("Titular", "NO HAGAS ESTO", "Anton", "Regular", 0.12, (-385, -132), rgb=(1, 0.86, 0),
                   outline=((0, 0, 0), 0.03), hard=((0, 0, 0), (0.01, -0.014))),
            styled("Apoyo", "(MIRA HASTA EL FINAL)", "Montserrat", "ExtraBold", 0.035, (-330, -132), outline=((0, 0, 0), 0.06)),
            mover("Anim1", "Titular", (-385, -66), cx=f"0.5 + {shake}*sin(time*2.9)", cy=f"0.54 + {shake}*sin(time*3.7 + 1)",
                 size=f"1 + {h}.Golpe*(1 - {land})*(1 - {land})", angle=f"{h}.Inclinacion"),
            mover("Anim2", "Apoyo", (-330, -66), cy=f"0.42 - 0.02*(1 - {phase(h, 0.6, 1)})")]
    pubs = [pub("Titular", "StyledText", "Titular"), pub("Apoyo", "StyledText", "Texto de apoyo"),
            *text_pubs("Titular", " del titular", 0.12, (1, 0.86, 0), 1), pub_color("Titular", "Color de la sombra", (0, 0, 0), "s1", prefix="", suffix="4"),
            pub("Titular", "Offset4", "Desplazamiento de la sombra"), *text_pubs("Apoyo", " del apoyo", 0.035, (1, 1, 1), 2),
            pub(h, "Golpe", "Fuerza del golpe", 2), pub(h, "Temblor", "Temblor al aterrizar", 1), pub(h, "Inclinacion", "Inclinación (grados)", -4)]
    layers = [("Anim1", f"min(1, 4*{h}.U)*{h}.Xs"), ("Anim2", stage(h, 0.6, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_h=0.05, dy_v=0.12, size_v=0.9)


@register("Titles", "PRO_TTL_Estilo_Trailer")
def estilo_trailer(name, anim_):
    """Trailer de cine: Bebas Neue con letras que se separan lentamente durante todo el clip y aparecen desenfocadas."""
    h = "Trailer"
    s = phase(h, 0, 1)
    ucs, inputs = kit(h, 0.3, 0.2, [uc("Expansion", "Separación de letras durante el clip", 0.15, 0, 1)], {"Expansion": I(0.15)})
    body = [styled("Titulo", "EL ÚLTIMO VIAJE", "Bebas Neue", "Regular", 0.13, (-385, -132), spacing=f"1 + {h}.Expansion*{h}.Progreso"),
            styled("Sub", "PRÓXIMAMENTE", "Montserrat", "Light", 0.025, (-330, -132), rgb=(0.8, 0.8, 0.8), spacing=2.2),
            Tool("Enfoque", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, f"25*(1 - {s})"), "Input": I(link="Titulo")},
                 pos=(-385, -99)),
            mover("Anim1", "Enfoque", (-385, -66), cy="0.53", size=f"1.06 - 0.06*{s}"),
            mover("Anim2", "Sub", (-330, -66), cy="0.41")]
    pubs = [pub("Titulo", "StyledText", "Título"), pub("Sub", "StyledText", "Subtítulo"),
            *text_pubs("Titulo", " del título", 0.13, (1, 1, 1), 1), *text_pubs("Sub", " del subtítulo", 0.025, (0.8, 0.8, 0.8), 2),
            pub(h, "Expansion", "Separación de letras durante el clip", 0.15)]
    layers = [("Anim1", stage(h, 0, 1)), ("Anim2", stage(h, 0.5, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=0.8)


@register("Titles", "PRO_TTL_Estilo_Elegante")
def estilo_elegante(name, anim_):
    """Bodas y lifestyle: nombres en Segoe Script con fecha en Montserrat Light espaciada y una linea fina."""
    h = "Elegante"
    s1, s2 = phase(h, 0, 0.7), phase(h, 0.4, 1)
    ucs, inputs = kit(h, 0.35, 0.2)
    cream = (1, 0.95, 0.88)
    body = [styled("Nombres", "Ana & Luis", "Segoe Script", "Regular", 0.1, (-385, -132), rgb=cream,
                   soft=((0, 0, 0), (0.003, -0.006), 3)),
            styled("Fecha", "28 · OCTUBRE · 2026", "Montserrat", "Light", 0.025, (-330, -132), rgb=cream, spacing=1.8),
            Tool("Desenfoque", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, f"10*(1 - {s1})"), "Input": I(link="Nombres")},
                 pos=(-385, -99)),
            mover("Anim1", "Desenfoque", (-385, -66), cy=f"0.55 - 0.03*(1 - {s1})"),
            mover("Anim2", "Fecha", (-330, -66), cy=f"0.405 - 0.02*(1 - {s2})"),
            rect("MascLinea", (-275, -165), Center=I((0.5, 0.457)), Width=I(0, f"0.18*{s2}"), Height=I(0.0012)),
            solid("Linea", cream, (-275, -132), alpha=0.7, mask="MascLinea")]
    for ch in ("Red", "Green", "Blue"):
        body[1].inputs[f"{ch}1"] = I(1, f"Nombres.{ch}1")
        body[-1].inputs[f"TopLeft{ch}"] = I(1, f"Nombres.{ch}1")
    pubs = [pub("Nombres", "StyledText", "Nombres"), pub("Fecha", "StyledText", "Fecha"),
            *text_pubs("Nombres", " de los nombres", 0.1, cream, 1), pub("Fecha", "Font", "Fuente de la fecha", group="f2"),
            pub("Fecha", "Style", group="f2"), pub("Fecha", "Size", "Tamaño de la fecha", 0.025)]
    layers = [("Anim1", stage(h, 0, 0.7)), ("Linea", f"{h}.Xs"), ("Anim2", stage(h, 0.4, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_v=0.05, size_v=0.95)


@register("Titles", "PRO_TTL_Estilo_Minimal")
def estilo_minimal(name, anim_):
    """Vlog y corporativo limpio: Poppins SemiBold + Poppins Light; sube, aparece y aprieta el espaciado."""
    h = "Minimal"
    s1, s2 = phase(h, 0, 0.7), phase(h, 0.3, 1)
    ucs, inputs = kit(h, 0.25, 0.15)
    body = [styled("Titulo", "Título limpio", "Poppins", "SemiBold", 0.065, (-385, -132), spacing=f"1 + 0.25*(1 - {s1})"),
            styled("Sub", "Subtítulo o descripción breve", "Poppins", "Light", 0.03, (-330, -132), rgb=(0.85, 0.85, 0.85)),
            mover("Anim1", "Titulo", (-385, -66), cy=f"0.53 - 0.04*(1 - {s1})"),
            mover("Anim2", "Sub", (-330, -66), cy=f"0.455 - 0.03*(1 - {s2})")]
    pubs = [pub("Titulo", "StyledText", "Título"), pub("Sub", "StyledText", "Subtítulo"),
            *text_pubs("Titulo", " del título", 0.065, (1, 1, 1), 1), *text_pubs("Sub", " del subtítulo", 0.03, (0.85, 0.85, 0.85), 2)]
    layers = [("Anim1", stage(h, 0, 0.7)), ("Anim2", stage(h, 0.3, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=0.85)


@register("Titles", "PRO_TTL_Estilo_Documental")
def estilo_documental(name, anim_):
    """Documental / video ensayo: Roboto Condensed en caja negra y lugar o fecha en caja blanca, abajo a la izquierda."""
    h = "Documental"
    s1, s2 = phase(h, 0, 0.6), phase(h, 0.35, 1)
    ucs, inputs = kit(h, 0.2, 0.12)
    body = [styled("Titulo", "TÍTULO DEL REPORTAJE", "Roboto Condensed", "Bold", 0.042, (-385, -132), center=(0.08, 0.2), left=True,
                   box=((0.05, 0.05, 0.05), 0.015, 0.012, 0)),
            styled("Dato", "Ciudad de México · 1985", "Roboto", "Regular", 0.026, (-330, -132), rgb=(0.1, 0.1, 0.1), center=(0.08, 0.135),
                   left=True, box=((0.95, 0.95, 0.95), 0.012, 0.008, 0)),
            mover("Anim1", "Titulo", (-385, -66), cx=f"0.5 - 0.3*(1 - {s1})"),
            mover("Anim2", "Dato", (-330, -66), cx=f"0.5 - 0.3*(1 - {s2})")]
    pubs = [pub("Titulo", "StyledText", "Título"), pub("Dato", "StyledText", "Lugar o fecha"),
            *text_pubs("Titulo", " del título", 0.042, (1, 1, 1), 1),
            pub_color("Titulo", "Color de la caja del título", (0.05, 0.05, 0.05), "b1", prefix="", suffix="6"),
            *text_pubs("Dato", " del dato", 0.026, (0.1, 0.1, 0.1), 2),
            pub_color("Dato", "Color de la caja del dato", (0.95, 0.95, 0.95), "b2", prefix="", suffix="6")]
    layers = [("Anim1", stage(h, 0, 0.6)), ("Anim2", stage(h, 0.35, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_v=0.15)


@register("Titles", "PRO_TTL_Estilo_Deportivo")
def estilo_deportivo(name, anim_):
    """Deportes y gaming competitivo: Teko condensada con sombra dura y barra inclinada de color; entra rapido con desenfoque."""
    h = "Deportivo"
    e1, e2, eb = phase(h, 0.2, 0.7), phase(h, 0.45, 1), phase(h, 0, 0.5)
    ucs, inputs = kit(h, 0.2, 0.1)
    accent = (0.9, 0.1, 0.15)
    body = [rect("MascBarra", (-440, -165), Center=I((0.3, 0.2), f"Point(0.06 + 0.25*{eb}, 0.205)"), Width=I(0.5, f"0.5*{eb}"),
                 Height=I(0.085), Angle=I(6)),
            solid("Barra", accent, (-440, -132), mask="MascBarra"),
            styled("Nombre", "APELLIDO", "Teko", "SemiBold", 0.11, (-385, -132), center=(0.08, 0.2), left=True,
                   hard=((0, 0, 0), (0.006, -0.01))),
            styled("Dato", "DELANTERO · 25 GOLES", "Teko", "Regular", 0.045, (-330, -132), rgb=accent, center=(0.08, 0.125), left=True),
            Tool("Rafaga1", "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0), "XBlurSize": I(0, f"40*(1 - {e1})"), "YBlurSize": I(0),
                                     "Input": I(link="Nombre")}, pos=(-385, -99)),
            Tool("Rafaga2", "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0), "XBlurSize": I(0, f"40*(1 - {e2})"), "YBlurSize": I(0),
                                     "Input": I(link="Dato")}, pos=(-330, -99)),
            mover("Anim1", "Rafaga1", (-385, -66), cx=f"0.5 - 0.6*(1 - {e1})"),
            mover("Anim2", "Rafaga2", (-330, -66), cx=f"0.5 - 0.6*(1 - {e2})")]
    body[3].inputs.update({f"{ch}1": I(1, f"Barra.TopLeft{ch}") for ch in ("Red", "Green", "Blue")})
    pubs = [pub("Nombre", "StyledText", "Nombre"), pub("Dato", "StyledText", "Dato"),
            *text_pubs("Nombre", " del nombre", 0.11, (1, 1, 1), 1), pub_color("Barra", "Color del equipo", accent, "c2"),
            pub("Dato", "Font", "Fuente del dato", group="f3"), pub("Dato", "Style", group="f3"), pub("Dato", "Size", "Tamaño del dato", 0.045)]
    layers = [("Barra", f"{h}.Xs"), ("Anim1", stage(h, 0.2, 0.5)), ("Anim2", stage(h, 0.45, 0.8))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_v=0.15)


@register("Titles", "PRO_TTL_Estilo_Retro80")
def estilo_retro80(name, anim_):
    """Synthwave de los 80: Monoton rosa con sombra cian desplazada y halo; se enciende parpadeando."""
    h = "Retro"
    on = f"iif({h}.U < 1, iif(sin(time*2.3)*sin(time*0.9 + 1) > 0, 1, 0.15), 1)"
    ucs, inputs = kit(h, 0.25, 0.1, [uc("Glow", "Brillo del halo", 0.8, 0, 1), uc("F", "Encendido interno", 1, 0, 1, clamp=False)],
                      {"Glow": I(0.8), "F": I(1, on)})
    body = [styled("Titulo", "NEON NIGHTS", "Monoton", "Regular", 0.1, (-385, -132), rgb=(1, 0.2, 0.8), hard=((0, 0.9, 1), (0.006, -0.009))),
            styled("Sub", "SYNTHWAVE · 1986", "Montserrat", "Bold", 0.03, (-330, -132), rgb=(0, 0.9, 1), spacing=1.8),
            mover("Anim1", "Titulo", (-385, -66), cy="0.53"),
            Tool("Halo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(30), "Input": I(link="Anim1")}, pos=(-385, -33)),
            mover("Anim2", "Sub", (-330, -66), cy=f"0.42 - 0.02*(1 - {phase(h, 0.5, 1)})")]
    pubs = [pub("Titulo", "StyledText", "Título"), pub("Sub", "StyledText", "Subtítulo"),
            *text_pubs("Titulo", " del título", 0.1, (1, 0.2, 0.8), 1), pub_color("Titulo", "Color de la sombra", (0, 0.9, 1), "s1", prefix="", suffix="4"),
            pub("Titulo", "Offset4", "Desplazamiento de la sombra"), pub(h, "Glow", "Brillo del halo", 0.8),
            pub_color("Sub", "Color del subtítulo", (0, 0.9, 1), "c2", prefix="", suffix="1")]
    layers = [("Halo", f"{h}.Glow*{h}.F*{h}.Xs"), ("Anim1", f"(0.3 + 0.7*{h}.F)*{h}.Xs"), ("Anim2", stage(h, 0.5, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=0.8)


@register("Titles", "PRO_TTL_Estilo_Gamer")
def estilo_gamer(name, anim_):
    """Videojuego retro: Press Start 2P con sombra de pixel, aparece a saltos y 'PRESS START' parpadea."""
    h = "Gamer"
    s = clamp01(f"{h}.U/0.6")
    ucs, inputs = kit(h, 0.2, 0.05)
    body = [styled("Titulo", "NIVEL 1", "Press Start 2P", "Regular", 0.06, (-385, -132), rgb=(0.3, 1, 0.35), hard=((0, 0, 0), (0.005, -0.008))),
            styled("Sub", "PRESS START", "Press Start 2P", "Regular", 0.025, (-330, -132), hard=((0, 0, 0), (0.003, -0.005))),
            mover("Anim1", "Titulo", (-385, -66), cy="0.54", size=f"floor(4*{s} + 0.0001)/4"),
            mover("Anim2", "Sub", (-330, -66), cy="0.43")]
    pubs = [pub("Titulo", "StyledText", "Título"), pub("Sub", "StyledText", "Texto que parpadea"),
            *text_pubs("Titulo", " del título", 0.06, (0.3, 1, 0.35), 1), *text_pubs("Sub", " del parpadeo", 0.025, (1, 1, 1), 2)]
    layers = [("Anim1", f"{h}.Xs*iif({h}.U > 0, 1, 0)"), ("Anim2", f"{h}.Xs*iif({h}.U >= 1, 1, 0)*iif(sin(time*0.3) > 0, 1, 0)")]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=1.2)


@register("Titles", "PRO_TTL_Estilo_Nota")
def estilo_nota(name, anim_):
    """Estilo UGC / nota a mano: Ink Free con subrayado de rotulador que se dibuja y un vaiven suave."""
    h = "Nota"
    g = phase(h, 0.3, 1)
    ucs, inputs = kit(h, 0.3, 0.12, [uc("Ancho", "Ancho del subrayado", 0.36, 0.02, 1), uc("Vaiven", "Vaivén", 1, 0, 5)],
                      {"Ancho": I(0.36), "Vaiven": I(1)})
    body = [styled("Texto", "nota rápida :)", "Ink Free", "Regular", 0.075, (-385, -132), soft=((0, 0, 0), (0.003, -0.005), 3)),
            mover("Anim1", "Texto", (-385, -66), cy=f"0.52 - 0.02*(1 - {phase(h, 0, 0.5)})", angle=f"{h}.Vaiven*1.5*sin(time*0.12)"),
            rect("MascRaya", (-330, -165), Center=I((0.32, 0.455), f"Point(0.5 - {h}.Ancho/2 + {h}.Ancho*{g}/2, 0.455)"),
                 Width=I(0, f"{h}.Ancho*{g}"), Height=I(0.01), Angle=I(-2), CornerRadius=I(0.5)),
            solid("Raya", (1, 0.85, 0.1), (-330, -132), alpha=0.85, mask="MascRaya")]
    pubs = [pub("Texto", "StyledText", "Texto"), *text_pubs("Texto", "", 0.075, (1, 1, 1), 1),
            pub_color("Raya", "Color del subrayado", (1, 0.85, 0.1), "c2"), pub(h, "Ancho", "Ancho del subrayado", 0.36),
            pub(h, "Vaiven", "Vaivén", 1)]
    layers = [("Raya", f"{h}.Xs"), ("Anim1", stage(h, 0, 0.5))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_v=0.05)


# ----------------------------------------------------------------------- efectos para horizontal y vertical
@register("Effects", "PRO_FX_Din_Eco")
def din_eco(name, anim):
    """Eco o estela (velocity edits): copias retrasadas del propio clip que se desvanecen detras del movimiento."""
    h = "Eco"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0))]
    last = "Entrada"
    for k in range(1, 5):
        tools += [Tool(f"Retraso{k}", "TimeSpeed", {"Input": I(link="Entrada"), "Speed": I(1), "Delay": I(2 * k, f"{k}*{h}.Separacion")},
                       pos=(-385 + 55 * k, -66)),
                  merge(f"Copia{k}", last, f"Retraso{k}", (-385 + 55 * k, 0), blend=0.5,
                        blend_expr=f"{h}.Intensidad*pow({h}.Decaimiento, {k})")]
        last = f"Copia{k}"
    tools.append(merge("Frente", last, "Entrada", (-55, 0), blend=1, blend_expr=f"1 - {h}.Fantasma"))
    ucs = [uc("Separacion", "Separación (fotogramas)", 2, 1, 15), uc("Intensidad", "Intensidad", 0.8, 0, 1),
           uc("Decaimiento", "Decaimiento", 0.6, 0.1, 1), uc("Fantasma", "Original transparente", 0, 0, 1)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Frente"), "Separacion": I(2), "Intensidad": I(0.8), "Decaimiento": I(0.6),
                                                "Fantasma": I(0)}, ucs, (0, 0)))
    pubs = [pub(h, "Separacion", "Separación (fotogramas)", 2), pub(h, "Intensidad", "Intensidad", 0.8),
            pub(h, "Decaimiento", "Decaimiento", 0.6), pub(h, "Fantasma", "Original transparente", 0)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_DesenfoqueMovimiento")
def din_desenfoque_movimiento(name, anim):
    """Desenfoque de movimiento direccional (DirectionalBlur) con pico opcional al inicio, para cortes de velocidad."""
    h = "Movimiento"
    pico = f"(1 - {h}.Pico + {h}.Pico*(1 - {smooth(clamp01(f'{h}.Progreso/max({h}.Duracion, 0.0001)'))}))"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Intensidad", "Intensidad", 0.1, 0, 1),
           uc("Pico", "Solo al inicio (1 = se apaga)", 0, 0, 1), uc("Duracion", "Duración del pico (% del clip)", 0.2, 0.01, 1)]
    tools = [Tool(h, "DirectionalBlur", {"Length": I(0.1, f"{h}.Intensidad*{pico}"), "Angle": I(0), "ClippingMode": I(FuID("None")),
                                         "Progreso": I(link=anim, out="Value"), "Intensidad": I(0.1), "Pico": I(0), "Duracion": I(0.2)},
                  ucs, (0, 0))]
    pubs = [pub(h, "Intensidad", "Intensidad", 0.1), pub(h, "Angle", "Ángulo (grados)", 0),
            pub(h, "Pico", "Solo al inicio (1 = se apaga)", 0), pub(h, "Duracion", "Duración del pico (% del clip)", 0.2)]
    return macro(name, [(h, "Input")], pubs, h, tools, anim)


@register("Effects", "PRO_FX_Social_Reencuadre")
def social_reencuadre(name, anim):
    """Clip horizontal en timeline vertical (o al reves) con fondo del mismo clip ampliado y desenfocado en lugar de barras negras."""
    h = "Reencuadre"
    ac, at = f"{h}.AspClip", f"{h}.AspTL"
    wide = f"{ac} > {at}"
    tools = [Tool("Entrada", "PipeRouter", pos=(-330, 0)),
             Tool("Ampliar", "Transform", {"Input": I(link="Entrada"),
                                           "Size": I(3.2, f"max({ac}/{at}, {at}/{ac})*{h}.ZoomFondo")}, pos=(-275, -66)),
             Tool("Difuminar", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(40), "Input": I(link="Ampliar")}, pos=(-220, -66)),
             Tool("Fondo", "BrightnessContrast", {"Input": I(link="Difuminar"), "Gain": I(0.7), "Saturation": I(1.1)}, pos=(-165, -66)),
             Tool("Frente", "Transform", {"Input": I(link="Entrada"), "Size": I(1, f"{h}.EscalaFrente"),
                                          "Center": I((0.5, 0.5), f"Point(0.5, 0.5 + {h}.MoverY)")}, pos=(-220, 33)),
             rect("MascFrente", (-165, 66), Center=I((0.5, 0.5), f"Point(0.5, 0.5 + {h}.MoverY)"),
                  Width=I(1, f"iif({wide}, 1, {ac}/{at})*{h}.EscalaFrente"),
                  Height=I(0.5625, f"iif({wide}, 1/{ac}, 1/{at})*{h}.EscalaFrente"), CornerRadius=I(0, f"{h}.Redondeo"))]
    ucs = [uc("AspClip", "Aspecto del clip (16:9 = 1.778, 9:16 = 0.5625)", 1.7778, 0.4, 3),
           uc("AspTL", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 0.5625, 0.4, 3),
           uc("ZoomFondo", "Zoom extra del fondo", 1.05, 1, 3), uc("EscalaFrente", "Escala del clip", 1, 0.3, 3),
           uc("MoverY", "Posición vertical del clip", 0, -0.5, 0.5), uc("Redondeo", "Redondeo de esquinas", 0, 0, 0.5)]
    tools.append(merge(h, "Fondo", "Frente", (-110, 0), blend=1, ucs=ucs, extra={
        "EffectMask": I(link="MascFrente", out="Mask"), "AspClip": I(1.7778), "AspTL": I(0.5625), "ZoomFondo": I(1.05),
        "EscalaFrente": I(1), "MoverY": I(0), "Redondeo": I(0)}))
    pubs = [pub(h, "AspClip", "Aspecto del clip (16:9 = 1.778, 9:16 = 0.5625)", 1.7778),
            pub(h, "AspTL", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 0.5625),
            pub("Difuminar", "XBlurSize", "Desenfoque del fondo", 40), pub("Fondo", "Gain", "Brillo del fondo", 0.7),
            pub(h, "ZoomFondo", "Zoom extra del fondo", 1.05), pub(h, "EscalaFrente", "Escala del clip", 1),
            pub(h, "MoverY", "Posición vertical del clip", 0), pub(h, "Redondeo", "Redondeo de esquinas", 0)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Social_ZonaSegura")
def social_zona_segura(name, anim):
    """Guia de edicion: zonas que tapan los botones y textos de TikTok/Reels/Shorts (vertical) o marcos seguros (horizontal).
    Quitala antes de exportar."""
    h = "Zonas"
    asp, v = f"{h}.Aspecto", f"{h}.Vertical"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)), solid("Lienzo", (0, 0, 0), (-385, 0), alpha=0)]
    bands = [("Sup", f"Point(0.5, 1 - {h}.MSup/2)", "1", f"{h}.MSup/{asp}"),
             ("Inf", f"Point(0.5, {h}.MInf/2)", "1", f"{h}.MInf/{asp}"),
             ("Der", f"Point(1 - {h}.MDer/2, 0.5)", f"{h}.MDer", f"1.05/{asp}")]
    layers = []
    for i, (n, c, w, ht) in enumerate(bands):
        tools += [rect(f"Masc{n}", (-330 + 55 * i, -132), Center=I((0.5, 0.5), c), Width=I(1, w), Height=I(0.1, ht)),
                  solid(f"Zona{n}", (1, 0.15, 0.15), (-330 + 55 * i, -99), mask=f"Masc{n}")]
        layers.append((f"Zona{n}", f"0.35*{v}"))
    for i, (n, k) in enumerate((("Accion", 0.93), ("Titulos", 0.9))):
        tools += [rect(f"Masc{n}", (-165 + 55 * i, -132), Width=I(k), Height=I(k / 1.7778, f"{k:g}/{asp}"), Solid=I(0), BorderWidth=I(0.002)),
                  solid(f"Marco{n}", (0.2, 1, 0.4), (-165 + 55 * i, -99), mask=f"Masc{n}")]
        layers.append((f"Marco{n}", f"0.8*(1 - {v})"))
    for z in ("ZonaSup", "ZonaInf"):
        next(t for t in tools if t.name == z).inputs.update({f"TopLeft{ch}": I(1, f"ZonaDer.TopLeft{ch}") for ch in ("Red", "Green", "Blue")})
    t, last = compose(layers, x0=0)
    tools += t
    tools.append(merge("Guia", "Entrada", last, (330, 0), blend=1))
    ucs = [uc("Vertical", "Vertical (desmarcado = marcos 16:9)", 1, 0, 1, checkbox=True),
           uc("MSup", "Zona superior", 0.1, 0, 0.5), uc("MInf", "Zona inferior (descripción y subtítulos)", 0.22, 0, 0.5),
           uc("MDer", "Zona derecha (botones)", 0.13, 0, 0.5),
           uc("Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 0.5625, 0.4, 3)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Guia"), "Vertical": I(1), "MSup": I(0.1), "MInf": I(0.22), "MDer": I(0.13),
                                                "Aspecto": I(0.5625)}, ucs, (385, 0)))
    pubs = numbered([pub(h, "Vertical", "Vertical (desmarcado = marcos 16:9)", 1), pub(h, "MSup", "Zona superior", 0.1),
                     pub(h, "MInf", "Zona inferior (descripción y subtítulos)", 0.22), pub(h, "MDer", "Zona derecha (botones)", 0.13),
                     pub_color("ZonaDer", "Color de las zonas", (1, 0.15, 0.15), "c1"), pub("Guia", "Blend", "Opacidad de la guía", 1),
                     pub(h, "Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 0.5625)])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Look_Digicam")
def look_digicam(name, anim):
    """Camara digital de los 2000 (Y2K): saturacion y brillo marcados, ruido fino y fecha naranja en la esquina."""
    h = "Digicam"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Look", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(1.25), "Contrast": I(0.12), "Gain": I(1.05)},
                  pos=(-385, 0))]
    t, last = blk_cast("Frio", "Look", -330, (0.96, 1, 1), 1)
    tools += t
    t, last = blk_bloom("Bl", last, -275, low=0.65, radius=20, blend=0.35)
    tools += t
    t, last = blk_grain("Gr", last, None, -110, scale=90)
    tools += t
    tools[-1].inputs["Blend"] = I(0.06)
    tools += [solid("Lienzo", (0, 0, 0), (0, -66), alpha=0),
              text_tool("Fecha", "'26 10 28", 0.04, (0.84, 0.08), (0, -165), rgb=(1, 0.55, 0.1), font="OCR A Extended", style="Regular"),
              Tool("FechaHalo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(6), "Input": I(link="Fecha")}, pos=(55, -165))]
    t, over = compose([("FechaHalo", "0.7"), ("Fecha", None)], x0=0)
    tools += t
    tools.append(merge(h, last, over, (165, 0), blend=1))
    pubs = numbered([pub("Fecha", "StyledText", "Fecha"), pub_color("Fecha", "Color de la fecha", (1, 0.55, 0.1), "c1", prefix="", suffix="1"),
                     pub("Fecha", "Center", "Posición de la fecha"), pub(h, "Blend", "Opacidad de la fecha", 1),
                     pub("Look", "Saturation", "Saturación", 1.25), pub("BlBloom", "Blend", "Brillo", 0.35), pub("GrGrano", "Blend", "Ruido", 0.06)])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Transitions", "PRO_TR_Remolino")
def tr_remolino(name, anim):
    """Remolino: la imagen se retuerce (Vortex) hasta el centro de la transicion y se destuerce ya en el clip B."""
    h = "Mezcla"
    p = f"{h}.Progreso"
    bell = f"sin({p}*{PI})*sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Giro", "Giro (grados)", 400, -1500, 1500), uc("Radio", "Radio del remolino", 1.2, 0.1, 3)]
    tools = [Tool(h, "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.4)/0.2"))), "Progreso": I(link=anim, out="Value"),
                                  "Giro": I(400), "Radio": I(1.2)}, ucs, (0, 0)),
             Tool("Remolino", "Vortex", {"Input": I(link=h), "Angle": I(0, f"{h}.Giro*{bell}"), "Size": I(1.2, f"{h}.Radio")}, pos=(55, 0)),
             Tool("Suaviza", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, f"6*{bell}"), "Input": I(link="Remolino")}, pos=(110, 0))]
    pubs = [pub(h, "Giro", "Giro (grados)", 400), pub(h, "Radio", "Radio del remolino", 1.2)]
    return macro(name, [(h, "Background"), (h, "Foreground")], pubs, "Suaviza", tools, anim)


if __name__ == "__main__":
    for (cat, name), fn in BUILT.items():
        anim = "PRO" + name.split("_", 2)[-1].replace("_", "") + "Anim"
        out = ROOT / cat / f"{name}.setting"
        out.write_text(fn(name, anim), encoding="utf-8", newline="\n")
        print(f"{cat}/{out.name}")
