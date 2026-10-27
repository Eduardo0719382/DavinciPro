"""
Mini-libreria para escribir macros de Fusion (.setting) desde Python.

Sigue la misma estructura que las plantillas oficiales de Blackmagic
(Developer/Fusion Templates): MacroOperator + InstanceInput/InstanceOutput,
modificador LUTLookup (Anim Curves) al nivel raiz para la animacion.
"""


class FuID:
    def __init__(self, v):
        self.v = v


class Raw:
    """Valor Lua literal (p. ej. Gradient { Colors = {...} })."""
    def __init__(self, s):
        self.s = s


def gradient(stops):
    """stops: lista de (posicion, (r, g, b, a))."""
    body = ", ".join(f"[{p:g}] = {{ {', '.join(f'{c:g}' for c in col)} }}" for p, col in stops)
    return Raw(f"Gradient {{ Colors = {{ {body} }} }}")


def val(v):
    if isinstance(v, Raw):
        return v.s
    if isinstance(v, FuID):
        return f'FuID {{ "{v.v}" }}'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, (tuple, list)):
        return "{ " + ", ".join(val(x) for x in v) + " }"
    if isinstance(v, int):
        return str(v)
    return f"{v:.6g}"


def I(value=None, expr=None, link=None, out="Output"):
    """Una entrada de herramienta: valor fijo, expresion y/o conexion."""
    parts = []
    if link:
        parts += [f'SourceOp = "{link}"', f'Source = "{out}"']
    if value is not None:
        parts.append(f"Value = {val(value)}")
    if expr:
        parts.append(f"Expression = {val(expr)}")
    return "Input { " + ", ".join(parts) + ", }"


def frame_format():
    """Imagen generada con la resolucion de la timeline."""
    return {
        "Width": I(1920),
        "Height": I(1080),
        "UseFrameFormatSettings": I(1),
        '["Gamut.SLogVersion"]': I(FuID("SLog2")),
    }


def mask_format():
    return {
        "Filter": I(FuID("Fast Gaussian")),
        "OutputSize": I(FuID("Custom")),
        "MaskWidth": I(1920),
        "MaskHeight": I(1080),
        "PixelAspect": I((1, 1)),
        "UseFrameFormatSettings": I(1),
        "ClippingMode": I(FuID("None")),
    }


def uc(name, label, default, lo, hi, integer=False, checkbox=False, clamp=True):
    """Control de usuario (UserControls) de tipo deslizador o casilla."""
    lines = [f'LINKS_Name = {val(label)}', 'LINKID_DataType = "Number"']
    if checkbox:
        lines += ['INPID_InputControl = "CheckboxControl"', "INP_Integer = true", "CBC_TriState = false"]
    else:
        lines.append('INPID_InputControl = "SliderControl"')
        if integer:
            lines.append("INP_Integer = true")
    lines += [f"INP_Default = {val(default)}", f"INP_MinScale = {val(lo)}", f"INP_MaxScale = {val(hi)}"]
    if clamp:
        lines += [f"INP_MinAllowed = {val(lo)}", f"INP_MaxAllowed = {val(hi)}"]
    lines.append('ICS_ControlPage = "Controls"')
    return name, lines


class Tool:
    def __init__(self, name, kind, inputs=None, ucs=None, pos=(0, 0)):
        self.name, self.kind = name, kind
        self.inputs = inputs or {}
        self.ucs = ucs or []
        self.pos = pos

    def render(self, ind):
        t = "\t" * ind
        out = [f"{t}{self.name} = {self.kind} {{", f"{t}\tCtrlWShown = false,"]
        if self.inputs:
            out.append(f"{t}\tInputs = {{")
            for k, v in self.inputs.items():
                out.append(f"{t}\t\t{k} = {v},")
            out.append(f"{t}\t}},")
        info = "PipeRouterInfo" if self.kind == "PipeRouter" else "OperatorInfo"
        out.append(f"{t}\tViewInfo = {info} {{ Pos = {{ {self.pos[0]}, {self.pos[1]} }} }},")
        if self.ucs:
            out.append(f"{t}\tUserControls = ordered() {{")
            for name, lines in self.ucs:
                out.append(f"{t}\t\t{name} = {{")
                out += [f"{t}\t\t\t{l}," for l in lines]
                out.append(f"{t}\t\t}},")
            out.append(f"{t}\t}},")
        out.append(f"{t}}},")
        return "\n".join(out)


def pub(tool, source, name=None, default=None, group=None):
    return {"tool": tool, "source": source, "name": name, "default": default, "group": group}


def pub_color(tool, label, rgb, group, prefix="TopLeft", suffix=""):
    """Publica un color (R, G, B) como un unico selector en el Inspector."""
    return [pub(tool, f"{prefix}{ch}{suffix}", label if i == 0 else None, rgb[i], group)
            for i, ch in enumerate(("Red", "Green", "Blue"))]


def macro(name, mains, published, output, tools, anim=None):
    """
    mains: lista de (tool, source) para MainInput1, MainInput2...
    published: lista de pub() (o listas de pub()) que se ven en el Inspector.
    anim: nombre del modificador LUTLookup (progreso 0..1) o None.
    """
    flat = []
    for p in published:
        flat += p if isinstance(p, list) else [p]
    L = ["{", "\tTools = ordered() {", f"\t\t{name} = MacroOperator {{", "\t\t\tCtrlWZoom = false,",
         "\t\t\tInputs = ordered() {"]
    for i, (tool, src) in enumerate(mains, 1):
        L.append(f'\t\t\t\tMainInput{i} = InstanceInput {{ SourceOp = "{tool}", Source = "{src}", }},')
    for i, p in enumerate(flat, 1):
        parts = [f'SourceOp = "{p["tool"]}"', f'Source = "{p["source"]}"']
        if p["name"]:
            parts.append(f"Name = {val(p['name'])}")
        if p["group"] is not None:
            parts.append(f"ControlGroup = {p['group']}")
        if p["default"] is not None:
            parts.append(f"Default = {val(p['default'])}")
        L.append(f"\t\t\t\tInput{i} = InstanceInput {{ " + ", ".join(parts) + ", },")
    L += ["\t\t\t},",
          "\t\t\tOutputs = {",
          f'\t\t\t\tMainOutput1 = InstanceOutput {{ SourceOp = "{output}", Source = "Output", }},',
          "\t\t\t},",
          "\t\t\tViewInfo = GroupInfo { Pos = { 0, 0 } },",
          "\t\t\tTools = ordered() {"]
    L += [t.render(4) for t in tools]
    L += ["\t\t\t},", "\t\t},"]
    if anim:
        L += [f"\t\t{anim} = LUTLookup {{", "\t\t\tInputs = {", "\t\t\t},", "\t\t\tCtrlWZoom = false,", "\t\t},"]
    L += ["\t},", f'\tActiveTool = "{name}"', "}", ""]
    return "\n".join(L)


# ----------------------------------------------------------------- ayudas para expresiones
PI = "3.14159265"


def smooth(x):
    return f"({x})*({x})*(3-2*({x}))"


def clamp01(x):
    return f"max(0, min(1, {x}))"


def envelope_ucs(host, entrada, salida):
    """Controles Progreso/Entrada/Salida/Raw/Env para animaciones de entrada-salida en % del clip."""
    raw = clamp01(f"min({host}.Progreso/max({host}.Entrada, 0.0001), (1-{host}.Progreso)/max({host}.Salida, 0.0001))")
    ucs = [uc("Progreso", "Progreso", 0, 0, 1),
           uc("Entrada", "Duración entrada (% del clip)", entrada, 0, 1),
           uc("Salida", "Duración salida (% del clip, 0 = sin salida)", salida, 0, 1),
           uc("Raw", "Envolvente lineal", 1, 0, 1, clamp=False),
           uc("Env", "Envolvente suave", 1, 0, 1, clamp=False)]
    inputs = {"Entrada": I(entrada), "Salida": I(salida),
              "Raw": I(1, raw), "Env": I(1, smooth(f"{host}.Raw"))}
    return ucs, inputs
