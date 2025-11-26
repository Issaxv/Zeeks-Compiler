#Lenguajes y Autómatas II. Analizador Semantico.
#TECNM. ITCG. Ing. en Sistemas Computacionales. 7mo semestre
#01-10-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

# La librerías necesarias
from DataStructures import Nodo, Simbolo, TablaSimbolos

# ==================================================
# Inicialización de estructuras y estados
# ==================================================
tabla_global = None
tabla_actual = None
errores_semanticos = []
funcion_actual = None
tipo_retorno_actual = None
imports_registrados = set()

if_cont = for_cont = foreach_cont = loop_cont = case_cont = 0

# ==================================================
# Funciones auxiliares
# ==================================================
def agregar_error(mensaje, linea=None):
    linea_str = f" en línea {linea}" if linea else ""
    errores_semanticos.append(f"❌ Error semántico{linea_str}: {mensaje}")

def decorar_nodo(nodo, **atributos):
    nodo.attrs.update(atributos)

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
    if tipo.endswith('[]'):
        base = tipo[:-2]
        return []
    return None

def obtener_tipo_nodo_tipo(nodo_tipo):
    if not nodo_tipo:
        return None
    if nodo_tipo.tipo == "Tipo":
        return nodo_tipo.valor
    elif nodo_tipo.tipo == "TipoArray":
        return f"{nodo_tipo.valor}[]"

    return None

def obtener_tamano_array_desde_tipo(nodo_tipo):
    if not nodo_tipo or nodo_tipo.tipo != "TipoArray":
        return None
    if not nodo_tipo.hijos:
        return None

    tam_nodo = nodo_tipo.hijos[0]
    if tam_nodo and tam_nodo.tipo == "TamanoArray":
        return tam_nodo.valor

    return None

def tipos_compatibles(destino, origen):
    if destino == origen:
        return True
    if destino in ('int','float') and origen in ('int','float'):
        return True

    if destino and origen and destino.endswith('[]') and origen.endswith('[]'):
        base_d = destino[:-2]
        base_o = origen[:-2]
        return tipos_compatibles(base_d, base_o)

    return False

def inferir_tipo_operacion(op, izq, der, linea):
    if izq in (None, 'error') or der in (None, 'error'):
        return 'error'

    if op in ['+', '-', '*', '/', '%']:
        if op == '+':
            if izq in ('string', 'char') and der in ('string', 'char'):
                return 'string'

        if izq in ('int','float') and der in ('int','float'):
            return 'float' if 'float' in (izq, der) else 'int'

        agregar_error(f"Operación '{op}' no válida entre {izq} y {der}", linea)
        return 'error'

    if op in ['==','!=']:
        if izq in ('int','float') and der in ('int','float'):
            return 'bool'
        if izq == 'bool' and der == 'bool':
            return 'bool'
        if izq == 'string' and der == 'string':
            return 'bool'
        if izq == 'char' and der == 'char':
            return 'bool'

        agregar_error(f"Comparación '{op}' no válida entre {izq} y {der}", linea)
        return 'error'

    if op in ['<','>','<=','>=']:
        if izq in ('int','float') and der in ('int','float'):
            return 'bool'

        agregar_error(f"Operador relacional '{op}' no válido para tipos {izq} y {der}", linea)
        return 'error'

    if op in ['&&','||']:
        if izq == 'bool' and der == 'bool':
            return 'bool'

        agregar_error(f"Operador lógico '{op}' requiere booleanos, no {izq} y {der}", linea)
        return 'error'

    agregar_error(f"Operador desconocido '{op}'", linea)
    return 'error'

# ==================================================
# VISITADORES PRINCIPALES
# ==================================================
def analizar(arbol: Nodo):
    if not arbol or arbol.tipo != "Programa":
        agregar_error("Árbol sintáctico inválido")
        return

    try:
        visitar_programa(arbol)
    except Exception as e:
        agregar_error(f"Error durante análisis semántico: {str(e)}")

def visitar_programa(nodo: Nodo):
    global tabla_global, tabla_actual
    decorar_nodo(nodo, scope="global")

    tabla_global = TablaSimbolos()
    tabla_actual = tabla_global

    registrar_funciones(nodo)

    for hijo in nodo.hijos:
        if hijo.tipo == "Import":
            visitar_import(hijo)
        elif hijo.tipo == "DeclaracionVariable":
            visitar_declaracion_variable(hijo, es_global=True)
        elif hijo.tipo == "Constante":
            visitar_constante(hijo, es_global=True)
        elif hijo.tipo == "Funcion":
            visitar_funcion(hijo)

def visitar_import(nodo: Nodo):
    mod = nodo.valor.strip('"')
    if mod in imports_registrados:
        agregar_error(f"Módulo '{mod}' ya importado", nodo.linea)
    else:
        imports_registrados.add(mod)
    decorar_nodo(nodo, modulo=mod)

def visitar_declaracion_variable(nodo: Nodo, es_global=False):
    tipo_declarado = None
    tam_declarado = None

    for hijo in nodo.hijos:
        if hijo.tipo in ("Tipo", "TipoArray"):
            tipo_declarado = obtener_tipo_nodo_tipo(hijo)
            tam_declarado = obtener_tamano_array_desde_tipo(hijo)
            break

    if not tipo_declarado:
        agregar_error("No se pudo determinar el tipo de la variable", nodo.linea)
        tipo_declarado = "error"

    categoria = 'variable_global' if es_global else 'variable_local'

    for hijo in nodo.hijos:
        if hijo.tipo == "Identificador":
            attrs = {}

            if tipo_declarado.endswith('[]') and tam_declarado is not None:
                if tam_declarado < 2:
                    agregar_error("El tamaño de la array tiene que ser mayor a 2", nodo.linea)

                attrs['array_size'] = tam_declarado
                attrs['valor_defecto'] = [valor_por_defecto(tipo_declarado[:-2])] * tam_declarado
            else:
                attrs['valor_defecto'] = valor_por_defecto(tipo_declarado)
            attrs['inicializada'] = True 

            if not tabla_actual.insertar_variable(hijo.valor, tipo_declarado, categoria, hijo.linea, attrs):
                agregar_error(f"Variable '{hijo.valor}' ya declarada", hijo.linea)

            decorar_nodo(hijo, tipo_inferido=tipo_declarado, categoria=categoria)

        elif hijo.tipo == "AsignacionInicial":
            if tipo_declarado.endswith('[]'):
                if not hijo.hijos:
                    agregar_error(f"Inicialización de array '{hijo.valor}' sin valor", hijo.linea)
                    continue

                expr = hijo.hijos[0]
                tipo_expr = visitar_expresion(expr)

                if expr.tipo == "ArrayLiteral":
                    elementos = expr.hijos or []
                    tamanio = len(elementos)

                    base_expr = tipo_expr[:-2] if tipo_expr.endswith('[]') else tipo_expr
                    base_decl = tipo_declarado[:-2]

                    if not tipos_compatibles(base_decl, base_expr):
                        agregar_error(f"Inicializador de array incompatible: {base_expr} no es {base_decl}", hijo.linea)

                    if tam_declarado is not None:
                        if tamanio != tam_declarado:
                            agregar_error(f"Tamaño de inicializador ({tamanio}) no coincide con tamaño declarado ({tam_declarado}) para '{hijo.valor}'", hijo.linea)
                        attrs = {'inicializada': True, 'array_size': tam_declarado, 'valor_defecto': [valor_por_defecto(base_decl)] * tam_declarado}
                    else:
                        attrs = {'inicializada': True, 'array_size': tamanio, 'valor_defecto': [valor_por_defecto(base_decl)] * tamanio}

                    if not tabla_actual.insertar_variable(hijo.valor, tipo_declarado, categoria, hijo.linea, attrs):
                        agregar_error(f"Variable '{hijo.valor}' ya declarada", hijo.linea)

                    decorar_nodo(hijo, tipo_inferido=tipo_declarado, tipo_expresion=tipo_expr, array_size=attrs.get('array_size'))

                else:
                    if not tipo_expr.endswith('[]'):
                        agregar_error(f"No se puede inicializar array '{hijo.valor}' con valor de tipo {tipo_expr}", hijo.linea)
                        attrs = {'inicializada': True, 'valor_defecto': []}
                        tabla_actual.insertar_variable(hijo.valor, tipo_declarado, categoria, hijo.linea, attrs)
                    else:
                        if tam_declarado is not None:
                            agregar_error(f"No se permite inicializar array con expresión cuando se declaró tamaño explícito ({tam_declarado})", hijo.linea)
                        attrs = {'inicializada': True, 'valor_defecto': [], 'array_size': None}
                        tabla_actual.insertar_variable(hijo.valor, tipo_declarado, categoria, hijo.linea, attrs)
            else:
                attrs = {'inicializada': True, 'valor_defecto': None}

                if not tabla_actual.insertar_variable(hijo.valor, tipo_declarado, categoria, hijo.linea, attrs):
                    agregar_error(f"Variable '{hijo.valor}' ya declarada", hijo.linea)
                if hijo.hijos:
                    tipo_expr = visitar_expresion(hijo.hijos[0])

                    if not tipos_compatibles(tipo_declarado, tipo_expr):
                        agregar_error(f"No se puede asignar {tipo_expr} a variable de tipo {tipo_declarado}", hijo.linea)

                    decorar_nodo(hijo, tipo_inferido=tipo_declarado, tipo_expresion=tipo_expr)

def visitar_constante(nodo: Nodo, es_global=False):
    tipo_constante = None
    
    for hijo in nodo.hijos:
        if hijo.tipo in ["Tipo", "TipoArray"]:
            tipo_constante = obtener_tipo_nodo_tipo(hijo)
            break

    if not tipo_constante:
        agregar_error("No se pudo determinar el tipo de la constante", nodo.linea)
        tipo_constante = "error"

    categoria = 'constante_global' if es_global else 'constante_local'
    attrs = {'inicializada': True, 'valor_defecto': None}

    if not tabla_actual.insertar_variable(nodo.valor, tipo_constante, categoria, nodo.linea, attrs):
        agregar_error(f"Constante '{nodo.valor}' ya declarada", nodo.linea)
    
    if len(nodo.hijos) > 1:
        tipo_expr = visitar_expresion(nodo.hijos[1])

        if not tipos_compatibles(tipo_constante, tipo_expr):
            agregar_error(f"No se puede asignar {tipo_expr} a constante de tipo {tipo_constante}", nodo.linea)
        
        decorar_nodo(nodo, tipo_inferido=tipo_constante, tipo_expresion=tipo_expr, categoria=categoria)

# ==================================================
# Funciones
# ==================================================
def registrar_funciones(nodo: Nodo):
    for hijo in nodo.hijos:
        if hijo.tipo == "Funcion":
            nombre = hijo.valor
            tipo_retorno = "void"
            parametros = []

            for sub in hijo.hijos:
                if sub.tipo == "Tipo":
                    tipo_retorno = sub.valor
                elif sub.tipo == "Parametro":
                    tipo_param = None
                    if sub.hijos and sub.hijos[0].tipo in ("Tipo","TipoArray"):
                        tipo_param = obtener_tipo_nodo_tipo(sub.hijos[0])
                    else:
                        tipo_param = 'error'
                    parametros.append((sub.valor, tipo_param))
            if not tabla_global.insertar_funcion(nombre, tipo_retorno, 'funcion', hijo.linea, {'parametros': parametros, 'tiene_return': False}):
                agregar_error(f"Función '{nombre}' ya declarada", hijo.linea)

def visitar_funcion(nodo: Nodo):
    global tabla_actual, funcion_actual, tipo_retorno_actual

    nombre_func = nodo.valor
    funcion_anterior = funcion_actual
    tabla_anterior = tabla_actual

    tabla_actual = tabla_global.crear_hijo(f"funcion_{nombre_func}")
    funcion_actual = nombre_func

    simbolo_func = tabla_global.buscar_funcion(nombre_func)
    if not simbolo_func or simbolo_func.categoria != 'funcion':
        agregar_error(f"Función '{nombre_func}' no declarada previamente", nodo.linea)
        parametros = []
        tipo_retorno = 'void'
    else:
        tipo_retorno = simbolo_func.tipo or "void"
        tipo_retorno_actual = tipo_retorno
        parametros = simbolo_func.attrs.get('parametros', [])
    
    for (pname, ptype) in parametros:
        attrs = {'inicializada': True, 'valor_defecto': valor_por_defecto(ptype)}
        if not tabla_actual.insertar_variable(pname, ptype, 'parametro', nodo.linea, attrs):
            agregar_error(f"Parámetro '{pname}' duplicado en función '{nombre_func}'", nodo.linea)
        decorar_nodo(Nodo("Parametro", valor=pname), tipo_inferido=ptype, categoria='parametro')

    cuerpo = None
    for hijo in nodo.hijos:
        if hijo.tipo == "Tipo":
            tipo_retorno = hijo.valor
            tipo_retorno_actual = tipo_retorno
        elif hijo.tipo == "Cuerpo":
            cuerpo = hijo

    if cuerpo:
        visitar_cuerpo(cuerpo)

        if tipo_retorno != 'void':
            simbolo_func = tabla_global.buscar_funcion(nombre_func)
            if simbolo_func and not simbolo_func.attrs.get('tiene_return', False):
                agregar_error(f"Función '{nombre_func}' debe retornar un valor (se requiere al menos un return)", nodo.linea)

    tabla_actual = tabla_anterior
    funcion_actual = funcion_anterior
    tipo_retorno_actual = None

    decorar_nodo(nodo, tipo_retorno=tipo_retorno, parametros=parametros, scope=f"funcion_{nombre_func}")

# ==================================================
# Cuerpo de bloque
# ==================================================
def visitar_cuerpo(nodo):
    for instruccion in nodo.hijos:
        if not isinstance(instruccion, Nodo):
            continue

        if instruccion.tipo == "DeclaracionVariable":
            visitar_declaracion_variable(instruccion, es_global=False)
        elif instruccion.tipo == "AsignacionVariable":
            visitar_asignacion(instruccion)
        elif instruccion.tipo == "If":
            visitar_if(instruccion)
        elif instruccion.tipo in ("While", "Until", "DoWhile"):
            visitar_loop_condicional(instruccion)
        elif instruccion.tipo == "For":
            visitar_for(instruccion)
        elif instruccion.tipo == "ForEach":
            visitar_foreach(instruccion)
        elif instruccion.tipo == "Switch":
            visitar_switch(instruccion)
        elif instruccion.tipo == "LlamadaFuncion":
            visitar_llamada_funcion(instruccion)
        elif instruccion.tipo == "Return":
            visitar_return(instruccion)
        elif instruccion.tipo == "InstruccionSimple":
            visitar_instruccion_simple(instruccion)
        elif instruccion.tipo == "PostIncDec":
            visitar_inc_dec(instruccion)

def visitar_instruccion_simple(nodo: Nodo):
    global tabla_actual, funcion_actual

    if nodo.valor in ("break", "continue"):
        esta_en_ciclo = False
        tabla_temporal = tabla_actual
        
        while tabla_temporal is not None:
            scope_name = tabla_temporal.nombre_scope.lower()
            
            if any(ciclo in scope_name for ciclo in ('for', 'foreach', 'loop')):
                esta_en_ciclo = True
                break
                
            tabla_temporal = tabla_temporal.padre
        
        if not esta_en_ciclo:
            agregar_error(f"La instrucción '{nodo.valor}' solo se puede usar dentro de ciclos", nodo.linea)

def visitar_inc_dec(nodo: Nodo):
    variable = nodo.hijos[0].valor
    simbolo = tabla_actual.buscar_variable(variable)

    if not simbolo:
        agregar_error(f"Variable '{variable}' no declarada", nodo.linea)
        decorar_nodo(nodo, tipo_inferido='error')
        return 'error'

    if simbolo.tipo not in ('int', 'float'):
        agregar_error(f"Incremento/decremento no válido para tipo {simbolo.tipo}", nodo.linea)

    decorar_nodo(nodo, tipo_inferido=simbolo.tipo)
    return simbolo.tipo

# ==================================================
# Expresiones
# ==================================================
def visitar_expresion(nodo: Nodo):
    if nodo is None:
        return 'error'

    if nodo.tipo == "Constante":
        valor = nodo.valor
        if isinstance(valor, int):
            decorar_nodo(nodo, tipo_inferido='int', es_constante=True, valor_constante=valor)
            return 'int'
        if isinstance(valor, float):
            decorar_nodo(nodo, tipo_inferido='float', es_constante=True, valor_constante=valor)
            return 'float'
        if isinstance(valor, str):
            cont = valor
            if len(cont) == 1:
                decorar_nodo(nodo, tipo_inferido='char', es_constante=True, valor_constante=cont)
                return 'char'
            else:
                decorar_nodo(nodo, tipo_inferido='string', es_constante=True, valor_constante=cont)
                return 'string'

        return 'error'
    
    elif nodo.tipo == "ConstanteBooleana":
        decorar_nodo(nodo, tipo_inferido='bool', es_constante=True, valor_constante=nodo.valor)
        return 'bool'
    
    elif nodo.tipo == "Identificador":
        simbolo = tabla_actual.buscar_variable(nodo.valor)

        if not simbolo:
            agregar_error(f"Identificador '{nodo.valor}' no declarado", nodo.linea)
            return 'error'
        
        decorar_nodo(nodo, tipo_inferido=simbolo.tipo, simbolo=simbolo, categoria=simbolo.categoria)
        return simbolo.tipo
    
    elif nodo.tipo == "OperacionBinaria":
        tipo_izq = visitar_expresion(nodo.hijos[0])
        tipo_der = visitar_expresion(nodo.hijos[1])
        tipo_res = inferir_tipo_operacion(nodo.valor, tipo_izq, tipo_der, nodo.linea)

        decorar_nodo(nodo, tipo_inferido=tipo_res, tipo_operando_izq=tipo_izq, tipo_operando_der=tipo_der)
        return tipo_res
    
    elif nodo.tipo == "OperacionUnaria":
        operador = nodo.valor
        tipo_operando = visitar_expresion(nodo.hijos[0])

        if operador not in ['!', '+', '-']:
            agregar_error(f"Operador unario desconocido '{operador}'", nodo.linea)
            return 'error'
        elif operador == '!' and tipo_operando != 'bool':
            agregar_error(f"Operación '{operador}' solo se puede aplicar a expresiones booleanas, no a '{tipo_operando}'",
                          nodo.linea)
            return 'error'
        elif operador in ('+', '-') and tipo_operando not in ('int', 'float'):
            agregar_error(f"El operador '{operador}' solo se puede aplicar a valores numéricos, no a '{tipo_operando}'",
                          nodo.linea)
            return 'error'

        decorar_nodo(nodo, tipo_inferido=tipo_operando)
        return tipo_operando
    
    elif nodo.tipo == "LlamadaFuncion":
        return visitar_llamada_funcion(nodo, en_expresion=True)
    
    elif nodo.tipo == "ArrayLiteral":
        elems = nodo.hijos or []
        tipos = [visitar_expresion(e) for e in elems]

        if not tipos:
            agregar_error("Array literal vacío sin tipo inferible", nodo.linea)
            return 'error'

        base = tipos[0]
        for t in tipos[1:]:
            if not tipos_compatibles(base, t):
                agregar_error(f"Elementos de array con tipos incompatibles: {base} y {t}", nodo.linea)
                return 'error'

        tipo_arr = f"{base}[]"
        decorar_nodo(nodo, tipo_inferido=tipo_arr, array_size=len(elems))
        return tipo_arr

    elif nodo.tipo == "ArrayAccess":
        nombre = nodo.valor
        simbolo = tabla_actual.buscar_variable(nombre)

        if not simbolo:
            agregar_error(f"Array '{nombre}' no declarado", nodo.linea)
            return 'error'
        
        t_arr = simbolo.tipo
        if not t_arr or not t_arr.endswith('[]'):
            agregar_error(f"'{nombre}' no es un array", nodo.linea)
            return 'error'

        idx_tipo = visitar_expresion(nodo.hijos[0])
        if idx_tipo != 'int':
            agregar_error(f"Índice de array debe ser int, no {idx_tipo}", nodo.linea)
            return 'error'

        base = t_arr[:-2]
        decorar_nodo(nodo, tipo_inferido=base)
        return base

    elif nodo.tipo == "PostIncDec":
        return visitar_inc_dec(nodo) or 'error'
    
    agregar_error(f"Tipo de expresión no manejado: {nodo.tipo}", nodo.linea)
    return 'error'


# ==================================================
# LLAMADAS A FUNCIÓN
# ==================================================
def visitar_llamada_funcion(nodo: Nodo, en_expresion=False):
    nombre_funcion = nodo.valor
    argumentos = nodo.hijos
    tipos_args = [visitar_expresion(a) for a in argumentos]
    
    simbolo_func = tabla_global.buscar_funcion(nombre_funcion)
    if not simbolo_func:
        agregar_error(f"Función '{nombre_funcion}' no declarada", nodo.linea)
        return 'error'
    
    params = simbolo_func.attrs.get('parametros', [])
    if len(params) != len(tipos_args):
        agregar_error(f"Función '{nombre_funcion}' espera {len(params)} argumentos, se proveyeron {len(tipos_args)}", nodo.linea)
        return 'error'

    for i, ((pname, ptype), atipo) in enumerate(zip(params, tipos_args)):
        if not tipos_compatibles(ptype, atipo):
            agregar_error(f"Argumento {i+1} de '{nombre_funcion}': se esperaba {ptype}, se obtuvo {atipo}", nodo.linea)

    tipo_retorno = simbolo_func.tipo
    if tipo_retorno == "void" and en_expresion:
        agregar_error(f"Función '{nombre_funcion}' no retorna ningun valor", nodo.linea)
        return 'error'

    decorar_nodo(nodo, tipo_inferido=tipo_retorno, simbolo=simbolo_func)
    return tipo_retorno

# ==================================================
# Asignaciones y returns
# ==================================================
def visitar_asignacion(nodo: Nodo):
    lvalue, expresion = nodo.hijos
    
    if lvalue.tipo == "Identificador":
        simbolo = tabla_actual.buscar_variable(lvalue.valor)
        if not simbolo:
            agregar_error(f"Variable '{lvalue.valor}' no declarada", lvalue.linea)
            tipo_destino = 'error'
        else:
            tipo_destino = simbolo.tipo
    elif lvalue.tipo == "ArrayAccess":
        tipo_destino = visitar_expresion(lvalue)
    else:
        tipo_destino = visitar_expresion(lvalue)
    
    tipo_origen = visitar_expresion(expresion)

    if tipo_destino.endswith('[]') and tipo_origen.endswith('[]'):
        simbolo_destino = tabla_actual.buscar_variable(lvalue.valor) if lvalue.tipo == "Identificador" else None
        tam_destino = simbolo_destino.attrs.get('array_size') if simbolo_destino else None

        origen_es_literal = isinstance(expresion, Nodo) and expresion.tipo == "ArrayLiteral"
        if tam_destino is not None:
            if origen_es_literal:
                tam_origen = len(expresion.hijos or [])
                if tam_origen != tam_destino:
                    agregar_error(f"Tamaño de array no coincide ({tam_origen} != {tam_destino})", nodo.linea)
            else:
                agregar_error("Asignación de array no permitida cuando el lado izquierdo tiene tamaño explícito y la derecha no es literal", nodo.linea)
        else:
            if not origen_es_literal:
                agregar_error("Asignación entre arrays sin tamaño explícito no está permitida en esta versión", nodo.linea)


    es_compatible = tipos_compatibles(tipo_destino, tipo_origen)
    if not es_compatible:
        agregar_error(f"No se puede asignar {tipo_origen} a {tipo_destino}", nodo.linea)
    
    decorar_nodo(nodo, tipo_destino=tipo_destino, tipo_origen=tipo_origen, es_compatible=es_compatible)

def visitar_return(nodo: Nodo):
    global funcion_actual, tipo_retorno_actual
    if nodo.hijos:
        tipo_expresion = visitar_expresion(nodo.hijos[0])
    else:
        tipo_expresion = "void"
    
    if tipo_retorno_actual == 'void':
        if tipo_expresion != 'void':
            agregar_error("Return con valor en función void", nodo.linea)
    else:
        if tipo_expresion == 'void':
            agregar_error("Return vacío en función no-void", nodo.linea)
        elif not tipos_compatibles(tipo_retorno_actual, tipo_expresion):
            agregar_error(f"Return de tipo {tipo_expresion} incompatible con tipo de retorno {tipo_retorno_actual}", nodo.linea)

    if funcion_actual:
        simbolo_func = tabla_global.buscar_funcion(funcion_actual)
        if simbolo_func:
            simbolo_func.attrs['tiene_return'] = True
    
    decorar_nodo(nodo, tipo_inferido=tipo_expresion)

# ==================================================
# Estructuras de control
# ==================================================
def visitar_if(nodo: Nodo):
    global tabla_actual, if_cont
    if_cont += 1
    elif_cont = 0

    tipo_cond = visitar_expresion(nodo.hijos[0])
    if tipo_cond != 'bool':
        agregar_error(f"Condición de if debe ser booleana, no {tipo_cond}", nodo.hijos[0].linea)
    
    for i, hijo in enumerate(nodo.hijos[1:]):
        if hijo.tipo == "Cuerpo":
            tabla_anterior = tabla_actual
            tabla_actual = tabla_actual.crear_hijo(f"if_{if_cont}")
            
            visitar_cuerpo(hijo)
            
            tabla_actual = tabla_anterior

        if hijo.tipo == "Elif":
            elif_cont += 1
            visitar_elif(hijo, elif_cont)

        if hijo.tipo == "Else":
            tabla_anterior = tabla_actual
            tabla_actual = tabla_actual.crear_hijo(f"else_{if_cont}")

            visitar_cuerpo(hijo.hijos[0])
            
            tabla_actual = tabla_anterior

def visitar_elif(nodo: Nodo, elif_cont):
    global tabla_actual, if_cont

    tipo_cond = visitar_expresion(nodo.hijos[0])
    if tipo_cond != 'bool':
        agregar_error(f"Condición de elif debe ser booleana, no {tipo_cond}", nodo.hijos[0].linea)

    tabla_anterior = tabla_actual
    tabla_actual = tabla_actual.crear_hijo(f"elif_{elif_cont}_if_{if_cont}")
            
    visitar_cuerpo(nodo.hijos[1])
            
    tabla_actual = tabla_anterior

def visitar_loop_condicional(nodo: Nodo):
    global tabla_actual, loop_cont
    loop_cont += 1

    tipo_cond = visitar_expresion(nodo.hijos[0])
    if tipo_cond != 'bool':
        agregar_error(f"Condición de {nodo.tipo} debe ser booleana, no {tipo_cond}", nodo.hijos[0].linea)
    
    tabla_anterior = tabla_actual
    tabla_actual = tabla_actual.crear_hijo(f"loop_{loop_cont}")
            
    visitar_cuerpo(nodo.hijos[1])
            
    tabla_actual = tabla_anterior

def visitar_for(nodo: Nodo):
    global tabla_actual, for_cont
    for_cont += 1

    tabla_anterior = tabla_actual
    tabla_actual = tabla_actual.crear_hijo(f"for_{for_cont}")

    for hijo in nodo.hijos:
        if not isinstance(hijo, Nodo):
            continue

        if hijo.tipo == "InicializacionFor":
            tipo_declarado = hijo.valor

            if not tipo_declarado:
                agregar_error("No se pudo determinar el tipo de la variable", nodo.linea)
                tipo_declarado = "error"

            for inicializacion in hijo.hijos:
                if not tabla_actual.insertar_variable(inicializacion.valor, tipo_declarado, 'variable_local', inicializacion.linea, {'inicializada': True, 'valor_defecto': valor_por_defecto(tipo_declarado)}):
                    agregar_error(f"Variable '{inicializacion.valor}' ya declarada", inicializacion.linea)

                if inicializacion.hijos:
                    tipo_expr = visitar_expresion(inicializacion.hijos[0])
                    if not tipos_compatibles(tipo_declarado, tipo_expr):
                        agregar_error(f"No se puede asignar {tipo_expr} a variable de tipo {tipo_declarado}", hijo.linea)

        if hijo.tipo == "AsignacionNoPC":
            visitar_asignacion(hijo)

        if hijo.tipo == "CondicionFor":
            tipo_cond = visitar_expresion(hijo.hijos[0])

            if tipo_cond != 'bool':
                agregar_error(f"Condición de for debe ser booleana, no {tipo_cond}", nodo.linea)

        if hijo.tipo == "ActualizacionFor":
            if hijo.hijos[0].tipo == "AsignacionNoPC":
                visitar_asignacion(hijo.hijos[0])
            if hijo.hijos[0].tipo == "PostIncDec":
                visitar_inc_dec(hijo.hijos[0])

        if hijo.tipo == "Cuerpo":
            visitar_cuerpo(hijo)

    tabla_actual = tabla_anterior
               
def visitar_foreach(nodo: Nodo):
    global tabla_actual, foreach_cont
    foreach_cont += 1

    if len(nodo.hijos) < 4:
        agregar_error(f"Expresion For Each declarada incorrectamente")
        return

    tipo_variable = nodo.hijos[0].valor
    variable = nodo.hijos[1].valor
    coleccion = nodo.hijos[2]
            
    tabla_anterior = tabla_actual
    tabla_actual = tabla_actual.crear_hijo(f"foreach_{foreach_cont}")
            
    tabla_actual.insertar_variable(variable, tipo_variable, 'variable_local', nodo.linea, {'inicializada': True, 'valor_defecto': valor_por_defecto(tipo_variable)})
            
    tipo_coleccion = visitar_expresion(coleccion)
    if not tipo_coleccion.endswith('[]'):
        agregar_error(f"Colección en foreach debe ser array, no {tipo_coleccion}", coleccion.linea)
    else:
        if tipo_variable != tipo_coleccion[:-2]:
            agregar_error(f"El iterador de tipo {tipo_variable} no es compatible con la colección tipo {tipo_coleccion}", coleccion.linea)
            
    visitar_cuerpo(nodo.hijos[3])
            
    tabla_actual = tabla_anterior

def visitar_switch(nodo: Nodo):
    global tabla_actual, case_cont

    tipo_expr = visitar_expresion(nodo.hijos[0])
    
    for caso in nodo.hijos[1:]:
        if caso.tipo == "Case":
            case_cont += 1
            expr_caso = caso.hijos[0]

            tipo_caso = visitar_expresion(expr_caso)
            if not tipos_compatibles(tipo_expr, tipo_caso):
                agregar_error(f"Tipo de caso {tipo_caso} incompatible con switch {tipo_expr}", expr_caso.linea)
            
            tabla_anterior = tabla_actual
            tabla_actual = tabla_actual.crear_hijo(f"case_{case_cont}")

            visitar_cuerpo(caso.hijos[1])

            tabla_actual = tabla_anterior

        elif caso.tipo == "Default":
            case_cont += 1
            
            tabla_anterior = tabla_actual
            tabla_actual = tabla_actual.crear_hijo(f"default_{case_cont}")

            visitar_cuerpo(caso.hijos[0])

            tabla_actual = tabla_anterior

# ==================================================
# Verificaciones adicionales
# ==================================================
def verificar_return_en_funcion():
    if funcion_actual:
        simbolo = tabla_global.buscar_funcion(funcion_actual)
        return simbolo and simbolo.attrs.get('tiene_return', False)
    return False

# ==================================================
# Funciones de debug
# ==================================================
def imprimir_ast_decorado(nodo: Nodo, nivel=0):
    indent = "  " * nivel
    info = f"{nodo.tipo}"
    if nodo.valor:
        info += f" [valor: {nodo.valor}]"
    if nodo.attrs.get('tipo_inferido'):
        info += f" :: {nodo.attrs['tipo_inferido']}"
    print(f"{indent}{info}")
    for hijo in nodo.hijos:
        if isinstance(hijo, Nodo):
            imprimir_ast_decorado(hijo, nivel+1)

def obtener_errores():
    return errores_semanticos.copy()

def limpiar_estado():
    global tabla_global, tabla_actual, errores_semanticos, funcion_actual, tipo_retorno_actual, imports_registrados
    global if_cont, for_cont, foreach_cont, loop_cont, case_cont

    tabla_global = TablaSimbolos()
    tabla_actual = tabla_global
    errores_semanticos = []
    funcion_actual = None
    tipo_retorno_actual = None
    imports_registrados = set()
    if_cont = for_cont = foreach_cont = loop_cont = case_cont = 0

# ==================================================
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# ==================================================
def analizar_semanticamente(arbol):
    limpiar_estado()
    analizar(arbol)
    return tabla_global, errores_semanticos
