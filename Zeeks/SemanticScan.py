#Lenguajes y Autómatas II. Analizador Semantico.
#TECNM. ITCG. Ing. en Sistemas Computacionales. 7mo semestre
#01-10-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

from DataStructures import Nodo, Simbolo, TablaSimbolos

# ==================================================
# Inicialización de estructuras y estados
# ==================================================
tabla_global = TablaSimbolos()
tabla_actual = tabla_global
errores_semanticos = []
funcion_actual = None
tipo_retorno_actual = None
imports_registrados = set()
tipos_basicos = {'int', 'float', 'bool', 'char', 'string', 'void'}
if_cont = 0
for_cont = 0
foreach_cont = 0
loop_cont = 0
case_cont = 0

# ==================================================
# Funciones auxiliares
# ==================================================
def agregar_error(mensaje, linea=None):
    linea_str = f" en línea {linea}" if linea else ""
    errores_semanticos.append(f"❌ Error semántico{linea_str}: {mensaje}")

def decorar_nodo(nodo, **atributos):
    nodo.attrs.update(atributos)

def obtener_tipo_nodo_tipo(nodo_tipo):
    if nodo_tipo.tipo == "Tipo":
        return nodo_tipo.valor
    elif nodo_tipo.tipo == "TipoArray":
        return f"{nodo_tipo.valor}[]"
    elif nodo_tipo.tipo == "TipoMap":
        tipo_clave = obtener_tipo_nodo_tipo(nodo_tipo.hijos[0])
        tipo_valor = obtener_tipo_nodo_tipo(nodo_tipo.hijos[1])
        return f"map<{tipo_clave},{tipo_valor}>"

    return None

def obtener_tipo_constante(valor):
    if isinstance(valor, int):
        return 'int'
    elif isinstance(valor, float):
        return 'float'
    elif isinstance(valor, bool):
        return 'bool'
    elif isinstance(valor, str):
        contenido = valor.strip('"\'')
        return 'string' if len(contenido) != 1 else 'char'
    return 'desconocido'

def tipos_compatibles(tipo1, tipo2): # ERROR: agregar verificacion de map
    compatibilidad = {
        'int': {'int', 'float'},
        'float': {'int', 'float'},
        'bool': {'bool'},
        'string': {'string'},
        'char': {'char', 'string'},
    }

    if tipo1 in compatibilidad and tipo2 in compatibilidad[tipo1]:
        return True

    # TODO: Implementar soporte para Map y Array
    # if tipo1.endswith('[]') and tipo2.endswith('[]'):
    #     return tipos_compatibles(tipo1[:-2], tipo2[:-2])

    return False

def inferir_tipo_operacion(op, tipo_izq, tipo_der, linea):
    reglas = {
        '+': {('int', 'int'): 'int', ('float', 'float'): 'float', ('int', 'float'): 'float', ('float', 'int'): 'float',
              ('string', 'string'): 'string', ('char', 'char'): 'string'},
        '-': {('int', 'int'): 'int', ('float', 'float'): 'float', ('int', 'float'): 'float', ('float', 'int'): 'float'},
        '*': {('int', 'int'): 'int', ('float', 'float'): 'float', ('int', 'float'): 'float', ('float', 'int'): 'float'},
        '/': {('int', 'int'): 'int', ('float', 'float'): 'float', ('int', 'float'): 'float', ('float', 'int'): 'float'},
        '%': {('int', 'int'): 'int'},
        '==': {('int', 'int'): 'bool', ('float', 'float'): 'bool', ('bool', 'bool'): 'bool',
               ('string', 'string'): 'bool', ('char', 'char'): 'bool', ('string', 'char'): 'bool', ('char', 'string'): 'bool'},
        '!=': {('int', 'int'): 'bool', ('float', 'float'): 'bool', ('bool', 'bool'): 'bool',
               ('string', 'string'): 'bool', ('char', 'char'): 'bool', ('string', 'char'): 'bool', ('char', 'string'): 'bool'},
        '<': {('int', 'int'): 'bool', ('float', 'float'): 'bool'},
        '>': {('int', 'int'): 'bool', ('float', 'float'): 'bool'},
        '<=': {('int', 'int'): 'bool', ('float', 'float'): 'bool'},
        '>=': {('int', 'int'): 'bool', ('float', 'float'): 'bool'},
        '&&': {('bool', 'bool'): 'bool'},
        '||': {('bool', 'bool'): 'bool'}
    }

    clave = (tipo_izq, tipo_der)
    if op in reglas and clave in reglas[op]:
        return reglas[op][clave]
    
    agregar_error(f"Operación '{op}' no válida entre {tipo_izq} y {tipo_der}", linea)
    return 'error'

def verificar_variable_inicializada(nombre, linea):
    simbolo = tabla_actual.buscar(nombre)

    if simbolo and simbolo.categoria in ['parametro', 'variable_local', 'variable_global', 'constante_local', 'constante_global']:
        if not simbolo.inicializada:
            agregar_error(f"Variable '{nombre}' no ha sido inicializada", linea)
            return False
        return True
    return False

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
    decorar_nodo(nodo, scope="global")

    registrar_firmas_funciones(nodo)

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
    modulo = nodo.valor.strip('"')
    if modulo in imports_registrados:
        agregar_error(f"Módulo '{modulo}' ya importado", nodo.linea)
    else:
        imports_registrados.add(modulo)
    decorar_nodo(nodo, modulo=modulo)

def visitar_declaracion_variable(nodo: Nodo, es_global=False):
    tipo_declarado = None

    for hijo in nodo.hijos:
        if hijo.tipo in ["Tipo", "TipoArray", "TipoMap"]:
            tipo_declarado = obtener_tipo_nodo_tipo(hijo)
            break

    if not tipo_declarado:
        agregar_error("No se pudo determinar el tipo de la variable", nodo.linea)
        tipo_declarado = "desconocido"

    categoria = 'variable_global' if es_global else 'variable_local'

    for hijo in nodo.hijos:
        if hijo.tipo == "Identificador":
            if not tabla_actual.insertar(hijo.valor, tipo_declarado, categoria, hijo.linea):
                agregar_error(f"Variable '{hijo.valor}' ya declarada", hijo.linea)
            decorar_nodo(hijo, tipo_inferido=tipo_declarado, categoria=categoria)
        elif hijo.tipo == "AsignacionInicial":
            if not tabla_actual.insertar(hijo.valor, tipo_declarado, categoria, hijo.linea, {'inicializada': True}):
                agregar_error(f"Variable '{hijo.valor}' ya declarada", hijo.linea)

            if hijo.hijos:
                tipo_expr = visitar_expresion(hijo.hijos[0])
                if not tipos_compatibles(tipo_declarado, tipo_expr):
                    agregar_error(f"No se puede asignar {tipo_expr} a variable de tipo {tipo_declarado}", hijo.linea)
                
                decorar_nodo(hijo, tipo_inferido=tipo_declarado, tipo_expresion=tipo_expr, categoria=categoria)

def visitar_constante(nodo: Nodo, es_global=False):
    tipo_constante = obtener_tipo_nodo_tipo(nodo.hijos[0])
    expresion = nodo.hijos[1] if len(nodo.hijos) > 1 else None
    
    for hijo in nodo.hijos:
        if hijo.tipo in ["Tipo", "TipoArray", "TipoMap"]:
            tipo_constante = obtener_tipo_nodo_tipo(hijo)
            break

    if not tipo_constante:
        agregar_error("No se pudo determinar el tipo de la constante", nodo.linea)
        tipo_constante = "desconocido"

    categoria = 'constante_global' if es_global else 'constante_local'
    
    if not tabla_actual.insertar(nodo.valor, tipo_constante, categoria, nodo.linea, {'inicializada': True}):
        agregar_error(f"Constante '{nodo.valor}' ya declarada", nodo.linea)
    
    if expresion:
        tipo_expr = visitar_expresion(expresion)
        if not tipos_compatibles(tipo_constante, tipo_expr):
            agregar_error(f"No se puede asignar {tipo_expr} a constante de tipo {tipo_constante}", nodo.linea)
        
        decorar_nodo(nodo, tipo_inferido=tipo_constante, tipo_expresion=tipo_expr, categoria=categoria)

# ==================================================
# Funciones
# ==================================================
def registrar_firmas_funciones(nodo: Nodo):
    for hijo in nodo.hijos:
        if hijo.tipo == "Funcion":
            nombre_func = hijo.valor
            tipo_retorno = "void"
            parametros_nodos = []
            param_types = []

            for subhijo in hijo.hijos:
                if subhijo.tipo == "Tipo":
                    tipo_retorno = subhijo.valor
                elif subhijo.tipo == "Parametro":
                    parametros_nodos.append(subhijo)
                    # intentar extraer tipo del parámetro si existe (Nodo Parametro -> hijos[0] es Tipo)
                    if subhijo.hijos and subhijo.hijos[0].tipo == "Tipo":
                        param_types.append(subhijo.hijos[0].valor)
                    else:
                        param_types.append('desconocido')

            # Insertamos la firma en la tabla global. attrs contiene tanto nodos como lista de tipos
            if not tabla_global.insertar(
                nombre_func, tipo_retorno, 'funcion', hijo.linea,
                {'parametros': parametros_nodos, 'param_types': param_types, 'tiene_return': False}
            ):
                agregar_error(f"Función '{nombre_func}' ya declarada", hijo.linea)

def visitar_funcion(nodo: Nodo):
    global tabla_actual, funcion_actual, tipo_retorno_actual

    nombre_func = nodo.valor
    funcion_anterior = funcion_actual
    tabla_anterior = tabla_actual

    tabla_actual = tabla_global.crear_hijo(f"funcion_{nombre_func}")
    funcion_actual = nombre_func
    tipo_retorno = "void"

    simbolo_func = tabla_global.buscar(nombre_func)
    if not simbolo_func or simbolo_func.categoria != 'funcion':
        agregar_error(f"Función '{nombre_func}' no declarada previamente", nodo.linea)
    else:
        tipo_retorno = simbolo_func.tipo or "void"
        tipo_retorno_actual = tipo_retorno
        parametros = simbolo_func.attrs.get('parametros', [])

    cuerpo = None
    
    for i, param in enumerate(parametros):
        tipo_param = None
        if param.hijos and param.hijos[0].tipo == "Tipo":
            tipo_param = param.hijos[0].valor
        nombre_param = param.valor
        
        if not tabla_actual.insertar(nombre_param, tipo_param, 'parametro', param.linea, {'inicializada': True}):
            agregar_error(f"Parámetro '{nombre_param}' duplicado en función '{nombre_func}'", param.linea)

        decorar_nodo(param, tipo_inferido=tipo_param, categoria='parametro')

    for hijo in nodo.hijos:
        if hijo.tipo == "Tipo":
            tipo_retorno = hijo.valor
            tipo_retorno_actual = tipo_retorno
        elif hijo.tipo == "Cuerpo":
            cuerpo = hijo

    if cuerpo:
        visitar_cuerpo(cuerpo)

        if tipo_retorno != "void" and not verificar_return_en_funcion():
            agregar_error(f"Función '{nombre_func}' debe retornar un valor", nodo.linea)

    tabla_actual = tabla_anterior
    funcion_actual = funcion_anterior
    tipo_retorno_actual = None

    decorar_nodo(nodo, tipo_retorno=tipo_retorno, parametros=parametros, scope=f"funcion_{nombre_func}")

def visitar_parametro(nodo: Nodo):
    tipo_param = nodo.hijos[0].valor if nodo.hijos else None
    nombre_param = nodo.valor

    if not tabla_actual.insertar(nombre_param, tipo_param, 'parametro', nodo.linea, {'inicializada': True}):
        agregar_error(f"Parámetro '{nombre_param}' duplicado", nodo.linea)

    decorar_nodo(nodo, tipo_inferido=tipo_param, categoria='parametro')

# ==================================================
# Cuerpo de bloque
# ==================================================
def visitar_cuerpo(nodo):
    instrucciones = nodo.hijos
    
    for instruccion in instrucciones:
        if isinstance(instruccion, Nodo):
            if instruccion.tipo == "DeclaracionVariable":
                visitar_declaracion_variable(instruccion, es_global=False)
            elif instruccion.tipo == "AsignacionVariable":
                visitar_asignacion(instruccion)
            elif instruccion.tipo == "If":
                visitar_if(instruccion)
            elif instruccion.tipo in ["While", "Until", "DoWhile"]:
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

    if nodo.valor in ["break", "continue"]:
        esta_en_ciclo = False
        tabla_temporal = tabla_actual
        
        while tabla_temporal is not None:
            scope_name = tabla_temporal.nombre_scope.lower()
            
            if any(ciclo in scope_name for ciclo in ['for', 'foreach', 'loop']):
                esta_en_ciclo = True
                break
                
            tabla_temporal = tabla_temporal.padre
        
        if not esta_en_ciclo:
            agregar_error(f"La instrucción '{nodo.valor}' solo se puede usar dentro de ciclos", nodo.linea)

def visitar_inc_dec(nodo: Nodo):
    variable = nodo.valor
    simbolo = tabla_actual.buscar(variable)
    if not simbolo:
        agregar_error(f"Variable '{variable}' no declarada", nodo.linea)
    elif simbolo.tipo not in ['int', 'float']:
        agregar_error(f"Incremento/decremento no válido para tipo {simbolo.tipo}", nodo.linea)

    if not verificar_variable_inicializada(nodo.valor, nodo.linea):
        agregar_error(f"Variable '{nodo.valor}' no ha sido inicializada", nodo.linea)

    decorar_nodo(nodo, tipo_inferido=simbolo.tipo if simbolo else 'error')

# ==================================================
# Expresiones
# ==================================================
def visitar_expresion(nodo: Nodo):
    if nodo.tipo == "Constante":
        tipo = obtener_tipo_constante(nodo.valor)
        decorar_nodo(nodo, tipo_inferido=tipo, es_constante=True, valor_constante=nodo.valor)
        return tipo
    
    elif nodo.tipo == "ConstanteBooleana":
        decorar_nodo(nodo, tipo_inferido='bool', es_constante=True, valor_constante=nodo.valor)
        return 'bool'
    
    elif nodo.tipo == "Identificador":
        simbolo = tabla_actual.buscar(nodo.valor)

        if not simbolo:
            agregar_error(f"Identificador '{nodo.valor}' no declarado", nodo.linea)
            return 'error'
        
        if not verificar_variable_inicializada(nodo.valor, nodo.linea):
            agregar_error(f"Variable '{nodo.valor}' no ha sido inicializada", nodo.linea)

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

        if operador not in ['!', '+', '-', 'error', 'desconocido']:
            agregar_error(f"Operador unario desconocido '{operador}'", nodo.linea)
            return 'error'
        elif operador == '!' and tipo_operando != 'bool':
            agregar_error(f"Operación '{operador}' solo se puede aplicar a expresiones booleanas, no a '{tipo_operando}'",
                          nodo.linea)
            return 'error'
        elif operador in ['+', '-'] and tipo_operando not in ['int', 'float']:
            agregar_error(f"El operador '{operador}' solo se puede aplicar a valores numéricos, no a '{tipo_operando}'",
                          nodo.linea)
            return 'error'

        decorar_nodo(nodo, tipo_inferido=tipo_operando)
        return tipo_operando
    
    elif nodo.tipo == "LlamadaFuncion":
        return visitar_llamada_funcion(nodo, en_expresion=True)
    
    # TODO: Implementar soporte completo para Map y Array
    # elif nodo.tipo == "ArrayLiteral":
    #     tipos_elementos = []
    #     for elemento in nodo.hijos:
    #         tipo_elemento = visitar_expresion(elemento)
    #         tipos_elementos.append(tipo_elemento)
    #     
    #     tipo_base = tipos_elementos[0] if tipos_elementos else 'desconocido'
    #     for tipo in tipos_elementos:
    #         if not tipos_compatibles(tipo_base, tipo):
    #             agregar_error(f"Elementos de array con tipos incompatibles: {tipo_base} y {tipo}", nodo.linea)
    #             tipo_base = 'error'
    #             break
    #     
    #     tipo_array = f"{tipo_base}[]"
    #     decorar_nodo(nodo, tipo_inferido=tipo_array, tipos_elementos=tipos_elementos)
    #     return tipo_array
    #
    # elif nodo.tipo == "MapLiteral":
    #     # Verificar pares clave-valor
    #     for par in nodo.hijos:
    #         if par.tipo == "MapPair":
    #             tipo_clave = visitar_expresion(par.hijos[0])
    #             tipo_valor = visitar_expresion(par.hijos[1])
    #
    #             # ERROR: Podrías agregar verificaciones específicas para claves de map
    #
    #     decorar_nodo(nodo, tipo_inferido='map')
    #     return 'map' # ERROR: Acomodar el tipo map
    #
    # elif nodo.tipo == "ArrayAccess":
    #     # Verificar que el array existe y el índice es válido
    #     array = nodo.valor
    #     simbolo_array = tabla_actual.buscar(array)
    #     if not simbolo_array:
    #         agregar_error(f"Array '{array}' no declarado", nodo.linea)
    #         return 'error'
    #     
    #     if not simbolo_array.tipo.endswith('[]'):
    #         agregar_error(f"'{array}' no es un array", nodo.linea)
    #         return 'error'
    #     
    #     tipo_indice = visitar_expresion(nodo.hijos[0])
    #     if tipo_indice != 'int':
    #         agregar_error(f"Índice de array debe ser int, no {tipo_indice}", nodo.linea)
    #         return 'error'
    #     
    #     # ERROR: Verificar que el indice este dentro del rango de la array
    #     
    #     tipo_elemento = simbolo_array.tipo[:-2]  # Remover []
    #     decorar_nodo(nodo, tipo_inferido=tipo_elemento)
    #     return tipo_elemento
    #
    # elif nodo.tipo == "MapAccess":
    #     mapa = nodo.valor
    #     simbolo_mapa = tabla_actual.buscar(mapa)
    #     if not simbolo_mapa:
    #         agregar_error(f"Map '{mapa}' no declarado", nodo.linea)
    #         return 'error'
    #     
    #     # En tu implementación, MapAccess tiene un nodo Clave como hijo
    #     if nodo.hijos and hasattr(nodo.hijos[0], 'valor'):
    #         tipo_clave = obtener_tipo_constante(nodo.hijos[0].valor)
    #     else:
    #         tipo_clave = 'desconocido'
    #     
    #     decorar_nodo(nodo, tipo_inferido='int')  # ERROR: Asumimos que los maps retornan int por ahora
    #     return 'int'
    
    elif nodo.tipo == "PostIncDec":
        return visitar_inc_dec(nodo) or 'error'
    
    else:
        agregar_error(f"Tipo de expresión no manejado: {nodo.tipo}", nodo.linea)
        return 'error'


# ==================================================
# LLAMADAS A FUNCIÓN
# ==================================================
def visitar_llamada_funcion(nodo: Nodo, en_expresion=False):
    nombre_funcion = nodo.valor
    argumentos = nodo.hijos
    
    tipos_argumentos = []
    if argumentos:
        for arg in argumentos:
            tipo_arg = visitar_expresion(arg)
            tipos_argumentos.append(tipo_arg)

    simbolo_func = tabla_global.buscar_funcion_especifica(nombre_funcion, tipos_argumentos)
    
    if not simbolo_func:
        simbolo_func = tabla_global.buscar(nombre_funcion)
        if not simbolo_func or simbolo_func.categoria != 'funcion':
            agregar_error(f"Función '{nombre_funcion}' no declarada", nodo.linea)
            return 'error'
        
        parametros_esperados = simbolo_func.parametros
        if len(parametros_esperados) != len(argumentos):
            agregar_error(
                f"Función '{nombre_funcion}' espera {len(parametros_esperados)} argumentos, "
                f"se proveyeron {len(argumentos)}", nodo.linea
            )
            return 'error'
        else:
            for i, (param, arg, tipo_arg) in enumerate(zip(parametros_esperados, argumentos, tipos_argumentos)):
                tipo_param = param.attrs.get('tipo_inferido') or 'desconocido'
                if not tipos_compatibles(tipo_param, tipo_arg):
                    agregar_error(
                        f"Argumento {i+1} de '{nombre_funcion}': se esperaba {tipo_param}, "
                        f"se obtuvo {tipo_arg}", arg.linea
                    )
    
    tipo_retorno = simbolo_func.tipo

    if tipo_retorno == "void" and en_expresion:
        agregar_error(f"Función '{nombre_funcion}' no retorna ningun valor", nodo.linea)
        return 'error'

    decorar_nodo(nodo, tipo_inferido=tipo_retorno, simbolo=simbolo_func, es_llamada_valida=bool(simbolo_func))
    return tipo_retorno

# ==================================================
# Asignaciones y returns
# ==================================================
def visitar_asignacion(nodo: Nodo):
    lvalue, expresion = nodo.hijos
    
    if lvalue.tipo == "Identificador":
        simbolo = tabla_actual.buscar(lvalue.valor)
        if not simbolo:
            agregar_error(f"Variable '{lvalue.valor}' no declarada", lvalue.linea)
            tipo_destino = 'error'
        else:
            tipo_destino = simbolo.tipo
            simbolo.inicializada = True
            decorar_nodo(lvalue, tipo_inferido=tipo_destino, simbolo=simbolo)
    else:
        tipo_destino = visitar_expresion(lvalue)
    
    tipo_origen = visitar_expresion(expresion)
    es_compatible = tipos_compatibles(tipo_destino, tipo_origen)
    
    if not es_compatible:
        agregar_error(f"No se puede asignar {tipo_origen} a {tipo_destino}", nodo.linea)
    
    decorar_nodo(nodo, tipo_destino=tipo_destino, tipo_origen=tipo_origen, es_compatible=es_compatible)

def visitar_return(nodo: Nodo):
    if nodo.hijos:
        tipo_expresion = visitar_expresion(nodo.hijos[0])
    else:
        tipo_expresion = "void"
    
    # Verificar compatibilidad con tipo de retorno de la función
    es_compatible = True
    if tipo_retorno_actual and tipo_retorno_actual != 'error':
        es_compatible = tipos_compatibles(tipo_retorno_actual, tipo_expresion)
        if not es_compatible:
            agregar_error(
                f"Return de tipo {tipo_expresion} incompatible con "
                f"tipo de retorno {tipo_retorno_actual}", 
                nodo.linea
            )

    if not tipo_retorno_actual and tipo_expresion != 'void':
        agregar_error(
            f"Return de tipo {tipo_expresion} incompatible con "
            f"tipo de retorno void", 
            nodo.linea
        )

    if funcion_actual:
        simbolo_func = tabla_global.buscar(funcion_actual)
        if simbolo_func:
            simbolo_func.attrs['tiene_return'] = True
    
    decorar_nodo(nodo, tipo_inferido=tipo_expresion, es_compatible=es_compatible)

# ==================================================
# Estructuras de control
# ==================================================
def visitar_if(nodo: Nodo):
    global tabla_actual, if_cont
    if_cont += 1
    elif_cont = 0

    condicion = nodo.hijos[0]
    tipo_cond = visitar_expresion(condicion)
    if tipo_cond != 'bool':
        agregar_error(f"Condición de if debe ser booleana, no {tipo_cond}", condicion.linea)
    
    for i, hijo in enumerate(nodo.hijos[1:]):
        if hijo.tipo == "Cuerpo":
            tabla_anterior = tabla_actual
            tabla_actual = tabla_actual.crear_hijo(f"if_{if_cont}")
            
            visitar_cuerpo(hijo)
            
            tabla_actual = tabla_anterior

        if hijo.tipo == "Else":
            tabla_anterior = tabla_actual
            tabla_actual = tabla_actual.crear_hijo(f"else_{if_cont}")

            visitar_cuerpo(hijo.hijos[0])
            
            tabla_actual = tabla_anterior

        if hijo.tipo == "Elif":
            elif_cont += 1
            visitar_elif(hijo, elif_cont)

def visitar_elif(nodo: Nodo, elif_cont):
    global tabla_actual, if_cont

    condicion = nodo.hijos[0]
    tipo_cond = visitar_expresion(condicion)
    if tipo_cond != 'bool':
        agregar_error(f"Condición de elif debe ser booleana, no {tipo_cond}", condicion.linea)

    tabla_anterior = tabla_actual
    tabla_actual = tabla_actual.crear_hijo(f"elif_{elif_cont}_if_{if_cont}")
            
    visitar_cuerpo(nodo.hijos[1])
            
    tabla_actual = tabla_anterior

def visitar_loop_condicional(nodo: Nodo):
    global tabla_actual, loop_cont
    loop_cont += 1

    condicion = nodo.hijos[0]
    tipo_cond = visitar_expresion(condicion)
    if tipo_cond != 'bool':
        agregar_error(f"Condición de {nodo.tipo} debe ser booleana, no {tipo_cond}", condicion.linea)
    
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
        if isinstance(hijo, Nodo):
            if hijo.tipo == "InicializacionFor":
                tipo_declarado = hijo.valor

                if not tipo_declarado:
                    agregar_error("No se pudo determinar el tipo de la variable", nodo.linea)
                    tipo_declarado = "desconocido"

                for inicializacion in hijo.hijos:
                    if not tabla_actual.insertar(inicializacion.valor, tipo_declarado, 'variable_local', inicializacion.linea, {'inicializada': True}):
                        agregar_error(f"Variable '{inicializacion.valor}' ya declarada", inicializacion.linea)

                    if inicializacion.hijos:
                        tipo_expr = visitar_expresion(inicializacion.hijos[0])
                        if not tipos_compatibles(tipo_declarado, tipo_expr):
                            agregar_error(f"No se puede asignar {tipo_expr} a variable de tipo {tipo_declarado}", hijo.linea)
                
                        decorar_nodo(inicializacion, tipo_inferido=tipo_declarado, tipo_expresion=tipo_expr)

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

    if len(nodo.hijos) >= 4:
        tipo_variable = nodo.hijos[0].valor
        variable = nodo.hijos[1].valor
        coleccion = nodo.hijos[2]
            
        tabla_anterior = tabla_actual
        tabla_actual = tabla_actual.crear_hijo(f"foreach_{foreach_cont}")
            
        tabla_actual.insertar(variable, tipo_variable, 'variable_local', nodo.linea, {'inicializada': True})
            
        tipo_coleccion = visitar_expresion(coleccion)
        if not tipo_coleccion.endswith('[]'):
            agregar_error(f"Colección en foreach debe ser array, no {tipo_coleccion}", coleccion.linea)

        if tipo_coleccion.endswith('[]') and tipo_variable != tipo_coleccion[:-2]:
            agregar_error(f"El iterador de tipo {tipo_variable} no es compatible con la colección tipo {tipo_coleccion}", coleccion.linea)
            
        visitar_cuerpo(nodo.hijos[3])
            
        tabla_actual = tabla_anterior
    else:
        agregar_error(f"Expresion For Each declarada incorrectamente")

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
        simbolo = tabla_global.buscar(funcion_actual)
        return simbolo and simbolo.attrs.get('tiene_return', False)
    return False

def verificar_funciones_no_utilizadas():
    """Verificación básica de funciones no utilizadas"""
    # Esta es una verificación opcional que podrías implementar
    pass

def verificar_variables_no_utilizadas():
    """Verificación básica de variables no utilizadas"""
    # Esta es una verificación opcional que podrías implementar
    pass

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
    global tabla_global
    limpiar_estado()

    analizar(arbol)

    return tabla_global, errores_semanticos
