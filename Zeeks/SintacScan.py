#Lenguajes y Autómatas I. Analizador Sintactico.
#TECNM. ITCG. Ing. en Sistemas Computacionales. 6to semestre
#28-05-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

# La librerías necesarias
from ply.yacc import yacc
from DataStructures import Nodo
from LexScan import tokens, crear_lexer

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('nonassoc', 'IGUAL', 'DIF', 'MENOR', 'MENOR_IG', 'MAYOR', 'MAYOR_IG'),
    ('left', 'MAS', 'MENOS'),
    ('left', 'MUL', 'DIV', 'MOD'),
    ('right', 'NOT', 'UPLUS', 'UMINUS'),
    ('nonassoc', 'INC', 'DEC'),
)

errores_sintacticos = []

# -------------------------------------------------
# Reglas de la gramática
# -------------------------------------------------
def p_programa(p):
    '''programa : imports_opt globales_opt funciones'''
    hijos = (p[1] or []) + (p[2] or []) + (p[3] or [])
    p[0] = Nodo("Programa", hijos=hijos, linea=p.lineno(1))

# ----- Imports -----
def p_imports_opt(p):
    '''imports_opt : imports
                   | '''
    p[0] = p[1] if len(p) > 1 else []

def p_imports(p):
    '''imports : import_decl imports
               | import_decl'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_import_decl(p):
    '''import_decl : IMPORT CADENA PUNTOCOMA'''
    p[0] = Nodo("Import", valor=p[2], linea=p.lineno(1))

# ----- Variables globales -----
def p_globales_opt(p):
    '''globales_opt : declaraciones
                    | '''
    p[0] = p[1] if len(p) > 1 else []

# ----- Funciones -----
def p_funciones(p):
    '''funciones : funcion funciones
                 | funcion'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_funcion(p):
    '''funcion : FN ID PAREN_A parametros_opt PAREN_C retorno_opt LLAVE_A instrucciones LLAVE_C'''
    p[0] = Nodo("Funcion", valor=p[2], hijos=(p[6] or []) + (p[4] or [])  + [Nodo("Cuerpo", hijos=p[8])], linea=p.lineno(1))

def p_parametros_opt(p):
    '''parametros_opt : parametros
                      | '''
    p[0] = p[1] if len(p) > 1 else []

def p_parametros(p):
    '''parametros : parametro COMA parametros
                  | parametro'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_parametro(p):
    'parametro : tipo ID'
    p[0] = Nodo("Parametro", valor=p[2], hijos=[p[1]], linea=p.lineno(2))

def p_retorno_opt(p):
    '''retorno_opt : DOSPTOS tipo
                   | '''
    if len(p) == 3:
        p[0] = [p[2]]
    else:
        p[0] = []

# -------------------------------------------------
# Declaraciones de variables
# -------------------------------------------------
def p_declaraciones(p):
    '''declaraciones : declaracion declaraciones
                     | declaracion'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_declaracion(p):
    '''declaracion : tipo lista_vars PUNTOCOMA
                   | CONST tipo ID ASIG expresion PUNTOCOMA'''
    if len(p) == 4:
        p[0] = Nodo("DeclaracionVariable", hijos=[p[1]] + p[2], linea=p.lineno(1))
    else:
        p[0] = Nodo("Constante", valor=p[3], hijos=[p[2]] + [p[5]], linea=p.lineno(1))

def p_lista_vars(p):
    'lista_vars : var_inicializada mas_vars'
    p[0] = [p[1]] + p[2]

def p_var_inicializada(p):
    '''var_inicializada : ID
                        | ID ASIG expresion'''
    if len(p) == 2:
        p[0] = Nodo("Identificador", valor=p[1], linea=p.lineno(1))
    else:
        p[0] = Nodo("AsignacionInicial", valor=p[1], hijos=[p[3]], linea=p.lineno(1))

def p_mas_vars(p):
    '''mas_vars : COMA var_inicializada mas_vars
                | '''
    if len(p) == 4:
        p[0] = [p[2]] + p[3]
    else:
        p[0] = []

# ----- Tipos -----
def p_tipo(p):
    '''tipo : TIPO
            | TIPO COR_A tamanio_opt COR_C'''
    if len(p) == 2:
        p[0] = Nodo("Tipo", valor=p[1], linea=p.lineno(1))
    else:
        p[0] = Nodo("TipoArray", valor=p[1], hijos=p[3], linea=p.lineno(1))

def p_tamanio_opt(p):
    '''tamanio_opt : ENTERO
                   | '''
    if len(p) == 2:
        p[0] = [Nodo("TamanoArray", valor=p[1])]
    else:
        p[0] = []

# -------------------------------------------------
# Instrucciones
# -------------------------------------------------
def p_instrucciones(p):
    '''instrucciones : instruccion instrucciones
                     | instruccion'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_instruccion(p):
    '''instruccion : declaracion
                   | asignacion
                   | llamada_funcion PUNTOCOMA
                   | if_instr
                   | while_instr
                   | until_instr
                   | for_instr
                   | foreach_instr
                   | do_while_instr
                   | switch_instr
                   | PASS PUNTOCOMA
                   | CONTINUE PUNTOCOMA
                   | BREAK PUNTOCOMA
                   | RETURN expresion_opt PUNTOCOMA
                   | inc_dec PUNTOCOMA'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p.slice[1].type in ['PASS', 'CONTINUE', 'BREAK']:
            p[0] = Nodo("InstruccionSimple", valor=p[1], linea=p.lineno(1))
        else:
            p[0] = p[1]
    else:
        p[0] = Nodo("Return", hijos=[p[2]], linea=p.lineno(1))

# Asignación
def p_asignacion(p):
    'asignacion : lvalue ASIG expresion PUNTOCOMA'
    p[0] = Nodo("AsignacionVariable", hijos=[p[1], p[3]], linea=p.lineno(2))

def p_lvalue(p):
    '''lvalue : ID
              | ID COR_A expresion COR_C'''
    if len(p) == 2:
        p[0] = Nodo("Identificador", valor=p[1], linea=p.lineno(1))
    else:
        p[0] = Nodo("ArrayAccess", valor=p[1], hijos=[p[3]], linea=p.lineno(1))

def p_expresion_opt(p):
    '''expresion_opt : expresion
                     | '''
    p[0] = p[1] if len(p) > 1 else []

def p_llamada_funcion(p):
    '''llamada_funcion : ID PAREN_A argumentos_opt PAREN_C'''
    p[0] = Nodo("LlamadaFuncion", valor=p[1], hijos=p[3] or [], linea=p.lineno(1))

def p_argumentos_opt(p):
    '''argumentos_opt : argumentos
                      | '''
    p[0] = p[1] if len(p) > 1 else []

def p_argumentos(p):
    '''argumentos : expresion COMA argumentos
                  | expresion'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

# -------------------------------------------------
# Estructuras de control
# -------------------------------------------------
def p_if_instr(p):
    '''if_instr : IF COR_A expresion COR_C THEN instrucciones elif_opt else_opt FI'''
    hijos_if = [p[3], Nodo("Cuerpo", hijos=p[6])]

    h_elif = p[7] if isinstance(p[7], list) else []
    h_else = p[8] if isinstance(p[8], list) else []

    p[0] = Nodo("If", hijos=hijos_if + h_elif + h_else, linea=p.lineno(1))

def p_elif_opt(p):
    '''elif_opt : elif_instrs
                | '''
    p[0] = p[1] if len(p) > 1 else []

def p_elif_instrs(p):
    '''elif_instrs : elif elif_instrs
                   | elif'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_elif(p):
    '''elif : ELIF COR_A expresion COR_C THEN instrucciones'''
    p[0] = Nodo("Elif", hijos=[p[3], Nodo("Cuerpo", hijos=p[6])])

def p_else_opt(p):
    '''else_opt : ELSE THEN instrucciones
                | '''
    if len(p) == 4:
        p[0] = [Nodo("Else", hijos=[Nodo("Cuerpo", hijos=p[3])])]
    else:
        p[0] = []

def p_while_instr(p):
    'while_instr : WHILE COR_A expresion COR_C DO instrucciones DONE'
    p[0] = Nodo("While", hijos=[p[3]] + [Nodo("Cuerpo", hijos=p[6])], linea=p.lineno(1))

def p_until_instr(p):
    'until_instr : UNTIL COR_A expresion COR_C DO instrucciones DONE'
    p[0] = Nodo("Until", hijos=[p[3]] + [Nodo("Cuerpo", hijos=p[6])], linea=p.lineno(1))

def p_do_while_instr(p):
    'do_while_instr : DO instrucciones DONE WHILE COR_A expresion COR_C PUNTOCOMA'
    p[0] = Nodo("DoWhile", hijos=[p[6]] + [Nodo("Cuerpo", hijos=p[2])], linea=p.lineno(1))

def p_for_instr(p):
    'for_instr : FOR PAREN_A asignacion_for_opt PUNTOCOMA condicion_opt PUNTOCOMA actualizacion_opt PAREN_C DO instrucciones DONE'
    asignacion = p[3]
    condicion = p[5]
    actualizacion = p[7]
    
    children = []

    if isinstance(asignacion, list):
        children += asignacion
    elif asignacion:
        children.append(asignacion)

    if isinstance(condicion, list):
        children += condicion
    elif condicion:
        children.append(condicion)

    if isinstance(actualizacion, list):
        children += actualizacion
    elif actualizacion:
        children.append(actualizacion)

    cuerpo = Nodo("Cuerpo", hijos=p[10])

    p[0] = Nodo("For", hijos=children + [cuerpo], linea=p.lineno(1))

def p_asignacion_for_opt(p):
    '''asignacion_for_opt : asignacion_no_pc
                          | TIPO lista_vars_for
                          | '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = Nodo("InicializacionFor", valor=p[1], hijos=p[2], linea=p.lineno(1))
    else:
        p[0] = []

def p_asignacion_no_pc(p):
    'asignacion_no_pc : lvalue ASIG expresion'
    p[0] = Nodo("AsignacionNoPC", hijos=[p[1], p[3]], linea=p.lineno(2))

def p_lista_vars_for(p):
    'lista_vars_for : inicializacion_var_for mas_vars_for'
    p[0] = [p[1]] + p[2]

def p_inicializacion_var_for(p):
    '''inicializacion_var_for : ID ASIG expresion'''
    p[0] = Nodo("AsignacionInicial", valor=p[1], hijos=[p[3]], linea=p.lineno(1))

def p_mas_vars_for(p):
    '''mas_vars_for : COMA inicializacion_var_for mas_vars_for
                    | '''
    if len(p) == 4:
        p[0] = [p[2]] + p[3]
    else:
        p[0] = []

def p_condicion_opt(p):
    '''condicion_opt : expresion
                     | '''
    if len(p) == 2:
        p[0] = Nodo("CondicionFor", hijos=[p[1]])
    else:
        p[0] = []

def p_actualizacion_opt(p):
    '''actualizacion_opt : asignacion_no_pc
                         | inc_dec
                         | '''
    if len(p) == 2:
        p[0] = Nodo("ActualizacionFor", hijos=[p[1]])
    else:
        p[0] = []

def p_foreach_instr(p):
    '''foreach_instr : FOR TIPO ID IN expresion DO instrucciones DONE'''
    p[0] = Nodo("ForEach",
            hijos=[
                Nodo("Tipo", valor=p[2], linea=p.lineno(2)),
                Nodo("Identificador", valor=p[3], linea=p.lineno(3)), 
                p[5],
                Nodo("Cuerpo", hijos=p[7])
            ],
            linea=p.lineno(1))

def p_switch_instr(p):
    'switch_instr : SWITCH PAREN_A expresion PAREN_C THEN case_list default_part FI'
    casos = p[6] if isinstance(p[6], list) else []
    default = p[7] if isinstance(p[7], list) else []
    p[0] = Nodo("Switch", hijos=[p[3]] + casos + default, linea=p.lineno(1))

def p_case_list(p):
    '''case_list : case_clause case_list
                 | case_clause'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_case_clause(p):
    'case_clause : CASE COR_A expresion COR_C DO instrucciones DONE'
    p[0] = Nodo("Case", hijos=[p[3]] + [Nodo("Cuerpo", hijos=p[6])], linea=p.lineno(1))

def p_default_part(p):
    '''default_part : DEFAULT DO instrucciones DONE
                    | '''
    if len(p) == 5:
        p[0] = [Nodo("Default", hijos=[Nodo("Cuerpo", hijos=p[3])], linea=p.lineno(1))]
    else:
        p[0] = []

# -------------------------------------------------
# Expresiones
# -------------------------------------------------
def p_expresion(p):
    '''expresion : expresion_or'''
    p[0] = p[1]

def p_expresion_or(p):
    '''expresion_or : expresion_or OR expresion_and
                    | expresion_and'''
    if len(p) == 4:
        p[0] = Nodo("OperacionBinaria", valor=p[2], hijos=[p[1], p[3]], linea=p.lineno(2))
    else:
        p[0] = p[1]

def p_expresion_and(p):
    '''expresion_and : expresion_and AND expresion_comp
                     | expresion_comp'''
    if len(p) == 4:
        p[0] = Nodo("OperacionBinaria", valor=p[2], hijos=[p[1], p[3]], linea=p.lineno(2))
    else:
        p[0] = p[1]

def p_expresion_comp(p):
    '''expresion_comp : expresion_rel IGUAL expresion_rel
                      | expresion_rel DIF expresion_rel
                      | expresion_rel'''
    if len(p) == 4:
        p[0] = Nodo("OperacionBinaria", valor=p[2], hijos=[p[1], p[3]], linea=p.lineno(2))
    else:
        p[0] = p[1]

def p_expresion_rel(p):
    '''expresion_rel : expresion_add MENOR expresion_add
                     | expresion_add MENOR_IG expresion_add
                     | expresion_add MAYOR expresion_add
                     | expresion_add MAYOR_IG expresion_add
                     | expresion_add'''
    if len(p) == 4:
        p[0] = Nodo("OperacionBinaria", valor=p[2], hijos=[p[1], p[3]], linea=p.lineno(2))
    else:
        p[0] = p[1]

def p_expresion_add(p):
    '''expresion_add : expresion_add MAS expresion_mult
                     | expresion_add MENOS expresion_mult
                     | expresion_mult'''
    if len(p) == 4:
        p[0] = Nodo("OperacionBinaria", valor=p[2], hijos=[p[1], p[3]], linea=p.lineno(2))
    else:
        p[0] = p[1]

def p_expresion_mult(p):
    '''expresion_mult : expresion_mult MUL expresion_unaria
                      | expresion_mult DIV expresion_unaria
                      | expresion_mult MOD expresion_unaria
                      | expresion_unaria'''
    if len(p) == 4:
        p[0] = Nodo("OperacionBinaria", valor=p[2], hijos=[p[1], p[3]], linea=p.lineno(2))
    else:
        p[0] = p[1]

def p_expresion_unaria(p):
    '''expresion_unaria : MAS expresion_primaria %prec UPLUS
                        | MENOS expresion_primaria %prec UMINUS
                        | NOT expresion_primaria
                        | expresion_primaria'''
    if len(p) == 3:
        p[0] = Nodo("OperacionUnaria", valor=p[1], hijos=[p[2]], linea=p.lineno(1))
    else:
        p[0] = p[1]

def p_expresion_primaria(p):
    '''expresion_primaria : termino
                          | PAREN_A expresion PAREN_C'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

def p_termino(p):
    '''termino : llamada_funcion
               | lvalue
               | ENTERO
               | FLOTANTE
               | CADENA
               | CARACTER
               | TRUE
               | FALSE
               | inc_dec
               | array_literal'''
    t = p.slice[1].type
    if t in ['ENTERO', 'FLOTANTE', 'CADENA', 'CARACTER']:
        p[0] = Nodo("Constante", valor=p[1], linea=p.lineno(1))
    elif t == 'TRUE':
        p[0] = Nodo("ConstanteBooleana", valor=True, linea=p.lineno(1))
    elif t == 'FALSE':
        p[0] = Nodo("ConstanteBooleana", valor=False, linea=p.lineno(1))
    else:
        p[0] = p[1]

def p_array_literal(p):
    'array_literal : COR_A array_items_opt COR_C'
    p[0] = Nodo("ArrayLiteral", hijos=p[2] or [], linea=p.lineno(1))

def p_array_items_opt(p):
    '''array_items_opt : expresion mas_array_items_opt
                       | '''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

def p_mas_array_items_opt(p):
    '''mas_array_items_opt : COMA expresion mas_array_items_opt
                           | '''
    if len(p) == 4:
        p[0] = [p[2]] + p[3]
    else:
        p[0] = []

def p_inc_dec(p):
    '''inc_dec : ID DEC
               | ID INC'''
    p[0] = Nodo("PostIncDec", valor=p[2], hijos=[Nodo("Identificador", valor=p[1])], linea=p.lineno(1))


# -------------------------------------------------
# Manejo de errores
# -------------------------------------------------
def p_error(p):
    if p:
        errores_sintacticos.append(f"❌ Error de sintaxis en token '{p.value}' (tipo {p.type}) en línea {p.lineno}")
    else:
        errores_sintacticos.append("❌ Error de sintaxis: fin de entrada inesperado")

# -------------------------------------------------
# Creación del parser
# -------------------------------------------------
parser = yacc(start='programa')

def analisis_sintactico(codigo):
    global errores_sintacticos
    
    errores_sintacticos = []
    lexer, errores_lexicos = crear_lexer()
    errores_lexicos.clear()
    
    lexer.input(codigo)
    arbol = parser.parse(codigo, lexer=lexer)
    
    return arbol, errores_lexicos, errores_sintacticos
