"""
Genera las plantillas de Fusion del lote "Dinamico y Cine".

Uso:  python tools/build_templates.py      (escribe en Effects/ y Transitions/)
Las 4 piezas del piloto estan escritas a mano y este script no las toca.
"""
import math
import re
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
                                                      "Gain": I(1, f"1 + 0.2*{h}.Danos*{bell}*sin(time*9.1)*sin(time*3.7 + 1)")}, pos=(55, 0))]
    t, last = blk_dust_scratch("Dano", "Parpadeo", h, 110)
    tools += t
    # fuga de luz calida que cruza la tira (como PRO_TR_LightLeak), maxima a mitad de la transicion
    tools += [ellipse("FugaMasc1", (330, -132), SoftEdge=I(0.5), Width=I(0.9), Height=I(0.9),
                      Center=I((0.5, 0.5), f"Point(-0.3 + 1.6*{p}, 0.6 + 0.1*{bell})")),
              ellipse("FugaMasc2", (385, -132), SoftEdge=I(0.4), Width=I(0.6), Height=I(0.6),
                      Center=I((0.5, 0.5), f"Point(1.2 - 1.2*{p}, 0.35)")),
              solid("FugaColor1", (1, 0.55, 0.2), (330, -99), mask="FugaMasc1"),
              solid("FugaColor2", (1, 0.25, 0.1), (385, -99), mask="FugaMasc2"),
              merge("Fuga1", last, "FugaColor1", (385, 0), "Screen", blend=0, blend_expr=f"{h}.Fuga*{bell}"),
              merge("Fuga2", "Fuga1", "FugaColor2", (440, 0), "Screen", blend=0, blend_expr=f"0.8*{h}.Fuga*{bell}")]
    ucs, inputs = film_host(h, anim, (495, 0), extra_ucs=[
        uc("Alejamiento", "Alejamiento", 0.3, 0, 0.6), uc("Fuga", "Fuga de luz", 0.7, 0, 1),
        uc("Escala", "Escala interna", 1, 0, 2, clamp=False)],
        extra_inputs={"Alejamiento": I(0.3), "Fuga": I(0.7), "Escala": I(1, f"1 - {h}.Alejamiento*{bell}")}, danos=0.35)
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Fuga2"), **inputs}, ucs, (495, 0)))
    pubs = numbered([pub(h, "Alejamiento", "Alejamiento", 0.3), pub(h, "Danos", "Daños de película (polvo, rayas, parpadeo)", 0.35),
                     pub_color("LuzIzq", "Color de la luz en perforaciones", (0.92, 0.88, 0.78), "c1"),
                     pub(h, "Fuga", "Fuga de luz", 0.7), pub_color("FugaColor1", "Color principal de la fuga", (1, 0.55, 0.2), "c2"),
                     pub_color("FugaColor2", "Color secundario de la fuga", (1, 0.25, 0.1), "c3")])
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
                  "Width": I(0.03, f"{h}.Largo"), "Height": I(0.0034, f"{h}.Grosor*{h}.Aspecto")}
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
    pubs += vertical_text(tools, h, ("Texto",), factor=2.2, pubs=pubs)
    return macro(name, [], pubs, "Posicion", tools, anim)


# ======================================================================= GRAFICOS ANIMADOS (lote 7)
# RectangleMask.Height es fraccion del ALTO del cuadro. Estos titulos estan pensados para 16:9, asi que un alto
# pensado en unidades del ancho se multiplica por W16 (= 16/9) para que las formas tengan la proporcion exacta.
W16 = 1.7778


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


def title(name, h, ucs, inputs, body, layers, pubs, x_end=440, vertical=True, **fmt):
    """Lienzo transparente + cuerpo + capas + transform final que aloja los controles (Posicion/Escala).
    Con vertical=True usa style_title (casilla 'Formato vertical'); fmt: dy_v, size_v, dx_v."""
    if vertical:
        for pp in pubs:
            if isinstance(pp, dict) and isinstance(pp["default"], str):
                pp["default"] = float(pp["default"])
        return style_title(name, h, ucs, inputs, body, layers, pubs, **fmt)
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
                 Height=I(0.0213, f"{h}.Alto*{W16}"), CornerRadius=I(0.5, f"{h}.Redondeo")),
            solid("Pista", (1, 1, 1), (-385, -66), alpha=0.25, mask="MascFondo"),
            rect("MascRelleno", (-330, -99), Center=I((0.5, 0.06), f"Point(0.5 - {h}.Ancho/2 + {h}.Ancho*{p}/2, {h}.PosY)"),
                 Width=I(0, f"{h}.Ancho*{p}"), Height=I(0.0213, f"{h}.Alto*{W16}"), CornerRadius=I(0.5, f"{h}.Redondeo")),
            solid("Relleno", (1, 0.25, 0.25), (-330, -66), mask="MascRelleno")]
    pubs = [pub_color("Pista", "Color de la pista", (1, 1, 1), 1), pub("Pista", "TopLeftAlpha", "Opacidad de la pista", 0.25),
            pub_color("Relleno", "Color del relleno", (1, 0.25, 0.25), 5), pub(h, "Ancho", "Ancho total", 0.8),
            pub(h, "Alto", "Grosor", 0.012), pub(h, "PosY", "Altura en pantalla", 0.06), pub(h, "Redondeo", "Redondeo", 0.5)]
    return title(name, h, ucs, inputs, body, [("Pista", f"{h}.Xs*{stage(h, 0, 1)}"), ("Relleno", f"{h}.Xs")], pubs, dy_v=-0.3)


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
    return title(name, h, ucs, inputs, body, [("Numero", stage(h, 0, 0.6)), ("Etiqueta", stage(h, 0.4, 1))], pubs, size_v=2.0)


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
                    Width=I(0.03), Height=I(0.03 * W16), Solid=I(0), BorderWidth=I(0.002)),
            rect("MascLinea", (-275, -132), Width=I(0, f"{h}.Largo*{sl}"), Height=I(0.0025 * W16), Angle=I(35, f"{h}.Angulo"),
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
    return title(name, h, ucs, inputs, body, layers, pubs, vertical=False)


@register("Titles", "PRO_TTL_EndScreen")
def end_screen(name, anim):
    h = "Final"
    ucs, inputs = kit(h, 0.15, 0.08)
    body = [text_tool("Titulo", "¡GRACIAS POR VER!", 0.06, (0.5, 0.86), (-385, -165)),
            rect("MascVideo1", (-385, -132), Center=I((0.28, 0.55)), Width=I(0.36), Height=I(0.36), CornerRadius=I(0.06),
                 Solid=I(0), BorderWidth=I(0.003)),
            rect("MascVideo2", (-330, -132), Center=I((0.72, 0.55)), Width=I(0.36), Height=I(0.36), CornerRadius=I(0.06),
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
    body = [rect("MascBoton", (-385, -132), Center=I((0.5, 0.2)), Width=I(0.26), Height=I(0.065 * W16), CornerRadius=I(1)),
            solid("Boton", (0.9, 0.1, 0.1), (-385, -99), mask="MascBoton"),
            text_tool("Texto", "SUSCRÍBETE", 0.04, (0.5, 0.2), (-330, -99), extra={"CharacterSpacing": I(1.1)}),
            merge("Pastilla", "Lienzo", "Boton", (-275, -66)),
            merge("ConTexto", "Pastilla", "Texto", (-220, -66)),
            Tool("Pop", "Transform", {"Input": I(link="ConTexto"), "Pivot": I((0.5, 0.2)), "Center": I((0.5, 0.2)),
                                      "Size": I(1, f"max(0, {h}.E*{h}.Xs*(1 - 0.12*{pulse}))")}, pos=(-165, -66))]
    pubs = [pub("Texto", "StyledText", "Texto"), pub_color("Boton", "Color del botón", (0.9, 0.1, 0.1), 2),
            pub_color("Texto", "Color del texto", (1, 1, 1), 5, prefix="", suffix="1"), pub(h, "Rebote", "Rebote", 1.5)]
    return title(name, h, ucs, inputs, body, [("Pop", None)], pubs, size_v=2.2, dy_v=-0.05)


@register("Titles", "PRO_TTL_Cita")
def cita(name, anim):
    h = "Cita"
    sl = stage(h, 0.3, 0.8)
    ucs, inputs = kit(h, 0.25, 0.12)
    body = [text_tool("Comillas", "“", 0.25, (0.5, 0.72), (-385, -132), rgb=(0.95, 0.75, 0.3), font="Georgia"),
            text_tool("Frase", "La creatividad es la inteligencia\ndivirtiéndose.", 0.05, (0.5, 0.52), (-330, -132),
                      font="Georgia", style="Italic"),
            rect("MascRaya", (-275, -165), Center=I((0.5, 0.38)), Width=I(0, f"0.12*{sl}"), Height=I(0.002 * W16)),
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
    return title(name, h, ucs, inputs, body, layers, pubs, size_v=1.6)


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
            rect("MascSup", (-275, -165), Center=I((0.5, 0.6)), Width=I(0, f"0.3*{sl}"), Height=I(0.0015 * W16)),
            rect("MascInf", (-220, -165), Center=I((0.5, 0.385)), Width=I(0, f"0.3*{sl}"), Height=I(0.0015 * W16)),
            solid("LineaSup", (1, 1, 1), (-275, -132), alpha=0.7, mask="MascSup"),
            solid("LineaInf", (1, 1, 1), (-220, -132), alpha=0.7, mask="MascInf")]
    pubs = [pub("Principal", "StyledText", "Título"), pub("Sub", "StyledText", "Subtítulo"),
            pub("Principal", "Font", "Fuente", group=3), pub("Principal", "Style", group=3), pub("Principal", "Size", "Tamaño", 0.075),
            pub_color("Principal", "Color", (1, 1, 1), 6, prefix="", suffix="1"), pub(h, "Tracking", "Separación inicial de letras", 0.4)]
    layers = [("Principal", s_main), ("LineaSup", f"{h}.Xs"), ("LineaInf", f"{h}.Xs"), ("Sub", stage(h, 0.5, 1))]
    return title(name, h, ucs, inputs, body, layers, pubs, size_v=1.2)


@register("Titles", "PRO_TTL_Separador")
def separador(name, anim):
    h = "Separador"
    sl = stage(h, 0, 0.7)
    ucs, inputs = kit(h, 0.25, 0.12, [uc("Largo", "Largo", 0.4, 0.02, 1)], {"Largo": I(0.4)})
    body = [rect("MascLinea", (-385, -132), Center=I((0.5, 0.5)), Width=I(0, f"{h}.Largo*{sl}"), Height=I(0.0018 * W16)),
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
    return title(name, h, ucs, inputs, body, layers, pubs, size_v=1.6)


@register("Titles", "PRO_TTL_LineaTiempo")
def linea_tiempo(name, anim):
    h = "Cronologia"
    n = 5
    xs = [0.15 + 0.7 * i / (n - 1) for i in range(n)]
    years = ["1990", "2000", "2010", "2020", "2030"]
    ucs, inputs = kit(h, 0.6, 0.1)
    body = [rect("MascBase", (-385, -198), Center=I((0.5, 0.5), f"Point(0.15 + 0.35*{stage(h, 0, 0.3)}, 0.5)"),
                 Width=I(0, f"0.7*{stage(h, 0, 0.3)}"), Height=I(0.002 * W16)),
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
             rect("MascTarjeta", (-275, -165), Width=I(0.85, f"{h}.Tamano"), Height=I(0.85, f"{h}.Tamano"),
                  CornerRadius=I(0.08, f"{h}.Redondeo")),
             rect("MascSombra", (-220, -165), Width=I(0.85, f"{h}.Tamano"), Height=I(0.85, f"{h}.Tamano"),
                  CornerRadius=I(0.08, f"{h}.Redondeo"), SoftEdge=I(0.03), Center=I((0.5, 0.49))),
             solid("Sombra", (0, 0, 0), (-220, -132), mask="MascSombra"),
             merge("ConSombra", "Fondo", "Sombra", (-165, -66), blend=0.35),
             merge(h, "ConSombra", "Reducir", (-110, 0), blend=1, extra={"EffectMask": I(link="MascTarjeta", out="Mask")},
                   ucs=[uc("Tamano", "Tamaño", 0.85, 0.3, 1), uc("Redondeo", "Redondeo de esquinas", 0.08, 0, 0.5)])]
    tools[-1].inputs.update({"Tamano": I(0.85), "Redondeo": I(0.08)})
    pubs = [pub(h, "Tamano", "Tamaño", 0.85), pub(h, "Redondeo", "Redondeo de esquinas", 0.08),
            pub_color("Fondo", "Color del fondo", (0.95, 0.93, 0.9), 3), pub("ConSombra", "Blend", "Sombra", 0.35)]
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
    return title(name, h, ucs, inputs, body, [("Texto", f"{h}.Xs")], pubs, size_v=1.3, dx_v=0.05)


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
                 Width=I(0, f"{h}.Ancho*{grow}"), Height=I(0.133, f"{h}.Alto*{W16}"), CornerRadius=I(0.15),
                 Angle=I(-2, f"{h}.Inclinacion")),
            solid("Banda", (1, 0.85, 0.1), (-385, -132), mask="MascBanda"),
            text_tool("Texto", "PALABRA CLAVE", 0.07, (0.5, 0.5), (-330, -132), rgb=(0.05, 0.05, 0.05))]
    pubs = numbered([pub("Texto", "StyledText", "Texto"), *text_pubs("Texto", " del texto", 0.07, (0.05, 0.05, 0.05), 1),
                     pub_color("Banda", "Color del resaltado", (1, 0.85, 0.1), "c2"), pub(h, "Ancho", "Ancho del resaltado", 0.42),
                     pub(h, "Alto", "Alto del resaltado", 0.075), pub(h, "Inclinacion", "Inclinación (grados)", -2)])
    return title(name, h, ucs, inputs, body, [("Banda", f"{h}.Xs"), ("Texto", stage(h, 0, 0.35))], pubs, size_v=1.6)


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
    return title(name, h, ucs, inputs, body, [("Destello", stage(h, 0, 1))], pubs, size_v=2.2)


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
    return title(name, h, ucs, inputs, body, layers, pubs, size_v=2.5)


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
                       Width=I(1 / n + 0.002), Height=I(1.05)),
                  merge(f"Barra{i}", last, "EntradaB", (-385 + 44 * i, 0), extra={"EffectMask": I(link=f"MascBarra{i}", out="Mask")})]
        last = f"Barra{i}"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Escalonado", "Escalonado", 0.6, 0, 3),
           uc("Alternar", "Alternar arriba / abajo", 1, 0, 1, checkbox=True)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Progreso": I(link=anim, out="Value"),
                                                "Escalonado": I(0.6), "Alternar": I(1)}, ucs, (0, 0)))
    pubs = [pub(h, "Escalonado", "Escalonado", 0.6), pub(h, "Alternar", "Alternar arriba / abajo", 1)]
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
        for k, (center, w, ht) in enumerate(((f"Point({cx} - {sx}*{h}.Largo/2, {cy})", f"{h}.Largo", f"{h}.Grosor*{asp}"),
                                             (f"Point({cx}, {cy} - {sy}*{h}.Largo*{asp}/2)", f"{h}.Grosor", f"{h}.Largo*{asp}"))):
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
              rect("MascPila", (-55, -198), Center=I((0.86, 0.12)), Width=I(0.05), Height=I(0.039, f"0.022*{asp}"), Solid=I(0), BorderWidth=I(0.002)),
              ui_color(solid("Pila", (1, 1, 1), (-55, -165), mask="MascPila")),
              rect("MascCarga", (0, -198), Center=I((0.86, 0.12), f"Point(0.84 + 0.02*{h}.Bateria, 0.12)"),
                   Width=I(0.028, f"0.04*{h}.Bateria"), Height=I(0.025, f"0.014*{asp}")),
              ui_color(solid("Carga", (1, 1, 1), (0, -165), mask="MascCarga")),
              rect("MascBorne", (55, -198), Center=I((0.888, 0.12)), Width=I(0.004), Height=I(0.018, f"0.01*{asp}")),
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
    vertical_text(tools, h, ("TextoREC", "Codigo", "Info"), checkbox=False)
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
    pubs += vertical_text(tools, h, ("Camara", "Fecha", "Reloj"))
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
              rect("MascPantalla", (110, -99), Invert=I(1), Width=I(0.96), Height=I(0.96),
                   CornerRadius=I(0.12), SoftEdge=I(0.01)),
              solid("Marco", (0.02, 0.02, 0.02), (110, -66), mask="MascPantalla"),
              merge("ConMarco", "Parpadeo", "Marco", (165, 0), blend=1)]
    t, last = blk_vignette("Vin", "ConMarco", 220, amount=0.35)
    tools += t
    ucs = [uc("Separacion", "Separación de color", 0.002, 0, 0.02), uc("Lineas", "Líneas", 0.3, 0, 1),
           uc("NumLineas", "Número de líneas", 300, 50, 1000), uc("Parpadeo", "Parpadeo", 1, 0, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Separacion": I(0.002), "Lineas": I(0.3), "NumLineas": I(300),
                                                "Parpadeo": I(1)}, ucs, (330, 0)))
    pubs = [pub(h, "Separacion", "Separación de color", 0.002), pub("BlBloom", "Blend", "Brillo", 0.35),
            pub(h, "Lineas", "Líneas", 0.3), pub(h, "NumLineas", "Número de líneas", 300), pub(h, "Parpadeo", "Parpadeo", 1),
            pub("ConMarco", "Blend", "Marco de la pantalla", 1), pub("MascPantalla", "CornerRadius", "Redondeo de la pantalla", 0.12),
            pub("VinVineta", "Blend", "Viñeta", 0.35)]
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
                  Width=I(1, f"max(0, {cw} - {h}.Separacion)"), Height=I(0.49, f"max(0, {ch} - {h}.Separacion*{h}.Aspecto)"),
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


# En Fusion, el tamano de Text+ y el alto de RectangleMask son fracciones del ALTO del cuadro, y el ancho y las X
# son fracciones del ANCHO. Un titulo disenado en 16:9 se veria en 9:16 con el texto 3.16 veces mas grande que sus
# formas. vertical_map() lo evita: en vertical multiplica por K = (9/16)/(16/9) = 0.3164 los tamanos de texto, los altos
# de rectangulo y la distancia vertical al centro, de modo que el bloque queda identico al de 16:9 escalado al ancho.
# Las entradas que ya dependen de 'Vertical' (iconos, comentario) o que estan publicadas no se tocan.
K_VERT = 0.3164


def _point_args(expr):
    inner = expr.strip()[len("Point("):-1]
    depth = 0
    for i, ch in enumerate(inner):
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            return inner[:i].strip(), inner[i + 1:].strip()
    raise ValueError(expr)


def _parts(spec):
    """(valor, expresion) de una cadena Input { ... } generada por I()."""
    m = re.search(r'Expression = "((?:[^"\\]|\\.)*)"', spec)
    expr = m.group(1).replace('\\"', '"') if m else None
    m2 = re.search(r"Value = \{ ([-\d.e]+), ([-\d.e]+) \}", spec)
    if m2:
        return (float(m2.group(1)), float(m2.group(2))), expr
    m3 = re.search(r"Value = ([-\d.e]+)", spec)
    return (float(m3.group(1)) if m3 else None), expr


def vertical_map(h, body, ucs, inputs, pubs):
    k = f"iif({h}.Vertical > 0.5, {K_VERT}, 1)"
    published = {(pp["tool"], pp["source"]) for pp in pubs}

    def skip(t, key):
        spec = t.inputs.get(key)
        return spec is None or "SourceOp" in spec or "Vertical" in spec or (t.name, key) in published

    def map_point(t, key):
        if skip(t, key):
            return
        val, expr = _parts(t.inputs[key])
        if expr:
            if not expr.startswith("Point("):
                return
            x, y = _point_args(expr)
        else:
            if val[1] == 0.5:
                return
            x, y = f"{val[0]:g}", f"{val[1]:g}"
        t.inputs[key] = I(val, f"Point({x}, 0.5 + (({y}) - 0.5)*{k})")

    def map_scalar(t, key):
        if skip(t, key):
            return
        val, expr = _parts(t.inputs[key])
        t.inputs[key] = I(val, f"({expr if expr else f'{val:g}'})*{k}")

    for t in body:
        if t.kind in ("Transform", "TextPlus", "RectangleMask", "EllipseMask"):
            map_point(t, "Center")
        if t.kind == "TriangleMask":
            for i in (1, 2, 3):
                map_point(t, f"Point{i}")
        if t.kind == "RectangleMask":
            map_scalar(t, "Height")
        spec = t.inputs.get("Size", "")
        if t.kind == "TextPlus" and spec and "SourceOp" not in spec and "Vertical" not in spec:
            # el tamano pasa a un control del titulo (para poder editarlo) multiplicado por K
            val, _ = _parts(t.inputs["Size"])
            cname = f"Tam{t.name}"
            ucs.insert(-2, uc(cname, f"Tamaño {t.name}", val, 0, 1, clamp=False))
            inputs[cname] = I(val)
            t.inputs["Size"] = I(val, f"{h}.{cname}*{k}")
    for pp in pubs:
        if pp["source"] == "Size" and any(t.name == pp["tool"] and t.kind == "TextPlus" for t in body):
            pp["tool"], pp["source"] = h, f"Tam{pp['tool']}"


def vertical_text(tools, h, names, factor=1.6, checkbox=True, extra=(), pubs=()):
    """El texto de Text+ se mide sobre el alto del cuadro: en vertical saldria 3.16 veces mas grande (respecto al ancho)
    que en 16:9. Multiplica el tamano por K*factor cuando el formato es vertical. Con checkbox=True agrega la casilla
    'Formato vertical (9:16)' al host; si no, usa h.Aspecto < 1. extra: [(tool, input)] numericos a escalar igual."""
    cond = f"{h}.Vertical > 0.5" if checkbox else f"{h}.Aspecto < 1"
    k = f"iif({cond}, {K_VERT * factor:.4f}, 1)"
    host = next(x for x in tools if x.name == h)
    for t in tools:
        if t.name in names:
            val, _ = _parts(t.inputs["Size"])
            flat = [x for pp in pubs for x in (pp if isinstance(pp, list) else [pp])]
            sized = [pp for pp in flat if pp["tool"] == t.name and pp["source"] == "Size"]
            if sized:
                # tamano publicado: pasa a un control del host para que siga siendo editable
                host.ucs.insert(0, uc(f"Tam{t.name}", "Tamaño", val, 0, 1, clamp=False))
                host.inputs[f"Tam{t.name}"] = I(val)
                t.inputs["Size"] = I(val, f"{h}.Tam{t.name}*{k}")
                for pp in sized:
                    pp["tool"], pp["source"] = h, f"Tam{t.name}"
            else:
                t.inputs["Size"] = I(val, f"{val:g}*{k}")
    for tn, key in extra:
        t = next(x for x in tools if x.name == tn)
        val, expr = _parts(t.inputs[key])
        t.inputs[key] = I(val, f"({expr if expr else f'{val:g}'})*{k}")
    if checkbox:
        host.ucs.insert(0, uc("Vertical", "Formato vertical (9:16)", 0, 0, 1, checkbox=True))
        host.inputs["Vertical"] = I(0)
        return [pub(h, "Vertical", "Formato vertical (9:16)", 0)]
    return []


def style_title(name, h, ucs, inputs, body, layers, pubs, dy_h=0.0, dy_v=0.0, size_v=1.0, mains=(), dx_v=0.0):
    """Como title(), con un Transform 'Formato' que recoloca y escala el bloque si se marca 'Formato vertical (9:16)'.
    En vertical el bloque se ve igual que en 16:9 (vertical_map) y 'Formato' lo escala (size_v) y lo mueve (dx_v, dy_v).
    mains: entradas de video si la pieza es un efecto (p. ej. la foto del comentario)."""
    v = f"{h}.Vertical"
    ucs = ucs[:-2] + [uc("Vertical", "Formato vertical (9:16)", 0, 0, 1, checkbox=True)] + ucs[-2:]
    inputs = {**inputs, "Vertical": I(0)}
    pubs = numbered(pubs)
    vertical_map(h, body, ucs, inputs, pubs)
    tools = [solid("Lienzo", (0, 0, 0), (-440, 0), alpha=0)] + body
    t, last = compose(layers, x0=110)
    tools += t
    tools.append(Tool("Formato", "Transform", {"Input": I(link=last),
                                               "Center": I((0.5, 0.5 + dy_h), f"Point(0.5 + iif({v} > 0.5, {dx_v:g}, 0), 0.5 + iif({v} > 0.5, {dy_v:g}, {dy_h:g}))"),
                                               "Size": I(1, f"iif({v} > 0.5, {size_v:g}, 1)")}, pos=(385, 0)))
    tools.append(Tool(h, "Transform", {"Input": I(link="Formato"), **inputs}, ucs, (440, 0)))
    entrada = float(inputs["Entrada"].split("Value = ")[1].split(",")[0])
    salida = float(inputs["Salida"].split("Value = ")[1].split(",")[0])
    pubs = numbered(pubs + [pub(h, "Vertical", "Formato vertical (9:16)", 0), pub(h, "Center", "Posición"), pub(h, "Size", "Escala", 1),
                            pub(h, "Entrada", "Duración entrada (% del clip)", entrada),
                            pub(h, "Salida", "Duración salida (% del clip, 0 = sin salida)", salida)])
    a = "PRO" + name.split("_", 2)[-1].replace("_", "") + "Anim"
    return macro(name, list(mains), pubs, h, tools, a).replace('"PRO_ANIM"', f'"{a}"')


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
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_h=-0.28, dy_v=-0.14, size_v=1.7)


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
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_h=0.05, dy_v=0.12, size_v=1.5)


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
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=1.4)


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
            rect("MascLinea", (-275, -165), Center=I((0.5, 0.457)), Width=I(0, f"0.18*{s2}"), Height=I(0.0021, f"0.0012*{icon_asp(h)}")),
            solid("Linea", cream, (-275, -132), alpha=0.7, mask="MascLinea")]
    for ch in ("Red", "Green", "Blue"):
        body[1].inputs[f"{ch}1"] = I(1, f"Nombres.{ch}1")
        body[-1].inputs[f"TopLeft{ch}"] = I(1, f"Nombres.{ch}1")
    pubs = [pub("Nombres", "StyledText", "Nombres"), pub("Fecha", "StyledText", "Fecha"),
            *text_pubs("Nombres", " de los nombres", 0.1, cream, 1), pub("Fecha", "Font", "Fuente de la fecha", group="f2"),
            pub("Fecha", "Style", group="f2"), pub("Fecha", "Size", "Tamaño de la fecha", 0.025)]
    layers = [("Anim1", stage(h, 0, 0.7)), ("Linea", f"{h}.Xs"), ("Anim2", stage(h, 0.4, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_v=0.05, size_v=1.8)


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
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.0)


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
    return style_title(name, h, ucs, inputs, body, layers, pubs, dx_v=0.484, dy_v=0.03, size_v=2.2)


@register("Titles", "PRO_TTL_Estilo_Deportivo")
def estilo_deportivo(name, anim_):
    """Deportes y gaming competitivo: Teko condensada con sombra dura y barra inclinada de color; entra rapido con desenfoque."""
    h = "Deportivo"
    e1, e2, eb = phase(h, 0.2, 0.7), phase(h, 0.45, 1), phase(h, 0, 0.5)
    ucs, inputs = kit(h, 0.2, 0.1)
    accent = (0.9, 0.1, 0.15)
    # barra detras del nombre; el dato va debajo de la barra, en blanco, para que no se pierda sobre el color
    body = [rect("MascBarra", (-440, -165), Center=I((0.28, 0.2), f"Point(0.055 + 0.225*{eb}, 0.2)"), Width=I(0.45, f"0.45*{eb}"),
                 Height=I(0.105), Angle=I(2)),
            solid("Barra", accent, (-440, -132), mask="MascBarra"),
            styled("Nombre", "APELLIDO", "Teko", "SemiBold", 0.11, (-385, -132), center=(0.08, 0.197), left=True,
                   hard=((0, 0, 0), (0.004, -0.006))),
            styled("Dato", "DELANTERO · 25 GOLES", "Teko", "Medium", 0.045, (-330, -132), rgb=(1, 1, 1), center=(0.08, 0.115), left=True,
                   hard=((0, 0, 0), (0.003, -0.004))),
            Tool("Rafaga1", "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0), "XBlurSize": I(0, f"40*(1 - {e1})"), "YBlurSize": I(0),
                                     "Input": I(link="Nombre")}, pos=(-385, -99)),
            Tool("Rafaga2", "Blur", {"Filter": I(FuID("Fast Gaussian")), "LockXY": I(0), "XBlurSize": I(0, f"40*(1 - {e2})"), "YBlurSize": I(0),
                                     "Input": I(link="Dato")}, pos=(-330, -99)),
            mover("Anim1", "Rafaga1", (-385, -66), cx=f"0.5 - 0.6*(1 - {e1})"),
            mover("Anim2", "Rafaga2", (-330, -66), cx=f"0.5 - 0.6*(1 - {e2})")]
    pubs = [pub("Nombre", "StyledText", "Nombre"), pub("Dato", "StyledText", "Dato"),
            *text_pubs("Nombre", " del nombre", 0.11, (1, 1, 1), 1), pub_color("Barra", "Color del equipo", accent, "c2"),
            *text_pubs("Dato", " del dato", 0.045, (1, 1, 1), 3)]
    layers = [("Barra", f"{h}.Xs"), ("Anim1", stage(h, 0.2, 0.5)), ("Anim2", stage(h, 0.45, 0.8))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dx_v=0.23, dy_v=-0.05, size_v=1.6)


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
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=1.4)


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
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.2)


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
                 Width=I(0, f"{h}.Ancho*{g}"), Height=I(0.018, f"0.01*{icon_asp(h)}"), Angle=I(-2), CornerRadius=I(0.5)),
            solid("Raya", (1, 0.85, 0.1), (-330, -132), alpha=0.85, mask="MascRaya")]
    pubs = [pub("Texto", "StyledText", "Texto"), *text_pubs("Texto", "", 0.075, (1, 1, 1), 1),
            pub_color("Raya", "Color del subrayado", (1, 0.85, 0.1), "c2"), pub(h, "Ancho", "Ancho del subrayado", 0.36),
            pub(h, "Vaiven", "Vaivén", 1)]
    layers = [("Raya", f"{h}.Xs"), ("Anim1", stage(h, 0, 0.5))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_v=0.05, size_v=2.0)


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
                  Height=I(0.316, f"iif({wide}, {at}/{ac}, 1)*{h}.EscalaFrente"), CornerRadius=I(0, f"{h}.Redondeo"))]
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
    v = f"{h}.Vertical"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)), solid("Lienzo", (0, 0, 0), (-385, 0), alpha=0)]
    bands = [("Sup", f"Point(0.5, 1 - {h}.MSup/2)", "1", f"{h}.MSup"),
             ("Inf", f"Point(0.5, {h}.MInf/2)", "1", f"{h}.MInf"),
             ("Der", f"Point(1 - {h}.MDer/2, 0.5)", f"{h}.MDer", "1.05")]
    layers = []
    for i, (n, c, w, ht) in enumerate(bands):
        tools += [rect(f"Masc{n}", (-330 + 55 * i, -132), Center=I((0.5, 0.5), c), Width=I(1, w), Height=I(0.1, ht)),
                  solid(f"Zona{n}", (1, 0.15, 0.15), (-330 + 55 * i, -99), mask=f"Masc{n}")]
        layers.append((f"Zona{n}", f"0.35*{v}"))
    for i, (n, k) in enumerate((("Accion", 0.93), ("Titulos", 0.9))):
        tools += [rect(f"Masc{n}", (-165 + 55 * i, -132), Width=I(k), Height=I(k), Solid=I(0), BorderWidth=I(0.002)),
                  solid(f"Marco{n}", (0.2, 1, 0.4), (-165 + 55 * i, -99), mask=f"Masc{n}")]
        layers.append((f"Marco{n}", f"0.8*(1 - {v})"))
    for z in ("ZonaSup", "ZonaInf"):
        next(t for t in tools if t.name == z).inputs.update({f"TopLeft{ch}": I(1, f"ZonaDer.TopLeft{ch}") for ch in ("Red", "Green", "Blue")})
    t, last = compose(layers, x0=0)
    tools += t
    tools.append(merge("Guia", "Entrada", last, (330, 0), blend=1))
    ucs = [uc("Vertical", "Vertical (desmarcado = marcos 16:9)", 1, 0, 1, checkbox=True),
           uc("MSup", "Zona superior", 0.1, 0, 0.5), uc("MInf", "Zona inferior (descripción y subtítulos)", 0.22, 0, 0.5),
           uc("MDer", "Zona derecha (botones)", 0.13, 0, 0.5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Guia"), "Vertical": I(1), "MSup": I(0.1), "MInf": I(0.22), "MDer": I(0.13)}, ucs, (385, 0)))
    pubs = numbered([pub(h, "Vertical", "Vertical (desmarcado = marcos 16:9)", 1), pub(h, "MSup", "Zona superior", 0.1),
                     pub(h, "MInf", "Zona inferior (descripción y subtítulos)", 0.22), pub(h, "MDer", "Zona derecha (botones)", 0.13),
                     pub_color("ZonaDer", "Color de las zonas", (1, 0.15, 0.15), "c1"), pub("Guia", "Blend", "Opacidad de la guía", 1)])
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
    pubs += vertical_text(tools, h, ("Fecha",))
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


# ======================================================================= LOTE 10: generadores
def color_from(tool, src):
    """El fondo 'tool' toma el color del selector publicado en 'src'."""
    tool.inputs.update({f"TopLeft{ch}": I(1, f"{src}.TopLeft{ch}") for ch in ("Red", "Green", "Blue")})
    return tool


@register("Generators", "PRO_GEN_Aurora")
def gen_aurora(name, anim):
    """Degradado de malla (aurora): cuatro manchas de color grandes que derivan y se mezclan sobre un fondo oscuro."""
    h = "Aurora"
    v = f"{h}.Velocidad"
    blobs = [((0.3, 0.65), 0.9, (0.5, 0.2, 1)), ((0.7, 0.6), 0.8, (1, 0.3, 0.6)),
             ((0.35, 0.3), 0.85, (0.1, 0.8, 1)), ((0.75, 0.3), 0.7, (1, 0.6, 0.2))]
    tools = [solid("Fondo", (0.03, 0.02, 0.08), (-440, 0))]
    last = "Fondo"
    for i, ((x, y), size, col) in enumerate(blobs, 1):
        ph = 1.7 * i
        c = f"Point({x} + 0.22*sin(time*0.011*{v} + {ph:g}), {y} + 0.16*sin(time*0.0083*{v} + {ph * 1.3:g}))"
        tools += [ellipse(f"MascMancha{i}", (-385 + 55 * i, -132), Center=I((x, y), c), Width=I(size), Height=I(size), SoftEdge=I(0.4)),
                  solid(f"Mancha{i}", col, (-385 + 55 * i, -99), mask=f"MascMancha{i}"),
                  merge(f"Capa{i}", last, f"Mancha{i}", (-385 + 55 * i, 0), "Screen", blend=0.8, blend_expr=f"{h}.Intensidad*0.8")]
        last = f"Capa{i}"
    tools.append(Tool("Fusion", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(60), "Input": I(link=last)}, pos=(-55, 0)))
    t, last = blk_grain("Gr", "Fusion", None, 0, scale=80)
    tools += t
    tools[-1].inputs["Blend"] = I(0.03)
    ucs = [uc("Velocidad", "Velocidad", 1, 0, 5), uc("Intensidad", "Intensidad", 1, 0, 1.5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Velocidad": I(1), "Intensidad": I(1)}, ucs, (110, 0)))
    pubs = numbered([pub_color("Fondo", "Color de fondo", (0.03, 0.02, 0.08), "c0"),
                     *[pub_color(f"Mancha{i}", f"Color {i}", col, f"c{i}") for i, (_, _, col) in enumerate(blobs, 1)],
                     pub(h, "Velocidad", "Velocidad", 1), pub(h, "Intensidad", "Intensidad", 1),
                     pub("Fusion", "XBlurSize", "Suavidad", 60), pub("GrGrano", "Blend", "Textura", 0.03),
                     pub(h, "Saturation", "Saturación", 1)])
    return macro(name, [], pubs, h, tools)


@register("Generators", "PRO_GEN_FugaLuz")
def gen_fuga_luz(name, anim):
    """Fuga de luz organica sobre negro. Ponla en una pista superior con modo de composicion Screen o Add."""
    h = "Fuga"
    v = f"{h}.Velocidad"
    tools = [solid("Negro", (0, 0, 0), (-440, 0))]
    last = "Negro"
    for i, (scale, col, sp, ph) in enumerate(((1.4, (1, 0.5, 0.15), 1, 0), (2.2, (1, 0.2, 0.35), 1.6, 2)), 1):
        y = -165 + 99 * (i - 1)
        tools += [Tool(f"Forma{i}", "FastNoise", {**frame_format(), "Detail": I(2), "Contrast": I(1.6), "XScale": I(scale),
                                                   "SeetheRate": I(0.01, f"0.01*{v}"),
                                                   "Center": I((0.5, 0.5), f"Point(0.5 + time*0.002*{sp}*{v}, 0.5 + 0.1*sin(time*0.01*{v} + {ph}))")},
                       pos=(-385, y)),
                  Tool(f"Umbral{i}", "BrightnessContrast", {"Input": I(link=f"Forma{i}"), "Saturation": I(0),
                                                             "Low": I(0.45, f"0.6 - 0.3*{h}.Cantidad"), "High": I(1)}, pos=(-330, y)),
                  solid(f"Color{i}", col, (-330, y - 33)),
                  merge(f"Tenido{i}", f"Umbral{i}", f"Color{i}", (-275, y), "Multiply"),
                  merge(f"Capa{i}", last, f"Tenido{i}", (-220 + 55 * i, 0), "Screen", blend=1, blend_expr=f"{h}.Intensidad")]
        last = f"Capa{i}"
    tools += [ellipse("MascNucleo", (-110, -132), SoftEdge=I(0.5), Width=I(0.6), Height=I(0.6),
                      Center=I((0.2, 0.7), f"Point(0.5 + 0.45*sin(time*0.009*{v}), 0.65 + 0.15*sin(time*0.006*{v} + 1))")),
              solid("Nucleo", (1, 0.85, 0.6), (-110, -99), mask="MascNucleo"),
              merge("ConNucleo", last, "Nucleo", (-55, 0), "Screen", blend=0.5, blend_expr=f"0.5*{h}.Intensidad"),
              Tool("Difuso", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(30), "Input": I(link="ConNucleo")}, pos=(0, 0))]
    ucs = [uc("Velocidad", "Velocidad", 1, 0, 5), uc("Intensidad", "Intensidad", 1, 0, 2), uc("Cantidad", "Cantidad de luz", 0.5, 0, 1)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Difuso"), "Velocidad": I(1), "Intensidad": I(1), "Cantidad": I(0.5)},
                      ucs, (55, 0)))
    pubs = numbered([pub(h, "Intensidad", "Intensidad", 1), pub(h, "Cantidad", "Cantidad de luz", 0.5), pub(h, "Velocidad", "Velocidad", 1),
                     pub_color("Color1", "Color principal", (1, 0.5, 0.15), "c1"), pub_color("Color2", "Color secundario", (1, 0.2, 0.35), "c2"),
                     pub_color("Nucleo", "Color del núcleo", (1, 0.85, 0.6), "c3"), pub("Difuso", "XBlurSize", "Suavidad", 30)])
    return macro(name, [], pubs, h, tools)


@register("Generators", "PRO_GEN_EstaticaTV")
def gen_estatica_tv(name, anim):
    """Estatica de television: ruido que cambia en cada fotograma, lineas de barrido y una banda que rueda."""
    h = "Estatica"
    tools = [Tool("Ruido", "FastNoise", {**frame_format(), "Detail": I(2), "Contrast": I(2.5), "XScale": I(220), "SeetheRate": I(5),
                                         "Discontinuous": I(1)}, pos=(-385, 0)),
             Tool("Grises", "BrightnessContrast", {"Input": I(link="Ruido"), "Saturation": I(0), "Contrast": I(0.2)}, pos=(-330, 0))]
    t, last = blk_cast("Tinte", "Grises", -275, (1, 1, 1), 1)
    tools += t
    t, last = scanlines("Lineas", last, h, -165, high=0.6)
    tools += t
    tools += [rect("MascBanda", (-55, -99), Width=I(3), Height=I(0.08), SoftEdge=I(0.05),
                   Center=I((0.5, 0.5), f"Point(0.5, 1.2 - 1.4*(time*0.01*{h}.VelBanda - floor(time*0.01*{h}.VelBanda)))")),
              Tool("BandaLuz", "BrightnessContrast", {"Input": I(link=last), "Gain": I(1.6)}, pos=(-55, -66)),
              merge("Banda", last, "BandaLuz", (0, 0), blend=1, blend_expr=f"{h}.Banda", extra={"EffectMask": I(link="MascBanda", out="Mask")})]
    t, last = blk_vignette("Vin", "Banda", 55, amount=0.4)
    tools += t
    ucs = [uc("Lineas", "Líneas", 0.4, 0, 1), uc("NumLineas", "Número de líneas", 300, 50, 1000),
           uc("Banda", "Banda que rueda", 0.6, 0, 1), uc("VelBanda", "Velocidad de la banda", 1, 0, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Lineas": I(0.4), "NumLineas": I(300), "Banda": I(0.6), "VelBanda": I(1)},
                      ucs, (165, 0)))
    pubs = numbered([pub("Grises", "Contrast", "Contraste", 0.2), pub(h, "Gain", "Brillo", 1),
                     pub_color("TinteColor", "Tinte", (1, 1, 1), "c1"), pub(h, "Lineas", "Líneas", 0.4),
                     pub(h, "NumLineas", "Número de líneas", 300), pub(h, "Banda", "Banda que rueda", 0.6),
                     pub(h, "VelBanda", "Velocidad de la banda", 1), pub("VinVineta", "Blend", "Viñeta", 0.4)])
    return macro(name, [], pubs, h, tools)


@register("Generators", "PRO_GEN_CuentaRegresiva")
def gen_cuenta_regresiva(name, anim):
    """Cola de pelicula (film leader): numeros que bajan cada segundo, aros, cruz y una linea que gira, con grano y parpadeo."""
    h = "Cuenta"
    fps = f"{h}.FPS"
    n = f"max(1, {h}.Desde - floor(time/{fps}))"
    tools = [solid("Fondo", (0.55, 0.55, 0.52), (-440, 0)), solid("Lienzo", (0, 0, 0), (-440, 66), alpha=0)]
    marks = [("AroExt", ellipse("MascAroExt", (-385, -132), Width=I(0.5), Height=I(0.5), Solid=I(0), BorderWidth=I(0.004))),
             ("AroInt", ellipse("MascAroInt", (-330, -132), Width=I(0.42), Height=I(0.42), Solid=I(0), BorderWidth=I(0.003))),
             ("CruzH", rect("MascCruzH", (-275, -132), Width=I(2), Height=I(0.003))),
             ("CruzV", rect("MascCruzV", (-220, -132), Width=I(0.003), Height=I(2))),
             ("Barrido", rect("MascBarrido", (-165, -132), Width=I(0.005), Height=I(0.6),
                              Angle=I(0, f"-360*(time/{fps} - floor(time/{fps}))")))]
    layers = []
    for i, (n_, m) in enumerate(marks):
        tools += [m, color_from(solid(n_, (0.1, 0.1, 0.1), (-385 + 55 * i, -99), mask=m.name), "Lineas")]
        layers.append((n_, None))
    tools.insert(0, solid("Lineas", (0.1, 0.1, 0.1), (-440, -66)))
    tools.append(text_tool("Numero", "5", 0.3, (0.5, 0.5), (-110, -99), rgb=(0.1, 0.1, 0.1), font="Arial", style="Bold",
                           extra={"StyledText": I("5", f'Text(string.format("%d", {n}))')}))
    next(t for t in tools if t.name == "Numero").inputs.update({f"{ch}1": I(1, f"Lineas.TopLeft{ch}") for ch in ("Red", "Green", "Blue")})
    layers.append(("Numero", None))
    t, over = compose(layers, x0=-55)
    tools += t
    tools.append(merge("Marcas", "Fondo", over, (220, 0), blend=1))
    t, last = blk_grain("Gr", "Marcas", f"{h}.Grano", 275, scale=60)
    tools += t
    t, last = blk_vignette("Vin", last, 385, amount=0.5)
    tools += t
    ucs = [uc("Desde", "Empieza en", 5, 1, 10, integer=True), uc("FPS", "Fotogramas por segundo", 30, 1, 120),
           uc("Grano", "Grano", 0.15, 0, 0.5), uc("Parpadeo", "Parpadeo", 1, 0, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Desde": I(5), "FPS": I(30), "Grano": I(0.15), "Parpadeo": I(1),
                                                "Gain": I(1, f"1 + {h}.Parpadeo*0.05*sin(time*9.1)*sin(time*4.3 + 1)")}, ucs, (495, 0)))
    pubs = numbered([pub(h, "Desde", "Empieza en", 5), pub(h, "FPS", "Fotogramas por segundo", 30),
                     pub_color("Fondo", "Color de fondo", (0.55, 0.55, 0.52), "c1"), pub_color("Lineas", "Color de líneas y número", (0.1, 0.1, 0.1), "c2"),
                     pub("Numero", "Font", "Fuente del número", group="f1"), pub("Numero", "Style", group="f1"),
                     pub(h, "Grano", "Grano", 0.15), pub(h, "Parpadeo", "Parpadeo", 1), pub("VinVineta", "Blend", "Viñeta", 0.5)])
    pubs += vertical_text(tools, h, ("Numero",), factor=1, extra=[("MascBarrido", "Height")])
    return macro(name, [], pubs, h, tools)


@register("Generators", "PRO_GEN_Brasas")
def gen_brasas(name, anim):
    """Brasas o chispas que suben y titilan sobre negro. Ponla encima con modo Screen o Add (fuego, epica, trailers)."""
    h = "Brasas"
    v = f"{h}.Velocidad"
    tools = [solid("Negro", (0, 0, 0), (-440, 0)), solid("ColorBrasa", (1, 0.45, 0.1), (-440, -198))]
    last = "Negro"
    for i, (scale, low, blur, speed, ph) in enumerate(((70, 0.9, 1, 0.002, 0), (40, 0.92, 2, 0.0035, 2), (22, 0.94, 3.5, 0.005, 4)), 1):
        y = -198 + 66 * (i - 1)
        cx = f"0.5 + 0.015*sin(time*0.04*{v} + {ph})"
        tools += [Tool(f"Chispas{i}", "FastNoise", {**frame_format(), "Detail": I(8), "Contrast": I(2.5), "XScale": I(scale),
                                                     "SeetheRate": I(0.08),
                                                     "Center": I((0.5, 0.5), f"Point({cx}, 0.5 + time*{speed}*{v})")}, pos=(-385, y)),
                  Tool(f"Umbral{i}", "BrightnessContrast", {"Input": I(link=f"Chispas{i}"), "Saturation": I(0),
                                                             "Low": I(low, f"{low} + (1 - {h}.Cantidad)*0.05"), "High": I(1)}, pos=(-330, y)),
                  Tool(f"Suave{i}", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(blur), "Input": I(link=f"Umbral{i}")},
                       pos=(-275, y)),
                  merge(f"Tenido{i}", f"Suave{i}", "ColorBrasa", (-220, y), "Multiply"),
                  merge(f"Capa{i}", last, f"Tenido{i}", (-165 + 55 * i, 0), "Screen", blend=1, blend_expr=f"{h}.Brillo")]
        last = f"Capa{i}"
    tools += [Tool("Resplandor", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(10), "Input": I(link=last)}, pos=(55, -66)),
              merge("ConResplandor", last, "Resplandor", (55, 0), "Screen", blend=0.8)]
    ucs = [uc("Cantidad", "Cantidad", 0.5, 0, 1), uc("Brillo", "Brillo", 1, 0, 2), uc("Velocidad", "Velocidad", 1, 0, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConResplandor"), "Cantidad": I(0.5), "Brillo": I(1), "Velocidad": I(1)},
                      ucs, (110, 0)))
    pubs = numbered([pub(h, "Cantidad", "Cantidad", 0.5), pub(h, "Brillo", "Brillo", 1), pub(h, "Velocidad", "Velocidad", 1),
                     pub_color("ColorBrasa", "Color", (1, 0.45, 0.1), "c1"), pub("ConResplandor", "Blend", "Resplandor", 0.8)])
    return macro(name, [], pubs, h, tools)


@register("Generators", "PRO_GEN_Synthwave")
def gen_synthwave(name, anim):
    """Atardecer synthwave: cielo degradado, sol con franjas y suelo con rejilla en perspectiva que avanza.
    Los angulos de la rejilla se calculan aqui para 16:9 y 9:16 (casilla 'Formato vertical')."""
    import math
    from fusion_builder import gradient
    h = "Synthwave"
    vert = f"{h}.Vertical"
    H = 0.42
    tools = [Tool("Cielo", "Background", {**frame_format(), "Type": I(FuID("Gradient")), "Start": I((0.5, 1)), "End": I((0.5, H)),
                                          "Gradient": I(gradient([(0, (0.05, 0, 0.12, 1)), (1, (0.6, 0.1, 0.5, 1))]))}, pos=(-550, 0)),
             ellipse("MascSol", (-495, -165), Center=I((0.5, H + 0.14)), Width=I(0.3), Height=I(0.3)),
             Tool("Sol", "Background", {"EffectMask": I(link="MascSol", out="Mask"), **frame_format(), "Type": I(FuID("Gradient")),
                                        "Start": I((0.5, H + 0.4)), "End": I((0.5, H)),
                                        "Gradient": I(gradient([(0, (1, 0.9, 0.3, 1)), (1, (1, 0.2, 0.55, 1))]))}, pos=(-495, -132)),
             merge("ConSol", "Cielo", "Sol", (-440, 0))]
    last = "ConSol"
    for i, (y, ht) in enumerate(((H + 0.1, 0.006), (H + 0.065, 0.01), (H + 0.03, 0.014), (H + 0.003, 0.018))):
        tools += [rect(f"MascFranja{i}", (-385 + 33 * i, -165), Center=I((0.5, y)), Width=I(0.4), Height=I(ht)),
                  solid(f"Franja{i}", (0.6, 0.1, 0.5), (-385 + 33 * i, -132), mask=f"MascFranja{i}"),
                  merge(f"ConFranja{i}", last, f"Franja{i}", (-385 + 33 * i, 0))]
        last = f"ConFranja{i}"
    tools += [rect("MascSuelo", (-220, -165), Center=I((0.5, H / 2)), Width=I(1.2),
                   Height=I(H)),
              solid("Suelo", (0.03, 0, 0.08), (-220, -132), mask="MascSuelo"),
              merge("ConSuelo", last, "Suelo", (-220, 0)),
              ellipse("MascHorizonte", (-165, -165), Center=I((0.5, H)), Width=I(1.4), Height=I(0.12), SoftEdge=I(0.15)),
              solid("Resplandor", (1, 0.2, 0.8), (-165, -132), mask="MascHorizonte"),
              merge("ConHorizonte", "ConSuelo", "Resplandor", (-165, 0), "Screen", blend=0.6, blend_expr=f"0.6*{h}.Brillo")]
    last = "ConHorizonte"
    f = f"(time*0.01*{h}.Velocidad - floor(time*0.01*{h}.Velocidad))"
    nh = 10
    for i in range(nh):
        k = f"(({i} + {f})/{nh})"
        tools += [rect(f"MascH{i}", (-110 + 22 * i, -198), Center=I((0.5, H), f"Point(0.5, {H} - {H}*{k}*{k})"), Width=I(1.2),
                       Height=I(0.003, f"0.002 + 0.004*{k}")),
                  color_from(solid(f"LineaH{i}", (1, 0.2, 0.8), (-110 + 22 * i, -165), mask=f"MascH{i}"), "Resplandor"),
                  merge(f"RejH{i}", last, f"LineaH{i}", (-110 + 22 * i, 0), blend=1, blend_expr=f"{h}.Brillo*min(1, 2*{k})")]
        last = f"RejH{i}"
    for j in range(-7, 8):
        xb = 0.5 + 0.16 * j
        geo = {}
        for tag, a in (("h", 1.7778), ("v", 0.5625)):
            geo[tag] = (math.degrees(math.atan((xb - 0.5) * a / H)), math.hypot((xb - 0.5) * a, H))
        n = f"V{j + 7}"
        tools += [rect(f"Masc{n}", (110 + 22 * (j + 7), -198), Center=I(((0.5 + xb) / 2, H / 2)), Width=I(0.003),
                       Height=I(geo["h"][1], f"iif({vert} > 0.5, {geo['v'][1]:.4f}, {geo['h'][1]:.4f})"),
                       Angle=I(geo["h"][0], f"iif({vert} > 0.5, {geo['v'][0]:.3f}, {geo['h'][0]:.3f})")),
                  color_from(solid(f"Linea{n}", (1, 0.2, 0.8), (110 + 22 * (j + 7), -165), mask=f"Masc{n}"), "Resplandor"),
                  merge(f"Rej{n}", last, f"Linea{n}", (110 + 22 * (j + 7), 0), blend=0.8, blend_expr=f"0.8*{h}.Brillo")]
        last = f"Rej{n}"
    ucs = [uc("Vertical", "Formato vertical (9:16)", 0, 0, 1, checkbox=True), uc("Velocidad", "Velocidad de la rejilla", 1, 0, 5),
           uc("Brillo", "Brillo de las líneas", 1, 0, 2)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Vertical": I(0), "Velocidad": I(1), "Brillo": I(1)}, ucs, (495, 0)))
    pubs = numbered([pub(h, "Vertical", "Formato vertical (9:16)", 0), pub(h, "Velocidad", "Velocidad de la rejilla", 1),
                     pub(h, "Brillo", "Brillo de las líneas", 1), pub_color("Resplandor", "Color de las líneas", (1, 0.2, 0.8), "c1"),
                     pub_color("Suelo", "Color del suelo", (0.03, 0, 0.08), "c2")])
    return macro(name, [], pubs, h, tools)


# ======================================================================= LOTE 11: dinamicos para videos virales
def beat_ucs(bpm=120):
    """Controles de ritmo: BPM, FPS y desfase en fotogramas para alinear con el primer golpe."""
    return [uc("BPM", "BPM de la música", bpm, 40, 220), uc("FPS", "Fotogramas por segundo", 30, 1, 120),
            uc("Desfase", "Desfase (fotogramas hasta el primer golpe)", 0, 0, 120)], {"BPM": I(bpm), "FPS": I(30), "Desfase": I(0)}


def beat(h):
    """(fase 0..1 dentro del golpe, numero de golpe) a partir de BPM/FPS/Desfase."""
    x = f"(max(0, time - {h}.Desfase)/({h}.FPS*60/{h}.BPM))"
    return f"({x} - floor({x}))", f"floor({x})"


def beat_pubs(h, bpm=120):
    return [pub(h, "BPM", "BPM de la música", bpm), pub(h, "FPS", "Fotogramas por segundo", 30),
            pub(h, "Desfase", "Desfase (fotogramas hasta el primer golpe)", 0)]


@register("Effects", "PRO_FX_Din_PulsoRitmo")
def din_pulso_ritmo(name, anim):
    """Zoom, flash y sacudida en cada golpe de la musica (BPM). Ponlo en un Adjustment Clip sobre todo el edit."""
    h = "Ritmo"
    ph, _ = beat(h)
    d = f"pow(1 - {ph}, {h}.Caida)"
    ucs, inputs = beat_ucs()
    ucs += [uc("Zoom", "Zoom por golpe", 0.08, 0, 0.5), uc("Flash", "Flash por golpe", 0, 0, 1),
            uc("Temblor", "Sacudida por golpe", 0, 0, 3), uc("Caida", "Rapidez de la caída", 4, 1, 12)]
    tools = [Tool("Pulso", "Transform", {"Size": I(1, f"1 + {h}.Zoom*{d}"),
                                         "Center": I((0.5, 0.5), f"Point(0.5 + {h}.Temblor*0.01*{d}*sin(time*7.3), 0.5 + {h}.Temblor*0.01*{d}*sin(time*9.1 + 1))")},
                  pos=(-110, 0)),
             Tool(h, "BrightnessContrast", {"Input": I(link="Pulso"), "Gain": I(1, f"1 + {h}.Flash*{d}"), **inputs, "Zoom": I(0.08),
                                            "Flash": I(0), "Temblor": I(0), "Caida": I(4)}, ucs, (0, 0))]
    pubs = beat_pubs(h) + [pub(h, "Zoom", "Zoom por golpe", 0.08), pub(h, "Flash", "Flash por golpe", 0),
                           pub(h, "Temblor", "Sacudida por golpe", 0), pub(h, "Caida", "Rapidez de la caída", 4)]
    return macro(name, [("Pulso", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_Estrobo")
def din_estrobo(name, anim):
    """Estrobo al ritmo: en golpes alternos la imagen pasa a blanco y negro duro o a negativo."""
    h = "Estrobo"
    _, n = beat(h)
    on = f"({n} - 2*floor({n}/2))"
    ucs, inputs = beat_ucs()
    ucs += [uc("Negativo", "Negativo (desmarcado = blanco y negro)", 0, 0, 1, checkbox=True), uc("Mezcla", "Intensidad", 1, 0, 1)]
    tools = [Tool("Entrada", "PipeRouter", pos=(-330, 0)),
             Tool("BN", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(0), "Contrast": I(0.45)}, pos=(-275, -66)),
             solid("Blanco", (1, 1, 1), (-275, -132)),
             merge("Inverso", "Blanco", "Entrada", (-220, -132), "Difference"),
             merge("ConBN", "Entrada", "BN", (-165, 0), blend=0, blend_expr=f"{h}.Mezcla*{on}*(1 - {h}.Negativo)"),
             merge("ConInverso", "ConBN", "Inverso", (-110, 0), blend=0, blend_expr=f"{h}.Mezcla*{on}*{h}.Negativo")]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConInverso"), **inputs, "Negativo": I(0), "Mezcla": I(1)}, ucs, (-55, 0)))
    pubs = beat_pubs(h) + [pub(h, "Negativo", "Negativo (desmarcado = blanco y negro)", 0), pub(h, "Mezcla", "Intensidad", 1),
                           pub("BN", "Contrast", "Contraste del blanco y negro", 0.45)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_ImpactoFrames")
def din_impacto_frames(name, anim):
    """Impact frames (estilo anime): unos fotogramas en blanco y negro extremo que alternan con su negativo, con sacudida.
    Al inicio del clip o en cada golpe de la musica."""
    h = "Impacto"
    ph, _ = beat(h)
    fpb = f"({h}.FPS*60/{h}.BPM)"
    lt = f"iif({h}.AlRitmo > 0.5, {ph}*{fpb}, time)"
    act = f"iif({lt} < {h}.Duracion, 1, 0)"
    alt = f"(floor({lt}/2) - 2*floor({lt}/4))"
    ucs, inputs = beat_ucs()
    ucs = [uc("Duracion", "Duración (fotogramas)", 6, 1, 30), uc("AlRitmo", "Repetir en cada golpe (usa BPM)", 0, 0, 1, checkbox=True),
           uc("Temblor", "Sacudida", 1, 0, 5), uc("Act", "Activo interno", 0, 0, 1, clamp=False)] + ucs
    tools = [Tool("Entrada", "PipeRouter", pos=(-385, 0)),
             Tool("Tinta", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(0), "Low": I(0.4), "High": I(0.6)}, pos=(-330, -66)),
             solid("Blanco", (1, 1, 1), (-330, -132)),
             merge("Negativo", "Tinta", "Blanco", (-275, -66), "Difference", blend=0, blend_expr=alt),
             Tool("Golpe", "Transform", {"Input": I(link="Negativo"), "Size": I(1.06),
                                         "Center": I((0.5, 0.5), f"Point(0.5 + {h}.Temblor*0.012*sin(time*11.3), 0.5 + {h}.Temblor*0.012*sin(time*13.7 + 1))")},
                  pos=(-220, -66)),
             merge("Mezcla", "Entrada", "Golpe", (-165, 0), blend=0, blend_expr=f"{h}.Act")]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Mezcla"), "Duracion": I(6), "AlRitmo": I(0), "Temblor": I(1),
                                                "Act": I(0, act), **inputs}, ucs, (-110, 0)))
    pubs = [pub(h, "Duracion", "Duración (fotogramas)", 6), pub(h, "AlRitmo", "Repetir en cada golpe (usa BPM)", 0),
            pub(h, "Temblor", "Sacudida", 1), pub("Tinta", "Low", "Umbral de tinta", 0.4)] + beat_pubs(h)
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_Clones")
def din_clones(name, anim):
    """Rejilla de clones: el clip se repite en mosaico (2x2, 3x3...), fijo o cambiando en cada golpe. Con espejo opcional."""
    h = "Clones"
    _, n = beat(h)
    grid = f"iif({h}.AlRitmo > 0.5, 1 + ({n} - {h}.Maximo*floor({n}/{h}.Maximo)), {h}.Cantidad)"
    ucs, inputs = beat_ucs()
    ucs = [uc("Cantidad", "Clones por lado", 2, 1, 6, integer=True), uc("AlRitmo", "Cambiar en cada golpe (usa BPM)", 0, 0, 1, checkbox=True),
           uc("Maximo", "Máximo al ritmo", 3, 2, 6, integer=True), uc("Espejo", "Espejo", 0, 0, 1, checkbox=True)] + ucs
    tools = [Tool(h, "Transform", {"Size": I(0.5, f"1/{grid}"), "Edges": I(1, f"iif({h}.Espejo > 0.5, 3, 1)"),
                                   "Cantidad": I(2), "AlRitmo": I(0), "Maximo": I(3), "Espejo": I(0), **inputs}, ucs, (0, 0))]
    pubs = [pub(h, "Cantidad", "Clones por lado", 2), pub(h, "AlRitmo", "Cambiar en cada golpe (usa BPM)", 0),
            pub(h, "Maximo", "Máximo al ritmo", 3), pub(h, "Espejo", "Espejo", 0)] + beat_pubs(h)
    return macro(name, [(h, "Input")], pubs, h, tools)


@register("Transitions", "PRO_TR_Puertas")
def tr_puertas(name, anim):
    """Puertas: el clip A se parte por la mitad y cada lado sale hacia fuera, mientras B se acerca detras."""
    h = "Puertas"
    p = f"{h}.Progreso"
    e = f"({p}*{p}*(3 - 2*{p}))"
    tools = [Tool("EntradaA", "PipeRouter", pos=(-330, -66)),
             Tool("Fondo", "Transform", {"Size": I(1.15, f"1 + {h}.Zoom*(1 - {e})")}, pos=(-330, 66))]
    last = "Fondo"
    for side, sx, mx in (("Izq", -1, 0.25), ("Der", 1, 0.75)):
        tools += [Tool(f"Hoja{side}", "Transform", {"Input": I(link="EntradaA"), "Center": I((0.5, 0.5), f"Point(0.5 + {sx}*0.55*{e}, 0.5)")},
                       pos=(-275, -66 if sx < 0 else 0)),
                  rect(f"Masc{side}", (-220, -132 if sx < 0 else -99), Center=I((mx, 0.5), f"Point({mx} + {sx}*0.55*{e}, 0.5)"),
                       Width=I(0.501), Height=I(8)),
                  merge(f"Con{side}", last, f"Hoja{side}", (-220 + 55 * (sx > 0), 0),
                        extra={"EffectMask": I(link=f"Masc{side}", out="Mask")})]
        last = f"Con{side}"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Zoom", "Zoom del clip B", 0.15, 0, 1)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Progreso": I(link=anim, out="Value"), "Zoom": I(0.15)}, ucs, (-55, 0)))
    pubs = [pub(h, "Zoom", "Zoom del clip B", 0.15)]
    return macro(name, [("EntradaA", "Input"), ("Fondo", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_Rebote")
def tr_rebote(name, anim):
    """Pop: A coge impulso y se encoge hasta desaparecer; B aparece de golpe con rebote. Con giro opcional."""
    h = "Rebote"
    p = f"{h}.Progreso"
    a, b = f"min(1, 2*{p})", f"max(0, 2*{p} - 1)"
    c1 = f"(1.70158*{h}.Fuerza)"
    in_back = f"(({c1} + 1)*{a}*{a}*{a} - {c1}*{a}*{a})"
    out_back = f"(1 + ({c1} + 1)*({b} - 1)*({b} - 1)*({b} - 1) + {c1}*({b} - 1)*({b} - 1))"
    tools = [Tool("PopA", "Transform", {"Size": I(1, f"max(0, 1 - {in_back})"), "Angle": I(0, f"{h}.Giro*{a}*{a}")}, pos=(-275, -66)),
             Tool("PopB", "Transform", {"Size": I(0, f"max(0, {out_back})"), "Angle": I(0, f"-{h}.Giro*(1 - {b})*(1 - {b})")}, pos=(-275, 66)),
             solid("Fondo", (0, 0, 0), (-220, -132)),
             merge("ConA", "Fondo", "PopA", (-220, 0), blend=1, blend_expr=f"iif({p} < 0.5, 1, 0)"),
             merge("ConB", "ConA", "PopB", (-165, 0), blend=0, blend_expr=f"iif({p} >= 0.5, 1, 0)")]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Fuerza", "Fuerza del rebote", 1, 0, 3), uc("Giro", "Giro (grados)", 0, -360, 360)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConB"), "Progreso": I(link=anim, out="Value"), "Fuerza": I(1), "Giro": I(0)},
                      ucs, (-110, 0)))
    pubs = numbered([pub(h, "Fuerza", "Fuerza del rebote", 1), pub(h, "Giro", "Giro (grados)", 0),
                     pub_color("Fondo", "Color de fondo", (0, 0, 0), "c1")])
    return macro(name, [("PopA", "Input"), ("PopB", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_RevelaLiquido")
def tr_revela_liquido(name, anim):
    """Revelado liquido: manchas organicas de ruido crecen y descubren el clip B, con un borde de color opcional."""
    h = "Liquido"
    e = smooth(f"{h}.Progreso")
    low = f"1 - 1.25*{e}"
    tools = [Tool("EntradaA", "PipeRouter", pos=(-385, -66)), Tool("EntradaB", "PipeRouter", pos=(-385, 66)),
             Tool("Manchas", "FastNoise", {**frame_format(), "Detail": I(6), "Contrast": I(1.6), "XScale": I(3), "SeetheRate": I(0.02)},
                  pos=(-385, -198)),
             Tool("Forma", "BrightnessContrast", {"Input": I(link="Manchas"), "Saturation": I(0), "Low": I(1, low),
                                                  "High": I(1.04, f"{low} + {h}.Suavidad")}, pos=(-330, -198)),
             Tool("FormaBorde", "BrightnessContrast", {"Input": I(link="Manchas"), "Saturation": I(0), "Low": I(1, f"{low} + 0.06"),
                                                       "High": I(1.1, f"{low} + 0.06 + {h}.Suavidad")}, pos=(-330, -264)),
             solid("Blanco", (1, 1, 1), (-275, -264)),
             merge("FormaInv", "Blanco", "Forma", (-275, -198), "Difference"),
             merge("ParteA", "EntradaA", "FormaInv", (-220, -66), "Multiply"),
             merge("ParteB", "EntradaB", "Forma", (-220, 66), "Multiply"),
             merge("Suma", "ParteA", "ParteB", (-165, 0), extra={"SubtractiveAdditive": I(0)}),
             merge("Banda", "FormaBorde", "Forma", (-220, -264), "Difference"),
             solid("ColorBorde", (1, 1, 1), (-165, -297)),
             merge("BandaTenida", "Banda", "ColorBorde", (-165, -264), "Multiply"),
             merge("ConBorde", "Suma", "BandaTenida", (-110, 0), "Screen", blend=0.6, blend_expr=f"{h}.Borde*sin({h}.Progreso*{PI})")]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Suavidad", "Suavidad del borde", 0.04, 0.005, 0.3), uc("Borde", "Borde de color", 0.6, 0, 1)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConBorde"), "Progreso": I(link=anim, out="Value"), "Suavidad": I(0.04),
                                                "Borde": I(0.6)}, ucs, (-55, 0)))
    pubs = numbered([pub(h, "Suavidad", "Suavidad del borde", 0.04), pub(h, "Borde", "Borde de color", 0.6),
                     pub_color("ColorBorde", "Color del borde", (1, 1, 1), "c1"),
                     pub("Manchas", "XScale", "Tamaño de las manchas (más alto = más pequeñas)", 3)])
    return macro(name, [("EntradaA", "Input"), ("EntradaB", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_AntesDespues")
def tr_antes_despues(name, anim):
    """Antes / despues: una linea recorre la imagen y descubre B, se detiene a la mitad para comparar y termina.
    Alarga la transicion para que la pausa dure mas."""
    h = "Comparar"
    p = f"{h}.Progreso"
    a = f"((1 - {h}.Pausa)/2)"
    e = f"iif({p} < {a}, 0.5*{smooth(clamp01(f'{p}/{a}'))}, iif({p} < 1 - {a}, 0.5, 0.5 + 0.5*{smooth(clamp01(f'({p} - (1 - {a}))/{a}'))}))"
    sh = dict(box=((0, 0, 0), 0.02, 0.015, 0.3))
    tools = [Tool("EntradaA", "PipeRouter", pos=(-330, -66)), Tool("EntradaB", "PipeRouter", pos=(-330, 66)),
             rect("MascB", (-275, -132), Center=I((0, 0.5), f"Point({h}.E/2, 0.5)"), Width=I(0, f"{h}.E"), Height=I(8)),
             merge("ConB", "EntradaA", "EntradaB", (-275, 0), extra={"EffectMask": I(link="MascB", out="Mask")}),
             rect("MascLinea", (-220, -132), Center=I((0, 0.5), f"Point({h}.E, 0.5)"), Width=I(0.005), Height=I(8)),
             solid("Linea", (1, 1, 1), (-220, -99), mask="MascLinea"),
             merge("ConLinea", "ConB", "Linea", (-220, 0), blend=1, blend_expr=f"iif({h}.E > 0.001, iif({h}.E < 0.999, 1, 0), 0)"),
             styled("Antes", "ANTES", "Montserrat", "ExtraBold", 0.03, (-165, -132), center=(0.88, 0.9), **sh),
             styled("Despues", "DESPUÉS", "Montserrat", "ExtraBold", 0.03, (-110, -132), center=(0.12, 0.9), **sh),
             merge("ConAntes", "ConLinea", "Antes", (-165, 0), blend=1, blend_expr=f"{h}.Etiquetas*{clamp01(f'(0.85 - {h}.E)/0.1')}"),
             merge("ConDespues", "ConAntes", "Despues", (-110, 0), blend=1, blend_expr=f"{h}.Etiquetas*{clamp01(f'({h}.E - 0.15)/0.1')}")]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Pausa", "Pausa a la mitad (% de la transición)", 0.4, 0, 0.9),
           uc("Etiquetas", "Etiquetas", 1, 0, 1), uc("E", "Posición interna", 0, 0, 1, clamp=False)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConDespues"), "Progreso": I(link=anim, out="Value"), "Pausa": I(0.4),
                                                "Etiquetas": I(1), "E": I(0, e)}, ucs, (-55, 0)))
    pubs = numbered([pub(h, "Pausa", "Pausa a la mitad (% de la transición)", 0.4), pub(h, "Etiquetas", "Etiquetas", 1),
                     pub("Antes", "StyledText", "Etiqueta de antes"), pub("Despues", "StyledText", "Etiqueta de después"),
                     pub_color("Linea", "Color de la línea", (1, 1, 1), "c1")])
    pubs += vertical_text(tools, h, ("Antes", "Despues"))
    return macro(name, [("EntradaA", "Input"), ("EntradaB", "Input")], pubs, h, tools, anim)


@register("Titles", "PRO_TTL_Social_Comentario")
def social_comentario(name, anim_):
    """Burbuja de 'responder al comentario' (TikTok/Reels): caja blanca redondeada, avatar de color y comentario; entra con pop."""
    return comentario(name, foto=False)


@register("Effects", "PRO_FX_Social_ComentarioFoto")
def social_comentario_foto(name, anim_):
    """La misma burbuja, pero el avatar es la foto del clip al que se aplica: pon la foto del usuario en una pista
    superior y aplicale este efecto. Solo se ve la burbuja; el resto queda transparente."""
    return comentario(name, foto=True)


def comentario(name, foto):
    """Burbuja de comentario. Todo se mide en unidades del ancho del cuadro (como el tamano del texto), y las alturas de
    texto se pasan a coordenadas del cuadro con el aspecto que fija 'Formato vertical', para que avatar y textos queden
    dentro de la caja en 16:9 y en 9:16."""
    h = "Comentario"
    asp = f"iif({h}.Vertical > 0.5, 0.5625, 1.7778)"
    extra_ucs = [uc("Rebote", "Rebote", 1.2, 0, 3), uc("Ancho", "Ancho de la burbuja", 0.52, 0.2, 1)]
    extra_inputs = {"Rebote": I(1.2), "Ancho": I(0.52)}
    if foto:
        extra_ucs += [uc("ZoomFoto", "Zoom de la foto", 1, 0.3, 4), uc("FotoX", "Encuadre X de la foto", 0, -0.5, 0.5),
                      uc("FotoY", "Encuadre Y de la foto", 0, -0.5, 0.5)]
        extra_inputs.update({"ZoomFoto": I(1), "FotoX": I(0), "FotoY": I(0)})
    ucs, inputs = kit(h, 0.12, 0.08, extra_ucs, extra_inputs)
    pad, d = 0.016, 0.064
    x0 = f"(0.5 - {h}.Ancho/2)"
    xa = f"{x0} + {pad + d / 2:g}"
    xt = f"{x0} + {2 * pad + d:g}"
    body = [solid("Base", (0, 0, 0), (-440, -198), alpha=0),
            rect("MascCaja", (-385, -231), Width=I(0.52, f"{h}.Ancho"), Height=I(d + 2 * pad, f"{d + 2 * pad:g}*{asp}"), CornerRadius=I(0.35)),
            solid("Caja", (1, 1, 1), (-385, -198), mask="MascCaja"),
            # avatar con la misma mascara que la caja (rectangulo con esquinas al maximo = circulo), para que las unidades coincidan
            rect("MascAvatar", (-330, -231), Center=I((0.27, 0.5), f"Point({xa}, 0.5)"), Width=I(d), Height=I(d, f"{d:g}*{asp}"), CornerRadius=I(1))]
    if foto:
        # el centro de la foto (un circulo del alto del cuadro, 1/aspecto en unidades de ancho) se escala al diametro del avatar
        body += [Tool("Foto", "Transform", {"Input": I(link="Entrada"), "Size": I(d * 1.7778, f"{d:g}*{asp}*{h}.ZoomFoto"),
                                            "Center": I((0.5, 0.5), f"Point({xa} - {h}.FotoX*{d:g}*{asp}*{h}.ZoomFoto, 0.5 - {h}.FotoY*{d:g}*{asp}*{h}.ZoomFoto)")},
                      pos=(-330, -264)),
                 merge("Avatar", "Base", "Foto", (-330, -198), blend=1, extra={"EffectMask": I(link="MascAvatar", out="Mask")})]
        body.insert(0, Tool("Entrada", "PipeRouter", pos=(-440, -264)))
    else:
        body.append(solid("Avatar", (0.95, 0.3, 0.45), (-330, -198), mask="MascAvatar"))
    body += [
            styled("Cabecera", "Responder al comentario de @usuario", "Poppins", "Regular", 0.016, (-275, -231), rgb=(0.45, 0.45, 0.45),
                   left=True),
            styled("Texto", "¿Cómo hiciste ese efecto?", "Poppins", "SemiBold", 0.026, (-220, -231), rgb=(0.08, 0.08, 0.08),
                   left=True),
            merge("B1", "Base", "Caja", (-385, -132)), merge("B2", "B1", "Avatar", (-330, -132)),
            merge("B3", "B2", "Cabecera", (-275, -132)), merge("B4", "B3", "Texto", (-220, -132)),
            mover("Pop", "B4", (-165, -132), size=f"max(0, {pop(h, 0, 1)})")]
    for tn, dy in (("Cabecera", 0.018), ("Texto", -0.012)):
        next(t for t in body if t.name == tn).inputs["Center"] = I((0.31, 0.5), f"Point({xt}, 0.5 + {dy:g}*{asp})")
    pubs = [pub("Cabecera", "StyledText", "Cabecera"), pub("Texto", "StyledText", "Comentario"),
            pub("Texto", "Font", "Fuente", group="f1"), pub("Texto", "Style", group="f1"), pub("Texto", "Size", "Tamaño del comentario", 0.026),
            pub_color("Caja", "Color de la burbuja", (1, 1, 1), "c1")]
    if foto:
        pubs += [pub(h, "ZoomFoto", "Zoom de la foto", 1), pub(h, "FotoX", "Encuadre X de la foto", 0),
                 pub(h, "FotoY", "Encuadre Y de la foto", 0)]
    else:
        pubs.append(pub_color("Avatar", "Color del avatar", (0.95, 0.3, 0.45), "c2"))
    pubs += [pub(h, "Ancho", "Ancho de la burbuja", 0.52), pub(h, "Rebote", "Rebote", 1.2)]
    return style_title(name, h, ucs, inputs, body, [("Pop", f"{h}.Xs*min(1, 3*{h}.U)")], pubs, dy_h=0.2, dy_v=0.12, size_v=1.6,
                       mains=[("Entrada", "Input")] if foto else ())


# ----------------------------------------------------------------------- lote 12: transiciones
@register("Transitions", "PRO_TR_DestelloLente")
def tr_destello_lente(name, anim):
    """Destello de lente: un nucleo de luz cruza la imagen con una raya anamorfica y tapa el corte con un golpe de luz."""
    h = "Destello"
    p = f"{h}.Progreso"
    bell = f"sin({p}*{PI})"
    tools = [Tool("Mezcla", "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.46)/0.08")))}, pos=(-330, 0)),
             Tool("Exposicion", "BrightnessContrast", {"Input": I(link="Mezcla"), "Gain": I(1, f"1 + 1.5*{h}.Intensidad*{bell}*{bell}*{bell}")},
                  pos=(-275, 0)),
             ellipse("MascNucleo", (-220, -132), SoftEdge=I(0.5), Width=I(0.5, f"0.15 + 0.6*{bell}"), Height=I(0.5, f"0.15 + 0.6*{bell}"),
                     Center=I((0.5, 0.5), f"Point(-0.2 + 1.4*{p}, {h}.Altura)")),
             solid("Nucleo", (1, 0.92, 0.8), (-220, -99), mask="MascNucleo"),
             rect("MascRaya", (-165, -132), Width=I(4), Height=I(0.006), SoftEdge=I(0.01),
                  Center=I((0.5, 0.5), f"Point(-0.2 + 1.4*{p}, {h}.Altura)")),
             solid("Raya", (0.55, 0.75, 1), (-165, -99), mask="MascRaya"),
             merge("ConNucleo", "Exposicion", "Nucleo", (-220, 0), "Screen", blend=0, blend_expr=f"{h}.Intensidad*{bell}"),
             merge("ConRaya", "ConNucleo", "Raya", (-165, 0), "Screen", blend=0, blend_expr=f"{h}.Intensidad*{bell}")]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Intensidad", "Intensidad", 1, 0, 2), uc("Altura", "Altura del destello", 0.6, 0, 1)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConRaya"), "Progreso": I(link=anim, out="Value"), "Intensidad": I(1),
                                                "Altura": I(0.6)}, ucs, (-110, 0)))
    pubs = numbered([pub(h, "Intensidad", "Intensidad", 1), pub(h, "Altura", "Altura del destello", 0.6),
                     pub_color("Nucleo", "Color del núcleo", (1, 0.92, 0.8), "c1"), pub_color("Raya", "Color de la raya", (0.55, 0.75, 1), "c2")])
    return macro(name, [("Mezcla", "Background"), ("Mezcla", "Foreground")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_ZoomTraves")
def tr_zoom_traves(name, anim):
    """Zoom a traves: se entra con zoom a un punto de A (por ejemplo, un ojo o una ventana) y se sale desde un punto de B."""
    h = "Traves"
    p = f"{h}.Progreso"
    a, b = f"min(1, 2*{p})", f"(1 - max(0, 2*{p} - 1))"
    bell = f"sin({p}*{PI})*sin({p}*{PI})"
    tools = []
    for n_, k, px, py, y in (("ZoomA", a, f"{h}.AX", f"{h}.AY", -33), ("ZoomB", b, f"{h}.BX", f"{h}.BY", 33)):
        s = f"(1 + {h}.Zoom*pow({k}, 3))"
        tools.append(Tool(n_, "Transform", {"Size": I(1, s), "Center": I((0.5, 0.5), f"Point(0.5 + ({px} - 0.5)*(1 - {s}), 0.5 + ({py} - 0.5)*(1 - {s}))")},
                          pos=(-275, y)))
    tools += [Tool("Mezcla", "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.45)/0.1"))), "Background": I(link="ZoomA"),
                                          "Foreground": I(link="ZoomB")}, pos=(-220, 0)),
              Tool("Movimiento", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, f"{h}.Desenfoque*{bell}"),
                                          "Input": I(link="Mezcla")}, pos=(-165, 0))]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("AX", "Punto de A: X", 0.5, 0, 1), uc("AY", "Punto de A: Y", 0.5, 0, 1),
           uc("BX", "Punto de B: X", 0.5, 0, 1), uc("BY", "Punto de B: Y", 0.5, 0, 1), uc("Zoom", "Zoom", 6, 0.5, 20),
           uc("Desenfoque", "Desenfoque", 20, 0, 100)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Movimiento"), "Progreso": I(link=anim, out="Value"), "AX": I(0.5), "AY": I(0.5),
                                                "BX": I(0.5), "BY": I(0.5), "Zoom": I(6), "Desenfoque": I(20)}, ucs, (-110, 0)))
    pubs = [pub(h, "AX", "Punto de A: X", 0.5), pub(h, "AY", "Punto de A: Y", 0.5), pub(h, "BX", "Punto de B: X", 0.5),
            pub(h, "BY", "Punto de B: Y", 0.5), pub(h, "Zoom", "Zoom", 6), pub(h, "Desenfoque", "Desenfoque", 20)]
    return macro(name, [("ZoomA", "Input"), ("ZoomB", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_EstaticaTV")
def tr_estatica_tv(name, anim):
    """Cambio de canal: rafaga de estatica con lineas y saltos verticales entre A y B."""
    h = "Canal"
    p = f"{h}.Progreso"
    bell = f"sin({p}*{PI})"
    tools = [Tool("Mezcla", "Dissolve", {"Mix": I(0, f"iif({p} < 0.5, 0, 1)")}, pos=(-385, 0)),
             Tool("Salto", "Transform", {"Input": I(link="Mezcla"),
                                         "Center": I((0.5, 0.5), f"Point(0.5 + 0.02*{h}.Saltos*{bell}*sin(time*17.3), 0.5 + 0.08*{h}.Saltos*{bell}*sin(time*7.9))")},
                  pos=(-330, 0)),
             Tool("Ruido", "FastNoise", {**frame_format(), "Detail": I(2), "Contrast": I(2.5), "XScale": I(220), "SeetheRate": I(5),
                                         "Discontinuous": I(1)}, pos=(-330, -132)),
             Tool("RuidoBN", "BrightnessContrast", {"Input": I(link="Ruido"), "Saturation": I(0)}, pos=(-275, -132)),
             merge("ConRuido", "Salto", "RuidoBN", (-275, 0), blend=0, blend_expr=f"min(1, {h}.Estatica*1.6*{bell}*{bell})")]
    t, last = scanlines("Lineas", "ConRuido", h, -220, high=0.6)
    tools += t
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Estatica", "Estática", 1, 0, 1), uc("Saltos", "Saltos de imagen", 1, 0, 3),
           uc("Lineas", "Líneas", 0.4, 0, 1), uc("NumLineas", "Número de líneas", 300, 50, 1000)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Progreso": I(link=anim, out="Value"), "Estatica": I(1), "Saltos": I(1),
                                                "Lineas": I(0.4), "NumLineas": I(300)}, ucs, (-110, 0)))
    pubs = [pub(h, "Estatica", "Estática", 1), pub(h, "Saltos", "Saltos de imagen", 1), pub(h, "Lineas", "Líneas", 0.4)]
    return macro(name, [("Mezcla", "Background"), ("Mezcla", "Foreground")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_Apagon")
def tr_apagon(name, anim):
    """Apagon: la luz de A parpadea hasta apagarse y B se enciende parpadeando (terror, misterio, cambios de escena)."""
    h = "Apagon"
    p = f"{h}.Progreso"
    env = f"abs(1 - 2*{p})"
    on = f"iif(abs(sin(time*2.9*{h}.Velocidad)*sin(time*1.1*{h}.Velocidad + 2)) > 0.9*(1 - {env}), 1, 0.08)"
    tools = [Tool("Mezcla", "Dissolve", {"Mix": I(0, f"iif({p} < 0.5, 0, 1)")}, pos=(-275, 0)),
             Tool("Luz", "BrightnessContrast", {"Input": I(link="Mezcla"), "Gain": I(1, f"{on}*(0.25 + 0.75*{env})"),
                                                "Saturation": I(1, f"0.6 + 0.4*{env}")}, pos=(-220, 0))]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Velocidad", "Velocidad del parpadeo", 1, 0.2, 4)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Luz"), "Progreso": I(link=anim, out="Value"), "Velocidad": I(1)}, ucs, (-165, 0)))
    pubs = [pub(h, "Velocidad", "Velocidad del parpadeo", 1)]
    return macro(name, [("Mezcla", "Background"), ("Mezcla", "Foreground")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_Corte")
def tr_corte(name, anim):
    """Corte de espada (anime / gaming): una linea blanca raja A en diagonal y las dos mitades se deslizan y descubren B."""
    h = "Corte"
    p = f"{h}.Progreso"
    th = f"({h}.Angulo*{PI}/180)"
    asp = f"{h}.Aspecto"
    line = clamp01(f"{p}/0.15")
    e = smooth(clamp01(f"({p} - 0.15)/0.85"))
    tools = [Tool("EntradaA", "PipeRouter", pos=(-385, -66)), Tool("EntradaB", "PipeRouter", pos=(-385, 66))]
    last = "EntradaB"
    for side, sg in (("Sup", 1), ("Inf", -1)):
        mx = f"0.5 + {sg}*4*(-sin({th}))/{asp}"
        my = f"0.5 + {sg}*4*cos({th})"
        dx = f"{sg}*{h}.Distancia*{e}*cos({th})"
        dy = f"{sg}*{h}.Distancia*{e}*sin({th})*{asp}"
        sep_x = f"{sg}*0.04*{e}*(-sin({th}))"
        sep_y = f"{sg}*0.04*{e}*cos({th})*{asp}"
        tools += [Tool(f"Mitad{side}", "Transform", {"Input": I(link="EntradaA"),
                                                      "Center": I((0.5, 0.5), f"Point(0.5 + {dx} + {sep_x}, 0.5 + {dy} + {sep_y})")},
                       pos=(-330, -66 * sg)),
                  rect(f"Masc{side}", (-275, -132 * sg), Width=I(8), Height=I(8), Angle=I(30, f"{h}.Angulo"),
                       Center=I((0.5, 0.5), f"Point({mx} + {dx} + {sep_x}, {my} + {dy} + {sep_y})")),
                  merge(f"Con{side}", last, f"Mitad{side}", (-275 + 55 * (sg < 0), 0), extra={"EffectMask": I(link=f"Masc{side}", out="Mask")})]
        last = f"Con{side}"
    tools += [rect("MascTajo", (-165, -132), Width=I(0, f"8*{line}"), Height=I(0.004), Angle=I(30, f"{h}.Angulo")),
              solid("Tajo", (1, 1, 1), (-165, -99), mask="MascTajo"),
              merge("ConTajo", last, "Tajo", (-165, 0), blend=0, blend_expr=f"min(1, 3*(1 - {e}))*iif({p} > 0, 1, 0)")]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Angulo", "Ángulo del corte (grados)", 30, -90, 90),
           uc("Distancia", "Distancia que se deslizan", 1.2, 0, 3),
           uc("Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778, 0.4, 3)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConTajo"), "Progreso": I(link=anim, out="Value"), "Angulo": I(30),
                                                "Distancia": I(1.2), "Aspecto": I(1.7778)}, ucs, (-110, 0)))
    pubs = numbered([pub(h, "Angulo", "Ángulo del corte (grados)", 30), pub(h, "Distancia", "Distancia que se deslizan", 1.2),
                     pub_color("Tajo", "Color de la línea", (1, 1, 1), "c1"),
                     pub(h, "Aspecto", "Aspecto del timeline (16:9 = 1.778, 9:16 = 0.5625)", 1.7778)])
    return macro(name, [("EntradaA", "Input"), ("EntradaB", "Input")], pubs, h, tools, anim)


@register("Titles", "PRO_TTL_Social_Ranking")
def social_ranking(name, anim_):
    """Videos de top / ranking: numero enorme en Anton con contorno, golpe de entrada y nombre del puesto debajo."""
    h = "Ranking"
    land = clamp01(f"{h}.U/0.5")
    ucs, inputs = kit(h, 0.2, 0.08, [uc("Golpe", "Fuerza del golpe", 1.5, 0, 4)], {"Golpe": I(1.5)})
    body = [styled("Numero", "#1", "Anton", "Regular", 0.22, (-385, -132), rgb=(1, 0.86, 0), outline=((0, 0, 0), 0.04),
                   hard=((0, 0, 0), (0.012, -0.018))),
            styled("Nombre", "EL MEJOR TRUCO", "Montserrat", "ExtraBold", 0.05, (-330, -132), outline=((0, 0, 0), 0.07),
                   soft=((0, 0, 0), (0.004, -0.008), 4)),
            mover("Anim1", "Numero", (-385, -66), cy="0.56", size=f"1 + {h}.Golpe*(1 - {land})*(1 - {land})", angle=f"-6*(1 - {land})"),
            mover("Anim2", "Nombre", (-330, -66), cy=f"0.38 - 0.03*(1 - {phase(h, 0.5, 1)})")]
    pubs = [pub("Numero", "StyledText", "Puesto"), pub("Nombre", "StyledText", "Nombre"),
            *text_pubs("Numero", " del puesto", 0.22, (1, 0.86, 0), 1), *text_pubs("Nombre", " del nombre", 0.05, (1, 1, 1), 2),
            pub(h, "Golpe", "Fuerza del golpe", 1.5)]
    layers = [("Anim1", f"min(1, 4*{h}.U)*{h}.Xs"), ("Anim2", stage(h, 0.5, 1))]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dy_v=0.05, size_v=2.0)



# ======================================================================= LOTE 13: iconos animados
# Los iconos se dibujan con mascaras (rectangulos con esquinas al maximo = circulos, triangulos) en unidades del ancho
# del cuadro; las alturas se pasan a coordenadas del cuadro con el aspecto de 'Formato vertical'.
def icon_asp(h):
    return f"iif({h}.Vertical > 0.5, 0.5625, 1.7778)"


def ipt(h, dx, dy, cx="0.5", cy="0.5"):
    return f"Point({cx} + ({dx}), {cy} + ({dy})*{icon_asp(h)})"


def shape(name, h, pos, dx, dy, w, ht, rgb, radius=0, angle=None, alpha=1, border=None):
    """Forma rectangular (o circular con radius=1) y su relleno de color. w/ht pueden ser numeros o expresiones."""
    kw = {"Center": I((0.5, 0.5), ipt(h, dx, dy)), "Width": I(0.05, str(w)), "Height": I(0.05, f"({ht})*{icon_asp(h)}"),
          "CornerRadius": I(radius)}
    if angle is not None:
        kw["Angle"] = I(0, str(angle))
    if border is not None:
        kw.update({"Solid": I(0), "BorderWidth": I(border)})
    return [rect(f"M{name}", (pos[0], pos[1] - 33), **kw), solid(name, rgb, pos, alpha=alpha, mask=f"M{name}")]


def triangle(name, h, pos, pts, rgb):
    kw = {**mask_format(), **{f"Point{i}": I((0.5, 0.5), ipt(h, dx, dy)) for i, (dx, dy) in enumerate(pts, 1)}}
    return [Tool(f"M{name}", "TriangleMask", kw, pos=(pos[0], pos[1] - 33)), solid(name, rgb, pos, mask=f"M{name}")]


def chain(prefix, base, layers, x0, y):
    """Apila capas [(herramienta, opacidad o None)] sobre 'base' con nombres propios (prefix1, prefix2...)."""
    tools, last = [], base
    for i, (fg, blend_expr) in enumerate(layers, 1):
        tools.append(merge(f"{prefix}{i}", last, fg, (x0 + 22 * i, y), blend=1 if blend_expr else None, blend_expr=blend_expr))
        last = f"{prefix}{i}"
    return tools, last


def icon_label(name, text, size, h, dy, pos, rgb=(1, 1, 1)):
    t = styled(name, text, "Montserrat", "ExtraBold", size, pos, rgb=rgb, outline=((0, 0, 0), 0.06), soft=((0, 0, 0), (0.003, -0.006), 3))
    t.inputs["Center"] = I((0.5, 0.4), ipt(h, 0, dy))
    return t


def tool_named(tools, name):
    return next(t for t in tools if t.name == name)


@register("Titles", "PRO_TTL_Icono_Like")
def icono_like(name, anim_):
    """Corazon de 'me gusta': aparece con rebote, suelta una explosion de puntos y late mientras dura el clip."""
    h = "Like"
    a = 0.09
    o = a / (2 * 2 ** 0.5)
    ucs, inputs = kit(h, 0.15, 0.08, [uc("Rebote", "Rebote", 1.5, 0, 3), uc("Latido", "Latido", 1, 0, 3)], {"Rebote": I(1.5), "Latido": I(1)})
    red = (1, 0.18, 0.33)
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0)]
    body += shape("Rombo", h, (-385, -198), 0, -a * 0.2, a, a, red, angle=45)
    body += shape("LobuloI", h, (-330, -198), -o, -a * 0.2 + o, a, a, red, radius=1)
    body += shape("LobuloD", h, (-275, -198), o, -a * 0.2 + o, a, a, red, radius=1)
    for n in ("LobuloI", "LobuloD"):
        color_from(tool_named(body, n), "Rombo")
    burst = phase(h, 0.3, 1)
    r = f"(0.06 + 0.07*{burst})"
    for k in range(8):
        ang = 2 * math.pi * k / 8 + 0.3
        body += shape(f"Chispa{k}", h, (-385 + 22 * k, -330), f"{r}*{math.cos(ang):.4f}", f"{r}*{math.sin(ang):.4f}", 0.012, 0.012,
                      (1, 0.8, 0.3), radius=1)
    body.append(icon_label("Etiqueta", "¡DALE LIKE!", 0.035, h, -0.085, (-110, -264)))
    t, corazon = chain("Corazon", "Base", [("Rombo", None), ("LobuloI", None), ("LobuloD", None)], -385, -132)
    body += t
    latido = f"(1 + 0.06*{h}.Latido*max(0, sin(time*0.35))*max(0, sin(time*0.35))*iif({h}.U >= 1, 1, 0))"
    body.append(mover("Pop", corazon, (-220, -132), size=f"max(0, {pop(h, 0, 0.6)})*{latido}"))
    t, chispas = chain("Chispas", "Base", [(f"Chispa{k}", None) for k in range(8)], -385, -99)
    body += t
    layers = [(chispas, f"{h}.Xs*{burst}*(1 - {burst})*4"), ("Pop", f"{h}.Xs*min(1, 3*{h}.U)"), ("Etiqueta", stage(h, 0.5, 1))]
    pubs = [pub_color("Rombo", "Color del corazón", red, "c1"), pub("Etiqueta", "StyledText", "Texto"),
            pub(h, "Rebote", "Rebote", 1.5), pub(h, "Latido", "Latido", 1)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.5)


@register("Titles", "PRO_TTL_Icono_Play")
def icono_play(name, anim_):
    """Boton de reproducir estilo YouTube: entra con rebote, pulsa suavemente y lleva un texto debajo."""
    h = "Play"
    ucs, inputs = kit(h, 0.15, 0.08, [uc("Rebote", "Rebote", 1.4, 0, 3)], {"Rebote": I(1.4)})
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0)]
    body += shape("Boton", h, (-385, -198), 0, 0, 0.16, 0.112, (1, 0.05, 0.05), radius=0.35)
    body += triangle("Triangulo", h, (-330, -198), [(-0.022, 0.028), (-0.022, -0.028), (0.032, 0)], (1, 1, 1))
    body.append(icon_label("Etiqueta", "MIRA EL VIDEO COMPLETO", 0.03, h, -0.1, (-110, -264)))
    t, boton = chain("Icono", "Base", [("Boton", None), ("Triangulo", None)], -385, -132)
    body += t
    pulso = f"(1 + 0.03*sin(time*0.2)*iif({h}.U >= 1, 1, 0))"
    body.append(mover("Pop", boton, (-220, -132), size=f"max(0, {pop(h, 0, 0.6)})*{pulso}"))
    layers = [("Pop", f"{h}.Xs*min(1, 3*{h}.U)"), ("Etiqueta", stage(h, 0.45, 1))]
    pubs = [pub_color("Boton", "Color del botón", (1, 0.05, 0.05), "c1"), pub_color("Triangulo", "Color del triángulo", (1, 1, 1), "c2"),
            pub("Etiqueta", "StyledText", "Texto"), pub(h, "Rebote", "Rebote", 1.4)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.5)


@register("Titles", "PRO_TTL_Icono_Checklist")
def icono_checklist(name, anim_):
    """Lista con tres puntos que se van marcando con un check verde que salta (tutoriales, pasos, 'cosas que necesitas')."""
    h = "Lista"
    asp = icon_asp(h)
    ucs, inputs = kit(h, 0.6, 0.08, [uc("Rebote", "Rebote", 1.6, 0, 3)], {"Rebote": I(1.6)})
    green = (0.2, 0.8, 0.4)
    body = [solid("Base", (0, 0, 0), (-440, -330), alpha=0)]
    layers = []
    for i, txt in enumerate(("Primer paso", "Segundo paso", "Tercer paso")):
        y = 0.075 - 0.075 * i
        a0 = i / 3
        x = -385 + 165 * i
        body += shape(f"Circulo{i}", h, (x, -264), 0, 0, 0.05, 0.05, green, radius=1)
        body += shape(f"Corto{i}", h, (x + 33, -264), -0.008, -0.003, 0.006, 0.016, (1, 1, 1), angle=45)
        body += shape(f"Largo{i}", h, (x + 66, -264), 0.005, 0.002, 0.006, 0.03, (1, 1, 1), angle=-40)
        if i:
            color_from(tool_named(body, f"Circulo{i}"), "Circulo0")
        t = styled(f"Texto{i}", txt, "Poppins", "SemiBold", 0.035, (x + 99, -264), left=True, soft=((0, 0, 0), (0.003, -0.005), 3))
        t.inputs["Center"] = I((0.36, 0.5), ipt(h, -0.14, y))
        body.append(t)
        tt, check = chain(f"Check{i}_", "Base", [(f"Circulo{i}", None), (f"Corto{i}", None), (f"Largo{i}", None)], x, -198)
        body += tt
        s = f"max(0, {pop(h, a0 + 0.08, a0 + 0.3)})"
        # el check se dibuja en el centro del cuadro y se lleva a su fila: escalar y luego mover
        body.append(Tool(f"Salto{i}", "Transform", {"Input": I(link=check), "Size": I(1, s),
                                                    "Center": I((0.5, 0.5), f"Point(0.5 - 0.18, 0.5 + {y:g}*{asp})")}, pos=(x + 99, -198)))
        layers += [(f"Texto{i}", stage(h, a0, a0 + 0.2)), (f"Salto{i}", f"{h}.Xs*iif({h}.U > {a0 + 0.08:g}, 1, 0)")]
        if i:
            t.inputs.update({"Font": I("Poppins", "Texto0.Font"), "Style": I("SemiBold", "Texto0.Style")})
    pubs = [pub(f"Texto{i}", "StyledText", f"Punto {i + 1}") for i in range(3)]
    pubs += [pub("Texto0", "Font", "Fuente", group="f1"), pub("Texto0", "Style", group="f1"),
             pub_color("Circulo0", "Color del check", green, "c1"), pub(h, "Rebote", "Rebote", 1.6)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, dx_v=0.1, size_v=2.0)


@register("Titles", "PRO_TTL_Icono_Ubicacion")
def icono_ubicacion(name, anim_):
    """Pin de ubicacion que cae y rebota sobre su sombra, con el nombre del lugar en una etiqueta (viajes, vlogs)."""
    h = "Ubicacion"
    asp = icon_asp(h)
    ucs, inputs = kit(h, 0.3, 0.08, [uc("Rebote", "Rebote", 1.4, 0, 3)], {"Rebote": I(1.4)})
    red = (0.95, 0.2, 0.25)
    drop = f"max(0, {pop(h, 0, 0.7)})"
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0)]
    body += shape("Sombra", h, (-385, -330), 0, -0.058, f"0.02 + 0.03*{drop}", 0.012, (0, 0, 0), radius=1, alpha=0.45)
    body += shape("Cabeza", h, (-330, -198), 0, 0.02, 0.07, 0.07, red, radius=1)
    body += triangle("Punta", h, (-275, -198), [(-0.03, 0.006), (0.03, 0.006), (0, -0.055)], red)
    body += shape("Hueco", h, (-220, -198), 0, 0.02, 0.025, 0.025, (1, 1, 1), radius=1)
    color_from(tool_named(body, "Punta"), "Cabeza")
    t, pin = chain("Pin", "Base", [("Cabeza", None), ("Punta", None), ("Hueco", None)], -385, -132)
    body += t
    body.append(Tool("Caida", "Transform", {"Input": I(link=pin), "Center": I((0.5, 0.5), f"Point(0.5, 0.5 + 0.2*(1 - {drop})*{asp})")},
                     pos=(-220, -132)))
    lbl = styled("Lugar", "Ciudad de México", "Poppins", "SemiBold", 0.032, (-110, -264), rgb=(0.08, 0.08, 0.08),
                 box=((1, 1, 1), 0.02, 0.012, 0.4))
    lbl.inputs["Center"] = I((0.5, 0.4), ipt(h, 0, -0.1))
    body.append(lbl)
    layers = [("Sombra", f"{h}.Xs*min(1, 2*{h}.U)"), ("Caida", f"{h}.Xs*min(1, 4*{h}.U)"), ("Lugar", stage(h, 0.6, 1))]
    pubs = [pub("Lugar", "StyledText", "Lugar"), pub("Lugar", "Font", "Fuente", group="f1"), pub("Lugar", "Style", group="f1"),
            pub_color("Cabeza", "Color del pin", red, "c1"), pub(h, "Rebote", "Rebote", 1.4)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.5)


@register("Titles", "PRO_TTL_Icono_Flecha")
def icono_flecha(name, anim_):
    """Flecha que senala y rebota sin parar en su direccion (para indicar un boton, un objeto o 'mira aqui')."""
    h = "Flecha"
    asp = icon_asp(h)
    th = f"({h}.Angulo*{PI}/180)"
    ucs, inputs = kit(h, 0.12, 0.08, [uc("Angulo", "Ángulo (0 = hacia abajo)", 0, -180, 180), uc("Rebote", "Rebote", 1.4, 0, 3),
                                      uc("Recorrido", "Recorrido del rebote", 0.02, 0, 0.1)],
                      {"Angulo": I(0), "Rebote": I(1.4), "Recorrido": I(0.02)})
    yellow = (1, 0.85, 0.1)
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0)]
    body += shape("Asta", h, (-385, -198), 0, 0.03, 0.022, 0.07, yellow)
    body += triangle("Punta", h, (-330, -198), [(-0.04, 0), (0.04, 0), (0, -0.05)], yellow)
    color_from(tool_named(body, "Punta"), "Asta")
    t, flecha = chain("Icono", "Base", [("Asta", None), ("Punta", None)], -385, -132)
    body += t
    bob = f"{h}.Recorrido*sin(time*0.25)"
    body.append(Tool("Mover", "Transform", {"Input": I(link=flecha), "Angle": I(0, f"{h}.Angulo"), "Size": I(1, f"max(0, {pop(h, 0, 1)})"),
                                            "Center": I((0.5, 0.5), f"Point(0.5 + {bob}*sin({th}), 0.5 - {bob}*cos({th})*{asp})")},
                     pos=(-220, -132)))
    layers = [("Mover", f"{h}.Xs*min(1, 3*{h}.U)")]
    pubs = [pub(h, "Angulo", "Ángulo (0 = hacia abajo)", 0), pub_color("Asta", "Color", yellow, "c1"),
            pub(h, "Recorrido", "Recorrido del rebote", 0.02), pub(h, "Rebote", "Rebote", 1.4)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.5)


@register("Titles", "PRO_TTL_Icono_Estrellas")
def icono_estrellas(name, anim_):
    """Valoracion de 1 a 5 estrellas que aparecen una a una (resenas, productos, recomendaciones)."""
    h = "Estrellas"
    ucs, inputs = kit(h, 0.35, 0.08, [uc("Valoracion", "Estrellas encendidas", 5, 0, 5, integer=True), uc("Rebote", "Rebote", 1.6, 0, 3)],
                      {"Valoracion": I(5), "Rebote": I(1.6)})
    gold = (1, 0.78, 0.1)
    body = [solid("Oro", gold, (-440, -330))]
    layers = []
    for i in range(5):
        a0 = i * 0.15
        star = styled(f"Estrella{i}", "★", "Segoe UI Symbol", "Regular", 0.08, (-385 + 55 * i, -264), rgb=gold,
                      soft=((0, 0, 0), (0.003, -0.005), 3))
        star.inputs.update({f"{ch}1": I(1, f"iif({h}.Valoracion > {i}, Oro.TopLeft{ch}, 0.35)") for ch in ("Red", "Green", "Blue")})
        body += [star, mover(f"Pop{i}", f"Estrella{i}", (-385 + 55 * i, -198), cx=f"{0.5 + 0.075 * (i - 2):g}",
                             size=f"max(0, {pop(h, a0, a0 + 0.4)})")]
        layers.append((f"Pop{i}", f"{h}.Xs*iif({h}.U > {a0:g}, 1, 0)"))
    body.append(icon_label("Etiqueta", "4.9 · +2.000 reseñas", 0.028, h, -0.06, (-110, -264)))
    layers.append(("Etiqueta", stage(h, 0.7, 1)))
    pubs = [pub(h, "Valoracion", "Estrellas encendidas", 5), pub_color("Oro", "Color de las estrellas", gold, "c1"),
            pub("Etiqueta", "StyledText", "Texto"), pub(h, "Rebote", "Rebote", 1.6)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.0)


@register("Titles", "PRO_TTL_Icono_Redes")
def icono_redes(name, anim_):
    """Usuario de redes: circulo con '@' que salta y una pastilla que se abre con tu nombre de usuario ('sigueme en...')."""
    h = "Redes"
    ucs, inputs = kit(h, 0.3, 0.1, [uc("Rebote", "Rebote", 1.4, 0, 3), uc("Ancho", "Ancho de la pastilla", 0.36, 0.1, 1)],
                      {"Rebote": I(1.4), "Ancho": I(0.36)})
    grow = phase(h, 0.35, 1)
    left = f"(-{h}.Ancho/2)"
    w = f"max(0.07, {h}.Ancho*{grow})"
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0)]
    body += shape("Pastilla", h, (-385, -198), f"{left} + {w}/2", 0, w, 0.07, (0.1, 0.1, 0.12), radius=1)
    body += shape("Insignia", h, (-330, -198), f"{left} + 0.035", 0, 0.07, 0.07, (0.95, 0.25, 0.55), radius=1)
    arroba = styled("Arroba", "@", "Montserrat", "Bold", 0.045, (-275, -198))
    arroba.inputs["Center"] = I((0.5, 0.5), ipt(h, f"{left} + 0.035", -0.003))
    usuario = styled("Usuario", "@tuusuario", "Poppins", "SemiBold", 0.032, (-220, -198), left=True)
    usuario.inputs["Center"] = I((0.5, 0.5), ipt(h, f"{left} + 0.085", 0))
    body += [arroba, usuario]
    t, insignia = chain("Circulo", "Base", [("Insignia", None), ("Arroba", None)], -385, -132)
    body += t
    s = f"max(0, {pop(h, 0, 0.4)})"
    # la insignia esta a la izquierda: se escala respecto al centro del cuadro y se compensa el desplazamiento
    body.append(Tool("Salto", "Transform", {"Input": I(link=insignia), "Size": I(1, s),
                                            "Center": I((0.5, 0.5), f"Point(0.5 + ({left} + 0.035)*(1 - {s}), 0.5)")}, pos=(-220, -132)))
    layers = [("Pastilla", f"{h}.Xs*iif({h}.U > 0.35, 1, 0)"), ("Salto", f"{h}.Xs*min(1, 3*{h}.U)"), ("Usuario", stage(h, 0.6, 1))]
    pubs = [pub("Usuario", "StyledText", "Usuario"), pub("Arroba", "StyledText", "Símbolo"),
            pub_color("Insignia", "Color del círculo", (0.95, 0.25, 0.55), "c1"), pub_color("Pastilla", "Color de la pastilla", (0.1, 0.1, 0.12), "c2"),
            pub(h, "Ancho", "Ancho de la pastilla", 0.36), pub(h, "Rebote", "Rebote", 1.4)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.2)


@register("Titles", "PRO_TTL_Icono_Cursor")
def icono_cursor(name, anim_):
    """Cursor que se desliza hasta el centro y hace clic, con una onda que se expande (tutoriales y 'haz clic aqui')."""
    h = "Cursor"
    asp = icon_asp(h)
    ucs, inputs = kit(h, 0.5, 0.08, [uc("DesdeX", "Viene desde X", 0.18, -0.5, 0.5), uc("DesdeY", "Viene desde Y", -0.12, -0.5, 0.5)],
                      {"DesdeX": I(0.18), "DesdeY": I(-0.12)})
    mv = phase(h, 0, 0.7)
    click = clamp01(f"({h}.U - 0.7)/0.3")
    press = f"(1 - 0.18*sin({click}*{PI}))"
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0)]
    body += triangle("Borde", h, (-385, -198), [(-0.004, 0.006), (-0.004, -0.062), (0.044, -0.03)], (0.05, 0.05, 0.05))
    body += triangle("Flecha", h, (-330, -198), [(0, 0), (0, -0.05), (0.035, -0.027)], (1, 1, 1))
    body += shape("Cola", h, (-275, -198), 0.016, -0.05, 0.01, 0.026, (1, 1, 1), angle=25)
    body += shape("Onda", h, (-220, -198), 0, 0, f"0.02 + 0.09*{click}", f"0.02 + 0.09*{click}", (1, 1, 1), radius=1, border=0.003)
    color_from(tool_named(body, "Cola"), "Flecha")
    t, cursor = chain("Icono", "Base", [("Borde", None), ("Flecha", None), ("Cola", None)], -385, -132)
    body += t
    body.append(Tool("Movimiento", "Transform", {"Input": I(link=cursor), "Size": I(1, press),
                                                 "Center": I((0.5, 0.5), f"Point(0.5 + {h}.DesdeX*(1 - {mv}), 0.5 + {h}.DesdeY*(1 - {mv})*{asp})")},
                     pos=(-220, -132)))
    layers = [("Onda", f"{h}.Xs*{click}*(1 - {click})*4*iif({h}.U >= 0.7, 1, 0)"), ("Movimiento", f"{h}.Xs*min(1, 4*{h}.U)")]
    pubs = [pub_color("Flecha", "Color del cursor", (1, 1, 1), "c1"), pub_color("Onda", "Color de la onda", (1, 1, 1), "c2"),
            pub(h, "DesdeX", "Viene desde X", 0.18), pub(h, "DesdeY", "Viene desde Y", -0.12)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.5)


# ======================================================================= LOTE 14: edicion dinamica de podcast
# Recursos del estilo "clip de podcast viral": brillo cinematico, pendulo flotante, zoom con destello, look retro,
# televisor, fondo granulado, frases y subtitulos palabra a palabra en Inter, texto con giro, texto con contorno
# para poner detras de la persona, e icono de llama.
INTER = "Inter 24pt"   # nombre de familia de los .ttf estaticos de Google Fonts (con la variable, elige "Inter")


@register("Effects", "PRO_FX_Din_BrilloCine")
def din_brillo_cine(name, anim):
    """Brillo cinematico: halo suave cercano y amplio sobre las luces de la imagen y grano fino. Va bien en textos
    (aplicalo al clip compuesto), personas recortadas y fondos."""
    h = "BrilloCine"
    tools = [Tool("Entrada", "PipeRouter", pos=(-440, 0)),
             Tool("Luces", "BrightnessContrast", {"Input": I(link="Entrada"), "Low": I(0.45, f"{h}.Umbral"), "High": I(1),
                                                  "Saturation": I(1.1)}, pos=(-385, -66)),
             Tool("HaloCerca", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(10, f"{h}.Tamano*0.25"),
                                        "Input": I(link="Luces")}, pos=(-330, -99)),
             Tool("HaloLejos", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(40, f"{h}.Tamano"),
                                        "Input": I(link="Luces")}, pos=(-330, -33)),
             merge("ConCerca", "Entrada", "HaloCerca", (-275, 0), "Screen", blend=0.5, blend_expr=f"{h}.Intensidad*0.6"),
             merge("ConLejos", "ConCerca", "HaloLejos", (-220, 0), "Screen", blend=0.8, blend_expr=f"{h}.Intensidad")]
    t, last = blk_grain("Gr", "ConLejos", f"{h}.Grano", -165, scale=60)
    tools += t
    ucs = [uc("Intensidad", "Intensidad", 0.8, 0, 2), uc("Tamano", "Tamaño del halo", 40, 2, 200),
           uc("Umbral", "Umbral (más bajo = más brillo)", 0.45, 0, 1), uc("Grano", "Grano", 0.12, 0, 1)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Intensidad": I(0.8), "Tamano": I(40), "Umbral": I(0.45),
                                                "Grano": I(0.12)}, ucs, (-55, 0)))
    pubs = [pub(h, "Intensidad", "Intensidad", 0.8), pub(h, "Tamano", "Tamaño del halo", 40),
            pub(h, "Umbral", "Umbral (más bajo = más brillo)", 0.45), pub(h, "Grano", "Grano", 0.12)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_Pendulo")
def din_pendulo(name, anim):
    """Movimiento flotante de pendulo: el plano se balancea colgado de un punto, con un vaiven suave de posicion.
    Con Giro = 0 queda solo el flote (recomendado en caras para que no se deforme)."""
    h = "Pendulo"
    w = f"(time*2*{PI}/{h}.Periodo)"
    ucs = [uc("Fuerza", "Fuerza del flote", 1, 0, 5), uc("Giro", "Giro (grados)", 1.5, 0, 15),
           uc("Periodo", "Fotogramas por vaivén", 90, 10, 600), uc("Zoom", "Zoom (tapa los bordes)", 1.06, 1, 1.5)]
    tools = [Tool(h, "Transform", {
        "Pivot": I((0.5, 1)),
        "Angle": I(0, f"{h}.Giro*sin({w})"),
        "Center": I((0.5, 0.5), f"Point(0.5 + {h}.Fuerza*0.008*sin({w} + 0.6), 0.5 + {h}.Fuerza*0.01*sin(2*{w} + 1.3))"),
        "Size": I(1.06, f"{h}.Zoom + {h}.Fuerza*0.006*sin({w}*0.5)"),
        "Fuerza": I(1), "Giro": I(1.5), "Periodo": I(90), "Zoom": I(1.06)}, ucs, (0, 0))]
    pubs = [pub(h, "Fuerza", "Fuerza del flote", 1), pub(h, "Giro", "Giro (grados)", 1.5),
            pub(h, "Periodo", "Fotogramas por vaivén", 90), pub(h, "Zoom", "Zoom (tapa los bordes)", 1.06),
            pub(h, "Pivot", "Punto del que cuelga")]
    return macro(name, [(h, "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Din_ZoomDestello")
def din_zoom_destello(name, anim):
    """Entrada con zoom y destello: el clip entra desde mas cerca, desenfocado y con un flash que se apaga.
    Con 'Salida' > 0 tambien sale con zoom y flash. Es la entrada que se repite en cada corte de un clip viral."""
    h = "ZoomDestello"
    ucs, env = envelope_ucs(h, 0.1, 0)
    ucs[3:3] = [uc("Zoom", "Zoom inicial", 0.3, 0, 2), uc("Destello", "Destello", 0.8, 0, 1), uc("Desenfoque", "Desenfoque", 12, 0, 80)]
    k = f"(1 - {h}.Env)"
    tools = [Tool("Acerca", "Transform", {"Size": I(1, f"1 + {h}.Zoom*{k}"), "Center": I((0.5, 0.5))}, pos=(-165, 0)),
             Tool("Suaviza", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, f"{h}.Desenfoque*{k}"),
                                      "Input": I(link="Acerca")}, pos=(-110, 0)),
             solid("Flash", (1, 1, 1), (-55, -66)),
             merge("ConFlash", "Suaviza", "Flash", (-55, 0), "Screen", blend=0, blend_expr=f"{h}.Destello*{k}*{k}"),
             Tool(h, "BrightnessContrast", {"Input": I(link="ConFlash"), "Progreso": I(link=anim, out="Value"),
                                            "Zoom": I(0.3), "Destello": I(0.8), "Desenfoque": I(12), **env}, ucs, (0, 0))]
    pubs = numbered([pub(h, "Zoom", "Zoom inicial", 0.3), pub(h, "Destello", "Destello", 0.8), pub(h, "Desenfoque", "Desenfoque", 12),
                     pub_color("Flash", "Color del destello", (1, 1, 1), "c1"), pub("Acerca", "Center", "Centro del zoom"),
                     pub(h, "Entrada", "Duración entrada (% del clip)", 0.1),
                     pub(h, "Salida", "Duración salida (% del clip, 0 = sin salida)", 0)])
    return macro(name, [("Acerca", "Input")], pubs, h, tools, anim)


@register("Effects", "PRO_FX_Retro_1998")
def retro_1998(name, anim):
    """Look de video casero de finales de los 90: negros levantados, color calido y algo apagado, halo en las luces,
    leve sangrado de color, grano y vineta."""
    h = "Retro1998"
    tools = [Tool("Entrada", "PipeRouter", pos=(-660, 0))]
    t, last = blk_tone("Tn", "Entrada", -605, contrast=-0.12, lift=0.05, sat=0.8)
    tools += t
    t, last = blk_cast("Cl", last, -550, (1, 0.9, 0.75), 0.6)
    tools += t
    t, last = blk_channel_shift("Sep", last, "0.0015", "0", -440)
    tools += t
    t, last = blk_bloom("Bl", last, -165, low=0.5, radius=30, blend=0.5)
    tools += t
    t, last = blk_grain("Gr", last, f"{h}.Grano", 55, scale=50)
    tools += t
    t, last = blk_vignette("Vin", last, 165, amount=0.4)
    tools += t
    ucs = [uc("Grano", "Grano", 0.2, 0, 1)]
    tools.append(merge(h, "Entrada", last, (275, 0), blend=1, ucs=ucs, extra={"Grano": I(0.2)}))
    pubs = [pub(h, "Blend", "Intensidad", 1), pub("BlBloom", "Blend", "Brillo", 0.5), pub("ClDominante", "Blend", "Calidez", 0.6),
            pub("TnTono", "Saturation", "Saturación", 0.8), pub(h, "Grano", "Grano", 0.2), pub("VinVineta", "Blend", "Viñeta", 0.4)]
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Effects", "PRO_FX_Social_TV")
def social_tv(name, anim):
    """El clip se ve dentro de un televisor antiguo en una habitacion oscura, con lineas de barrido, brillo de pantalla
    y opcion de blanco y negro. Marca 'Formato vertical' en timelines 9:16."""
    h = "TV"
    v = f"{h}.Vertical"
    asp = f"iif({v} > 0.5, 0.5625, 1.7778)"
    s = f"({h}.Tamano*iif({v} > 0.5, 1.6, 1))"
    cy = "0.5"

    def box(n, pos, dx, dy, w, ht, rgb, radius=0.0, angle=None, inv=False):
        kw = {"Center": I((0.5, 0.5), f"Point(0.5 + ({dx})*{s}, {cy} + ({dy})*{s}*{asp})"), "Width": I(0.1, f"({w})*{s}"),
              "Height": I(0.1, f"({ht})*{s}*{asp}"), "CornerRadius": I(radius)}
        if angle is not None:
            kw["Angle"] = I(angle)
        return [rect(f"M{n}", (pos[0], pos[1] - 33), **kw), solid(n, rgb, pos, mask=f"M{n}")]

    sw, sh, sx = 0.40, 0.30, -0.045   # pantalla (unidades del ancho, relativas al centro)
    tools = [Tool("Entrada", "PipeRouter", pos=(-550, 132)),
             solid("Pared", (0.06, 0.055, 0.07), (-550, 0))]
    t, last = blk_vignette("Vin", "Pared", -495, amount=0.6)
    tools += t
    parts = [("AntenaI", (-0.06, 0.25, 0.006, 0.16, -25)), ("AntenaD", (0.06, 0.25, 0.006, 0.16, 25)),
             ("PataI", (-0.2, -0.235, 0.03, 0.05, 10)), ("PataD", (0.2, -0.235, 0.03, 0.05, -10))]
    for i, (n, (dx, dy, w, ht, ang)) in enumerate(parts):
        tools += box(n, (-440 + 44 * i, -198), dx, dy, w, ht, (0.08, 0.08, 0.08), angle=ang)
    tools += box("Mueble", (-264, -198), 0, 0, 0.56, 0.44, (0.32, 0.2, 0.12), radius=0.12)
    tools += box("Marco", (-220, -198), sx, 0, sw + 0.03, sh + 0.03, (0.05, 0.05, 0.05), radius=0.2)
    for i, dy in enumerate((0.09, 0.0)):
        tools += box(f"Perilla{i + 1}", (-176 + 44 * i, -198), 0.21, dy, 0.045, 0.045, (0.85, 0.75, 0.55), radius=1)
    tools += box("Rejilla", (-88, -198), 0.21, -0.11, 0.07, 0.08, (0.2, 0.12, 0.07), radius=0.2)
    for n in ("AntenaD", "PataI", "PataD"):
        color_from(tool_named(tools, n), "AntenaI")
    color_from(tool_named(tools, "Perilla2"), "Perilla1")
    t, last = chain("Capa", last, [(n, None) for n in ("AntenaI", "AntenaD", "PataI", "PataD", "Mueble", "Marco",
                                                        "Perilla1", "Perilla2", "Rejilla")], -440, -99)
    tools += t
    # el clip, escalado para cubrir la pantalla, con barrido y brillo de tubo
    tools += [Tool("Color", "BrightnessContrast", {"Input": I(link="Entrada"), "Saturation": I(1, f"1 - {h}.BN"),
                                                   "Contrast": I(0.1)}, pos=(-495, 132)),
              Tool("EnPantalla", "Transform", {"Input": I(link="Color"),
                                               "Center": I((0.5, 0.5), f"Point(0.5 + ({sx})*{s}, {cy})"),
                                               "Size": I(0.53, f"max({sw}, {sh}*{asp})*{s}")}, pos=(-440, 132))]
    t, img = scanlines("Barrido", "EnPantalla", h, -385, high=0.6)
    tools += t
    t, img = blk_bloom("Tubo", img, -275, low=0.55, radius=20, blend=0.4)
    tools += t
    tools += [rect("MPantalla", (-55, 66), Center=I((0.5, 0.5), f"Point(0.5 + ({sx})*{s}, {cy})"), Width=I(0.4, f"{sw}*{s}"),
                   Height=I(0.53, f"{sh}*{s}*{asp}"), CornerRadius=I(0.25), SoftEdge=I(0.002)),
              merge("ConImagen", last, img, (0, 0), extra={"EffectMask": I(link="MPantalla", out="Mask")}),
              ellipse("MReflejo", (55, 66), Center=I((0.5, 0.5), f"Point(0.5 + ({sx - 0.09})*{s}, {cy} + 0.08*{s}*{asp})"),
                      Width=I(0.1, f"0.16*{s}"), Height=I(0.1, f"0.06*{s}*{asp}"), SoftEdge=I(0.04), Angle=I(20)),
              solid("Reflejo", (1, 1, 1), (55, 33), mask="MReflejo"),
              merge("ConReflejo", "ConImagen", "Reflejo", (55, 0), "Screen", blend=0.12),
              Tool("Resplandor", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(60), "Input": I(link="ConReflejo")},
                   pos=(110, -66)),
              merge("ConResplandor", "ConReflejo", "Resplandor", (110, 0), "Screen", blend=0.25)]
    ucs = [uc("Vertical", "Formato vertical (9:16)", 0, 0, 1, checkbox=True), uc("Tamano", "Tamaño del televisor", 1, 0.3, 2),
           uc("BN", "Blanco y negro", 0, 0, 1), uc("Lineas", "Líneas de barrido", 0.3, 0, 1),
           uc("NumLineas", "Número de líneas", 220, 50, 1000)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="ConResplandor"), "Vertical": I(0), "Tamano": I(1), "BN": I(0),
                                                "Lineas": I(0.3), "NumLineas": I(220)}, ucs, (165, 0)))
    pubs = numbered([pub(h, "Vertical", "Formato vertical (9:16)", 0), pub(h, "Tamano", "Tamaño del televisor", 1),
                     pub(h, "BN", "Blanco y negro", 0), pub(h, "Lineas", "Líneas de barrido", 0.3),
                     pub(h, "NumLineas", "Número de líneas", 220), pub("TuboBloom", "Blend", "Brillo de la pantalla", 0.4),
                     pub("ConResplandor", "Blend", "Resplandor en la habitación", 0.25),
                     pub_color("Mueble", "Color del mueble", (0.32, 0.2, 0.12), "c1"),
                     pub_color("Pared", "Color de la pared", (0.06, 0.055, 0.07), "c2")])
    return macro(name, [("Entrada", "Input")], pubs, h, tools)


@register("Generators", "PRO_GEN_FondoGrano")
def gen_fondo_grano(name, anim):
    """Fondo oscuro con textura, luz suave que se desplaza y mucho grano: el fondo que se pone detras de la persona
    recortada en los clips de podcast."""
    h = "FondoGrano"
    w = f"(time*0.01*{h}.Velocidad)"
    tools = [solid("Base", (0.05, 0.045, 0.04), (-440, 0)),
             Tool("Nubes", "FastNoise", {**frame_format(), "Detail": I(3), "Contrast": I(1.2), "XScale": I(2.5),
                                         "SeetheRate": I(0, f"0.01*{h}.Velocidad")}, pos=(-385, -66)),
             merge("ConTextura", "Base", "Nubes", (-385, 0), "Overlay", blend=0.35, blend_expr=f"{h}.Textura"),
             ellipse("MLuz", (-330, -99), Center=I((0.5, 0.55), f"Point(0.5 + 0.15*sin({w}), 0.55 + 0.08*sin(1.7*{w} + 1))"),
                     Width=I(0.8), Height=I(0.8), SoftEdge=I(0.5)),
             solid("Luz", (0.55, 0.42, 0.3), (-330, -66), mask="MLuz"),
             merge("ConLuz", "ConTextura", "Luz", (-330, 0), "Screen", blend=0.35, blend_expr=f"{h}.Luz")]
    t, last = blk_grain("Gr", "ConLuz", f"{h}.Grano", -275, scale=70)
    tools += t
    t, last = blk_vignette("Vin", last, -165, amount=0.5)
    tools += t
    ucs = [uc("Grano", "Grano", 0.35, 0, 1), uc("Textura", "Textura", 0.35, 0, 1), uc("Luz", "Luz", 0.35, 0, 1),
           uc("Velocidad", "Velocidad", 1, 0, 5)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link=last), "Grano": I(0.35), "Textura": I(0.35), "Luz": I(0.35),
                                                "Velocidad": I(1)}, ucs, (-55, 0)))
    pubs = numbered([pub_color("Base", "Color del fondo", (0.05, 0.045, 0.04), "c1"), pub_color("Luz", "Color de la luz", (0.55, 0.42, 0.3), "c2"),
                     pub(h, "Luz", "Luz", 0.35), pub(h, "Textura", "Textura", 0.35), pub(h, "Grano", "Grano", 0.35),
                     pub(h, "Velocidad", "Velocidad", 1), pub("VinVineta", "Blend", "Viñeta", 0.5)])
    return macro(name, [], pubs, h, tools)


@register("Transitions", "PRO_TR_ZoomDestello")
def tr_zoom_destello(name, anim):
    """A se acerca de golpe, un destello blanco tapa el corte y B llega desde mas cerca (con desenfoque)."""
    h = "Mezcla"
    p = f"{h}.Progreso"
    a, b = f"min(1, 2*{p})", f"(1 - max(0, 2*{p} - 1))"
    bell = f"pow(sin({p}*{PI}), 6)"
    blur = f"{h}.Desenfoque*sin({p}*{PI})*sin({p}*{PI})"
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Zoom", "Zoom", 0.6, 0, 3), uc("Desenfoque", "Desenfoque", 25, 0, 100),
           uc("Destello", "Destello", 1, 0, 1)]
    tools = [Tool("ZoomSaliente", "Transform", {"Size": I(1, f"1 + {h}.Zoom*pow({a}, 3)")}, pos=(-275, -33)),
             Tool("ZoomEntrante", "Transform", {"Size": I(1, f"1 + {h}.Zoom*pow({b}, 3)")}, pos=(-275, 33)),
             Tool("Corte", "Dissolve", {"Mix": I(0, f"iif({p} < 0.5, 0, 1)"), "Background": I(link="ZoomSaliente"),
                                        "Foreground": I(link="ZoomEntrante")}, pos=(-220, 0)),
             Tool("Movimiento", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(0, blur), "Input": I(link="Corte")},
                  pos=(-165, 0)),
             solid("Flash", (1, 1, 1), (-110, -66)),
             merge(h, "Movimiento", "Flash", (-110, 0), "Screen", blend=0, blend_expr=f"{h}.Destello*{bell}", ucs=ucs,
                   extra={"Progreso": I(link=anim, out="Value"), "Zoom": I(0.6), "Desenfoque": I(25), "Destello": I(1)})]
    pubs = numbered([pub(h, "Zoom", "Zoom", 0.6), pub(h, "Desenfoque", "Desenfoque", 25), pub(h, "Destello", "Destello", 1),
                     pub_color("Flash", "Color del destello", (1, 1, 1), "c1")])
    return macro(name, [("ZoomSaliente", "Input"), ("ZoomEntrante", "Input")], pubs, h, tools, anim)


@register("Transitions", "PRO_TR_Balanceo")
def tr_balanceo(name, anim):
    """A se descuelga balanceandose hacia un lado y B entra balanceandose desde el otro, como un pendulo."""
    h = "Balanceo"
    p = f"{h}.Progreso"
    a, b = f"min(1, 2*{p})", f"(1 - max(0, 2*{p} - 1))"
    blur = f"{h}.Desenfoque*sin({p}*{PI})"
    tools = []
    for n_, k, sg, y in (("GiroA", a, "-1", -33), ("GiroB", b, "1", 33)):
        tools.append(Tool(n_, "Transform", {"Pivot": I((0.5, 1.2)), "Angle": I(0, f"{sg}*{h}.Giro*{k}*{k}"),
                                            "Size": I(1, f"1 + 0.25*{k}")}, pos=(-275, y)))
    tools += [Tool("Cambio", "Dissolve", {"Mix": I(0, smooth(clamp01(f"({p} - 0.45)/0.1"))), "Background": I(link="GiroA"),
                                          "Foreground": I(link="GiroB")}, pos=(-220, 0)),
              Tool("Arrastre", "DirectionalBlur", {"Length": I(0, f"{blur}*0.002"), "Angle": I(0), "ClippingMode": I(FuID("None")),
                                                   "Input": I(link="Cambio")}, pos=(-165, 0))]
    ucs = [uc("Progreso", "Progreso", 0, 0, 1), uc("Giro", "Giro (grados)", 25, 0, 90), uc("Desenfoque", "Desenfoque", 30, 0, 100)]
    tools.append(Tool(h, "BrightnessContrast", {"Input": I(link="Arrastre"), "Progreso": I(link=anim, out="Value"), "Giro": I(25),
                                                "Desenfoque": I(30)}, ucs, (-110, 0)))
    pubs = [pub(h, "Giro", "Giro (grados)", 25), pub(h, "Desenfoque", "Desenfoque", 30)]
    return macro(name, [("GiroA", "Input"), ("GiroB", "Input")], pubs, h, tools, anim)


def soft_shadow(opacity=0.25, offset=(0.003, -0.008), blur=6):
    """Sombra suave de los textos virales (opacidad baja, muy desenfocada, algo de distancia)."""
    d = shade(soft=((0, 0, 0), offset, blur))
    d["Alpha8"] = I(opacity)
    return d


def inter(name, text, style, size, pos, rgb=(1, 1, 1), center=(0.5, 0.5), **extra):
    return text_tool(name, text, size, center, pos, rgb, INTER, style, extra={**soft_shadow(), **extra})


def vpivot(h, cy):
    """Pivote a la altura de un texto, con el mismo mapeo a vertical que vertical_map() aplica a su centro."""
    return I((0.5, cy), f"Point(0.5, 0.5 + ({cy:g} - 0.5)*iif({h}.Vertical > 0.5, {K_VERT}, 1))")


@register("Titles", "PRO_TTL_Podcast_Frase")
def podcast_frase(name, anim_):
    """Frase de clip de podcast: Inter en mayusculas, sombra suave, sube un poco mientras aparece y la palabra clave en
    amarillo con brillo. Es el texto que acompana lo que dice la persona."""
    h = "Frase"
    ucs, inputs = kit(h, 0.15, 0.08, [uc("Glow", "Brillo", 0.6, 0, 2), uc("TamHalo", "Tamaño del brillo", 25, 2, 100)],
                      {"Glow": I(0.6), "TamHalo": I(25)})
    e1, e2 = phase(h, 0, 0.6), phase(h, 0.35, 1)
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0),
            inter("Linea1", "ESTAMOS EN UNA", "ExtraBold", 0.06, (-385, -198), center=(0.5, 0.56)),
            inter("Linea2", "SOCIEDAD", "Black", 0.1, (-330, -198), rgb=(1, 0.85, 0.15), center=(0.5, 0.46)),
            mover("Sube1", "Linea1", (-385, -132), cy=f"0.5 - 0.012*(1 - {e1})"),
            mover("Sube2", "Linea2", (-330, -132), cy=f"0.5 - 0.012*(1 - {e2})"),
            Tool("Halo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(25, f"{h}.TamHalo"), "Input": I(link="Sube2")},
                 pos=(-275, -132))]
    layers = [("Sube1", f"{e1}*{h}.Xs"), ("Halo", f"{h}.Glow*{e2}*{h}.Xs"), ("Sube2", f"{e2}*{h}.Xs")]
    pubs = [pub("Linea1", "StyledText", "Frase"), pub("Linea2", "StyledText", "Palabra clave"),
            *text_pubs("Linea1", " de la frase", 0.06, (1, 1, 1), 1), *text_pubs("Linea2", " de la palabra clave", 0.1, (1, 0.85, 0.15), 2),
            pub(h, "Glow", "Brillo", 0.6), pub(h, "TamHalo", "Tamaño del brillo", 25),
            pub("Linea1", "Alpha8", "Opacidad de la sombra", 0.25)]
    body[2].inputs["Alpha8"] = I(0.25, "Linea1.Alpha8")
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=1.7, dy_v=-0.05)


@register("Titles", "PRO_TTL_Podcast_Subtitulo")
def podcast_subtitulo(name, anim_):
    """Subtitulos palabra a palabra: escribe la frase y cada palabra sale sola, en mayusculas, con un pequeno rebote.
    Las palabras se reparten en toda la duracion del clip; 'Palabra destacada' pinta una (1 = la primera) de otro color."""
    h = "Subtitulo"
    src = "Fuente.StyledText.Value"
    count = f'string.len((string.gsub((string.gsub({src}, "%S+", "x")), "%s+", "")))'
    ucs, inputs = kit(h, 0.02, 0, [uc("Rebote", "Rebote", 1, 0, 3), uc("Destacada", "Palabra destacada (0 = ninguna)", 0, 0, 50, integer=True),
                                   uc("Mayus", "Mayúsculas", 1, 0, 1, checkbox=True), uc("Glow", "Brillo", 0.5, 0, 2),
                                   uc("N", "Palabras", 1, 1, 200, clamp=False), uc("Idx", "Palabra actual", 0, 0, 200, clamp=False),
                                   uc("Fr", "Avance de la palabra", 0, 0, 1, clamp=False)],
                      {"Rebote": I(1), "Destacada": I(0), "Mayus": I(1), "Glow": I(0.5),
                       "N": I(1, f"max(1, {count})"),
                       "Idx": I(0, f"min({h}.N - 1, floor({h}.Progreso*{h}.N))"),
                       "Fr": I(0, f"min(1, {h}.Progreso*{h}.N - {h}.Idx)")})
    # Idx < N, asi que la palabra siempre existe (salvo con la frase vacia)
    word = f'string.match({src}, string.rep("%S+%s+", {h}.Idx) .. "(%S+)")'
    shown = f"iif({h}.Mayus > 0.5, string.upper({word}), {word})"
    hit = f"{h}.Idx + 1 == {h}.Destacada"   # Destacada = 0 nunca coincide
    color = {f"{ch}1": I(1, f"iif({hit}, ColorClave.TopLeft{ch}, ColorBase.TopLeft{ch})") for ch in ("Red", "Green", "Blue")}
    bounce = f"(1 + 0.18*{h}.Rebote*pow(max(0, 1 - 5*{h}.Fr), 2))"
    body = [text_tool("Fuente", "ESTO ES LO QUE NADIE TE CUENTA", 0.06, (0.5, 0.5), (-385, -264)),
            solid("ColorBase", (1, 1, 1), (-330, -264)), solid("ColorClave", (1, 0.85, 0.15), (-275, -264)),
            inter("Palabra", "", "ExtraBold", 0.08, (-385, -198), center=(0.5, 0.3),
                  StyledText=I("", f"Text({shown})"), **color, **shade(outline=((0, 0, 0), 0.04))),
            mover("Rebota", "Palabra", (-385, -132), size=bounce),
            Tool("Halo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(25), "Input": I(link="Rebota")}, pos=(-330, -132))]
    layers = [("Halo", f"{h}.Glow*{h}.Xs"), ("Rebota", f"{h}.Xs")]
    pubs = [pub("Fuente", "StyledText", "Frase completa"), pub("Palabra", "Font", "Fuente", group="f1"), pub("Palabra", "Style", group="f1"),
            pub("Palabra", "Size", "Tamaño", 0.08), pub_color("ColorBase", "Color del texto", (1, 1, 1), "c1"),
            pub_color("ColorClave", "Color de la palabra destacada", (1, 0.85, 0.15), "c2"),
            pub(h, "Destacada", "Palabra destacada (0 = ninguna)", 0), pub(h, "Mayus", "Mayúsculas", 1),
            *outline_pubs("Palabra", 1, (0, 0, 0), 0.04), pub(h, "Rebote", "Rebote", 1), pub(h, "Glow", "Brillo", 0.5),
            pub("Halo", "XBlurSize", "Tamaño del brillo", 25)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=1.6, dy_v=0.05)


@register("Titles", "PRO_TTL_Texto_Giro")
def texto_giro(name, anim_):
    """Texto en bucle con giro: la frase se mece girando a un lado y otro y respira un poco, sin parar."""
    h = "Giro"
    w = f"(time*2*{PI}/{h}.Periodo)"
    ucs, inputs = kit(h, 0.12, 0.08, [uc("Angulo", "Giro (grados)", 4, 0, 30), uc("Periodo", "Fotogramas por vaivén", 50, 8, 300),
                                      uc("Respira", "Respiración", 1, 0, 3), uc("Rebote", "Rebote", 1.2, 0, 3)],
                      {"Angulo": I(4), "Periodo": I(50), "Respira": I(1), "Rebote": I(1.2)})
    body = [inter("Texto1", "NO TE VAN A", "ExtraBold", 0.06, (-385, -198), center=(0.5, 0.55)),
            inter("Texto2", "ABRIR PASO", "Black", 0.09, (-330, -198), rgb=(1, 0.85, 0.15), center=(0.5, 0.45)),
            mover("Mece1", "Texto1", (-385, -132), size=f"max(0, {pop(h, 0, 0.6)})*(1 + 0.02*{h}.Respira*sin(2*{w}))",
                  angle=f"{h}.Angulo*sin({w})"),
            mover("Mece2", "Texto2", (-330, -132), size=f"max(0, {pop(h, 0.3, 1)})*(1 + 0.02*{h}.Respira*sin(2*{w} + 1))",
                  angle=f"-{h}.Angulo*sin({w} + 0.8)")]
    for i, c in ((1, 0.55), (2, 0.45)):
        tool_named(body, f"Mece{i}").inputs["Pivot"] = vpivot(h, c)
    layers = [("Mece1", f"{h}.Xs*min(1, 4*{h}.U)"), ("Mece2", f"{h}.Xs*{phase(h, 0.3, 0.5)}")]
    pubs = [pub("Texto1", "StyledText", "Línea 1"), pub("Texto2", "StyledText", "Línea 2"),
            *text_pubs("Texto1", " de la línea 1", 0.06, (1, 1, 1), 1), *text_pubs("Texto2", " de la línea 2", 0.09, (1, 0.85, 0.15), 2),
            pub(h, "Angulo", "Giro (grados)", 4), pub(h, "Periodo", "Fotogramas por vaivén", 50), pub(h, "Respira", "Respiración", 1)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=1.7)


@register("Titles", "PRO_TTL_Texto_Contorno")
def texto_contorno(name, anim_):
    """Palabra gigante con ecos de contorno que se abren detras. Pensada para ir DETRAS de la persona: recorta a la persona
    con Magic Mask en una pista superior y deja este titulo debajo."""
    h = "Contorno"
    ucs, inputs = kit(h, 0.25, 0.1, [uc("Separacion", "Separación de los ecos", 0.08, 0, 0.4), uc("Pulso", "Pulso", 1, 0, 3),
                                     uc("Rebote", "Rebote", 1.2, 0, 3)],
                      {"Separacion": I(0.08), "Pulso": I(1), "Rebote": I(1.2)})
    grow = phase(h, 0.2, 1)
    pulse = f"(1 + 0.03*{h}.Pulso*sin(time*0.2))"
    body = [inter("Relleno", "CAOS", "Black", 0.3, (-385, -198), **soft_shadow(0.4))]
    for i in (1, 2, 3):
        # los ecos copian el texto y el tamano de la palabra (el tamano ya lleva el mapeo a vertical)
        t = text_tool(f"Eco{i}", "CAOS", 0.3, (0.5, 0.5), (-330 + 55 * (i - 1), -198), (1, 1, 1), INTER, "Black",
                      extra={**shade(outline=((1, 1, 1), 0.012)), "Enabled1": I(0),
                             "StyledText": I("CAOS", "Text(Relleno.StyledText.Value)"),
                             "Size": I(0.3, f"{h}.TamRelleno*iif({h}.Vertical > 0.5, {K_VERT}, 1)")})
        if i > 1:
            t.inputs.update({f"{ch}2": I(1, f"Eco1.{ch}2") for ch in ("Red", "Green", "Blue")})
            t.inputs["Thickness2"] = I(0.012, "Eco1.Thickness2")
        body.append(t)
        body.append(mover(f"Abre{i}", f"Eco{i}", (-330 + 55 * (i - 1), -132),
                          size=f"(1 + {i}*{h}.Separacion*{grow})*{pulse}"))
    body.append(mover("Golpe", "Relleno", (-440, -132), size=f"max(0, {pop(h, 0, 0.4)})"))
    layers = [(f"Abre{i}", f"{h}.Xs*{grow}*{1 - 0.25 * (i - 1):g}") for i in (3, 2, 1)] + [("Golpe", f"{h}.Xs*min(1, 4*{h}.U)")]
    # sin selector de fuente: los ecos usan la misma fuente fija que la palabra
    pubs = [pub("Relleno", "StyledText", "Palabra"), pub("Relleno", "Size", "Tamaño", 0.3),
            pub_color("Relleno", "Color de la palabra", (1, 1, 1), "c1", prefix="", suffix="1"),
            *outline_pubs("Eco1", 2, (1, 1, 1), 0.012), pub(h, "Separacion", "Separación de los ecos", 0.08), pub(h, "Pulso", "Pulso", 1)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=1.8)


@register("Titles", "PRO_TTL_Icono_Llama")
def icono_llama(name, anim_):
    """Llama animada que titila, con brillo naranja y texto opcional (para 'hoguera', 'en llamas', 'tendencia')."""
    h = "Llama"
    asp = icon_asp(h)
    ucs, inputs = kit(h, 0.15, 0.08, [uc("Titileo", "Titileo", 1, 0, 3), uc("Glow", "Brillo", 0.8, 0, 2), uc("Rebote", "Rebote", 1.5, 0, 3)],
                      {"Titileo": I(1), "Glow": I(0.8), "Rebote": I(1.5)})
    orange, yellow = (1, 0.42, 0.08), (1, 0.85, 0.3)
    body = [solid("Base", (0, 0, 0), (-440, -264), alpha=0)]
    body += shape("Bola", h, (-385, -198), 0, 0, 0.06, 0.06, orange, radius=1)
    body += triangle("Punta", h, (-330, -198), [(-0.0278, 0.01125), (0.0278, 0.01125), (0, 0.08)], orange)
    body += shape("BolaInt", h, (-275, -198), 0, -0.008, 0.034, 0.034, yellow, radius=1)
    body += triangle("PuntaInt", h, (-220, -198), [(-0.0163, -0.003), (0.0163, -0.003), (0, 0.042)], yellow)
    color_from(tool_named(body, "Punta"), "Bola")
    color_from(tool_named(body, "PuntaInt"), "BolaInt")
    t, ext = chain("Exterior", "Base", [("Bola", None), ("Punta", None)], -385, -132)
    body += t
    t, inn = chain("Interior", "Base", [("BolaInt", None), ("PuntaInt", None)], -275, -132)
    body += t
    flick = f"{h}.Titileo*sin(time*0.9)*sin(time*1.7 + 1)"
    for n, src, k in (("FlamaExt", ext, 1), ("FlamaInt", inn, 1.6)):
        body.append(Tool(n, "Transform", {"Input": I(link=src), "Pivot": I((0.5, 0.5), ipt(h, 0, -0.03)),
                                          "Aspect": I(1, f"1 - {k}*0.06*{flick}"), "Angle": I(0, f"{k}*3*{h}.Titileo*sin(time*0.6 + {k})")},
                         pos=(-220 + 55 * (k > 1), -99)))
    t, flame = chain("Fuego", "Base", [("FlamaExt", None), ("FlamaInt", None)], -165, -99)
    body += t
    body += [mover("Aparece", flame, (-110, -99), size=f"max(0, {pop(h, 0, 0.6)})"),
             Tool("Halo", "Blur", {"Filter": I(FuID("Fast Gaussian")), "XBlurSize": I(30), "Input": I(link="Aparece")}, pos=(-55, -99)),
             icon_label("Etiqueta", "EN LLAMAS", 0.035, h, -0.06, (-110, -264))]
    layers = [("Halo", f"{h}.Glow*(0.8 + 0.2*sin(time*1.3))*{h}.Xs*min(1, 3*{h}.U)"), ("Aparece", f"{h}.Xs*min(1, 3*{h}.U)"),
              ("Etiqueta", stage(h, 0.5, 1))]
    pubs = [pub_color("Bola", "Color exterior", orange, "c1"), pub_color("BolaInt", "Color interior", yellow, "c2"),
            pub("Etiqueta", "StyledText", "Texto"), pub(h, "Titileo", "Titileo", 1), pub(h, "Glow", "Brillo", 0.8),
            pub("Halo", "XBlurSize", "Tamaño del brillo", 30)]
    return style_title(name, h, ucs, inputs, body, layers, pubs, size_v=2.5)


if __name__ == "__main__":
    for (cat, name), fn in BUILT.items():
        anim = "PRO" + name.split("_", 2)[-1].replace("_", "") + "Anim"
        out = ROOT / cat / f"{name}.setting"
        out.write_text(fn(name, anim), encoding="utf-8", newline="\n")
        print(f"{cat}/{out.name}")
