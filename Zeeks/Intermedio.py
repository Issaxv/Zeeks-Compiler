#Lenguajes y Autómatas II. Generador de codigo intermedio (Cuadruplos).
#TECNM. ITCG. Ing. en Sistemas Computacionales. 7mo semestre
#26-11-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

# La librerías necesarias
from copy import deepcopy
import re

# ==================================================
# Clases auxiliares
# ==================================================
class Cuadruplo:
    def __init__(self, op, arg1=None, arg2=None, res=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.res = res

    def __repr__(self):
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.res})"


class TempManager:
    def __init__(self, prefix="t"):
        self.prefix = prefix
        self.count = 0

    def nuevo(self):
        self.count += 1
        return f"{self.prefix}{self.count}"

    def reiniciar(self):
        self.count = 0


class EtiquetaManager:
    def __init__(self, prefix="L"):
        self.prefix = prefix
        self.count = 0

    def nuevo(self):
        self.count += 1
        return f"{self.prefix}{self.count}"

    def reiniciar(self):
        self.count = 0


# ==================================================
# Inicialización de estructuras y estados
# ==================================================
temp_mgr = TempManager()
etiqueta_mgr = EtiquetaManager()
cuadruplos = []

funcion_actual = None
funcion_tiene_return = False

funcion_return_temp = {}

break_stack = []
continue_stack = []

break_switch_stack = []

tabla_simbolos_global = None

# ==================================================
# Funciones auxiliares
# ==================================================
def emitir(op, arg1=None, arg2=None, res=None):
    q = Cuadruplo(op, arg1, arg2, res)
    cuadruplos.append(q)
    return q


def imprimir():
    for i, q in enumerate(cuadruplos):
        print(f"{i:03}: {q}")


def limpiar():
    global cuadruplos, funcion_actual, funcion_tiene_return, tabla_simbolos_global, funcion_return_temp
    cuadruplos.clear()
    funcion_actual = None
    funcion_tiene_return = False
    temp_mgr.reiniciar()
    etiqueta_mgr.reiniciar()
    tabla_simbolos_global = None
    funcion_return_temp = {}
    break_stack.clear()
    continue_stack.clear()
    break_switch_stack.clear()


def exportar_as_list():
    return [(q.op, q.arg1, q.arg2, q.res) for q in cuadruplos]


def valor_por_defecto(tipo):
    if tipo is None:
        return None
    if tipo == 'int':
        return 0
    if tipo == 'float':
        return 0.0
    if tipo == 'bool':
        return False
    if tipo == 'char':
        return '\0'
    if tipo == 'string':
        return ""
    if isinstance(tipo, str) and tipo.endswith('[]'):
        return []
    return None


def construir_array_por_defecto(tipo_base, tam_array):
    def valor_simple(t):
        if t == 'int':
            return 0
        if t == 'float':
            return 0.0
        if t == 'bool':
            return False
        if t == 'char':
            return '\0'
        if t == 'string':
            return ""
        return None

    if not tam_array:
        return valor_simple(tipo_base)

    return [deepcopy(valor_simple(tipo_base)) for _ in range(tam_array)]


def _tipo_desde_nodo(nodo):
    try:
        if hasattr(nodo, 'attrs') and isinstance(nodo.attrs, dict):
            return nodo.attrs.get('tipo_inferido')
    except Exception:
        pass

    return None


def _tipo_desde_valor(valor):
    if isinstance(valor, bool):
        return 'bool'
    if isinstance(valor, int):
        return 'int'
    if isinstance(valor, float):
        return 'float'
    if isinstance(valor, str):
        return 'string'
    if isinstance(valor, list):
        return 'array'
    return None


def _obtener_tipo_operandos(nodo_op, valor_izq, valor_der):
    izq_node = nodo_op.hijos[0]
    der_node = nodo_op.hijos[1]

    tipo_izq = _tipo_desde_nodo(izq_node) or _tipo_desde_valor(valor_izq)
    tipo_der = _tipo_desde_nodo(der_node) or _tipo_desde_valor(valor_der)

    return tipo_izq, tipo_der


# ---------------- Helpers de interpolación ----------------
_re_split_interp = re.compile(r'(\{[^}]+\})')

def _parse_interpol_expr(expr):
    """
    Parse simple expressions inside { }:
      - "name"
      - "name[index]" where index can be a number or an identifier
    Returns a tuple (kind, data) where kind in {'ident', 'array', 'literal'}
    """
    expr = expr.strip()
    if '[' in expr and expr.endswith(']'):
        name, idx = expr.split('[', 1)
        idx = idx[:-1].strip()
        if idx.isdigit():
            return ('array_const_index', (name.strip(), int(idx)))
        else:
            return ('array_expr_index', (name.strip(), idx))  # idx is identifier name
    else:
        return ('ident', expr)


def _interpolar_cadena_literal(lit_str):
    """
    Dado un string literal (sin comillas externas),
    si tiene {expr} realiza la generación de CI para concatenarlo.
    Devuelve temp que contiene el string ya concatenado (o el literal si no requiere concatenación).
    """
    # Si no hay llaves -> devolvemos la literal tal cual (retornamos la literal string,
    # el código consumidor puede usarlo directamente como argumento)
    if '{' not in lit_str:
        # devolvemos la literal (se usa directamente en STRCAT/PARAM)
        return lit_str

    parts = _re_split_interp.split(lit_str)
    current_temp = None

    for part in parts:
        if not part:
            continue
        if part.startswith('{') and part.endswith('}'):
            inner = part[1:-1].strip()
            kind, data = _parse_interpol_expr(inner)

            if kind == 'ident':
                name = data
                # cargar variable (identificador) — en nuestro IR las variables se refieren por nombre
                # convertir a string si hace falta
                tmp_val = temp_mgr.nuevo()
                # TO_STRING acepta como arg una variable/temporal o literal
                emitir('TO_STRING', name, None, tmp_val)
                part_temp = tmp_val

            elif kind == 'array_const_index':
                name, idx = data
                tmp_idx = idx  # índice inmediato
                tmp_val = temp_mgr.nuevo()
                emitir('ARR_LOAD', name, tmp_idx, tmp_val)
                # convertir a string
                tmp_str = temp_mgr.nuevo()
                emitir('TO_STRING', tmp_val, None, tmp_str)
                part_temp = tmp_str

            elif kind == 'array_expr_index':
                name, idx_ident = data
                # index is variable name
                tmp_idx = temp_mgr.nuevo()
                # cargar índice variable into tmp_idx (COPY)
                emitir('COPY', idx_ident, None, tmp_idx)
                tmp_val = temp_mgr.nuevo()
                emitir('ARR_LOAD', name, tmp_idx, tmp_val)
                tmp_str = temp_mgr.nuevo()
                emitir('TO_STRING', tmp_val, None, tmp_str)
                part_temp = tmp_str
            else:
                # fallback: treat as literal
                part_temp = part
        else:
            # literal segment - use directly (string literal)
            part_temp = part

        # concatena `current_temp` con `part_temp`
        if current_temp is None:
            # si part_temp es literal, lo guardamos tal cual como "current"
            if isinstance(part_temp, str) and '{' not in part_temp and not part_temp.startswith('_TMP_'):
                # no crear temp si es sólo literal; lo devolvemos como literal por ahora
                current_temp = part_temp
            else:
                # part_temp is a temp name
                current_temp = part_temp
        else:
            # aseguremos que ambos sean temps o literales válidos para STRCAT
            tmp_res = temp_mgr.nuevo()
            emitir('STRCAT', current_temp, part_temp, tmp_res)
            current_temp = tmp_res

    # current_temp ahora contiene la cadena final (temp o literal)
    return current_temp


# ==================================================
# PROCESAR NODOS PRINCIPALES
# ==================================================
def procesar_Programa(nodo):
    for hijo in nodo.hijos:
        if hijo.tipo == "Import":
            generar(hijo)

    for hijo in nodo.hijos:
        if hijo.tipo in ["DeclaracionVariable", "Constante", "AsignacionVariable"]:
            generar(hijo)

    tmp = temp_mgr.nuevo()
    emitir("CALL", "main", 0, tmp)
    emitir("HALT", None, None, None)

    for hijo in nodo.hijos:
        if hijo.tipo == "Funcion":
            generar(hijo)

    return None


def procesar_Import(nodo):
    # TODO: Agregar el funcionamiento de los imports
    return None


def procesar_DeclaracionVariable(nodo):
    tipo_decl = None
    tam = None
    tipo_base = None

    if nodo.hijos and nodo.hijos[0].tipo in ('Tipo', 'TipoArray'):
        if nodo.hijos[0].tipo == 'Tipo':
            tipo_decl = nodo.hijos[0].valor
        else:
            tipo_decl = f"{nodo.hijos[0].valor}[]"

            if nodo.hijos[0].hijos:
                tam_n = nodo.hijos[0].hijos[0]
                if tam_n and tam_n.tipo == 'TamanoArray':
                    tam = tam_n.valor

        if isinstance(tipo_decl, str) and tipo_decl.endswith('[]'):
            tipo_base = tipo_decl[:-2]

    for hijo in nodo.hijos[1:]:
        if hijo.tipo == 'Identificador':
            name = hijo.valor
            default = None

            if tipo_base and tam is not None:
                default_list = construir_array_por_defecto(tipo_base, tam)
                emitir('=', deepcopy(default_list), None, name)
            else:
                default = valor_por_defecto(tipo_decl)
                if default is not None:
                    emitir('=', default, None, name)

        elif hijo.tipo == 'AsignacionInicial':
            procesar_AsignacionInicial(hijo)

        else:
            generar(hijo)

    return None


def procesar_Constante(nodo):
    # si la constante es una cadena y contiene interpolación -> generarla
    val = nodo.valor
    if isinstance(val, str):
        # quitar comillas externas si existiesen
        s = val
        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
            s = s[1:-1]

        # Si hay interpolación
        if '{' in s and '}' in s:
            res = _interpolar_cadena_literal(s)
            # si devuelve temp (string computed), retornarlo
            return res
        else:
            # devolver la literal original (con comillas) para que se use directamente
            # Mantengo el formato con comillas para compatibilidad con el resto del IR
            return f'"{s}"'

    # booleanos y numeros se devuelven tal cual
    return nodo.valor


def procesar_ConstanteBooleana(nodo):
    if isinstance(nodo.valor, bool):
        return nodo.valor
    if isinstance(nodo.valor, str):
        return nodo.valor.lower() == 'true'
    return bool(nodo.valor)


def procesar_Identificador(nodo):
    return nodo.valor


# ---------------- Operaciones ----------------
def procesar_OperacionBinaria(nodo):
    izq_val = generar(nodo.hijos[0])
    der_val = generar(nodo.hijos[1])

    tipo_izq, tipo_der = _obtener_tipo_operandos(nodo, izq_val, der_val)

    op = nodo.valor

    # Concatenación
    if op == '+' and (tipo_izq in ('string', 'char') or tipo_der in ('string', 'char')):
        if tipo_izq == 'char':
            tmp_izq = temp_mgr.nuevo()
            emitir('CHAR2STR', izq_val, None, tmp_izq)
            izq_val = tmp_izq
        if tipo_der == 'char':
            tmp_der = temp_mgr.nuevo()
            emitir('CHAR2STR', der_val, None, tmp_der)
            der_val = tmp_der

        res_tmp = temp_mgr.nuevo()
        emitir('STRCAT', izq_val, der_val, res_tmp)
        return res_tmp

    # Operaciones numéricas y comparaciones: manejar conversión int->float
    numeric_ops = ['+', '-', '*', '/', '%', '<', '>', '<=', '>=', '==', '!=']
    if op in numeric_ops:
        if tipo_izq == 'int' and tipo_der == 'float':
            nueva_izq = temp_mgr.nuevo()
            emitir('ITOF', izq_val, None, nueva_izq)
            izq_val = nueva_izq
            tipo_izq = 'float'
        elif tipo_izq == 'float' and tipo_der == 'int':
            nueva_der = temp_mgr.nuevo()
            emitir('ITOF', der_val, None, nueva_der)
            der_val = nueva_der 
            tipo_der = 'float'

        res_tmp = temp_mgr.nuevo()
        emitir(op, izq_val, der_val, res_tmp)
        return res_tmp

    res_tmp = temp_mgr.nuevo()
    emitir(op, izq_val, der_val, res_tmp)
    return res_tmp


def procesar_OperacionUnaria(nodo):
    val = generar(nodo.hijos[0])
    tmp = temp_mgr.nuevo()
    emitir(nodo.valor, val, None, tmp)
    return tmp


# ---------------- Array literal y acceso ----------------
def procesar_ArrayLiteral(nodo):
    elems = nodo.hijos or []
    vals = [generar(e) for e in elems]
    arr_temp = temp_mgr.nuevo()

    emitir('ARRAY_LITERAL', vals, len(vals), arr_temp)
    return arr_temp

def procesar_ArrayAccess(nodo):
    nombre = nodo.valor
    indice = generar(nodo.hijos[0]) if nodo.hijos else None

    tmp = temp_mgr.nuevo()
    emitir('ARR_LOAD', nombre, indice, tmp)
    return tmp


# ---------------- Asignaciones ----------------
def procesar_AsignacionVariable(nodo):
    lvalue = nodo.hijos[0]
    expr = nodo.hijos[1]

    if lvalue.tipo == 'Identificador':
        nombre = lvalue.valor
        val = generar(expr)
        emitir('=', val, None, nombre)
        return nombre

    if lvalue.tipo == 'ArrayAccess':
        nombre = lvalue.valor
        indice = generar(lvalue.hijos[0])
        val = generar(expr)
        emitir('ARR_STORE', nombre, indice, val)
        return None

    target = generar(lvalue)
    val = generar(expr)
    emitir('=', val, None, target)
    return target

def procesar_AsignacionInicial(nodo):
    nombre = nodo.valor
    val = generar(nodo.hijos[0]) if nodo.hijos else None
    emitir('=', val, None, nombre)
    return nombre

def procesar_AsignacionNoPC(nodo):
    return procesar_AsignacionVariable(nodo)

def procesar_InicializacionFor(nodo):
    for init in nodo.hijos:
        generar(init)
    return None


# ---------------- Post inc/dec ----------------
def procesar_PostIncDec(nodo):
    ident = nodo.hijos[0]
    nombre = ident.valor

    # Semántica postfix: guardamos el valor previo en un temp y luego actualizamos la variable.
    tmp = temp_mgr.nuevo()
    # usamos COPY para dejar claro que es copia previa
    emitir('COPY', nombre, None, tmp)

    if nodo.valor == '++':
        emitir('+', nombre, 1, nombre)
    else:
        emitir('-', nombre, 1, nombre)

    return tmp


# ---------------- Instrucciones simples ----------------
def procesar_InstruccionSimple(nodo):
    if not nodo.valor:
        return None

    v = str(nodo.valor).lower()
    if v == 'pass':
        return None

    if v == 'continue':
        if continue_stack:
            emitir('GOTO', None, None, continue_stack[-1])
        else:
            emitir('CONTINUE', None, None, None)
        return None

    if v == 'break':
        if break_stack:
            emitir('GOTO', None, None, break_stack[-1])
        elif break_switch_stack:
            emitir('GOTO', None, None, break_switch_stack[-1])
        else:
            emitir('BREAK', None, None, None)
        return None

    return None


# ---------------- RETURN ----------------
def procesar_Return(nodo):
    global funcion_tiene_return, funcion_actual

    funcion_tiene_return = True

    ret_temp = None
    if funcion_actual and funcion_actual in funcion_return_temp:
        ret_temp = funcion_return_temp[funcion_actual]
    else:
        ret_temp = temp_mgr.nuevo()
        if funcion_actual:
            funcion_return_temp[funcion_actual] = ret_temp

    if nodo.hijos and nodo.hijos[0] is not None:
        val = generar(nodo.hijos[0])
        emitir('=', val, None, ret_temp)

    else:
        emitir('=', None, None, ret_temp)

    if funcion_actual:
        emitir('GOTO', None, None, f"func_end_{funcion_actual}")

    else:
        emitir('RET', ret_temp, None, None)

    return '_RETURN_'


# ---------------- LLAMADAS A FUNCION ----------------
def procesar_LlamadaFuncion(nodo):
    nombre = nodo.valor
    args = nodo.hijos or []
    arg_temps = []

    for a in args:
        t = generar(a)
        arg_temps.append(t)
        emitir('PARAM', t, None, None)

    res_temp = temp_mgr.nuevo()
    emitir('CALL', nombre, len(arg_temps), res_temp)
    return res_temp


# ---------------- CONTROL DE FLUJO: IF / ELIF / ELSE ----------------
def procesar_If(nodo):
    cond = nodo.hijos[0]
    cuerpo_if = nodo.hijos[1]

    rest = nodo.hijos[2:]
    elifs = []
    else_node = None

    for item in rest:
        if item.tipo == 'Elif':
            elifs.append(item)
        elif item.tipo == 'Else':
            else_node = item

    end_label = etiqueta_mgr.nuevo()

    tcond = generar(cond)
    false_label = etiqueta_mgr.nuevo()
    emitir('IF_FALSE', tcond, None, false_label)

    generar(cuerpo_if)
    emitir('GOTO', None, None, end_label)

    current_false = false_label

    for e in elifs:
        emitir('LABEL', None, None, current_false)
        econd = e.hijos[0]
        ecuerpo = e.hijos[1]
        tcond_e = generar(econd)
        next_false = etiqueta_mgr.nuevo()

        emitir('IF_FALSE', tcond_e, None, next_false)
        generar(ecuerpo)
        emitir('GOTO', None, None, end_label)

        current_false = next_false

    emitir('LABEL', None, None, current_false)

    if else_node:
        generar(else_node.hijos[0])

    emitir('LABEL', None, None, end_label)
    return None


# ---------------- WHILE / UNTIL / DOWHILE ----------------
def procesar_While(nodo):
    cond_label = etiqueta_mgr.nuevo()
    body_label = etiqueta_mgr.nuevo()
    end = etiqueta_mgr.nuevo()

    break_stack.append(end)
    continue_stack.append(cond_label)

    emitir('LABEL', None, None, cond_label)
    tcond = generar(nodo.hijos[0])
    emitir('IF_FALSE', tcond, None, end)

    emitir('LABEL', None, None, body_label)
    generar(nodo.hijos[1])

    emitir('GOTO', None, None, cond_label)

    emitir('LABEL', None, None, end)

    break_stack.pop()
    continue_stack.pop()

def procesar_Until(nodo):
    start = etiqueta_mgr.nuevo()
    cond_label = etiqueta_mgr.nuevo()
    end = etiqueta_mgr.nuevo()

    break_stack.append(end)
    continue_stack.append(cond_label)

    emitir('LABEL', None, None, start)
    generar(nodo.hijos[1])

    emitir('LABEL', None, None, cond_label)
    tcond = generar(nodo.hijos[0])

    emitir('IF', tcond, None, end)
    emitir('GOTO', None, None, start)

    emitir('LABEL', None, None, end)

    break_stack.pop()
    continue_stack.pop()

def procesar_DoWhile(nodo):
    start = etiqueta_mgr.nuevo()
    cond_label = etiqueta_mgr.nuevo()
    end = etiqueta_mgr.nuevo()

    break_stack.append(end)
    continue_stack.append(cond_label)

    emitir('LABEL', None, None, start)
    generar(nodo.hijos[1])

    emitir('LABEL', None, None, cond_label)
    tcond = generar(nodo.hijos[0])
    emitir('IF', tcond, None, start)

    break_stack.pop()
    continue_stack.pop()

    return None


# ---------------- FOR / FOREACH ----------------
def procesar_For(nodo):
    init_nodes = []
    cond_node = None
    update_node = None
    cuerpo = None

    for h in nodo.hijos:
        if h.tipo == 'InicializacionFor' or h.tipo == 'AsignacionNoPC':
            init_nodes.append(h)
        elif h.tipo == 'CondicionFor':
            cond_node = h
        elif h.tipo == 'ActualizacionFor':
            update_node = h
        elif h.tipo == 'Cuerpo':
            cuerpo = h

    for ini in init_nodes:
        generar(ini)

    start = etiqueta_mgr.nuevo()
    end = etiqueta_mgr.nuevo()
    update_label = etiqueta_mgr.nuevo()

    break_stack.append(end)
    continue_stack.append(update_label)

    emitir('LABEL', None, None, start)

    if cond_node and cond_node.hijos:
        tcond = generar(cond_node.hijos[0])
        emitir('IF_FALSE', tcond, None, end)

    if cuerpo:
        generar(cuerpo)

    emitir('LABEL', None, None, update_label)

    if update_node and update_node.hijos:
        generar(update_node.hijos[0])

    emitir('GOTO', None, None, start)
    emitir('LABEL', None, None, end)

    break_stack.pop()
    continue_stack.pop()

    return None

def procesar_ForEach(nodo):
    tipo_var = nodo.hijos[0].valor
    iter_name = nodo.hijos[1].valor
    coleccion = nodo.hijos[2]
    cuerpo = nodo.hijos[3]

    idx = temp_mgr.nuevo()
    emitir('=', 0, None, idx)

    coll_temp = generar(coleccion)

    length_temp = temp_mgr.nuevo()
    emitir('ARRAY_LEN', coll_temp, None, length_temp)

    start = etiqueta_mgr.nuevo()
    end = etiqueta_mgr.nuevo()
    update_label = etiqueta_mgr.nuevo()

    break_stack.append(end)
    continue_stack.append(update_label)

    emitir('LABEL', None, None, start)

    cond_tmp = temp_mgr.nuevo()
    emitir('<', idx, length_temp, cond_tmp)
    emitir('IF_FALSE', cond_tmp, None, end)

    elem_tmp = temp_mgr.nuevo()
    emitir('ARR_LOAD', coll_temp, idx, elem_tmp)

    emitir('=', elem_tmp, None, iter_name)

    generar(cuerpo)

    emitir('LABEL', None, None, update_label)
    emitir('+', idx, 1, idx)
    emitir('GOTO', None, None, start)

    emitir('LABEL', None, None, end)

    break_stack.pop()
    continue_stack.pop()

    return None


# ---------------- SWITCH / CASE ----------------
def procesar_Switch(nodo):
    expr_tmp = generar(nodo.hijos[0])
    cases = nodo.hijos[1:]

    end_label = etiqueta_mgr.nuevo()
    case_labels = []
    default_label = None

    for c in cases:
        case_labels.append(etiqueta_mgr.nuevo())

    break_switch_stack.append(end_label)

    i = 0
    for c in cases:
        if c.tipo == 'Case':
            case_val = generar(c.hijos[0])
            cond_tmp = temp_mgr.nuevo()
            emitir('==', expr_tmp, case_val, cond_tmp)
            emitir('IF_FALSE', cond_tmp, None, case_labels[i])
        elif c.tipo == 'Default':
            default_label = case_labels[i]
        i += 1

    i = 0
    for c in cases:
        emitir('LABEL', None, None, case_labels[i])

        if c.tipo == 'Case':
            generar(c.hijos[1])
            emitir('GOTO', None, None, end_label)

        elif c.tipo == 'Default':
            generar(c.hijos[0])
            emitir('GOTO', None, None, end_label)

        i += 1

    emitir('LABEL', None, None, end_label)

    break_switch_stack.pop()

    return None


# ---------------- Funciones ----------------
def procesar_Funcion(nodo):
    global funcion_tiene_return, funcion_actual, funcion_return_temp

    nombre = nodo.valor
    tipo_retorno = None

    for h in nodo.hijos:
        if h.tipo == 'Tipo':
            tipo_retorno = h.valor

    funcion_actual = nombre
    funcion_tiene_return = False

    ret_temp = temp_mgr.nuevo()
    funcion_return_temp[nombre] = ret_temp

    emitir('FUNC', nombre, None, None)
    emitir('LABEL', None, None, f"func_start_{nombre}")

    if tabla_simbolos_global:
        simbolo_func = tabla_simbolos_global.buscar_funcion(nombre)
        if simbolo_func:
            params = simbolo_func.attrs.get('parametros', [])

            for idx, (pname, ptype) in enumerate(params):
                emitir('POP_PARAM', idx, None, pname)

    for h in nodo.hijos:
        generar(h)

    if not funcion_tiene_return:
        if tipo_retorno not in (None, 'void'):
            default_val = None
            if isinstance(tipo_retorno, str) and tipo_retorno.endswith('[]'):
                default_val = []
            else:
                default_val = valor_por_defecto(tipo_retorno)
            emitir('=', default_val, None, ret_temp)
        else:
            pass

    emitir('LABEL', None, None, f"func_end_{nombre}")

    if tipo_retorno not in (None, 'void'):
        emitir('RET', ret_temp, None, None)
    else:
        emitir('RET', None, None, None)

    emitir('END_FUNC', nombre, None, None)

    funcion_actual = None
    funcion_tiene_return = False

    return None


def procesar_Tipo(nodo):
    # actualmente no es necesario para generación IR, pero se deja para futuras extensiones
    return None


def procesar_Parametro(nodo):
    # parámetros ya son manejados por procesar_Funcion/tabla de símbolos (POP_PARAM)
    return None


def procesar_Cuerpo(nodo):
    for instruccion in nodo.hijos:
        generar(instruccion)


# ---------------- dispatch ----------------
def generar(nodo):
    if nodo is None:
        return None

    tipo = getattr(nodo, 'tipo', nodo.__class__.__name__)
    metodo = globals().get(f"procesar_{tipo}")

    if metodo is None:
        print(f"[ADVERTENCIA] No implementado: procesar_{tipo}\nNodo linea: {getattr(nodo, 'linea', '?')}")
        return None

    return metodo(nodo)

def generar_codigo_intermedio(arbol, tabla_simbolos=None):
    limpiar()
    global tabla_simbolos_global

    tabla_simbolos_global = tabla_simbolos
    procesar_Programa(arbol)

    return cuadruplos

if __name__ == '__main__':
    print("Generador de CI cargado correctamente.")
