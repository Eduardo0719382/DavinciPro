"""
Validador del Resolve Pro Pack.

Comprueba, sin abrir Resolve:
  - .setting: sintaxis de tabla Lua (subconjunto que usa Fusion), estructura de macro,
    entradas/salidas segun la categoria (Transitions/Titles/Effects/Generators),
    que cada SourceOp y cada referencia en expresiones apunte a una herramienta existente.
  - .cube: encabezado LUT_3D_SIZE, numero exacto de filas, valores numericos en dominio.
  - .dctl: que exista la funcion transform y que las llaves esten balanceadas.

Uso:  python tools/validate.py            (desde la raiz del paquete)
Sale con codigo 1 si hay errores.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------- parser Lua (subconjunto)
class ParseError(Exception):
    pass


TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<comment>--[^\n]*)
  | (?P<number>-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?)
  | (?P<string>"(?:[^"\\]|\\.)*")
  | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<punct>[{}\[\]=,;()])
""", re.VERBOSE)


def tokenize(text):
    pos, out = 0, []
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            line = text.count("\n", 0, pos) + 1
            raise ParseError(f"caracter inesperado {text[pos]!r} en linea {line}")
        kind = m.lastgroup
        if kind not in ("ws", "comment"):
            out.append((kind, m.group(kind), text.count("\n", 0, pos) + 1))
        pos = m.end()
    return out


class Call:
    """Constructor Fusion: Nombre { ... } o ordered() { ... }"""
    def __init__(self, name, table):
        self.name, self.table = name, table

    def __repr__(self):
        return f"{self.name}{{...}}"


class Parser:
    def __init__(self, tokens):
        self.t, self.i = tokens, 0

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else ("eof", "", -1)

    def take(self, value=None):
        tok = self.peek()
        if value is not None and tok[1] != value:
            raise ParseError(f"se esperaba {value!r} y llego {tok[1]!r} (linea {tok[2]})")
        self.i += 1
        return tok

    def value(self):
        kind, val, line = self.peek()
        if kind == "number":
            self.take()
            return float(val)
        if kind == "string":
            self.take()
            return bytes(val[1:-1], "utf-8").decode("unicode_escape") if "\\" in val else val[1:-1]
        if kind == "ident":
            self.take()
            if val in ("true", "false"):
                return val == "true"
            if val == "nil":
                return None
            if self.peek()[1] == "(":
                self.take("(")
                self.take(")")
            if self.peek()[1] == "{":
                return Call(val, self.table())
            raise ParseError(f"identificador suelto {val!r} en linea {line}")
        if val == "{":
            return self.table()
        raise ParseError(f"valor inesperado {val!r} en linea {line}")

    def table(self):
        self.take("{")
        d, n = {}, 0
        while self.peek()[1] != "}":
            kind, val, line = self.peek()
            if kind == "ident" and self.peek(1)[1] == "=":
                self.take()
                self.take("=")
                key = val
            elif val == "[":
                self.take("[")
                k = self.take()
                if k[0] == "string":
                    key = k[1][1:-1]
                elif k[0] == "number":
                    key = float(k[1])
                else:
                    raise ParseError(f"clave invalida en linea {k[2]}")
                self.take("]")
                self.take("=")
            else:
                n += 1
                key = n
            if key in d:
                raise ParseError(f"clave duplicada {key!r} en linea {line}")
            d[key] = self.value()
            if self.peek()[1] in (",", ";"):
                self.take()
            elif self.peek()[1] != "}":
                raise ParseError(f"falta ',' en linea {self.peek()[2]}")
        self.take("}")
        return d


def parse_setting(text):
    p = Parser(tokenize(text))
    root = p.value()
    if p.peek()[0] != "eof":
        raise ParseError(f"contenido sobrante tras la tabla raiz (linea {p.peek()[2]})")
    return root


# ----------------------------------------------------------------- comprobaciones .setting
EXPECTED_MAIN_INPUTS = {"Transitions": 2, "Effects": 1, "Titles": 0, "Generators": 0}
EXPR_FUNCS = {"min", "max", "sin", "cos", "abs", "Point", "iif", "floor", "ceil",
              "sqrt", "pow", "time", "comp", "self", "Text"}


def tables(obj):
    return obj.table if isinstance(obj, Call) else obj


def check_setting(path, errors, warnings):
    category = path.parent.name
    try:
        root = parse_setting(path.read_text(encoding="utf-8"))
    except ParseError as e:
        errors.append(f"{path.name}: sintaxis: {e}")
        return
    top = tables(root.get("Tools"))
    if not isinstance(top, dict):
        errors.append(f"{path.name}: falta Tools en la raiz")
        return
    macros = {k: v for k, v in top.items()
              if isinstance(v, Call) and v.name in ("MacroOperator", "GroupOperator")}
    if len(macros) != 1:
        errors.append(f"{path.name}: debe haber exactamente 1 MacroOperator/GroupOperator")
        return
    mname, macro = next(iter(macros.items()))
    if root.get("ActiveTool") != mname:
        errors.append(f"{path.name}: ActiveTool deberia ser {mname!r}")
    if mname != path.stem:
        warnings.append(f"{path.name}: el nombre interno {mname!r} no coincide con el archivo")
    m = macro.table
    inner = tables(m.get("Tools", {}))
    all_tools = {**{k: v for k, v in top.items() if k != mname}, **inner}

    # entradas publicadas
    mains = 0
    for key, inst in tables(m.get("Inputs", {})).items():
        it = tables(inst)
        src = it.get("SourceOp")
        if src not in inner:
            errors.append(f"{path.name}: {key} apunta a SourceOp inexistente {src!r}")
            continue
        if str(key).startswith("MainInput"):
            mains += 1
    exp = EXPECTED_MAIN_INPUTS.get(category)
    if exp is None:
        errors.append(f"{path.name}: carpeta {category!r} no es una categoria de Edit")
    elif mains != exp:
        errors.append(f"{path.name}: {category} requiere {exp} MainInput y tiene {mains}")

    outs = tables(m.get("Outputs", {}))
    if "MainOutput1" not in outs:
        errors.append(f"{path.name}: falta MainOutput1")
    elif tables(outs["MainOutput1"]).get("SourceOp") not in inner:
        errors.append(f"{path.name}: MainOutput1 apunta a una herramienta inexistente")

    # conexiones y expresiones dentro de cada herramienta
    for tname, tool in all_tools.items():
        if not isinstance(tool, Call):
            continue
        t = tool.table
        for iname, inp in tables(t.get("Inputs", {})).items():
            if not (isinstance(inp, Call) and inp.name == "Input"):
                continue
            it = inp.table
            if "SourceOp" in it and it["SourceOp"] not in all_tools:
                errors.append(f"{path.name}: {tname}.{iname} conecta a {it['SourceOp']!r}, que no existe")
            expr = it.get("Expression")
            if expr:
                if expr.count("(") != expr.count(")"):
                    errors.append(f"{path.name}: {tname}.{iname}: parentesis desbalanceados en expresion")
                for ref_tool, ref_inp in re.findall(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)", expr):
                    if ref_tool in ("comp", "self", "string", "math"):
                        continue
                    if ref_tool not in all_tools:
                        errors.append(f"{path.name}: {tname}.{iname}: expresion usa {ref_tool!r}, que no existe")
                        continue
                    rt = all_tools[ref_tool].table
                    known = set(tables(rt.get("Inputs", {})).keys()) | set(tables(rt.get("UserControls", {})).keys())
                    if ref_inp not in known:
                        warnings.append(f"{path.name}: {tname}.{iname}: {ref_tool}.{ref_inp} no esta declarado")
                # los textos entre comillas (p. ej. formatos de string.format) no son identificadores
                bare = re.sub(r'"[^"]*"|\'[^\']*\'', "", expr)
                for ident in re.findall(r"(?<![.\w])([A-Za-z_]\w*)\b(?!\s*\.)", bare):
                    if ident not in EXPR_FUNCS and ident not in all_tools:
                        errors.append(f"{path.name}: {tname}.{iname}: identificador desconocido {ident!r}")


# ----------------------------------------------------------------- comprobaciones .cube
def check_cube(path, errors, warnings):
    size, rows, title = None, 0, False
    for n, raw in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("TITLE"):
            title = True
            continue
        if line.startswith("LUT_3D_SIZE"):
            size = int(line.split()[1])
            continue
        if line.startswith(("DOMAIN_MIN", "DOMAIN_MAX", "LUT_1D_SIZE")):
            continue
        parts = line.split()
        if len(parts) != 3:
            errors.append(f"{path.name}: linea {n} no tiene 3 valores")
            return
        vals = [float(v) for v in parts]
        if any(v < 0 or v > 1 for v in vals):
            errors.append(f"{path.name}: linea {n} fuera de [0,1]")
            return
        rows += 1
    if size is None:
        errors.append(f"{path.name}: falta LUT_3D_SIZE")
    elif rows != size ** 3:
        errors.append(f"{path.name}: {rows} filas, se esperaban {size ** 3}")
    if not title:
        warnings.append(f"{path.name}: sin TITLE")


# ----------------------------------------------------------------- comprobaciones .dctl
def check_dctl(path, errors, warnings):
    src = path.read_text(encoding="utf-8")
    if "__DEVICE__ float3 transform(" not in src:
        errors.append(f"{path.name}: falta la funcion transform")
    if src.count("{") != src.count("}") or src.count("(") != src.count(")"):
        errors.append(f"{path.name}: llaves o parentesis desbalanceados")


def main():
    errors, warnings, counts = [], [], {}
    for pattern, fn in (("*.setting", check_setting), ("*.cube", check_cube), ("*.dctl", check_dctl)):
        for p in sorted(ROOT.rglob(pattern)):
            if "tools" in p.parts:
                continue
            fn(p, errors, warnings)
            counts[pattern] = counts.get(pattern, 0) + 1
    for name in (p.name for p in ROOT.rglob("*") if p.is_file() and p.suffix in (".setting", ".cube", ".dctl")):
        if not name.startswith("PRO_"):
            errors.append(f"{name}: falta el prefijo PRO_")
    print("Archivos revisados:", ", ".join(f"{k} = {v}" for k, v in counts.items()) or "ninguno")
    for w in warnings:
        print("  AVISO:", w)
    for e in errors:
        print("  ERROR:", e)
    print("RESULTADO:", "FALLO" if errors else "OK", f"({len(errors)} errores, {len(warnings)} avisos)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
